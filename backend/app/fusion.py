import re
import logging
from typing import Dict, Any, Optional, List
from .services.gemini_vision import GeminiProductLabelData

logger = logging.getLogger(__name__)

def normalize_text(text: Optional[str]) -> str:
    """
    Normalize text for comparison: remove all non-alphanumeric characters,
    trailing zeros for decimals, and convert to lowercase.
    """
    if text is None:
        return ""
    text_str = str(text).lower().strip()
    # Normalize currency and spacing
    text_str = re.sub(r'(?:rs\.?|inr|₹|/-)', '', text_str).strip()
    # Normalize common decimal trailing zeros (e.g. 100.00 -> 100)
    text_str = re.sub(r'\.00\b', '', text_str)
    return re.sub(r'[^a-z0-9]', '', text_str)

def fuse_results(
    local_fields: Dict[str, Any],
    gemini_data: Optional[GeminiProductLabelData],
    barcode_result: Optional[Dict[str, Any]] = None,
    evidence_map: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Combines Local OCR + Bounding Box evidence with Gemini Vision results and Barcode data.
    Computes genuine confidences, checks for discrepancies, and builds bounding box evidence mapping.
    """
    logger.info("Fusing OCR, Barcode, Evidence, and Gemini Vision results...")

    fusion_fields: Dict[str, Any] = {}
    evidence_map = evidence_map or {}
    
    # 1. Map Gemini response
    gemini_mapped: Dict[str, Any] = {}
    if gemini_data:
        d = gemini_data
        gemini_mapped["product_name"] = d.product_name or d.brand_name
        gemini_mapped["manufacturer_name"] = d.manufacturer_name or d.packer_name or d.importer_name
        gemini_mapped["manufacturer_address"] = d.manufacturer_address or d.packer_address or d.importer_address
        
        # Quantity
        qty_val = d.net_quantity_value
        qty_unit = d.net_quantity_unit
        gemini_mapped["net_quantity"] = f"{qty_val} {qty_unit}" if qty_val and qty_unit else None
        
        gemini_mapped["mrp"] = d.mrp
        gemini_mapped["mfg_date"] = d.manufacturing_date or d.packing_date
        gemini_mapped["expiry_date"] = d.expiry_date or d.best_before
        gemini_mapped["fssai_number"] = d.fssai_number
        
        # Consumer care
        cc_parts = []
        if d.customer_care_details:
            cc_parts.append(d.customer_care_details)
        if d.consumer_care_email:
            cc_parts.append(d.consumer_care_email)
        if d.consumer_care_phone:
            cc_parts.append(d.consumer_care_phone)
        gemini_mapped["consumer_care"] = ", ".join(cc_parts) if cc_parts else None
        
        gemini_mapped["country_of_origin"] = d.country_of_origin
        gemini_mapped["barcode"] = d.barcode
    else:
        gemini_mapped = {k: None for k in local_fields.keys()}

    important_keys = {"product_name", "net_quantity", "mrp", "mfg_date", "expiry_date", "manufacturer_name", "manufacturer_address", "fssai_number"}
    needs_manual_review = False
    conf_scores: List[float] = []

    all_keys = set(local_fields.keys()).union(gemini_mapped.keys())
    
    for key in all_keys:
        local_val = local_fields.get(key)
        gemini_val = gemini_mapped.get(key)
        field_evidence = evidence_map.get(key, {})
        
        local_norm = normalize_text(local_val)
        gemini_norm = normalize_text(gemini_val)
        
        field_meta = {
            "value": None,
            "selected_value": None,
            "source": "none",
            "agreement": "NONE",
            "status": "NOT_DETECTED",
            "confidence": "low",
            "confidence_score": 50,
            "conflict": False,
            "conflict_reason": None,
            "ocr_value": local_val,
            "gemini_value": gemini_val,
            "source_side": field_evidence.get("source_side", "front"),
            "bounding_box": field_evidence.get("bounding_box"),
            "raw_text_line": field_evidence.get("raw_text_line")
        }
        
        # Barcode Special handling
        if key == "barcode":
            if barcode_result and barcode_result.get("barcode"):
                field_meta["value"] = barcode_result.get("barcode")
                field_meta["selected_value"] = field_meta["value"]
                field_meta["source"] = "barcode_decoder"
                field_meta["agreement"] = "HIGH"
                field_meta["status"] = "VERIFIED"
                field_meta["confidence"] = "high"
                field_meta["confidence_score"] = 98
                fusion_fields[key] = field_meta
                conf_scores.append(98)
                continue
        
        # Case A: Both missing
        if not local_norm and not gemini_norm:
            field_meta["confidence_score"] = 0
            field_meta["confidence"] = "low"
            field_meta["status"] = "NOT_DETECTED"
            field_meta["agreement"] = "NONE"
            
        # Case B: Only Local exists
        elif local_norm and not gemini_norm:
            field_meta["value"] = local_val
            field_meta["selected_value"] = local_val
            field_meta["source"] = "local_ocr"
            field_meta["agreement"] = "SINGLE_SOURCE"
            field_meta["status"] = "EXTRACTED"
            field_meta["confidence"] = "medium"
            field_meta["confidence_score"] = 82
            conf_scores.append(82)
            
        # Case C: Only Gemini exists
        elif gemini_norm and not local_norm:
            field_meta["value"] = gemini_val
            field_meta["selected_value"] = gemini_val
            field_meta["source"] = "gemini_ai"
            field_meta["agreement"] = "SINGLE_SOURCE"
            field_meta["status"] = "EXTRACTED"
            if gemini_data and key in getattr(gemini_data, "uncertain_fields", []):
                field_meta["confidence"] = "low"
                field_meta["confidence_score"] = 60
                if key in important_keys:
                    needs_manual_review = True
            else:
                field_meta["confidence"] = "medium"
                field_meta["confidence_score"] = 88
            conf_scores.append(field_meta["confidence_score"])
                
        # Case D: Both exist
        else:
            if gemini_norm == local_norm or (len(gemini_norm) > 4 and (gemini_norm in local_norm or local_norm in gemini_norm)):
                # Agreed / Double-Verified
                field_meta["value"] = gemini_val if len(str(gemini_val)) >= len(str(local_val)) else local_val
                field_meta["selected_value"] = field_meta["value"]
                field_meta["source"] = "agreed"
                field_meta["agreement"] = "HIGH"
                field_meta["status"] = "VERIFIED"
                field_meta["confidence"] = "high"
                field_meta["confidence_score"] = 96
                conf_scores.append(96)
            else:
                # Conflict detected - preserve both values without silent overwrite
                field_meta["value"] = local_val or gemini_val
                field_meta["selected_value"] = field_meta["value"]
                field_meta["source"] = "conflict"
                field_meta["agreement"] = "CONFLICT"
                field_meta["status"] = "NEEDS_MANUAL_REVIEW"
                field_meta["confidence"] = "low"
                field_meta["confidence_score"] = 55
                field_meta["conflict"] = True
                field_meta["conflict_reason"] = f"Disagreement: Local OCR parsed '{local_val}', but Gemini AI parsed '{gemini_val}'"
                conf_scores.append(55)
                needs_manual_review = True
                    
        fusion_fields[key] = field_meta

    final_flat_fields = {k: v["value"] for k, v in fusion_fields.items()}
    avg_extraction_conf = int(round(sum(conf_scores) / len(conf_scores))) if conf_scores else 75

    return {
        "flat_fields": final_flat_fields,
        "fusion_fields": fusion_fields,
        "evidence_map": evidence_map,
        "needs_manual_review": needs_manual_review,
        "extraction_confidence": avg_extraction_conf
    }

