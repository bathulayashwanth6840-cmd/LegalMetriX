import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from PIL import Image, ImageOps, ImageEnhance

logger = logging.getLogger(__name__)

def preprocess_image_for_ocr(image_path: str) -> str:
    """
    Advanced preprocessing for legal metrology packaging photos:
    - Fixes EXIF rotation/orientation.
    - Enhances contrast and sharpness for small printed text (MRP, dates, FSSAI).
    - Preserves aspect ratio and clean text boundaries.
    """
    if not os.path.exists(image_path):
        return image_path

    try:
        with Image.open(image_path) as img:
            # 1. Correct EXIF orientation
            corrected = ImageOps.exif_transpose(img)
            if corrected is None:
                corrected = img

            # Convert to RGB
            if corrected.mode != "RGB":
                corrected = corrected.convert("RGB")

            # 2. Downscale if excessively large (e.g. > 1800px) to speed up OCR inference 3x
            max_dim = max(corrected.width, corrected.height)
            if max_dim > 1800:
                scale = 1800.0 / max_dim
                new_w = int(corrected.width * scale)
                new_h = int(corrected.height * scale)
                corrected = corrected.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # 3. Contrast enhancement
            enhancer = ImageEnhance.Contrast(corrected)
            enhanced = enhancer.enhance(1.2)

            # 4. Sharpness enhancement
            sharpener = ImageEnhance.Sharpness(enhanced)
            sharpened = sharpener.enhance(1.2)

            # Write back or save optimized version
            sharpened.save(image_path, format="JPEG", quality=90)
            return image_path
    except Exception as e:
        logger.warning(f"Image preprocessing skipped due to: {e}")
        return image_path


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extracts text from an image.
        Returns a dictionary containing 'raw_text' and 'bounding_boxes'.
        """
        pass


class PaddleOCRProvider(OCRProvider):
    def __init__(self):
        logger.info("Initializing PaddleOCRProvider...")
        self.ocr = None
        self.init_error = None
        try:
            os.environ["FLAGS_enable_pir_api"] = "0"
            from paddleocr import PaddleOCR
            try:
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en', enable_mkldnn=False, show_log=False)
            except Exception:
                try:
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='en', enable_mkldnn=False)
                except Exception:
                    self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("PaddleOCR successfully initialized.")
        except Exception as e:
            self.init_error = f"Failed to initialize PaddleOCR: {e}"
            logger.error(self.init_error)

    def extract_text(self, image_path: str) -> Dict[str, Any]:
        logger.info(f"Processing OCR for image: {image_path}")

        if self.ocr is None:
            logger.error(f"PaddleOCR is not initialized. Reason: {self.init_error}")
            return {"raw_text": "", "bounding_boxes": [], "error": self.init_error or "OCR not initialized"}

        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            return {"raw_text": "", "bounding_boxes": [], "error": "file_not_found"}

        if os.path.getsize(image_path) == 0:
            logger.error(f"Image file is empty: {image_path}")
            return {"raw_text": "", "bounding_boxes": [], "error": "empty_file"}

        try:
            # Preprocess image to enhance small labels
            preprocess_image_for_ocr(image_path)

            try:
                result = self.ocr.ocr(image_path, cls=True)
            except TypeError:
                result = self.ocr.ocr(image_path)

            raw_text_parts = []
            bounding_boxes = []

            def clean_box_coords(b):
                if b is None:
                    return None
                if hasattr(b, "tolist"):
                    return b.tolist()
                if isinstance(b, (list, tuple)):
                    return [clean_box_coords(item) for item in b]
                return b

            if result and isinstance(result, list):
                for page in result:
                    if page is None:
                        continue

                    # PaddleX / PaddleOCR 3.x dict format
                    if isinstance(page, dict) or hasattr(page, "get"):
                        texts = page.get("rec_texts", []) or []
                        scores = page.get("rec_scores", []) or []
                        polys = page.get("rec_polys", page.get("dt_polys", [])) or []
                        for i, text in enumerate(texts):
                            conf = scores[i] if i < len(scores) else 0.85
                            box = polys[i] if i < len(polys) else None
                            raw_text_parts.append(str(text))
                            bounding_boxes.append({
                                "box": clean_box_coords(box),
                                "text": str(text),
                                "confidence": float(conf)
                            })
                        continue

                    # PaddleOCR 2.x list of lines
                    for line in page:
                        if not isinstance(line, list) or len(line) < 2:
                            continue
                        box = line[0]
                        text_info = line[1]
                        if not isinstance(text_info, (tuple, list)) or len(text_info) < 2:
                            continue
                        text = text_info[0]
                        confidence = text_info[1]
                        raw_text_parts.append(str(text))
                        bounding_boxes.append({
                            "box": clean_box_coords(box),
                            "text": str(text),
                            "confidence": float(confidence)
                        })

            raw_text = "\n".join(raw_text_parts)
            logger.info(f"Successfully processed OCR. Extracted {len(bounding_boxes)} text segments.")
            return {
                "raw_text": raw_text,
                "bounding_boxes": bounding_boxes
            }
        except Exception as e:
            logger.error(f"PaddleOCR processing error for {image_path}: {e}")
            return {
                "raw_text": "",
                "bounding_boxes": [],
                "error": str(e)
            }

def get_ocr_provider() -> OCRProvider:
    return PaddleOCRProvider()
