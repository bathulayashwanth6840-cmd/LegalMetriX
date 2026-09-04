# app/services/reconcile.py
from difflib import SequenceMatcher
from typing import Optional

CRITICAL_FIELDS = {
    "mrp",
    "net_quantity",
    "expiry_date",
    "manufacturer_name",
    "manufacturer_address",
}

NON_CRITICAL_FIELDS = {
    "batch_number",
    "country_of_origin",
    "customer_care_details",
}

# Similarity threshold below which two string values count as a discrepancy.
# Tuned loose for addresses/names (OCR noise), tighter for exact-value fields.
FUZZY_MATCH_THRESHOLD = {
    "mrp": 1.0,              # numeric — must match exactly after normalization
    "net_quantity": 0.85,
    "expiry_date": 1.0,      # normalized date — must match exactly
    "manufacturer_name": 0.75,
    "manufacturer_address": 0.65,
    "batch_number": 0.85,
    "country_of_origin": 0.8,
    "customer_care_details": 0.7,
}


def _normalize(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _field_matches(field: str, local_value, gemini_value) -> bool:
    """
    Returns True if the two values are considered consistent.
    local_value/gemini_value come from local_ocr text search and gemini extraction respectively.
    """
    a, b = _normalize(local_value), _normalize(gemini_value)

    if not a or not b:
        # If Gemini found something the raw OCR text doesn't corroborate at all,
        # that's a real discrepancy for critical fields, not a free pass.
        return a == b

    if field == "mrp":
        try:
            return round(float(a.replace(",", "")), 2) == round(float(b.replace(",", "")), 2)
        except ValueError:
            return a == b

    threshold = FUZZY_MATCH_THRESHOLD.get(field, 0.8)
    return _similar(a, b) >= threshold


def reconcile_fields(local_ocr: dict, gemini_extraction: Optional[dict]) -> dict:
    """
    Compares local Cloud Vision OCR text against Gemini's structured extraction.
    Produces the extracted_fields blob consumed by ScanResponse.

    local_ocr: {"full_text": str, "blocks": [...], "confidence": "HIGH"|"LOW"}
    gemini_extraction: dict from extract_fields(), or None if Gemini was unavailable
    """
    full_text_lower = _normalize(local_ocr.get("full_text", ""))

    # --- Case 1: Gemini unavailable -> LOCAL_OCR_ONLY ---
    if gemini_extraction is None:
        return {
            "local_ocr": local_ocr,
            "gemini_extraction": None,
            "detailed_status": "LOCAL_OCR_ONLY",
            "confidence": "LOW",
            "manual_review_required": False,
            "discrepancies": [],
        }

    # --- Case 2: Compare fields ---
    discrepancies: list[str] = []
    critical_discrepancy = False

    for field in CRITICAL_FIELDS | NON_CRITICAL_FIELDS:
        gemini_value = gemini_extraction.get(field)
        if gemini_value is None:
            continue  # nothing to reconcile if Gemini didn't extract it

        # crude presence check: does the raw OCR text corroborate this value at all?
        # (a real implementation may want per-field raw_text anchors, e.g. mrp_raw_text)
        raw_anchor = gemini_extraction.get(f"{field}_raw_text") or gemini_value
        corroborated = _normalize(raw_anchor) in full_text_lower or _field_matches(
            field, raw_anchor, gemini_value
        )

        if not corroborated:
            discrepancies.append(field)
            if field in CRITICAL_FIELDS:
                critical_discrepancy = True

    if critical_discrepancy:
        detailed_status = "MANUAL_REVIEW"
        confidence = "LOW"
        manual_review_required = True
    elif discrepancies:
        detailed_status = "LOW_CONFIDENCE"
        confidence = "MEDIUM"
        manual_review_required = False
    else:
        detailed_status = "VERIFIED"
        confidence = "HIGH"
        manual_review_required = False

    return {
        "local_ocr": local_ocr,
        "gemini_extraction": gemini_extraction,
        "detailed_status": detailed_status,
        "confidence": confidence,
        "manual_review_required": manual_review_required,
        "discrepancies": discrepancies,
    }
