import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RuleResult:
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RuleEngine:
    """
    LegalMetriX Legal Metrology Compliance Rule Engine
    Based on the Legal Metrology (Packaged Commodities) Rules, 2011 and Amendments.

    Distinguishes:
    - PASS: Requirement declared and valid.
    - REVIEW: Information unclear, partial OCR, single-side scan, or requires officer verification.
    - FAIL: Conclusive legal violation or missing applicable mandatory requirement.
    - NOT_APPLICABLE: Rule does not apply to this category/origin.
    """

    def evaluate_rules(
        self,
        extracted_fields: Dict[str, Any],
        images_count: int = 1,
        is_food_product: bool = True
    ) -> Dict[str, Any]:
        """
        Runs comprehensive evaluation on extracted product declarations.
        Returns detailed rule outcomes, violation items, review items, and overall verdict.
        """
        logger.info("Evaluating Legal Metrology Rules (LMR 2011)...")

        rules_evaluated: List[Dict[str, Any]] = []

        def is_empty(val: Any) -> bool:
            if val is None:
                return True
            if isinstance(val, str) and not val.strip():
                return True
            return False

        # ==========================================================
        # 1. PRODUCT / GENERIC NAME (Rule 6(1)(b))
        # ==========================================================
        p_name = extracted_fields.get("product_name") or extracted_fields.get("generic_name")
        if not is_empty(p_name):
            rules_evaluated.append({
                "rule_code": "LMR_001",
                "rule_name": "Product Name / Generic Name",
                "status": RuleResult.PASS,
                "detected_value": str(p_name),
                "expected_requirement": "Name and generic identity of the packaged commodity on principal display panel.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(b), LMR 2011",
                "is_mandatory": True,
                "explanation": "Product/generic name is clearly declared.",
                "corrective_action": None
            })
        else:
            status = RuleResult.REVIEW if images_count < 2 else RuleResult.FAIL
            rules_evaluated.append({
                "rule_code": "LMR_001",
                "rule_name": "Product Name / Generic Name",
                "status": status,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Name and generic identity of the commodity must be prominently declared.",
                "severity": "HIGH" if status == RuleResult.FAIL else "MEDIUM",
                "legal_citation": "Rule 6(1)(b), LMR 2011",
                "is_mandatory": True,
                "explanation": "Product name was not identified on the visible packaging panels. Ensure Front panel is clearly captured.",
                "corrective_action": "Declare the generic or common name of the commodity on the principal display panel."
            })

        # ==========================================================
        # 2. MAXIMUM RETAIL PRICE (MRP) (Rule 6(1)(e))
        # ==========================================================
        mrp_val = extracted_fields.get("mrp")
        if not is_empty(mrp_val):
            # Validate numerical format
            try:
                num = float(str(mrp_val).replace(",", ""))
                if num > 0:
                    rules_evaluated.append({
                        "rule_code": "LMR_002",
                        "rule_name": "Maximum Retail Price (MRP)",
                        "status": RuleResult.PASS,
                        "detected_value": f"₹ {mrp_val} (Inclusive of all taxes)",
                        "expected_requirement": "Maximum Retail Price in Indian Rupees inclusive of all taxes.",
                        "severity": "NONE",
                        "legal_citation": "Rule 6(1)(e), LMR 2011",
                        "is_mandatory": True,
                        "explanation": "MRP is properly declared in valid currency format.",
                        "corrective_action": None
                    })
                else:
                    rules_evaluated.append({
                        "rule_code": "LMR_002",
                        "rule_name": "Maximum Retail Price (MRP)",
                        "status": RuleResult.FAIL,
                        "detected_value": str(mrp_val),
                        "expected_requirement": "MRP must be a positive monetary value.",
                        "severity": "HIGH",
                        "legal_citation": "Rule 6(1)(e), LMR 2011",
                        "is_mandatory": True,
                        "explanation": "MRP is zero or negative.",
                        "corrective_action": "Declare a valid non-zero retail price."
                    })
            except ValueError:
                rules_evaluated.append({
                    "rule_code": "LMR_002",
                    "rule_name": "Maximum Retail Price (MRP)",
                    "status": RuleResult.REVIEW,
                    "detected_value": str(mrp_val),
                    "expected_requirement": "Clear numerical price declaration in Rupees.",
                    "severity": "MEDIUM",
                    "legal_citation": "Rule 6(1)(e), LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Price text was detected but formatting requires manual verification.",
                    "corrective_action": "Ensure MRP is legibly printed as 'MRP ₹ XX.XX (incl. of all taxes)'."
                })
        else:
            status = RuleResult.REVIEW if images_count < 2 else RuleResult.FAIL
            rules_evaluated.append({
                "rule_code": "LMR_002",
                "rule_name": "Maximum Retail Price (MRP)",
                "status": status,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Mandatory MRP declaration in Rupees inclusive of all taxes.",
                "severity": "HIGH" if status == RuleResult.FAIL else "MEDIUM",
                "legal_citation": "Rule 6(1)(e), LMR 2011",
                "is_mandatory": True,
                "explanation": "MRP was not found on the visible panels. Often printed on back or top flaps.",
                "corrective_action": "Print MRP clearly with words 'Inclusive of all taxes'."
            })

        # ==========================================================
        # 3. NET QUANTITY (Rule 6(1)(c) & Rule 11)
        # ==========================================================
        net_qty = extracted_fields.get("net_quantity")
        if not is_empty(net_qty):
            qty_str = str(net_qty).strip()
            # Check for standard Legal Metrology units: g, kg, ml, l, N, U
            valid_units = re.compile(r"^\d+(?:\.\d+)?\s*(?:mg|g|kg|ml|l|litre|litres|liter|liters|n|u|units?)\b", re.IGNORECASE)
            if valid_units.search(qty_str):
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "status": RuleResult.PASS,
                    "detected_value": qty_str,
                    "expected_requirement": "Net weight, measure, or number of units in standard metric units.",
                    "severity": "NONE",
                    "legal_citation": "Rule 6(1)(c) & Rule 11, LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity is declared in standard metric units.",
                    "corrective_action": None
                })
            else:
                rules_evaluated.append({
                    "rule_code": "LMR_003",
                    "rule_name": "Net Quantity Declaration",
                    "status": RuleResult.REVIEW,
                    "detected_value": qty_str,
                    "expected_requirement": "Standard metric unit (g, kg, ml, L, N). Non-standard units (e.g. gms, pkt) are discouraged.",
                    "severity": "LOW",
                    "legal_citation": "Rule 11, LMR 2011",
                    "is_mandatory": True,
                    "explanation": "Net quantity unit requires verification to ensure standard symbol usage.",
                    "corrective_action": "Use standard symbols 'g', 'kg', 'ml', 'L', or 'N' with proper space."
                })
        else:
            status = RuleResult.REVIEW if images_count < 2 else RuleResult.FAIL
            rules_evaluated.append({
                "rule_code": "LMR_003",
                "rule_name": "Net Quantity Declaration",
                "status": status,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Net quantity must be declared on the principal display panel.",
                "severity": "HIGH" if status == RuleResult.FAIL else "MEDIUM",
                "legal_citation": "Rule 6(1)(c), LMR 2011",
                "is_mandatory": True,
                "explanation": "Net quantity declaration was not found on the captured panels.",
                "corrective_action": "Declare net weight or volume on the principal display panel."
            })

        # ==========================================================
        # 4. MANUFACTURER / PACKER / IMPORTER DETAILS (Rule 6(1)(a))
        # ==========================================================
        mfg_name = extracted_fields.get("manufacturer_name") or extracted_fields.get("packer_name") or extracted_fields.get("importer_name")
        mfg_addr = extracted_fields.get("manufacturer_address") or extracted_fields.get("packer_address") or extracted_fields.get("importer_address")

        if not is_empty(mfg_name) and not is_empty(mfg_addr):
            rules_evaluated.append({
                "rule_code": "LMR_004",
                "rule_name": "Manufacturer / Packer / Importer Details",
                "status": RuleResult.PASS,
                "detected_value": f"{mfg_name} | {mfg_addr}",
                "expected_requirement": "Name and complete address of the manufacturer, packer, or importer.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(a), LMR 2011",
                "is_mandatory": True,
                "explanation": "Complete manufacturer/packer identity and address are declared.",
                "corrective_action": None
            })
        elif not is_empty(mfg_name):
            rules_evaluated.append({
                "rule_code": "LMR_004",
                "rule_name": "Manufacturer / Packer / Importer Details",
                "status": RuleResult.REVIEW,
                "detected_value": str(mfg_name),
                "expected_requirement": "Both name and complete physical address must be declared.",
                "severity": "LOW",
                "legal_citation": "Rule 6(1)(a), LMR 2011",
                "is_mandatory": True,
                "explanation": "Manufacturer name detected; address could not be fully parsed from this angle.",
                "corrective_action": "Ensure complete postal address including PIN code is clearly legible."
            })
        else:
            status = RuleResult.REVIEW if images_count < 2 else RuleResult.FAIL
            rules_evaluated.append({
                "rule_code": "LMR_004",
                "rule_name": "Manufacturer / Packer / Importer Details",
                "status": status,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Name and address of manufacturer or packer must be stated.",
                "severity": "HIGH" if status == RuleResult.FAIL else "MEDIUM",
                "legal_citation": "Rule 6(1)(a), LMR 2011",
                "is_mandatory": True,
                "explanation": "Manufacturer information not detected on visible panels.",
                "corrective_action": "Declare complete name and address of manufacturer or packer."
            })

        # ==========================================================
        # 5. MANUFACTURING / PACKING DATE (Rule 6(1)(d))
        # ==========================================================
        mfg_date = extracted_fields.get("mfg_date") or extracted_fields.get("packing_date")
        if not is_empty(mfg_date):
            rules_evaluated.append({
                "rule_code": "LMR_005",
                "rule_name": "Month & Year of Manufacture / Packing",
                "status": RuleResult.PASS,
                "detected_value": str(mfg_date),
                "expected_requirement": "Month and year of manufacture, packing, or pre-packing.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(d), LMR 2011",
                "is_mandatory": True,
                "explanation": "Manufacturing/packing date is declared.",
                "corrective_action": None
            })
        else:
            status = RuleResult.REVIEW if images_count < 2 else RuleResult.FAIL
            rules_evaluated.append({
                "rule_code": "LMR_005",
                "rule_name": "Month & Year of Manufacture / Packing",
                "status": status,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Month and year of manufacture or packing.",
                "severity": "MEDIUM" if status == RuleResult.FAIL else "LOW",
                "legal_citation": "Rule 6(1)(d), LMR 2011",
                "is_mandatory": True,
                "explanation": "Date of manufacture/packing not found on captured panels.",
                "corrective_action": "Print month and year of manufacture/packing prominently."
            })

        # ==========================================================
        # 6. EXPIRY DATE / BEST BEFORE (Rule 6(1)(d) & FSSAI)
        # ==========================================================
        exp_date = extracted_fields.get("expiry_date") or extracted_fields.get("best_before")
        if not is_empty(exp_date):
            rules_evaluated.append({
                "rule_code": "LMR_006",
                "rule_name": "Expiry Date / Best Before",
                "status": RuleResult.PASS,
                "detected_value": str(exp_date),
                "expected_requirement": "Expiry date or 'Best Before' period for perishable commodities.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(d) Proviso, LMR 2011",
                "is_mandatory": False,
                "explanation": "Expiry/Best before date is declared.",
                "corrective_action": None
            })
        else:
            rules_evaluated.append({
                "rule_code": "LMR_006",
                "rule_name": "Expiry Date / Best Before",
                "status": RuleResult.REVIEW,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Required for food products and commodities that may deteriorate over time.",
                "severity": "LOW",
                "legal_citation": "Rule 6(1)(d) Proviso, LMR 2011",
                "is_mandatory": False,
                "explanation": "Expiry date was not visible. Non-perishable items are exempt.",
                "corrective_action": "If applicable to perishable goods, declare 'Best Before' or 'Expiry Date'."
            })

        # ==========================================================
        # 7. CONSUMER CARE DETAILS (Rule 6(1)(da))
        # ==========================================================
        care_val = extracted_fields.get("consumer_care") or extracted_fields.get("consumer_care_phone") or extracted_fields.get("consumer_care_email")
        if not is_empty(care_val):
            rules_evaluated.append({
                "rule_code": "LMR_007",
                "rule_name": "Consumer Care Details",
                "status": RuleResult.PASS,
                "detected_value": str(care_val),
                "expected_requirement": "Name, address, telephone number, and email address of the consumer care contact.",
                "severity": "NONE",
                "legal_citation": "Rule 6(1)(da), LMR 2011",
                "is_mandatory": True,
                "explanation": "Consumer care contact details are declared.",
                "corrective_action": None
            })
        else:
            status = RuleResult.REVIEW
            rules_evaluated.append({
                "rule_code": "LMR_007",
                "rule_name": "Consumer Care Details",
                "status": status,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Helpline number or email ID for consumer complaints.",
                "severity": "LOW",
                "legal_citation": "Rule 6(1)(da), LMR 2011",
                "is_mandatory": True,
                "explanation": "Consumer care helpline was not identified on the captured panels.",
                "corrective_action": "Provide customer care telephone number, email, and postal address."
            })

        # ==========================================================
        # 8. COUNTRY OF ORIGIN (Rule 6(10))
        # ==========================================================
        origin_val = extracted_fields.get("country_of_origin")
        if not is_empty(origin_val):
            rules_evaluated.append({
                "rule_code": "LMR_008",
                "rule_name": "Country of Origin",
                "status": RuleResult.PASS,
                "detected_value": str(origin_val),
                "expected_requirement": "Country of origin must be stated on imported and domestic packaged goods.",
                "severity": "NONE",
                "legal_citation": "Rule 6(10), LMR 2011 Amendment",
                "is_mandatory": False,
                "explanation": f"Origin declared as '{origin_val}'.",
                "corrective_action": None
            })
        else:
            rules_evaluated.append({
                "rule_code": "LMR_008",
                "rule_name": "Country of Origin",
                "status": RuleResult.REVIEW,
                "detected_value": "Not explicitly detected",
                "expected_requirement": "Country of origin statement (e.g. 'Made in India').",
                "severity": "LOW",
                "legal_citation": "Rule 6(10), LMR 2011 Amendment",
                "is_mandatory": False,
                "explanation": "Origin statement not explicitly identified; often implied by domestic manufacturer address.",
                "corrective_action": "Declare 'Country of Origin: India' or appropriate manufacturing country."
            })

        # ==========================================================
        # 9. FSSAI LICENSE NUMBER (Food Safety Act / LMR)
        # ==========================================================
        fssai_val = extracted_fields.get("fssai_number")
        if not is_empty(fssai_val):
            fssai_str = str(fssai_val).strip()
            if len(fssai_str) == 14 and fssai_str.isdigit():
                rules_evaluated.append({
                    "rule_code": "FSSAI_001",
                    "rule_name": "FSSAI License Number",
                    "status": RuleResult.PASS,
                    "detected_value": f"FSSAI Lic. No. {fssai_str}",
                    "expected_requirement": "14-digit FSSAI License Number with Logo for food products.",
                    "severity": "NONE",
                    "legal_citation": "FSS (Packaging & Labelling) Reg. 2011",
                    "is_mandatory": False,
                    "explanation": "Valid 14-digit FSSAI license number declared.",
                    "corrective_action": None
                })
            else:
                rules_evaluated.append({
                    "rule_code": "FSSAI_001",
                    "rule_name": "FSSAI License Number",
                    "status": RuleResult.REVIEW,
                    "detected_value": fssai_str,
                    "expected_requirement": "Exactly 14 numeric digits.",
                    "severity": "LOW",
                    "legal_citation": "FSS (Packaging & Labelling) Reg. 2011",
                    "is_mandatory": False,
                    "explanation": "FSSAI number detected but character count is not 14.",
                    "corrective_action": "Verify 14-digit FSSAI registration number."
                })
        else:
            rules_evaluated.append({
                "rule_code": "FSSAI_001",
                "rule_name": "FSSAI License Number",
                "status": RuleResult.REVIEW,
                "detected_value": "Not detected on scanned panel(s)",
                "expected_requirement": "Applicable for packaged food articles.",
                "severity": "LOW",
                "legal_citation": "FSS (Packaging & Labelling) Reg. 2011",
                "is_mandatory": False,
                "explanation": "FSSAI license was not detected. Non-food commodities are exempt.",
                "corrective_action": "If this is a food commodity, display 14-digit FSSAI license number."
            })

        # ==========================================================
        # 10. BARCODE / GTIN IDENTIFIER
        # ==========================================================
        barcode_val = extracted_fields.get("barcode")
        if not is_empty(barcode_val):
            rules_evaluated.append({
                "rule_code": "BARCODE_001",
                "rule_name": "Barcode / EAN-13 Identifier",
                "status": RuleResult.PASS,
                "detected_value": str(barcode_val),
                "expected_requirement": "Scannable GTIN/EAN-13 barcode for retail commodity tracking.",
                "severity": "NONE",
                "category": "PRODUCT_TRACKING",
                "legal_citation": "GS1 India / Retail Packaging Standards",
                "is_mandatory": False,
                "explanation": f"Barcode {barcode_val} decoded from packaging label. (Note: Barcode presence is label evidence; product identity is not verified against central national database).",
                "corrective_action": None
            })
        else:
            rules_evaluated.append({
                "rule_code": "BARCODE_001",
                "rule_name": "Barcode / EAN-13 Identifier",
                "status": RuleResult.REVIEW,
                "detected_value": "Not detected",
                "expected_requirement": "Retail barcode for product tracking.",
                "severity": "LOW",
                "category": "PRODUCT_TRACKING",
                "legal_citation": "GS1 Standards",
                "is_mandatory": False,
                "explanation": "Barcode was not present on the scanned faces or image angle.",
                "corrective_action": "Ensure barcode is clearly visible for digital inventory."
            })

        # ==========================================================
        # OVERALL COMPLIANCE VERDICT DETERMINATION
        # ==========================================================
        fail_items = [r for r in rules_evaluated if r["status"] == RuleResult.FAIL]
        review_items = [r for r in rules_evaluated if r["status"] == RuleResult.REVIEW]
        pass_items = [r for r in rules_evaluated if r["status"] == RuleResult.PASS]

        # Mandatory failures vs optional reviews
        mandatory_fails = [r for r in fail_items if r["is_mandatory"]]

        if mandatory_fails:
            overall_verdict = "non_compliant"
            verdict_text = "NON-COMPLIANT"
            verdict_summary = f"{len(mandatory_fails)} mandatory Legal Metrology requirement(s) violated."
        elif review_items:
            overall_verdict = "needs_review"
            verdict_text = "NEEDS MANUAL REVIEW"
            verdict_summary = f"{len(pass_items)} passed, {len(review_items)} declaration(s) require verification or multi-panel capture."
        else:
            overall_verdict = "compliant"
            verdict_text = "COMPLIANT WITH CHECKED REQUIREMENTS"
            verdict_summary = "All checked mandatory Legal Metrology packaging declarations verified successfully."

        # Compute accurate 0-100 score
        # Pass = +10 pts, Review = +5 pts, Fail = 0 pts
        total_possible = len(rules_evaluated) * 10
        earned_points = sum(
            10 if r["status"] == RuleResult.PASS else (5 if r["status"] == RuleResult.REVIEW else 0)
            for r in rules_evaluated
        )
        calculated_score = int(round((earned_points / total_possible) * 100))

        # Build violations format compatible with existing database and frontend
        violations_for_db = []
        for r in fail_items + review_items:
            violations_for_db.append({
                "rule_code": r["rule_code"],
                "rule_description": f"{r['rule_name']} ({r['status']})",
                "severity": r["severity"],
                "category": r.get("category", "LEGAL_METROLOGY"),
                "detail_text": f"{r['explanation']} [Expected: {r['expected_requirement']}]",
                "status": r["status"],
                "legal_citation": r["legal_citation"],
                "corrective_action": r["corrective_action"]
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