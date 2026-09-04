import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FieldExtractor:
    """
    Advanced context-aware, multi-side packaged goods label extractor.
    Extracts structured fields from raw OCR text with fuzzy variations,
    field-level confidence, and bounding box evidence mapping.
    """

    def normalize_text(self, text: str) -> List[str]:
        """
        Clean OCR text and return non-empty normalized lines.
        """
        if not text:
            return []
        lines = []
        for line in text.split("\n"):
            cleaned = re.sub(r"\s+", " ", line).strip()
            if cleaned:
                lines.append(cleaned)
        return lines

    def extract_from_multi_side_ocr(
        self,
        sides_ocr: Dict[str, Dict[str, Any]],
        barcode_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Combines and extracts information across multiple sides (Front, Back, Left, Right).
        Tracks the source side and bounding box evidence for each field.
        """
        all_lines_with_meta: List[Dict[str, Any]] = []
        full_text_parts = []

        for side, ocr_data in sides_ocr.items():
            if not ocr_data:
                continue
            text = ocr_data.get("full_text", "")
            boxes = ocr_data.get("bounding_boxes", [])
            lines = self.normalize_text(text)

            if lines:
                full_text_parts.append(f"--- [{side.upper()} SIDE] ---\n" + "\n".join(lines))

            # Pair lines with bounding boxes if available
            for idx, line in enumerate(lines):
                box = None
                conf = 0.85
                if idx < len(boxes):
                    b_item = boxes[idx]
                    box = b_item.get("box")
                    conf = b_item.get("confidence", 0.85)
                all_lines_with_meta.append({
                    "line": line,
                    "side": side,
                    "box": box,
                    "confidence": conf
                })

        combined_text = "\n\n".join(full_text_parts)
        return self.extract_fields_with_evidence(all_lines_with_meta, combined_text, barcode_result)

    def extract_fields(self, raw_text: str, barcode_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fallback extraction from single raw text string.
        """
        lines = self.normalize_text(raw_text)
        lines_with_meta = [{"line": l, "side": "front", "box": None, "confidence": 0.85} for l in lines]
        return self.extract_fields_with_evidence(lines_with_meta, raw_text, barcode_result)

    def extract_fields_with_evidence(
        self,
        lines_with_meta: List[Dict[str, Any]],
        full_text: str,
        barcode_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Performs extraction with evidence tracking (source side, bounding box, confidence).
        """
        lines = [item["line"] for item in lines_with_meta]

        extracted = {
            "product_name": None,
            "generic_name": None,
            "manufacturer_name": None,
            "manufacturer_address": None,
            "packer_name": None,
            "packer_address": None,
            "importer_name": None,
            "importer_address": None,
            "net_quantity": None,
            "net_quantity_value": None,
            "net_quantity_unit": None,
            "mrp": None,
            "mrp_currency": "INR",
            "tax_inclusive": True,
            "mfg_date": None,
            "packing_date": None,
            "expiry_date": None,
            "best_before": None,
            "fssai_number": None,
            "consumer_care": None,
            "consumer_care_phone": None,
            "consumer_care_email": None,
            "consumer_care_address": None,
            "country_of_origin": None,
            "batch_number": None,
            "unit_sale_price": None,
            "barcode": barcode_result.get("barcode") if barcode_result else None
        }

        # Evidence dictionary storing { field_key: { value, side, box, confidence, raw_evidence } }
        evidence: Dict[str, Any] = {}

        def record_evidence(key: str, val: str, meta_idx: int, conf_boost: float = 0.0):
            if not val:
                return
            meta = lines_with_meta[meta_idx] if 0 <= meta_idx < len(lines_with_meta) else {}
            base_conf = float(meta.get("confidence", 0.85))
            final_conf = min(0.99, max(0.50, base_conf + conf_boost))
            evidence[key] = {
                "value": val,
                "source_side": meta.get("side", "primary"),
                "bounding_box": meta.get("box"),
                "ocr_confidence": round(final_conf * 100, 1),
                "raw_text_line": meta.get("line", "")
            }

        # ============================================================
        # 1. MRP (Maximum Retail Price)
        # ============================================================
        mrp_patterns = [
            # Standard: MRP Rs. 100 / MRP ₹ 100.00 / M.R.P. Rs 100/-
            re.compile(
                r"(?:MRP|M\.R\.P\.?|Maximum\s+Retail\s+Price|Max\.?\s*Retail\s*Price)"
                r"[\s:.\-]*"
                r"(?:Rs\.?|INR|₹)?\s*"
                r"([\d,]+(?:\.\d{1,2})?)\s*"
                r"(?:/\-|\s*\(?\s*incl(?:usive)?\.?\s*of\s*all\s*taxes\s*\)?)?",
                re.IGNORECASE
            ),
            # Symbol first: ₹ 100 / Rs. 100 (incl of taxes)
            re.compile(
                r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)\s*"
                r"(?:/\-|\s*\(?\s*incl(?:usive)?\.?\s*of\s*all\s*taxes\s*\)?)",
                re.IGNORECASE
            ),
            # Loose MRP token
            re.compile(r"\bMRP\s*[:.\-]?\s*([\d,]+(?:\.\d{1,2})?)\b", re.IGNORECASE)
        ]

        for i, line in enumerate(lines):
            for pat in mrp_patterns:
                match = pat.search(line)
                if match:
                    val = match.group(1).replace(",", "").strip()
                    try:
                        num = float(val)
                        if 0.5 <= num <= 500000:
                            extracted["mrp"] = f"{num:.2f}" if "." in val else f"{int(num)}"
                            record_evidence("mrp", extracted["mrp"], i, 0.1)
                            break
                    except ValueError:
                        pass
            if extracted["mrp"]:
                break

        # ============================================================
        # 2. NET QUANTITY
        # ============================================================
        net_qty_patterns = [
            # Standard: Net Qty: 200 g / Net Weight: 1 kg / Net Content 500 ml / Net Wt. 250g
            re.compile(
                r"(?:Net\s*(?:Qty|Quantity|Wt|Weight|Content|Volume|Mass)?|N\.?\s*W\.?)"
                r"[\s:.\-]*"
                r"(\d+(?:\.\d+)?)\s*"
                r"(kg|g|gm|gms|mg|ml|l|litre|litres|liter|liters|unit|units|N|U)\b",
                re.IGNORECASE
            ),
            # Direct unit pattern: 200 g / 500 ml when preceded by net or weight
            re.compile(
                r"\b(\d+(?:\.\d+)?)\s*(kg|g|gm|gms|mg|ml|l|litre|litres|liter|liters)\b\s*(?:when\s*packed|at\s*packaging)?",
                re.IGNORECASE
            ),
            # Count pattern: Net Qty: 10 Units / 1 N
            re.compile(
                r"(?:Net\s*Quantity|Qty)[\s:.\-]*(\d+)\s*(?:N|U|Units|Pieces|Nos\.?)\b",
                re.IGNORECASE
            )
        ]

        for i, line in enumerate(lines):
            for pat in net_qty_patterns:
                match = pat.search(line)
                if match:
                    val_str = match.group(1).strip()
                    unit_str = match.group(2).strip().lower() if len(match.groups()) >= 2 else "N"
                    
                    # Normalize unit
                    unit_norm_map = {
                        "gm": "g", "gms": "g", "g": "g", "kg": "kg", "mg": "mg",
                        "ml": "ml", "l": "L", "litre": "L", "litres": "L", "liter": "L", "liters": "L",
                        "unit": "N", "units": "N", "pieces": "N", "nos": "N", "nos.": "N", "u": "N", "n": "N"
                    }
                    normalized_unit = unit_norm_map.get(unit_str, unit_str)
                    extracted["net_quantity_value"] = val_str
                    extracted["net_quantity_unit"] = normalized_unit
                    extracted["net_quantity"] = f"{val_str} {normalized_unit}"
                    record_evidence("net_quantity", extracted["net_quantity"], i, 0.1)
                    break
            if extracted["net_quantity"]:
                break

        # ============================================================
        # 3. MANUFACTURING / PACKING DATE
        # ============================================================
        mfg_patterns = [
            re.compile(
                r"(?:MFG|MFD|MFD\.|Manufactured|Manufacturing\s*Date|Packed\s*On|PKD|PKG|Packing\s*Date|Date\s*of\s*Packing)"
                r"[\s:.\-]*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s*[-/]?\s*\d{2,4}|\d{2,4}[/-]\d{1,2})",
                re.IGNORECASE
            )
        ]

        for i, line in enumerate(lines):
            for pat in mfg_patterns:
                match = pat.search(line)
                if match:
                    extracted["mfg_date"] = match.group(1).strip()
                    extracted["packing_date"] = extracted["mfg_date"]
                    record_evidence("mfg_date", extracted["mfg_date"], i, 0.08)
                    break
            if extracted["mfg_date"]:
                break

        # ============================================================
        # 4. EXPIRY DATE / BEST BEFORE / USE BY
        # ============================================================
        exp_patterns = [
            # Explicit date: EXP: 01/2027 / Expiry Date: 12/26 / Use By: 15/08/2026
            re.compile(
                r"(?:EXP|EXP\.?|Expiry|Expiry\s*Date|EXP\s*Date|Use\s*By|Use\s*Before)"
                r"[\s:.\-]*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s*[-/]?\s*\d{2,4})",
                re.IGNORECASE
            ),
            # Relative statement: Best Before 12 Months from PKD / Best before 6 months from manufacture
            re.compile(
                r"(?:Best\s*Before|Best\s*by)[\s:.\-]*(\d+\s*(?:months?|days?|years?)\s*(?:from\s*(?:mfg|mfd|pkd|packaging|manufacture|packing))?)",
                re.IGNORECASE
            ),
            re.compile(
                r"(?:Best\s*Before)[\s:.\-]*([A-Za-z0-9\s/.\-]+)",
                re.IGNORECASE
            )
        ]

        for i, line in enumerate(lines):
            for pat in exp_patterns:
                match = pat.search(line)
                if match:
                    val = match.group(1).strip()
                    if len(val) >= 4:
                        extracted["expiry_date"] = val
                        extracted["best_before"] = val
                        record_evidence("expiry_date", val, i, 0.08)
                        break
            if extracted["expiry_date"]:
                break

        # ============================================================
        # 5. FSSAI LICENSE NUMBER (14 digits)
        # ============================================================
        fssai_patterns = [
            re.compile(r"(?:FSSAI|Lic\.?\s*No\.?|License\s*No\.?)[\s:.\-]*(\d{14})\b", re.IGNORECASE),
            re.compile(r"\b(1\d{13})\b") # 14-digit starting with 1
        ]

        for i, line in enumerate(lines):
            for pat in fssai_patterns:
                match = pat.search(line)
                if match:
                    extracted["fssai_number"] = match.group(1).strip()
                    record_evidence("fssai_number", extracted["fssai_number"], i, 0.15)
                    break
            if extracted["fssai_number"]:
                break

        # ============================================================
        # 6. CONSUMER CARE / CUSTOMER CARE
        # ============================================================
        phone_match = re.search(r"(?:Toll\s*Free|Helpline|Tel|Phone|Ph|Call)[\s:.\-]*(\+?91[\s-]?)?([1800\d\s-]{10,14})\b", full_text, re.IGNORECASE)
        email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", full_text)

        care_lines = []
        for i, line in enumerate(lines):
            if re.search(r"(?:Customer|Consumer)\s*Care|Feedback|Complaints|Contact\s*Us|Write\s*to", line, re.IGNORECASE):
                care_lines.append(line)
                record_evidence("consumer_care", line, i, 0.08)

        if phone_match:
            extracted["consumer_care_phone"] = phone_match.group(0).strip()
        if email_match:
            extracted["consumer_care_email"] = email_match.group(1).strip()

        if care_lines or phone_match or email_match:
            parts = []
            if care_lines:
                parts.append(" ".join(care_lines[:2]))
            if email_match:
                parts.append(email_match.group(1))
            if phone_match:
                parts.append(phone_match.group(0))
            extracted["consumer_care"] = " | ".join(parts) if parts else "Customer Care Details Declared"

        # ============================================================
        # 7. COUNTRY OF ORIGIN
        # ============================================================
        origin_patterns = [
            re.compile(r"(?:Country\s*of\s*Origin|Origin|Made\s*in|Product\s*of)[\s:.\-]*([A-Za-z\s]+)\b", re.IGNORECASE),
            re.compile(r"\b(Made\s*in\s*India|Product\s*of\s*India)\b", re.IGNORECASE)
        ]

        for i, line in enumerate(lines):
            for pat in origin_patterns:
                match = pat.search(line)
                if match:
                    extracted["country_of_origin"] = match.group(1).strip()
                    record_evidence("country_of_origin", extracted["country_of_origin"], i, 0.1)
                    break
            if extracted["country_of_origin"]:
                break

        # ============================================================
        # 8. MANUFACTURER / PACKER / IMPORTER NAME & ADDRESS
        # ============================================================
        mfg_header_idx = -1
        for i, line in enumerate(lines):
            if re.search(r"(?:Mfg\s*by|Manufactured\s*(?:by|&)|Packed\s*by|Marketed\s*by|Imported\s*by|Mfd\s*By)", line, re.IGNORECASE):
                mfg_header_idx = i
                # Strip prefix
                mfg_name = re.sub(r"^(?:Mfg\s*by|Manufactured\s*(?:by|&)|Packed\s*by|Marketed\s*by|Imported\s*by|Mfd\s*By)[\s:.\-]*", "", line, flags=re.IGNORECASE).strip()
                if len(mfg_name) > 3:
                    extracted["manufacturer_name"] = mfg_name
                    record_evidence("manufacturer_name", mfg_name, i, 0.08)
                break

        # Look for address in subsequent lines
        if mfg_header_idx != -1:
            addr_parts = []
            for j in range(mfg_header_idx + 1, min(len(lines), mfg_header_idx + 5)):
                l = lines[j]
                # Stop if hitting another header
                if re.search(r"^(?:MRP|Net\s*Qty|EXP|MFG|FSSAI|Batch|Customer)", l, re.IGNORECASE):
                    break
                addr_parts.append(l)
            if addr_parts:
                extracted["manufacturer_address"] = ", ".join(addr_parts)
                record_evidence("manufacturer_address", extracted["manufacturer_address"], mfg_header_idx + 1, 0.05)

        # General pincode search for address if missing
        if not extracted["manufacturer_address"]:
            pin_match = re.search(r"(?:Pincode|Pin|Dist\.?)?[\s:.\-]*(\d{6})\b", full_text)
            if pin_match:
                extracted["manufacturer_address"] = f"Address with Pin {pin_match.group(1)}"

        # ============================================================
        # 9. PRODUCT NAME / BRAND NAME
        # ============================================================
        for i, line in enumerate(lines[:6]):
            # Skip obvious header tags or numeric lines
            if re.search(r"^(?:MRP|Net|MFG|EXP|FSSAI|Lic|Batch|Best|Made|---)", line, re.IGNORECASE):
                continue
            if len(line) >= 3 and not re.match(r"^[\d\s:.,/\-]+$", line):
                clean_name = re.sub(r"^(?:Product(?:\s*Name)?|Brand(?:\s*Name)?|Item(?:\s*Name)?)[\s:.\-]*", "", line, flags=re.IGNORECASE).strip()
                if len(clean_name) >= 3:
                    extracted["product_name"] = clean_name
                    extracted["generic_name"] = clean_name
                    record_evidence("product_name", clean_name, i, 0.05)
                    break

        # ============================================================
        # 10. BATCH NUMBER
        # ============================================================
        batch_match = re.search(r"(?:Batch\s*No\.?|Lot\s*No\.?|B\.?\s*No\.?)[\s:.\-]*([A-Za-z0-9\-_]+)", full_text, re.IGNORECASE)
        if batch_match:
            extracted["batch_number"] = batch_match.group(1).strip()

        # Build response with structured fields and evidence map
        return {
            "fields": extracted,
            "evidence": evidence,
            "full_text": full_text
        }