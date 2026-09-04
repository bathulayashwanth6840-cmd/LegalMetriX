import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)
REPORT_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_fpdf_report(scan_data: dict, file_path: str):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Colors
    NAVY = (15, 23, 42)
    BLUE = (30, 64, 175)
    GREEN = (22, 101, 52)
    AMBER = (180, 83, 9)
    RED = (185, 28, 28)
    GRAY_TEXT = (71, 85, 105)
    BORDER_GRAY = (226, 232, 240)
    HEADER_BG = (248, 250, 252)

    # ── Official Header ───────────────────────────────────────────
    pdf.set_fill_color(255, 153, 51) # Saffron strip
    pdf.rect(10, 10, 63, 3, 'F')
    pdf.set_fill_color(255, 255, 255) # White strip
    pdf.rect(73, 10, 64, 3, 'F')
    pdf.set_fill_color(19, 136, 8) # Green strip
    pdf.rect(137, 10, 63, 3, 'F')

    pdf.set_y(16)
    pdf.set_font('helvetica', 'B', 15)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, 'LEGAL METROLOGY COMPLIANCE INSPECTION REPORT', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('helvetica', 'B', 8.5)
    pdf.set_text_color(*GRAY_TEXT)
    pdf.cell(0, 5, 'DEPARTMENT OF CONSUMER AFFAIRS - LEGAL METROLOGY DIVISION (PACKAGED COMMODITIES)', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('helvetica', 'I', 7.5)
    pdf.cell(0, 4, f'Generated On: {datetime.now().strftime("%d %B %Y, %H:%M:%S IST")} | Docket ID: LM-SCAN-{scan_data.get("id")}', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_draw_color(*BORDER_GRAY)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # ── Executive Summary & Status Card ───────────────────────────
    status = str(scan_data.get("status", "pending")).lower()
    score = scan_data.get("compliance_score", {}).get("score", 85) if isinstance(scan_data.get("compliance_score"), dict) else 85
    product_name = scan_data.get("product_name") or "Packaged Commodity Sample"

    # Summary Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, pdf.get_y(), 190, 24, 'FD')
    start_y = pdf.get_y()

    pdf.set_xy(14, start_y + 2.5)
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(95, 5, f'Product: {str(product_name)[:45]}', new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(14, start_y + 8)
    pdf.set_font('helvetica', '', 8.5)
    pdf.set_text_color(*GRAY_TEXT)
    pdf.cell(95, 4.5, f'Inspection Case #: {scan_data.get("id")} | Barcode: {scan_data.get("barcode") or "N/A"}', new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(14, start_y + 13.5)
    pdf.cell(95, 4.5, f'Standard: Legal Metrology Rules, 2011 & FSSAI Reg., 2011', new_x="LMARGIN", new_y="NEXT")

    # Score Gauge Box on Right
    pdf.set_xy(125, start_y + 2.5)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(70, 4, f'STATUTORY SCORE: {score}/100', align='R', new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(125, start_y + 9)
    pdf.set_font('helvetica', 'B', 11)
    if status == 'compliant':
        pdf.set_text_color(*GREEN)
        pdf.cell(70, 6, 'VERDICT: COMPLIANT', align='R')
    elif status == 'needs_review':
        pdf.set_text_color(*AMBER)
        pdf.cell(70, 6, 'VERDICT: NEEDS MANUAL REVIEW', align='R')
    else:
        pdf.set_text_color(*RED)
        pdf.cell(70, 6, 'VERDICT: NON-COMPLIANT', align='R')

    pdf.set_y(start_y + 28)

    # ── Section 1A: Legal Metrology (LMR 2011) Declarations ──────────
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, '1A. Legal Metrology Mandatory Declarations (LMR 2011)', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)

    # Table Header
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('helvetica', 'B', 7.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(50, 5.5, 'Declaration / Field Name', border=1, fill=True)
    pdf.cell(85, 5.5, 'Verified Value / Content', border=1, fill=True)
    pdf.cell(25, 5.5, 'Panel Source', border=1, fill=True)
    pdf.cell(30, 5.5, 'Verification Status', border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    # Table Rows
    fields = scan_data.get("extracted_fields", {}).get("semantic_fields", {})
    fusion_fields = scan_data.get("extracted_fields", {}).get("fusion_fields", {})
    
    lmr_items = [
        ("Product / Generic Name", "product_name"),
        ("Maximum Retail Price (MRP)", "mrp"),
        ("Net Quantity", "net_quantity"),
        ("Manufacturer / Packer Name", "manufacturer_name"),
        ("Manufacturer Address", "manufacturer_address"),
        ("Date of Mfg / Packing", "mfg_date"),
        ("Consumer Care Details", "consumer_care"),
        ("Country of Origin", "country_of_origin")
    ]

    # Map evaluated rules for exact state lookup
    rules_eval_list = scan_data.get("rules_evaluated") or scan_data.get("extracted_fields", {}).get("rules_evaluated", [])
    rule_by_key = {r.get("field_key"): r for r in rules_eval_list if isinstance(r, dict) and r.get("field_key")}

    pdf.set_font('helvetica', '', 7.5)
    for label, key in lmr_items:
        val = str(fields.get(key) or "Not Detected")
        meta = fusion_fields.get(key, {})
        side = str(meta.get("source_side", "Front")).upper()
        rule_info = rule_by_key.get(key, {})
        state = rule_info.get("detection_state")

        pdf.set_text_color(*NAVY)
        pdf.cell(50, 4.8, label, border=1)

        pdf.set_text_color(30, 41, 59)
        pdf.cell(85, 4.8, val[:48], border=1)

        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(25, 4.8, side, border=1)

        if state == 'VERIFIED' or (val != 'Not Detected' and not meta.get('conflict')):
            pdf.set_text_color(*GREEN)
            pdf.cell(30, 4.8, 'Verified (Pass)', border=1, new_x="LMARGIN", new_y="NEXT")
        elif state == 'NOT_VISIBLE':
            pdf.set_text_color(*AMBER)
            pdf.cell(30, 4.8, 'Not Visible (Review)', border=1, new_x="LMARGIN", new_y="NEXT")
        elif state == 'UNCLEAR':
            pdf.set_text_color(*AMBER)
            pdf.cell(30, 4.8, 'Unclear (Review)', border=1, new_x="LMARGIN", new_y="NEXT")
        elif state == 'NEEDS_MANUAL_REVIEW':
            pdf.set_text_color(*AMBER)
            pdf.cell(30, 4.8, 'Discrepancy (Review)', border=1, new_x="LMARGIN", new_y="NEXT")
        elif state == 'CONFIRMED_MISSING':
            pdf.set_text_color(*RED)
            pdf.cell(30, 4.8, 'Confirmed Missing', border=1, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_text_color(*AMBER)
            pdf.cell(30, 4.8, 'Not Detected (Review)', border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # ── Section 1B: Food Safety Standards (FSSAI 2011) & Barcode ─────
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, '1B. Food Safety Standards (FSSAI 2011) & Barcode Tracking', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)

    fssai_items = [
        ("FSSAI License Number", "fssai_number"),
        ("Expiry Date / Best Before", "expiry_date"),
        ("Barcode (GTIN / EAN-13)", "barcode")
    ]

    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('helvetica', 'B', 7.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(50, 5.5, 'Standard / Identifier', border=1, fill=True)
    pdf.cell(85, 5.5, 'Detected Value', border=1, fill=True)
    pdf.cell(25, 5.5, 'Panel Source', border=1, fill=True)
    pdf.cell(30, 5.5, 'Registry Status', border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('helvetica', '', 7.5)
    for label, key in fssai_items:
        val = str(fields.get(key) or "Not Detected")
        meta = fusion_fields.get(key, {})
        side = str(meta.get("source_side", "Front")).upper()

        pdf.set_text_color(*NAVY)
        pdf.cell(50, 4.8, label, border=1)

        pdf.set_text_color(30, 41, 59)
        pdf.cell(85, 4.8, val[:48], border=1)

        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(25, 4.8, side, border=1)

        if key == "barcode":
            status_text = "Label Evidence (Unverified)" if val != "Not Detected" else "Not Present"
            pdf.set_text_color(*(AMBER if val != "Not Detected" else GRAY_TEXT))
        elif key == "fssai_number" and len(val) == 14 and val.isdigit():
            status_text = "Valid Format"
            pdf.set_text_color(*GREEN)
        else:
            status_text = "Declared" if val != "Not Detected" else "Exempt / Absent"
            pdf.set_text_color(*(NAVY if val != "Not Detected" else GRAY_TEXT))

        pdf.cell(30, 4.8, status_text, border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # ── Section 2: Rule Violations & Review Actions ───────────────
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, '2. Statutory Findings & Violations', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)

    violations = scan_data.get("violations", [])
    if not violations:
        pdf.set_font('helvetica', 'I', 8.5)
        pdf.set_text_color(*GREEN)
        pdf.cell(0, 5.5, 'No statutory violations detected. Product meets checked Legal Metrology requirements.', new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font('helvetica', 'B', 7.5)
        pdf.set_text_color(*NAVY)
        pdf.cell(24, 5.5, 'Rule Code', border=1, fill=True)
        pdf.cell(106, 5.5, 'Statutory Finding / Requirement', border=1, fill=True)
        pdf.cell(25, 5.5, 'Severity', border=1, fill=True)
        pdf.cell(35, 5.5, 'Status', border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font('helvetica', '', 7.5)
        for v in violations:
            code = str(v.get("rule_code", "LMR_RULE"))
            desc = str(v.get("detail_text") or v.get("rule_description") or "")
            sev = str(v.get("severity", "MEDIUM")).upper()
            st = str(v.get("status", "REVIEW")).upper()

            pdf.set_text_color(*NAVY)
            pdf.cell(24, 4.8, code, border=1)

            pdf.set_text_color(51, 65, 85)
            pdf.cell(106, 4.8, desc[:65], border=1)

            if sev == 'HIGH':
                pdf.set_text_color(*RED)
            elif sev == 'LOW':
                pdf.set_text_color(*GREEN)
            else:
                pdf.set_text_color(*AMBER)
            pdf.cell(25, 4.8, sev, border=1)

            pdf.set_text_color(*NAVY)
            pdf.cell(35, 4.8, st, border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    # ── Section 3: Officer Override & Verification Audit Trail ────
    officer_overrides = scan_data.get("extracted_fields", {}).get("officer_overrides", {})
    if officer_overrides:
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 6, '3. Officer Override & Verification Audit Trail', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)

        pdf.set_fill_color(241, 245, 249)
        pdf.set_font('helvetica', 'B', 7.5)
        pdf.set_text_color(*NAVY)
        pdf.cell(35, 5.5, 'Field Name', border=1, fill=True)
        pdf.cell(50, 5.5, 'Original AI/OCR Value', border=1, fill=True)
        pdf.cell(50, 5.5, 'Officer-Verified Value', border=1, fill=True)
        pdf.cell(55, 5.5, 'Timestamp & Reason', border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font('helvetica', '', 7.5)
        for f_name, o_info in officer_overrides.items():
            orig = str(o_info.get("original_value") or "None")
            verified = str(o_info.get("officer_value") or "None")
            reason_text = str(o_info.get("reason", "Manual correction"))

            pdf.set_text_color(*NAVY)
            pdf.cell(35, 4.8, f_name, border=1)
            pdf.set_text_color(*RED)
            pdf.cell(50, 4.8, orig[:30], border=1)
            pdf.set_text_color(*GREEN)
            pdf.cell(50, 4.8, verified[:30], border=1)
            pdf.set_text_color(*GRAY_TEXT)
            pdf.cell(55, 4.8, reason_text[:35], border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # ── Section 4: Official Sign-Off ──────────────────────────────
    pdf.set_draw_color(*BORDER_GRAY)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font('helvetica', 'I', 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 4, 'This electronic inspection report is generated by LegalMetriX AI Compliance Engine in accordance with Legal Metrology Act, 2009.', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.output(file_path)


def generate_pdf_report(scan_data: dict) -> str:
    unique_filename = f"report_{scan_data.get('id')}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(REPORT_DIR, unique_filename)
    generate_fpdf_report(scan_data, file_path)
    return file_path
