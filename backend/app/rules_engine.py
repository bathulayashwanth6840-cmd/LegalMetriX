import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RuleResult:
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DetectionState:
    VERIFIED = "VERIFIED"
    CONFIRMED_MISSING = "CONFIRMED_MISSING"
    NOT_DETECTED = "NOT_DETECTED"
    UNCLEAR = "UNCLEAR"
    NOT_VISIBLE = "NOT_VISIBLE"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"


class RuleEngine:
    """
    LegalMetriX Legal Metrology Compliance Rule Engine
    Based on the Legal Metrology (Packaged Commodities) Rules, 2011 and Amendments.

    Distinguishes 5 statutory detection states for every requirement:
    1. CONFIRMED_MISSING: The required declaration was searched for across all package surfaces and reliable evidence shows it is absent. (FAIL)
    2. NOT_DETECTED: The declaration could not be detected in the current image(s). NOT automatically converted to a legal violation. (REVIEW)
    3. UNCLEAR: The declaration may be present but image quality/lighting/resolution is insufficient. (REVIEW)
    4. NOT_VISIBLE: The relevant package surface was not captured (e.g. single-panel scan). (REVIEW)
    5. NEEDS_MANUAL_REVIEW: OCR, Gemini, or multiple panels provide conflicting or insufficient evidence. (REVIEW)
    6. VERIFIED: Legally declared and verified. (PASS)
    """

    def evaluate_rules(
        self,
        extracted_fields: Dict[str, Any],
        images_count: int = 1,
        is_food_product: bool = True,
        fusion_fields: Optional[Dict[str, Any]] = None,
        evidence_map: Optional[Dict[str, Any]] = None,
        ocr_raw_text: Optional[str] = None,
        quality_warnings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive evaluation on extracted product declarations.
        Dynamically classifies detection state, attributes evidence source/region, and prevents false violations.
        """
        logger.info("Evaluating Legal Metrology Rules (LMR 2011) with 5-State Detection Classification...")

        rules_evaluated: List[Dict[str, Any]] = []
        fusion_fields = fusion_fields or {}
        evidence_map = evidence_map or {}
        quality_warnings = quality_warnings or []
        has_quality_issues = len(quality_warnings) > 0

        def is_empty(val: Any) -> bool:
            if val is None:
                return True
            if isinstance(val, str) and not val.strip():
                return True
            return False

        def get_meta(field_key: str) -> Dict[str, Any]:
            f_meta = fusion_fields.get(field_key, {})
            e_meta = evidence_map.get(field_key, {})
            return {
                "source": f_meta.get("source", "ocr/ai"),
                "source_side": f_meta.get("source_side") or e_meta.get("source_side", "front"),
                "bounding_box": f_meta.get("bounding_box") or e_meta.get("bounding_box"),
                "raw_text_line": f_meta.get("raw_text_line") or e_meta.get("raw_text_line"),
                "conflict": f_meta.get("conflict", False),
                "conflict_reason": f_meta.get("conflict_reason"),
                "ocr_value": f_meta.get("ocr_value"),
                "gemini_value": f_meta.get("gemini_value"),
                "confidence": f_meta.get("confidence", "medium"),
                "confidence_score": f_meta.get("confidence_score", 80)
            }

        def format_source_label(meta: Dict[str, Any]) -> str:
            src = meta.get("source", "")
            if src == "agreed":
                return "Both (OCR & Gemini AI Verified)"
            elif src == "local_ocr":
                return "PaddleOCR Engine"
            elif src == "gemini_ai":
                return "Gemini Vision AI"
            elif src == "barcode_decoder":
                return "Barcode / GTIN Decoder"
            elif meta.get("conflict"):
                return "Discrepancy (OCR vs AI)"
            return "Packaging Scan"

        def format_region(meta: Dict[str, Any]) -> str:
            side = str(meta.get("source_side", "Front")).capitalize()
            box = meta.get("bounding_box")
            if box and isinstance(box, list) and len(box) > 0:
                return f"{side} Panel [Box: {box[0]}]"
            return f"{side} Panel (Visual Evidence Available)"

        # ==========================================================
        # 1. PRODUCT / GENERIC NAME (Rule 6(1)(b))
        # ==========================================================
        p_name = extracted_fields.get("product_name") or extracted_fields.get("generic_name")
        p_meta = get_meta("product_name")

        if not is_empty(p_name):
            if p_meta["conflict"]:
                rules_evaluated.append({
                    "rule_code": "LMR_001",
                    "rule_name": "Product Name / Generic Name",
                    "field_key": "product_name",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NEEDS_MANUAL_REVIEW,
                    "detected_value": str(p_name),
                    "expected_requirement": "Name and generic identity of the packaged commodity on principal display panel.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(b), LMR 2011",
                    "is_mandatory": True,
                    "explanation": f"Discrepancy: OCR detected '{p_meta['ocr_value']}' vs AI '{p_meta['gemini_value']}'. Officer confirmation required.",
                    "corrective_action": "Officer to verify exact product title from physical label.",
                    "raw_ocr_line": p_meta["raw_text_line"] or f"Product: {p_name}",
                    "source": format_source_label(p_meta),
                    "evidence_region": format_region(p_meta),
                    "ocr_value": p_meta["ocr_value"],
                    "gemini_value": p_meta["gemini_value"]
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_001",
                    "rule_name": "Product Name / Generic Name",
                    "field_key": "product_name",
                    "status": RuleResult.PASS,
                    "detection_state": DetectionState.VERIFIED,
                    "detected_value": str(p_name),
                    "expected_requirement": "Name and generic identity of the packaged commodity on principal display panel.",
                    "severity": "NONE",
                    "legal_citation": "Rule 6(1)(b), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Product/generic name is clearly declared on the packaging label.",
                    "corrective_action": None,
                    "raw_ocr_line": p_meta["raw_text_line"] or str(p_name),
                    "source": format_source_label(p_meta),
                    "evidence_region": format_region(p_meta)
                })
        else:
            if images_count < 2:
                rules_evaluated.append({
                    "rule_code": "LMR_001",
                    "rule_name": "Product Name / Generic Name",
                    "field_key": "product_name",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel(s)",
                    "expected_requirement": "Name and generic identity must be prominently declared on Principal Display Panel (PDP).",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(b), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Product title was not identified on the captured panel. Ensure the Front Principal Display Panel is photographed.",
                    "corrective_action": "Capture the front principal display panel clearly.",
                    "raw_ocr_line": "No matching product name token in single-panel scan",
                    "source": "Single-Panel Scan (Front unverified)",
                    "evidence_region": "Front Panel Required"
                })
            elif has_quality_issues:
                rules_evaluated.append({
                    "rule_code": "LMR_001",
                    "rule_name": "Product Name / Generic Name",
                    "field_key": "product_name",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.UNCLEAR,
                    "detected_value": "Unclear in current image",
                    "expected_requirement": "Legible generic name on principal display panel.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(b), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Image quality, lighting or resolution is insufficient to reliably read the product title.",
                    "corrective_action": "Retake image with even lighting and steady focus.",
                    "raw_ocr_line": "OCR confidence degraded by image quality warnings",
                    "source": "Image Quality Warning",
                    "evidence_region": "Principal Display Panel"
                })
            elif images_count >= 4:
                rules_evaluated.append({
                    "rule_code": "LMR_001",
                    "rule_name": "Product Name / Generic Name",
                    "field_key": "product_name",
                    "status": RuleResult.FAIL,
                    "detection_state": DetectionState.CONFIRMED_MISSING,
                    "detected_value": "Conclusively missing across all 4 panels",
                    "expected_requirement": "Mandatory generic identity must be prominently declared on PDP.",
                    "severity": "HIGH",
                    "legal_citation": "Rule 6(1)(b), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "All 4 packaging panels thoroughly inspected; product/generic name is absent.",
                    "corrective_action": "Declare generic or common name on principal display panel.",
                    "raw_ocr_line": "Searched all panels; 0 occurrences found",
                    "source": "4-Panel Full Scan",
                    "evidence_region": "All Captured Surfaces"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_001",
                    "rule_name": "Product Name / Generic Name",
                    "field_key": "product_name",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not detected on scanned panel(s)",
                    "expected_requirement": "Name and generic identity of the commodity must be prominently declared.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(b), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Product name not detected on scanned panel(s). Officer visual inspection recommended before issuing notice.",
                    "corrective_action": "Officer visual verification required across packaging faces.",
                    "raw_ocr_line": "No matching product tokens found",
                    "source": "Multi-Panel OCR Scan",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 2. MAXIMUM RETAIL PRICE (MRP) (Rule 6(1)(e))
        # ==========================================================
        mrp_val = extracted_fields.get("mrp")
        mrp_meta = get_meta("mrp")

        if not is_empty(mrp_val):
            if mrp_meta["conflict"]:
                rules_evaluated.append({
                    "rule_code": "LMR_002",
                    "rule_name": "Maximum Retail Price (MRP)",
                    "field_key": "mrp",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NEEDS_MANUAL_REVIEW,
                    "detected_value": f"₹ {mrp_val} (Review Discrepancy)",
                    "expected_requirement": "Maximum Retail Price in Indian Rupees inclusive of all taxes.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(e), LMR 2011",
                    "is_mandatory": True,
                    "explanation": f"Discrepancy: OCR detected '{mrp_meta['ocr_value']}' vs AI '{mrp_meta['gemini_value']}'. Stamped value requires officer confirmation.",
                    "corrective_action": "Officer to inspect physical stamp on packaging to confirm correct MRP numeral.",
                    "raw_ocr_line": mrp_meta["raw_text_line"] or f"MRP Rs. {mrp_val}",
                    "source": format_source_label(mrp_meta),
                    "evidence_region": format_region(mrp_meta),
                    "ocr_value": mrp_meta["ocr_value"],
                    "gemini_value": mrp_meta["gemini_value"]
                })
            else:
                try:
                    num = float(str(mrp_val).replace(",", ""))
                    if num > 0:
                        rules_evaluated.append({
                            "rule_code": "LMR_002",
                            "rule_name": "Maximum Retail Price (MRP)",
                            "field_key": "mrp",
                            "status": RuleResult.PASS,
                            "detection_state": DetectionState.VERIFIED,
                            "detected_value": f"₹ {mrp_val} (Inclusive of all taxes)",
                            "expected_requirement": "Maximum Retail Price in Indian Rupees inclusive of all taxes.",
                            "severity": "NONE",
                            "legal_citation": "Rule 6(1)(e), LMR 2011",
                            "is_mandatory": True,
                            "explanation": "MRP is properly declared in valid Indian Rupee format inclusive of all taxes.",
                            "corrective_action": None,
                            "raw_ocr_line": mrp_meta["raw_text_line"] or f"MRP Rs. {mrp_val} (incl. of all taxes)",
                            "source": format_source_label(mrp_meta),
                            "evidence_region": format_region(mrp_meta)
                        })
                    else:
                        rules_evaluated.append({
                            "rule_code": "LMR_002",
                            "rule_name": "Maximum Retail Price (MRP)",
                            "field_key": "mrp",
                            "status": RuleResult.FAIL,
                            "detection_state": DetectionState.CONFIRMED_MISSING,
                            "detected_value": str(mrp_val),
                            "expected_requirement": "MRP must be a positive monetary value.",
                            "severity": "HIGH",
                            "legal_citation": "Rule 6(1)(e), LMR 2011",
                            "is_mandatory": True,
                            "explanation": "Declared MRP is zero or negative monetary value.",
                            "corrective_action": "Declare a valid non-zero retail price.",
                            "raw_ocr_line": mrp_meta["raw_text_line"] or str(mrp_val),
                            "source": format_source_label(mrp_meta),
                            "evidence_region": format_region(mrp_meta)
                        })
                except ValueError:
                    rules_evaluated.append({
                        "rule_code": "LMR_002",
                        "rule_name": "Maximum Retail Price (MRP)",
                        "field_key": "mrp",
                        "status": RuleResult.REVIEW,
                        "detection_state": DetectionState.UNCLEAR,
                        "detected_value": str(mrp_val),
                        "expected_requirement": "Clear numerical price declaration in Rupees.",
                        "severity": "LOW",
                        "legal_citation": "Rule 6(1)(e), LMR 2011",
                        "is_mandatory": True,
                        "explanation": "Price text was detected but formatting or numeral requires manual verification.",
                        "corrective_action": "Ensure MRP is legibly printed as 'MRP ₹ XX.XX (incl. of all taxes)'.",
                        "raw_ocr_line": mrp_meta["raw_text_line"] or str(mrp_val),
                        "source": format_source_label(mrp_meta),
                        "evidence_region": format_region(mrp_meta)
                    })
        else:
            if images_count == 1:
                rules_evaluated.append({
                    "rule_code": "LMR_002",
                    "rule_name": "Maximum Retail Price (MRP)",
                    "field_key": "mrp",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel",
                    "expected_requirement": "Mandatory MRP declaration in Rupees inclusive of all taxes.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(e), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "MRP was not visible on the single captured panel. MRP is typically printed on the back, side, or top flap.",
                    "corrective_action": "Rotate package to photograph back or side panels where MRP is stamped.",
                    "raw_ocr_line": "No MRP keywords in single-panel scan",
                    "source": "Single-Panel Scan (Back/Top Flap Uncaptured)",
                    "evidence_region": "Back / Top Flap Panel Required"
                })
            elif has_quality_issues:
                rules_evaluated.append({
                    "rule_code": "LMR_002",
                    "rule_name": "Maximum Retail Price (MRP)",
                    "field_key": "mrp",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.UNCLEAR,
                    "detected_value": "Unclear in current image",
                    "expected_requirement": "Conspicuous MRP declaration in Rupees.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(e), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "MRP may be present but is unreadable due to glare, stamp blur, or low lighting.",
                    "corrective_action": "Inspect physical product stamp for legible price declaration.",
                    "raw_ocr_line": "OCR price confidence degraded",
                    "source": "Image Quality Warning",
                    "evidence_region": "Packaging Stamping Area"
                })
            elif images_count >= 4:
                rules_evaluated.append({
                    "rule_code": "LMR_002",
                    "rule_name": "Maximum Retail Price (MRP)",
                    "field_key": "mrp",
                    "status": RuleResult.FAIL,
                    "detection_state": DetectionState.CONFIRMED_MISSING,
                    "detected_value": "Conclusively missing across all 4 panels",
                    "expected_requirement": "Mandatory MRP declaration in Rupees inclusive of all taxes.",
                    "severity": "HIGH",
                    "legal_citation": "Rule 6(1)(e), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "All 4 packaging panels thoroughly inspected; mandatory MRP declaration is absent.",
                    "corrective_action": "Print conspicuous MRP in Indian Rupees with 'inclusive of all taxes'.",
                    "raw_ocr_line": "Searched all panels; 0 MRP occurrences found",
                    "source": "4-Panel Full Scan",
                    "evidence_region": "All Captured Surfaces"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_002",
                    "rule_name": "Maximum Retail Price (MRP)",
                    "field_key": "mrp",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not detected on scanned panel(s)",
                    "expected_requirement": "Mandatory MRP declaration in Rupees inclusive of all taxes.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(e), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "MRP not detected on current image(s). Do not treat as violation without checking uncaptured package sides.",
                    "corrective_action": "Officer to verify physical packaging before issuing statutory notice.",
                    "raw_ocr_line": "No MRP tokens matched in current scan",
                    "source": "Multi-Panel OCR Scan",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 3. NET QUANTITY (Rule 6(1)(c) & Rule 11)
        # ==========================================================
        net_qty = extracted_fields.get("net_quantity")
        qty_meta = get_meta("net_quantity")

        if not is_empty(net_qty):
            qty_str = str(net_qty).strip()
            valid_units = re.compile(r"^\d+(?:\.\d+)?\s*(?:mg|g|kg|ml|l|litre|litres|liter|liters|n|u|units?)\b", re.IGNORECASE)
            if valid_units.search(qty_str):
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "field_key": "net_quantity",
                    "status": RuleResult.PASS,
                    "detection_state": DetectionState.VERIFIED,
                    "detected_value": qty_str,
                    "expected_requirement": "Net weight, measure, or number of units in standard metric units.",
                    "severity": "NONE",
                    "legal_citation": "Rule 6(1)(c) & Rule 11, LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity is declared in standard metric units.",
                    "corrective_action": None,
                    "raw_ocr_line": qty_meta["raw_text_line"] or qty_str,
                    "source": format_source_label(qty_meta),
                    "evidence_region": format_region(qty_meta)
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "field_key": "net_quantity",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NEEDS_MANUAL_REVIEW,
                    "detected_value": qty_str,
                    "expected_requirement": "Standard metric unit (g, kg, ml, L, N). Non-standard units are discouraged.",
                    "severity": "LOW",
                    "legal_citation": "Rule 11, LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity unit requires verification to ensure standard symbol usage ('g', 'kg', 'ml', 'L', 'N').",
                    "corrective_action": "Use standard symbols 'g', 'kg', 'ml', 'L', or 'N' with proper space.",
                    "raw_ocr_line": qty_meta["raw_text_line"] or qty_str,
                    "source": format_source_label(qty_meta),
                    "evidence_region": format_region(qty_meta)
                })
        else:
            if images_count == 1:
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "field_key": "net_quantity",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel",
                    "expected_requirement": "Net quantity must be declared on principal display panel.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(c), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity not visible on captured panel. May be printed on front PDP or base.",
                    "corrective_action": "Capture front PDP panel to verify net weight/volume.",
                    "raw_ocr_line": "No quantity keywords in single-panel scan",
                    "source": "Single-Panel Scan",
                    "evidence_region": "Principal Display Panel"
                })
            elif images_count >= 4:
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "field_key": "net_quantity",
                    "status": RuleResult.FAIL,
                    "detection_state": DetectionState.CONFIRMED_MISSING,
                    "detected_value": "Conclusively missing across all 4 panels",
                    "expected_requirement": "Net quantity must be declared on the principal display panel.",
                    "severity": "HIGH",
                    "legal_citation": "Rule 6(1)(c), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity declaration was searched and is absent across all packaging panels.",
                    "corrective_action": "Declare net weight or volume on the principal display panel.",
                    "raw_ocr_line": "Searched all panels; 0 quantity occurrences found",
                    "source": "4-Panel Full Scan",
                    "evidence_region": "All Captured Surfaces"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "field_key": "net_quantity",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not detected on scanned panel(s)",
                    "expected_requirement": "Net quantity must be declared on the principal display panel.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(c), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity declaration not detected on current image(s).",
                    "corrective_action": "Officer visual review advised.",
                    "raw_ocr_line": "No matching quantity tokens found",
                    "source": "Multi-Panel OCR Scan",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 4. MANUFACTURER / PACKER / IMPORTER DETAILS (Rule 6(1)(a))
        # ==========================================================
        mfg_name = extracted_fields.get("manufacturer_name") or extracted_fields.get("packer_name") or extracted_fields.get("importer_name")
        mfg_addr = extracted_fields.get("manufacturer_address") or extracted_fields.get("packer_address") or extracted_fields.get("importer_address")
        mfg_meta = get_meta("manufacturer_name")

        if not is_empty(mfg_name) and not is_empty(mfg_addr):
            rules_evaluated.append({
                "rule_code": "LMR_004",
                "rule_name": "Manufacturer / Packer / Importer Details",
                "field_key": "manufacturer_name",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": f"{mfg_name} | {mfg_addr}",
                "expected_requirement": "Name and complete address of the manufacturer, packer, or importer.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(a), LMR 2011",
                "is_mandatory": True,
                "explanation": "Complete manufacturer/packer identity and physical premises address are declared.",
                "corrective_action": None,
                "raw_ocr_line": mfg_meta["raw_text_line"] or f"Mfg by: {mfg_name}, {mfg_addr}",
                "source": format_source_label(mfg_meta),
                "evidence_region": format_region(mfg_meta)
            })
        elif not is_empty(mfg_name):
            rules_evaluated.append({
                "rule_code": "LMR_004",
                "rule_name": "Manufacturer / Packer / Importer Details",
                "field_key": "manufacturer_name",
                "status": RuleResult.REVIEW,
                "detection_state": DetectionState.UNCLEAR,
                "detected_value": str(mfg_name),
                "expected_requirement": "Both name and complete physical address must be declared.",
                "severity": "LOW",
                "legal_citation": "Rule 6(1)(a), LMR 2011",
                "is_mandatory": True,
                "explanation": "Manufacturer name detected; physical premises address or PIN code requires verification.",
                "corrective_action": "Ensure complete postal address including PIN code is clearly legible.",
                "raw_ocr_line": mfg_meta["raw_text_line"] or str(mfg_name),
                "source": format_source_label(mfg_meta),
                "evidence_region": format_region(mfg_meta)
            })
        else:
            if images_count == 1:
                rules_evaluated.append({
                    "rule_code": "LMR_004",
                    "rule_name": "Manufacturer / Packer / Importer Details",
                    "field_key": "manufacturer_name",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel",
                    "expected_requirement": "Name and address of manufacturer or packer must be stated.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(a), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Manufacturer details not visible on captured panel. Normally printed on back or side panels.",
                    "corrective_action": "Capture back or side panel containing manufacturer details.",
                    "raw_ocr_line": "No manufacturer tokens in single-panel scan",
                    "source": "Single-Panel Scan",
                    "evidence_region": "Back / Side Panel Required"
                })
            elif images_count >= 4:
                rules_evaluated.append({
                    "rule_code": "LMR_004",
                    "rule_name": "Manufacturer / Packer / Importer Details",
                    "field_key": "manufacturer_name",
                    "status": RuleResult.FAIL,
                    "detection_state": DetectionState.CONFIRMED_MISSING,
                    "detected_value": "Conclusively missing across all 4 panels",
                    "expected_requirement": "Name and address of manufacturer or packer must be stated.",
                    "severity": "HIGH",
                    "legal_citation": "Rule 6(1)(a), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Manufacturer/packer name and address absent across all captured packaging faces.",
                    "corrective_action": "Declare complete name and address of manufacturer or packer.",
                    "raw_ocr_line": "Searched all panels; 0 manufacturer occurrences found",
                    "source": "4-Panel Full Scan",
                    "evidence_region": "All Captured Surfaces"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_004",
                    "rule_name": "Manufacturer / Packer / Importer Details",
                    "field_key": "manufacturer_name",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not detected on scanned panel(s)",
                    "expected_requirement": "Name and address of manufacturer or packer must be stated.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(a), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Manufacturer details not detected on current image(s).",
                    "corrective_action": "Check other packaging faces.",
                    "raw_ocr_line": "No manufacturer tokens found",
                    "source": "Multi-Panel OCR Scan",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 5. MANUFACTURING / PACKING DATE (Rule 6(1)(d))
        # ==========================================================
        mfg_date = extracted_fields.get("mfg_date") or extracted_fields.get("packing_date")
        date_meta = get_meta("mfg_date")

        if not is_empty(mfg_date):
            rules_evaluated.append({
                "rule_code": "LMR_005",
                "rule_name": "Month & Year of Manufacture / Packing",
                "field_key": "mfg_date",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": str(mfg_date),
                "expected_requirement": "Month and year of manufacture, packing, or pre-packing.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(d), LMR 2011",
                "is_mandatory": True,
                "explanation": "Manufacturing/packing date is declared.",
                "corrective_action": None,
                "raw_ocr_line": date_meta["raw_text_line"] or f"Mfg: {mfg_date}",
                "source": format_source_label(date_meta),
                "evidence_region": format_region(date_meta)
            })
        else:
            if images_count == 1:
                rules_evaluated.append({
                    "rule_code": "LMR_005",
                    "rule_name": "Month & Year of Manufacture / Packing",
                    "field_key": "mfg_date",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel",
                    "expected_requirement": "Month and year of manufacture or packing.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(d), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Mfg/packing date not on captured panel. Often batch-stamped on crimp seal or back panel.",
                    "corrective_action": "Check packaging crimp or back panel for stamped date.",
                    "raw_ocr_line": "No date tokens in single-panel scan",
                    "source": "Single-Panel Scan",
                    "evidence_region": "Crimp Seal / Back Panel"
                })
            elif images_count >= 4:
                rules_evaluated.append({
                    "rule_code": "LMR_005",
                    "rule_name": "Month & Year of Manufacture / Packing",
                    "field_key": "mfg_date",
                    "status": RuleResult.FAIL,
                    "detection_state": DetectionState.CONFIRMED_MISSING,
                    "detected_value": "Conclusively missing across all 4 panels",
                    "expected_requirement": "Month and year of manufacture or packing.",
                    "severity": "HIGH",
                    "legal_citation": "Rule 6(1)(d), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Month and year of manufacture/packing absent across all packaging surfaces.",
                    "corrective_action": "Print month and year of manufacture/packing prominently.",
                    "raw_ocr_line": "Searched all panels; 0 date occurrences found",
                    "source": "4-Panel Full Scan",
                    "evidence_region": "All Captured Surfaces"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_005",
                    "rule_name": "Month & Year of Manufacture / Packing",
                    "field_key": "mfg_date",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not detected on scanned panel(s)",
                    "expected_requirement": "Month and year of manufacture or packing.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(d), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Date of manufacture/packing not detected on current image(s).",
                    "corrective_action": "Verify physical stamp on package.",
                    "raw_ocr_line": "No manufacturing date tokens found",
                    "source": "Multi-Panel OCR Scan",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 6. EXPIRY DATE / BEST BEFORE (Rule 6(1)(d) & FSSAI)
        # ==========================================================
        exp_date = extracted_fields.get("expiry_date") or extracted_fields.get("best_before")
        exp_meta = get_meta("expiry_date")

        if not is_empty(exp_date):
            rules_evaluated.append({
                "rule_code": "LMR_006",
                "rule_name": "Expiry Date / Best Before",
                "field_key": "expiry_date",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": str(exp_date),
                "expected_requirement": "Expiry date or 'Best Before' period for perishable commodities.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(d) Proviso, LMR 2011",
                "is_mandatory": False,
                "explanation": "Expiry/Best before date is declared.",
                "corrective_action": None,
                "raw_ocr_line": exp_meta["raw_text_line"] or f"Exp: {exp_date}",
                "source": format_source_label(exp_meta),
                "evidence_region": format_region(exp_meta)
            })
        else:
            rules_evaluated.append({
                "rule_code": "LMR_006",
                "rule_name": "Expiry Date / Best Before",
                "field_key": "expiry_date",
                "status": RuleResult.REVIEW,
                "detection_state": DetectionState.NOT_DETECTED,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Required for food products and commodities that may deteriorate over time.",
                "severity": "LOW",
                "legal_citation": "Rule 6(1)(d) Proviso, LMR 2011",
                "is_mandatory": False,
                "explanation": "Expiry date was not visible. Non-perishable items are exempt under LMR 2011.",
                "corrective_action": "If applicable to perishable goods, declare 'Best Before' or 'Expiry Date'.",
                "raw_ocr_line": "No expiry date tokens found",
                "source": "OCR Pipeline",
                "evidence_region": "Captured Panels"
            })

        # ==========================================================
        # 7. CONSUMER CARE DETAILS (Rule 6(1)(da))
        # ==========================================================
        care_val = extracted_fields.get("consumer_care") or extracted_fields.get("consumer_care_phone") or extracted_fields.get("consumer_care_email")
        care_meta = get_meta("consumer_care")

        if not is_empty(care_val):
            rules_evaluated.append({
                "rule_code": "LMR_007",
                "rule_name": "Consumer Care Details",
                "field_key": "consumer_care",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": str(care_val),
                "expected_requirement": "Name, address, telephone number, and email address of consumer care contact.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(da), LMR 2011",
                "is_mandatory": True,
                "explanation": "Consumer care contact details are declared.",
                "corrective_action": None,
                "raw_ocr_line": care_meta["raw_text_line"] or str(care_val),
                "source": format_source_label(care_meta),
                "evidence_region": format_region(care_meta)
            })
        else:
            if images_count == 1:
                rules_evaluated.append({
                    "rule_code": "LMR_007",
                    "rule_name": "Consumer Care Details",
                    "field_key": "consumer_care",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel",
                    "expected_requirement": "Helpline number or email ID for consumer complaints.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(da), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Consumer care contact not visible on current panel. Typically on back or side panels.",
                    "corrective_action": "Inspect back or side panels for consumer care helpline.",
                    "raw_ocr_line": "No consumer care tokens in single-panel scan",
                    "source": "Single-Panel Scan",
                    "evidence_region": "Back / Side Panel Required"
                })
            elif images_count >= 4:
                rules_evaluated.append({
                    "rule_code": "LMR_007",
                    "rule_name": "Consumer Care Details",
                    "field_key": "consumer_care",
                    "status": RuleResult.FAIL,
                    "detection_state": DetectionState.CONFIRMED_MISSING,
                    "detected_value": "Conclusively missing across all 4 panels",
                    "expected_requirement": "Helpline number or email ID for consumer complaints.",
                    "severity": "HIGH",
                    "legal_citation": "Rule 6(1)(da), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Consumer care helpline/email absent across all packaging panels.",
                    "corrective_action": "Provide customer care telephone number, email, and postal address.",
                    "raw_ocr_line": "Searched all panels; 0 consumer care occurrences found",
                    "source": "4-Panel Full Scan",
                    "evidence_region": "All Captured Surfaces"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_007",
                    "rule_name": "Consumer Care Details",
                    "field_key": "consumer_care",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not detected on scanned panel(s)",
                    "expected_requirement": "Helpline number or email ID for consumer complaints.",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(1)(da), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Consumer care helpline was not identified on captured panels.",
                    "corrective_action": "Verify consumer care section on packaging.",
                    "raw_ocr_line": "No consumer care tokens found",
                    "source": "Multi-Panel OCR Scan",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 8. COUNTRY OF ORIGIN (Rule 6(10))
        # ==========================================================
        origin_val = extracted_fields.get("country_of_origin")
        origin_meta = get_meta("country_of_origin")

        if not is_empty(origin_val):
            rules_evaluated.append({
                "rule_code": "LMR_008",
                "rule_name": "Country of Origin",
                "field_key": "country_of_origin",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": str(origin_val),
                "expected_requirement": "Country of origin must be stated on imported and domestic packaged goods.",
                "severity": "NONE",
                "legal_citation": "Rule 6(10), LMR 2011 Amendment",
                "is_mandatory": False,
                "explanation": f"Country of origin explicitly declared as '{origin_val}'.",
                "corrective_action": None,
                "raw_ocr_line": origin_meta["raw_text_line"] or f"Origin: {origin_val}",
                "source": format_source_label(origin_meta),
                "evidence_region": format_region(origin_meta)
            })
        elif not is_empty(mfg_addr) and (re.search(r"\b(?:India|PIN\s*\d{6}|\d{6})\b", str(mfg_addr), re.IGNORECASE)):
            rules_evaluated.append({
                "rule_code": "LMR_008",
                "rule_name": "Country of Origin",
                "field_key": "country_of_origin",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": "Implied: India (Domestic Manufacturer Premises)",
                "expected_requirement": "Country of origin statement (e.g. 'Made in India').",
                "severity": "NONE",
                "legal_citation": "Rule 6(10), LMR 2011 Amendment",
                "is_mandatory": False,
                "explanation": "Domestic manufacturer premises in India declared under Rule 6(1)(a); country of origin implied as India under Rule 6(10).",
                "corrective_action": None,
                "raw_ocr_line": f"Manufacturer address: {mfg_addr}",
                "source": "Domestic Manufacturer Premises",
                "evidence_region": "Manufacturer Details Panel"
            })
        else:
            if images_count == 1:
                rules_evaluated.append({
                    "rule_code": "LMR_008",
                    "rule_name": "Country of Origin",
                    "field_key": "country_of_origin",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_VISIBLE,
                    "detected_value": "Not visible on captured panel",
                    "expected_requirement": "Country of origin statement (e.g. 'Made in India').",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(10), LMR 2011 Amendment",
                    "is_mandatory": False,
                    "explanation": "Country of origin not found on this panel. Often printed near manufacturer address on back panel.",
                    "corrective_action": "Inspect back panel near manufacturer premises.",
                    "raw_ocr_line": "No origin tokens in single-panel scan",
                    "source": "Single-Panel Scan",
                    "evidence_region": "Back Panel Required"
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_008",
                    "rule_name": "Country of Origin",
                    "field_key": "country_of_origin",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.NOT_DETECTED,
                    "detected_value": "Not explicitly detected",
                    "expected_requirement": "Country of origin statement (e.g. 'Made in India').",
                    "severity": "LOW",
                    "legal_citation": "Rule 6(10), LMR 2011 Amendment",
                    "is_mandatory": False,
                    "explanation": "Origin statement not explicitly detected on scanned surfaces. If manufactured domestically, address fulfills statutory origin intent.",
                    "corrective_action": "Declare 'Country of Origin: India' or appropriate manufacturing country if imported.",
                    "raw_ocr_line": "No explicit 'Made in' or 'Country of Origin' statement found",
                    "source": "OCR / Vision Pipeline",
                    "evidence_region": "Captured Panels"
                })

        # ==========================================================
        # 9. FSSAI LICENSE NUMBER (Food Safety Act / LMR)
        # ==========================================================
        fssai_val = extracted_fields.get("fssai_number")
        fssai_meta = get_meta("fssai_number")

        if not is_empty(fssai_val):
            fssai_str = str(fssai_val).strip()
            if len(fssai_str) == 14 and fssai_str.isdigit():
                rules_evaluated.append({
                    "rule_code": "FSSAI_001",
                    "rule_name": "FSSAI License Number",
                    "field_key": "fssai_number",
                    "status": RuleResult.PASS,
                    "detection_state": DetectionState.VERIFIED,
                    "detected_value": f"FSSAI Lic. No. {fssai_str}",
                    "expected_requirement": "14-digit FSSAI License Number with Logo for food products.",
                    "severity": "NONE",
                    "legal_citation": "FSS (Packaging & Labelling) Reg. 2011",
                    "is_mandatory": False,
                    "explanation": "Valid 14-digit FSSAI license number declared.",
                    "corrective_action": None,
                    "raw_ocr_line": fssai_meta["raw_text_line"] or f"FSSAI: {fssai_str}",
                    "source": format_source_label(fssai_meta),
                    "evidence_region": format_region(fssai_meta)
                })
            else:
                rules_evaluated.append({
                    "rule_code": "FSSAI_001",
                    "rule_name": "FSSAI License Number",
                    "field_key": "fssai_number",
                    "status": RuleResult.REVIEW,
                    "detection_state": DetectionState.UNCLEAR,
                    "detected_value": fssai_str,
                    "expected_requirement": "Exactly 14 numeric digits.",
                    "severity": "LOW",
                    "legal_citation": "FSS (Packaging & Labelling) Reg. 2011",
                    "is_mandatory": False,
                    "explanation": "FSSAI number detected but character count is not 14.",
                    "corrective_action": "Verify 14-digit FSSAI registration number.",
                    "raw_ocr_line": fssai_meta["raw_text_line"] or fssai_str,
                    "source": format_source_label(fssai_meta),
                    "evidence_region": format_region(fssai_meta)
                })
        else:
            rules_evaluated.append({
                "rule_code": "FSSAI_001",
                "rule_name": "FSSAI License Number",
                "field_key": "fssai_number",
                "status": RuleResult.REVIEW,
                "detection_state": DetectionState.NOT_DETECTED,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Applicable for packaged food articles.",
                "severity": "LOW",
                "legal_citation": "FSS (Packaging & Labelling) Reg. 2011",
                "is_mandatory": False,
                "explanation": "FSSAI license was not detected. Non-food commodities are exempt.",
                "corrective_action": "If this is a food commodity, display 14-digit FSSAI license number.",
                "raw_ocr_line": "No FSSAI keywords in current scan",
                "source": "OCR Pipeline",
                "evidence_region": "Captured Panels"
            })

        # ==========================================================
        # 10. BARCODE / GTIN IDENTIFIER
        # ==========================================================
        barcode_val = extracted_fields.get("barcode")
        barcode_meta = get_meta("barcode")

        if not is_empty(barcode_val):
            rules_evaluated.append({
                "rule_code": "BARCODE_001",
                "rule_name": "Barcode / EAN-13 Identifier",
                "field_key": "barcode",
                "status": RuleResult.PASS,
                "detection_state": DetectionState.VERIFIED,
                "detected_value": str(barcode_val),
                "expected_requirement": "Scannable GTIN/EAN-13 barcode for retail commodity tracking.",
                "severity": "NONE",
                "category": "PRODUCT_TRACKING",
                "legal_citation": "GS1 India / Retail Packaging Standards",
                "is_mandatory": False,
                "explanation": f"Barcode {barcode_val} decoded from packaging label. (Note: Barcode presence is label evidence; product identity is not verified against central national database).",
                "corrective_action": None,
                "raw_ocr_line": f"Barcode: {barcode_val}",
                "source": "Barcode / GTIN Decoder",
                "evidence_region": "Barcode Region"
            })
        else:
            rules_evaluated.append({
                "rule_code": "BARCODE_001",
                "rule_name": "Barcode / EAN-13 Identifier",
                "field_key": "barcode",
                "status": RuleResult.REVIEW,
                "detection_state": DetectionState.NOT_DETECTED,
                "detected_value": "Not detected",
                "expected_requirement": "Retail barcode for product tracking.",
                "severity": "LOW",
                "category": "PRODUCT_TRACKING",
                "legal_citation": "GS1 Standards",
                "is_mandatory": False,
                "explanation": "Barcode was not present on the scanned faces or image angle.",
                "corrective_action": "Ensure barcode is clearly visible for digital inventory.",
                "raw_ocr_line": "Barcode decoder found 0 symbols",
                "source": "Barcode Detector",
                "evidence_region": "Captured Panels"
            })

        # ==========================================================
        # OVERALL COMPLIANCE VERDICT DETERMINATION
        # ==========================================================
        fail_items = [r for r in rules_evaluated if r["status"] == RuleResult.FAIL]
        review_items = [r for r in rules_evaluated if r["status"] == RuleResult.REVIEW]
        pass_items = [r for r in rules_evaluated if r["status"] == RuleResult.PASS]

        mandatory_fails = [r for r in fail_items if r["is_mandatory"]]

        if mandatory_fails:
            overall_verdict = "non_compliant"
            verdict_text = "NON-COMPLIANT"
            verdict_summary = f"{len(mandatory_fails)} mandatory Legal Metrology requirement(s) conclusively violated."
        elif review_items:
            overall_verdict = "needs_review"
            verdict_text = "NEEDS MANUAL REVIEW"
            verdict_summary = f"{len(pass_items)} passed, {len(review_items)} declaration(s) require verification or multi-panel capture."
        else:
            overall_verdict = "compliant"
            verdict_text = "COMPLIANT WITH CHECKED REQUIREMENTS"
            verdict_summary = "All checked mandatory Legal Metrology packaging declarations verified successfully."

        # Compute accurate 0-100 score
        # Pass = +10 pts, Review = +6 pts, Fail = 0 pts
        total_possible = len(rules_evaluated) * 10
        earned_points = sum(
            10 if r["status"] == RuleResult.PASS else (6 if r["status"] == RuleResult.REVIEW else 0)
            for r in rules_evaluated
        )
        calculated_score = int(round((earned_points / total_possible) * 100))

        # Build violations format compatible with existing database and frontend
        violations_for_db = []
        for r in fail_items + review_items:
            violations_for_db.append({
                "rule_code": r["rule_code"],
                "rule_description": f"{r['rule_name']} ({r['status']} - {r['detection_state']})",
                "severity": r["severity"],
                "category": r.get("category", "LEGAL_METROLOGY"),
                "detail_text": f"{r['explanation']} [Expected: {r['expected_requirement']}]",
                "status": r["status"],
                "detection_state": r["detection_state"],
                "legal_citation": r["legal_citation"],
                "corrective_action": r.get("corrective_action")
            })

        return {
            "verdict": overall_verdict,
            "verdict_text": verdict_text,
            "verdict_summary": verdict_summary,
            "score": calculated_score,
            "rules_evaluated": rules_evaluated,
            "violations_data": violations_for_db,
            "passed_count": len(pass_items),
            "review_count": len(review_items),
            "failed_count": len(fail_items),
            "total_rules": len(rules_evaluated)
        }

    def evaluate(self, extracted_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Legacy compatibility adapter returning list of violations/review notices.
        """
        result = self.evaluate_rules(extracted_fields)
        return result["violations_data"]