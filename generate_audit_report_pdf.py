# generate_audit_report_pdf.py
import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "LegalMetriX — Technical Codebase Audit & Feature Verification Report")
            self.drawRightString(612 - 54, 750, "SIH Project Assessment • Legal Metrology")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential — LegalMetriX Compliance Checker • Official Audit Dossier")
        self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_audit_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    NAVY = colors.HexColor("#0f172a")
    PRIMARY_BLUE = colors.HexColor("#1e40af")
    SLATE_TEXT = colors.HexColor("#334155")
    LIGHT_BG = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#cbd5e1")
    EMERALD = colors.HexColor("#059669")
    AMBER = colors.HexColor("#d97706")
    ROSE = colors.HexColor("#dc2626")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=NAVY,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=PRIMARY_BLUE,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=PRIMARY_BLUE,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=SLATE_TEXT,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=SLATE_TEXT,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2.5
    )

    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#64748b")
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10,
        textColor=SLATE_TEXT
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10,
        textColor=NAVY
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a")
    )

    badge_pass = ParagraphStyle(
        'BadgePass',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#065f46")
    )

    badge_partial = ParagraphStyle(
        'BadgePartial',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#92400e")
    )

    story = []

    # 1. Document Title & Metadata
    story.append(Paragraph("LegalMetriX — Codebase & Feature Audit Report", title_style))
    story.append(Paragraph("Smart India Hackathon (SIH) Compliance Platform Inspection Dossier", subtitle_style))
    
    meta_table_data = [
        [
            Paragraph("<b>Target System:</b> LegalMetriX Compliance Checker", meta_style),
            Paragraph("<b>Audit Date:</b> September 2026", meta_style),
            Paragraph("<b>Audit Mode:</b> Zero-Modification / Read-Only", meta_style),
        ],
        [
            Paragraph("<b>Stack:</b> FastAPI • React (Vite) • PaddleOCR • Gemini 2.5", meta_style),
            Paragraph("<b>Statutory Scope:</b> Legal Metrology Rules, 2011", meta_style),
            Paragraph("<b>Verification Status:</b> 100% Grounded in Source Code", meta_style),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[180, 160, 164])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 2. Executive Summary Table
    story.append(Paragraph("Executive Audit Summary: 5 Target Features", h1_style))
    story.append(Paragraph("Direct inspection of frontend components, FastAPI routers, database schemas, local OCR providers, and cloud vision models:", body_style))

    summary_data = [
        [
            Paragraph("Feature", table_header),
            Paragraph("Status", table_header),
            Paragraph("Evidence in Code", table_header),
            Paragraph("Actual Working?", table_header),
            Paragraph("What is Missing", table_header),
        ],
        [
            Paragraph("<b>1. AI / LLM Extraction</b>", table_cell_bold),
            Paragraph("<font color='#059669'><b>IMPLEMENTED</b></font>", badge_pass),
            Paragraph("<code>gemini_vision.py:L40-140</code><br/><code>scans.py:L367-409</code>", table_cell),
            Paragraph("<b>Yes</b> (Gemini 2.5 Flash multimodal vision + Pydantic schema validation)", table_cell),
            Paragraph("None for basic extraction.", table_cell),
        ],
        [
            Paragraph("<b>2. Confidence & Uncertainty</b>", table_cell_bold),
            Paragraph("<font color='#059669'><b>IMPLEMENTED</b></font>", badge_pass),
            Paragraph("<code>fusion.py:L18-160</code><br/><code>scans.py:L105-156</code><br/><code>rules_engine.py:L444</code>", table_cell),
            Paragraph("<b>Yes</b> (3-tier system: OCR score %, fusion agreement %, and rule score)", table_cell),
            Paragraph("None. Discrepancies trigger <code>needs_review</code> status.", table_cell),
        ],
        [
            Paragraph("<b>3. Image Evidence / Highlighting</b>", table_cell_bold),
            Paragraph("<font color='#d97706'><b>PARTIAL</b></font>", badge_partial),
            Paragraph("<code>ocr.py:L112-150</code><br/><code>extractor.py:L120-133</code><br/><code>ScanPage.tsx:L1264</code>", table_cell),
            Paragraph("<b>Partial</b> (Panel side switching & backend coordinates work; main canvas overlay missing)", table_cell),
            Paragraph("Visual polygon bounding box overlay on the main scan preview canvas.", table_cell),
        ],
        [
            Paragraph("<b>4. Mobile-First Field Inspection</b>", table_cell_bold),
            Paragraph("<font color='#059669'><b>IMPLEMENTED</b></font>", badge_pass),
            Paragraph("<code>CameraCapture.tsx:L1-351</code><br/><code>Navigation.tsx:L130-147</code><br/><code>offlineQueue.ts</code>", table_cell),
            Paragraph("<b>Yes</b> (Rear camera capture, mobile gallery upload, bottom nav, offline queue)", table_cell),
            Paragraph("Native mobile PWA push notifications (optional).", table_cell),
        ],
        [
            Paragraph("<b>5. Hardware Dependency</b>", table_cell_bold),
            Paragraph("<font color='#059669'><b>NO SPECIAL HARDWARE</b></font>", badge_pass),
            Paragraph("<code>barcode.py:L8-71</code><br/><code>ocr.py:L56-163</code>", table_cell),
            Paragraph("<b>Yes</b> (100% software & cloud browser-based architecture)", table_cell),
            Paragraph("None. Works on any smartphone camera + browser.", table_cell),
        ]
    ]

    summary_table = Table(summary_data, colWidths=[90, 75, 110, 115, 114])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # 3. In-Depth Feature Verification
    story.append(Paragraph("1. Detailed Technical Verification of Target Features", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=6))

    # Feature 1
    story.append(Paragraph("Feature 1: AI / LLM-Based Extraction (Status: IMPLEMENTED)", h2_style))
    story.append(Paragraph("• <b>Model & SDK:</b> Utilizes <code>gemini-2.5-flash</code> via the official <code>google-genai</code> Python SDK in <code>backend/app/services/gemini_vision.py</code>.", bullet_style))
    story.append(Paragraph("• <b>Multimodal Binary Flow:</b> In <code>scans.py</code> (lines 367–409), uploaded image files are read as raw binary bytes and passed directly to the Gemini API as multimodal <code>types.Part.from_bytes(...)</code> payloads.", bullet_style))
    story.append(Paragraph("• <b>Structured Schema Extraction:</b> Enforces strict JSON return via Pydantic model <code>GeminiProductLabelData</code> extracting: product/brand name, MRP, net quantity value & unit, mfg/packing/expiry dates, manufacturer/packer/importer names & registered addresses, consumer care contact details, country of origin, FSSAI license number, and barcodes.", bullet_style))
    story.append(Paragraph("• <b>Anti-Hallucination Guardrails:</b> System prompt explicitly mandates: <i>'If a value is not visible or cannot be read confidently across any side, leave it as null. If any field is blurry or uncertain, do NOT guess; set it to null and add the field name to uncertain_fields'</i>. Temperature is locked at <code>0.1</code> for deterministic parsing.", bullet_style))

    # Feature 2
    story.append(Paragraph("Feature 2: Confidence / Uncertainty System (Status: IMPLEMENTED)", h2_style))
    story.append(Paragraph("• <b>3-Tier Confidence Architecture:</b> The system computes and returns three distinct confidence signals on every scan:", bullet_style))
    story.append(Paragraph("   1. <i>OCR Confidence:</i> Real mathematical average recognition certainty (0–100%) calculated directly from PaddleOCR polygon token scores.", bullet_style))
    story.append(Paragraph("   2. <i>Extraction Agreement Confidence:</i> Calculated in <code>fusion.py</code> (96% when local OCR and Gemini normalize identically, 82–88% for single-source resolution, and 65% for conflicting extractions).", bullet_style))
    story.append(Paragraph("   3. <i>Statutory Compliance Score:</i> Computed in <code>rules_engine.py</code> based on mandatory declaration coverage weighted against statutory violations.", bullet_style))
    story.append(Paragraph("• <b>Dispute Resolution:</b> Critical field mismatches automatically set <code>needs_manual_review = True</code>, setting scan status to <code>NEEDS_REVIEW</code> and preventing uncertain AI outputs from being treated as established facts.", bullet_style))

    # Feature 3
    story.append(Paragraph("Feature 3: Image Evidence / Highlighting (Status: PARTIAL)", h2_style))
    story.append(Paragraph("• <b>Implemented:</b> PaddleOCR extracts 4-point polygon coordinates (<code>bounding_boxes</code>) in <code>ocr.py</code>. <code>extractor.py</code> links each declaration to its bounding box (<code>record_evidence</code>). In <code>ScanPage.tsx</code>, selecting any declaration automatically switches the UI to the correct panel side (Front, Back, Left, Right) with an active badge.", bullet_style))
    story.append(Paragraph("• <b>Missing:</b> The main scan page preview currently does not draw the visual coordinate bounding boxes (Canvas/SVG rectangles) directly over the image, and the complaint creation handler does not forward coordinate boxes into <code>findingEvidences</code>.", bullet_style))

    story.append(PageBreak())

    # Feature 4
    story.append(Paragraph("Feature 4: Mobile-First Field Inspection (Status: IMPLEMENTED)", h2_style))
    story.append(Paragraph("• <b>Responsive Layout:</b> Complete Tailwind CSS responsive design with mobile viewport adaptation and a dedicated <b>Mobile Bottom Tab Navigation Bar</b> in <code>Navigation.tsx</code>.", bullet_style))
    story.append(Paragraph("• <b>Rear Camera & WebRTC:</b> <code>CameraCapture.tsx</code> connects to the smartphone camera with <code>facingMode: { ideal: 'environment' }</code> (rear camera default), camera flip toggle, viewfinder alignment guidelines, and client-side compression via <code>imageCompressor.ts</code>.", bullet_style))
    story.append(Paragraph("• <b>Offline Field Queue:</b> <code>offlineQueue.ts</code> provides an IndexedDB offline storage layer enabling enforcement officers to record scans in zero-connectivity field zones and sync upon returning online.", bullet_style))
    story.append(Paragraph("• <b>Desktop Dependency:</b> None. All workflows (Capture → Crop → Extraction → Officer Review → PDF Notice) operate smoothly on mobile smartphones.", bullet_style))

    # Feature 5
    story.append(Paragraph("Feature 5: Hardware Dependency (Status: NO SPECIAL HARDWARE REQUIRED)", h2_style))
    story.append(Paragraph("• <b>Software-Driven Architecture:</b> Barcode/QR code decoding is handled natively in software via OpenCV and PyZBar (<code>app/barcode.py</code>).", bullet_style))
    story.append(Paragraph("• <b>Zero Edge Hardware:</b> No Raspberry Pi, external cameras, load cells, or handheld hardware scanners are required. Any standard smartphone camera + web browser can execute the complete statutory inspection workflow.", bullet_style))

    story.append(Spacer(1, 8))

    # 4. Architecture Section
    story.append(Paragraph("A. Actual System Pipeline Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=6))
    
    arch_box_data = [
        [Paragraph("""
<b>[ Packaging Label Input ]</b> (Smartphone Camera / Multi-Panel Gallery Upload / 360° Video Keyframe Extractor)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;│<br/>
&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
<b>[ Client-Side Optimization ]</b> (imageCompressor.ts • imageQuality.ts • ImageCropModal.tsx • offlineQueue.ts)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;│<br/>
&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
<b>[ FastAPI Multi-Engine Backend: POST /api/scans/ ]</b> (app/routers/scans.py)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;├───▶ <b>1. PyZBar / OpenCV Barcode Engine</b> (app/barcode.py) ➔ EAN-13, UPC, Code 128, QR Codes<br/>
&nbsp;&nbsp;&nbsp;&nbsp;├───▶ <b>2. Local PaddleOCR Engine</b> (app/ocr.py + app/extractor.py) ➔ Raw text segments & polygon boxes<br/>
&nbsp;&nbsp;&nbsp;&nbsp;└───▶ <b>3. Cloud Gemini 2.5 Flash Vision Layer</b> (app/services/gemini_vision.py) ➔ Structured Pydantic JSON<br/>
&nbsp;&nbsp;&nbsp;&nbsp;│<br/>
&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
<b>[ Fusion & Reconciliation Engine ]</b> (app/fusion.py)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Differential comparison of Local OCR vs. Gemini extraction<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• 3-Tier Confidence Calculation (OCR %, Fusion Agreement %, Statutory Rule Score)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Discrepancy flagging & source attribution tagging<br/>
&nbsp;&nbsp;&nbsp;&nbsp;│<br/>
&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
<b>[ Deterministic Statutory Rules Engine ]</b> (app/rules_engine.py)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Evaluates Rule 6(1)(a)-(h), Rule 11, Rule 12 (LMR 2011) & FSSAI Standards<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Produces Verdict: COMPLIANT / NEEDS REVIEW / NON-COMPLIANT<br/>
&nbsp;&nbsp;&nbsp;&nbsp;│<br/>
&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
<b>[ Officer Enforcement Dashboard & Verification Panel ]</b> (ScanPage.tsx / ScanDetail.tsx)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Duplicate product inspection detection & one-click statutory value override<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• Official PDF Inspection Report & Legal Notice Generator (app/reports.py via ReportLab)<br/>
&nbsp;&nbsp;&nbsp;&nbsp;• SQLite / PostgreSQL Audit Database Persistence (app/models.py)
        """, code_style)]
    ]
    arch_table = Table(arch_box_data, colWidths=[504])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 10))

    # 5. Core Differentiators
    story.append(Paragraph("B. Core Architectural Differentiators", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=6))
    story.append(Paragraph("1. <b>Hybrid Multi-Engine Fusion Layer:</b> Rather than blindly relying on OCR or LLMs alone, LegalMetriX performs dual-source reconciliation. When PaddleOCR and Gemini agree, confidence is elevated to 96% (Double-Verified). When they conflict, the system flags a discrepancy for officer resolution.", bullet_style))
    story.append(Paragraph("2. <b>Deterministic Legal Citations:</b> The AI is strictly restricted to extraction; legal verdicts are determined by a rule engine mapping directly to Legal Metrology Rules, 2011 (e.g. Rule 6(1)(e) for MRP, Rule 11 for Metric Units, Rule 6(1)(d) for Dates).", bullet_style))
    story.append(Paragraph("3. <b>Multi-Panel & 360° Video Keyframe Extractor:</b> Addresses cylindrical and multi-faceted packaged goods by synthesizing Front, Back, Left, and Right faces into a unified declaration audit docket.", bullet_style))
    story.append(Paragraph("4. <b>Enforcement Tooling:</b> Includes duplicate product scan tracking to flag repeat offenders, an offline IndexedDB scan queue, and instant ReportLab PDF enforcement notices.", bullet_style))

    story.append(Spacer(1, 10))

    # 6. Top 3 Missing Features
    story.append(Paragraph("C. Top 3 Missing Features (Prioritized for SIH)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=6))
    story.append(Paragraph("1. <b>Visual Coordinate Bounding-Box Overlay on Image Canvas (Priority: High):</b> Connect the PaddleOCR polygon coordinates extracted in <code>ocr.py</code> to render color-coded SVG/Canvas rectangles (Green for Compliant, Red for Violation) directly over the label preview image.", bullet_style))
    story.append(Paragraph("2. <b>Font Size & Numeral Height Compliance (Rule 7 & Schedule II):</b> Implement physical numeral height measurement relative to package surface area to verify statutory minimum millimeter font requirements (2mm, 4mm, 6mm).", bullet_style))
    story.append(Paragraph("3. <b>Dual-MRP & Price Sticker Tampering Detection (Section 18):</b> Add dual-MRP conflict detection and edge-detection filters to catch price stickers illegally pasted over manufacturer pre-printed prices.", bullet_style))

    story.append(Spacer(1, 10))

    # 7. Audit Compliance Notice
    story.append(Paragraph("D. Audit Verification Checkpoint", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=6))
    story.append(Paragraph("<b>DO NOT MODIFY Compliance:</b> All source code files, configurations, database models, and UI components in the project repository remain completely unmodified. This document serves as the official static codebase audit record.", body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.getcwd(), "LegalMetriX_Codebase_Audit_Report.pdf")
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    build_audit_pdf(out_file)
