import os
import hashlib
import logging
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# In-memory cache keyed by SHA-256 hash of image contents + schema version
_GEMINI_EXTRACTION_CACHE: Dict[str, "GeminiProductLabelData"] = {}

class GeminiProductLabelData(BaseModel):
    product_name: Optional[str] = Field(None, description="The generic or brand name of the product. Only return if visibly printed on packaging; do NOT guess.")
    brand_name: Optional[str] = Field(None, description="The brand name of the product if visibly printed.")
    manufacturer_name: Optional[str] = Field(None, description="Name of the manufacturer. Only return if visibly printed on packaging.")
    manufacturer_address: Optional[str] = Field(None, description="Complete manufacturer address including PIN code if visible.")
    packer_name: Optional[str] = Field(None, description="Name of the packer if applicable.")
    packer_address: Optional[str] = Field(None, description="Complete packer address if visible.")
    importer_name: Optional[str] = Field(None, description="Name of the importer if applicable.")
    importer_address: Optional[str] = Field(None, description="Complete importer address if visible.")
    mrp: Optional[str] = Field(None, description="Maximum Retail Price in numerical form, e.g. '100' or '25.00'. Never guess.")
    currency: Optional[str] = Field(None, description="Currency of MRP, e.g. 'INR', '₹'")
    tax_inclusive: Optional[bool] = Field(None, description="Whether MRP is inclusive of all taxes")
    net_quantity_value: Optional[str] = Field(None, description="Value of net quantity, e.g. '70' or '1'")
    net_quantity_unit: Optional[str] = Field(None, description="Unit of net quantity, e.g. 'g', 'kg', 'ml', 'L'")
    unit_sale_price: Optional[str] = Field(None, description="Declared unit sale price if visible")
    manufacturing_date: Optional[str] = Field(None, description="Date of manufacturing/packing, e.g. '08/2026'")
    packing_date: Optional[str] = Field(None, description="Date of packing, e.g. '08/2026'")
    expiry_date: Optional[str] = Field(None, description="Date of expiry, e.g. '08/2027'")
    best_before: Optional[str] = Field(None, description="Best before declaration statement, e.g. '6 Months from manufacture'")
    customer_care_details: Optional[str] = Field(None, description="General customer care contact details")
    country_of_origin: Optional[str] = Field(None, description="Country of origin, e.g. 'India'")
    consumer_care_email: Optional[str] = Field(None, description="Customer care email address")
    consumer_care_phone: Optional[str] = Field(None, description="Customer care phone number")
    fssai_number: Optional[str] = Field(None, description="14-digit FSSAI license number")
    barcode: Optional[str] = Field(None, description="Barcode number if visible (e.g. EAN13)")
    declared_usp: Optional[str] = Field(None, description="Declared Unit Sale Price text")
    raw_text: Optional[str] = Field(None, description="All raw text visible on the label")
    uncertain_fields: List[str] = Field(default_factory=list, description="List of field names where text is blurry, truncated, or uncertain")


class GeminiVisionService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY environment variable is not set. Gemini service will be unavailable.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("GeminiVisionService successfully initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None

    def _compute_images_hash(self, image_bytes_list: List[bytes]) -> str:
        hasher = hashlib.sha256()
        for b in image_bytes_list:
            hasher.update(b)
        hasher.update(b"v2_strict_schema")
        return hasher.hexdigest()

    def analyze_product_label(self, image_input: Union[str, List[str]]) -> Optional[GeminiProductLabelData]:
        if not self.client:
            logger.warning("Gemini Client is not available. Skipping AI analysis.")
            return None

        # Normalize input to list of paths
        if isinstance(image_input, str):
            image_paths = [image_input]
        elif isinstance(image_input, list):
            image_paths = [p for p in image_input if p and isinstance(p, str)]
        else:
            logger.error(f"Invalid image input type for Gemini: {type(image_input)}")
            return None

        image_parts = []
        raw_bytes_list = []
        for path in image_paths:
            if not os.path.exists(path):
                logger.warning(f"Image file does not exist: {path}")
                continue

            try:
                with open(path, "rb") as f:
                    image_bytes = f.read()

                if not image_bytes:
                    continue

                raw_bytes_list.append(image_bytes)
                ext = path.split(".")[-1].lower()
                mime_type = "image/jpeg"
                if ext == "png":
                    mime_type = "image/png"
                elif ext == "webp":
                    mime_type = "image/webp"

                part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type
                )
                image_parts.append(part)
            except Exception as read_err:
                logger.warning(f"Failed to load image part from {path}: {read_err}")

        if not image_parts:
            logger.error("No valid image parts available for Gemini Vision analysis.")
            return None

        # Check Cache to prevent duplicate Gemini API billing
        cache_key = self._compute_images_hash(raw_bytes_list)
        if cache_key in _GEMINI_EXTRACTION_CACHE:
            logger.info(f"Returning cached Gemini extraction result for hash {cache_key[:12]} (API call prevented).")
            return _GEMINI_EXTRACTION_CACHE[cache_key]

        try:
            prompt = (
                "You are an AI assistant for Legal Metrology Packaged Commodity Enforcement Officers.\n"
                "CRITICAL MANDATE: Only extract information visibly supported by the provided image or packaging. "
                "Never infer, guess, or invent missing values. If a value is not visible or cannot be reliably extracted, "
                "return null or add the field name to 'uncertain_fields'. Never hallucinate brand names, addresses, or prices.\n\n"
                "Instructions:\n"
                "1. Read text from all visible packaging panels (Front, Back, Left, Right).\n"
                "2. Accurately identify MRP (Maximum Retail Price in INR/Rupees, inclusive of taxes).\n"
                "3. Accurately distinguish manufacturing date, packing date, and expiry/best-before dates.\n"
                "4. Extract net quantity numerical value and standard unit (g, kg, ml, L, N) separately.\n"
                "5. Identify complete manufacturer/packer/importer names and complete registered postal address with PIN.\n"
                "6. Identify consumer care contact details (telephone, email, postal address).\n"
                "7. Identify 14-digit FSSAI license numbers and retail barcode numbers (EAN-13, UPC).\n"
                "8. If any declaration is blurry, truncated, or absent, set it to null and append to 'uncertain_fields'."
            )

            contents = list(image_parts)
            contents.append(prompt)

            logger.info(f"Sending {len(image_parts)} consolidated image(s) to Gemini API (gemini-2.5-flash)...")
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiProductLabelData,
                    temperature=0.1
                )
            )

            if not response.text:
                logger.error("Received empty response from Gemini API.")
                return None

            parsed_data = GeminiProductLabelData.model_validate_json(response.text)
            
            # Post-validation: ensure null/unknown strings are standardized
            for attr in ["product_name", "manufacturer_name", "manufacturer_address", "mrp", "net_quantity_value"]:
                val = getattr(parsed_data, attr, None)
                if val and str(val).strip().upper() in {"NULL", "NONE", "UNKNOWN", "NOT_DETECTED", "N/A"}:
                    setattr(parsed_data, attr, None)

            # Store in cache
            _GEMINI_EXTRACTION_CACHE[cache_key] = parsed_data
            logger.info("Successfully received and validated structured response from Gemini API.")
            return parsed_data

        except Exception as e:
            logger.error(f"Error during Gemini Vision analysis: {e}", exc_info=True)
            return None

