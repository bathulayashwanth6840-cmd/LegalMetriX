# app/services/vision_ocr.py
from google.cloud import vision
from google.cloud.vision_v1 import types
import logging

logger = logging.getLogger(__name__)

_client = None

def get_vision_client() -> vision.ImageAnnotatorClient:
    global _client
    if _client is None:
        _client = vision.ImageAnnotatorClient()
    return _client


def run_ocr(image_bytes: bytes) -> dict:
    """
    Runs Cloud Vision OCR on raw image bytes.
    Returns dict with full_text, per-block text, and confidence signal.
    Raises on API failure — caller decides fallback behavior.
    """
    client = get_vision_client()
    image = types.Image(content=image_bytes)

    response = client.text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    annotations = response.text_annotations
    if not annotations:
        return {"full_text": "", "blocks": [], "confidence": "LOW"}

    full_text = annotations[0].description

    blocks = [
        {
            "text": a.description,
            "bounding_box": [
                {"x": v.x, "y": v.y} for v in a.bounding_poly.vertices
            ],
        }
        for a in annotations[1:]  # first entry is full text, rest are word-level
    ]

    return {
        "full_text": full_text,
        "blocks": blocks,
        "confidence": "HIGH" if full_text.strip() else "LOW",
    }
