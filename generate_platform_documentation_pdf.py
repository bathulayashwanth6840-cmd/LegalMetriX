# generate_platform_documentation_pdf.py
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
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
            self.drawString(54, 750, "LegalMetriX — Platform Specification & Statutory Reference Manual")
            self.drawRightString(612 - 54, 750, "Legal Metrology Packaged Commodities")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential — Legal Metrology Statutory Enforcement & AI Assessment Platform")
        self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def generate_pdf(output_path):
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
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=21,
        leading=25,
        textColor=NAVY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=PRIMARY_BLUE,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=SLATE_TEXT,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-6,
        spaceAfter=2.5
    )

    story = []

    # ── PAGE 1: TITLE, META, OVERVIEW, MODULES ──────────────────────────────────
    story.append(Paragraph("LegalMetriX — Platform Specification & Statutory Manual", title_style))
    story.append(Paragraph("End-to-End Legal Metrology Packaged Commodity Compliance, Inspection, Complaint & Enquiry Tracking System", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=8))

    meta_data = [
        [
            Paragraph("<b>Live Deployment URL:</b> https://legal-metrology-dist-three.vercel.app/", body_style),
            Paragraph("<b>Statutory Reference:</b> Legal Metrology Act, 2009", body_style)
        ],
        [
            Paragraph("<b>Frontend Framework:</b> React 18 + Vite + TypeScript + Tailwind v4", body_style),
            Paragraph("<b>Compliance Standard:</b> Packaged Commodities Rules, 2011", body_style)
        ],
        [
            Paragraph("<b>AI Assistance Engine:</b> PaddleOCR + Gemini Vision (Dual-Pass)", body_style),
            Paragraph("<b>Release Version:</b> v2.4.0 (Enterprise Enforcement Suite)", body_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[255, 249])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Executive Summary & Core Mission", h1_style))
    story.append(Paragraph(
        "<b>LegalMetriX</b> is a dedicated statutory compliance, inspection auditing, complaint management, and enquiry tracking platform engineered to enforce the <b>Legal Metrology (Packaged Commodities) Rules, 2011</b> and the <b>Legal Metrology Act, 2009</b> across Indian retail and commercial markets.",
        body_style
    ))
    story.append(Paragraph(
        "The platform bridges physical ground seizures and digital statutory governance by integrating multi-modal optical package capture with automated declaration extraction, intelligent non-compliance flagging, departmental case escalation, authorized officer verification, and sanitized citizen grievance tracking.",
        body_style
    ))

    story.append(Paragraph("2. System Architecture & Functional Modules", h1_style))

    modules = [
        ("Multi-Modal Package Scanner", "Supports 3 flexible capture workflows: Single Image quick scan, 4-Panel Multi-Surface Capture (Front, Back, Left, Right with cropping and quality diagnostics), and 360° Rotational Continuous Video Capture with automated motion-blur rejection and sharp keyframe synthesis."),
        ("AI Evidence & Extraction Layer", "Employs an intelligent dual-pass PaddleOCR and Gemini Vision pipeline with strict anti-hallucination guardrails: unverified or smudged text is never guessed. AI results are strictly labeled PASS, POTENTIAL VIOLATION, or NEEDS VERIFICATION."),
        ("Statutory Rule Engine", "Evaluates all mandatory declarations under Rule 6(1) and Rule 12: Maximum Retail Price (MRP inclusive of taxes), Net Quantity with standard units, Complete Manufacturer/Packer Name & Address with PIN code, Manufacturing/Packing Date, Expiry/Best Before, Consumer Care Telephone & Email, and Country of Origin."),
        ("8-Stage Complaint & Enquiry Docket", "Manages formal legal enforcement proceedings from initial seizure to final closure across 8 standardized lifecycle stages: Submitted, Under Review, Further Enquiry, Awaiting Verification, Verified Violation, Not Verified, Action Taken, and Closed."),
        ("Multi-Persona Role Switcher", "Provides authenticated persona toggling between Inspector (field seizure and preliminary finding referral), Senior Official (statutory determination, legal notice issuance, laboratory transfer), and Citizen Consumer (public grievance tracking)."),
        ("Citizen Public Tracking Portal", "Allows public consumers to track grievance dossiers by Complaint ID (e.g. LM-2026-XXXXXX). Implements mandatory privacy redaction, keeping internal enforcement notes, investigation memos, and officer contact details strictly confidential."),
        ("Compliance Assessment Reports", "Generates certified statutory assessment documents with declaration audit breakdown, rule non-conformance tags, evidence image bounding boxes, and official officer seal hashes (formally titled Inspection / Compliance Assessment Reports).")
    ]

    for title, desc in modules:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    story.append(PageBreak())

    # ── PAGE 2: LIFECYCLE, DECISION PRINCIPLES, TECH STACK ──────────────────────
    story.append(Paragraph("3. Statutory 8-Stage Complaint & Enquiry Lifecycle", h1_style))
    story.append(Paragraph(
        "Every potential violation detected during market sampling can be escalated into a formal Complaint Docket. The case progresses through an immutable, auditable statutory workflow:",
        body_style
    ))

    lifecycle_table = [
        ["Stage #", "Status Name", "Statutory Role & Enforcement Action", "Public Visibility"],
        ["1", "Submitted", "New complaint docket registered and linked to original Inspection ID.", "Visible"],
        ["2", "Under Review", "AI detection layer flags potential Rule 6 / Rule 12 non-conformances.", "Visible"],
        ["3", "Further Enquiry", "Escalated to Zonal Enforcement, Prosecution, or Laboratory Wings.", "Visible (Safe Msg)"],
        ["4", "Awaiting Verification", "Assigned to Senior Officer for statutory physical & legal determination.", "Visible (Safe Msg)"],
        ["5", "Verified Violation", "Officer confirms breach under Legal Metrology Act, 2009 (Sections 18/36).", "Visible (Notice Issued)"],
        ["6", "Not Verified", "Sample verified compliant upon physical caliper / measurement inspection.", "Visible (Resolved)"],
        ["7", "Action Taken", "Compounding fee recovered, seizure executed, or notice served.", "Visible (Action Logged)"],
        ["8", "Closed", "Case dossier officially archived with digital verification certificate.", "Visible (Closed)"]
    ]

    t_life = Table(lifecycle_table, colWidths=[38, 102, 296, 68])
    t_life.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('LEADING', (0,0), (-1,-1), 9.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_life)
    story.append(Spacer(1, 8))

    story.append(Paragraph("4. Statutory Decision-Making & AI Guardrails", h1_style))
    story.append(Paragraph(
        "<b>Core Statutory Guardrail:</b> Under Indian Administrative Law and the Legal Metrology Act, 2009, an Artificial Intelligence system cannot issue binding penal determinations. LegalMetriX enforces this principle at the architectural level:",
        body_style
    ))

    guardrails = [
        ("AI Decision Separation", "AI model outputs are restricted to 'PASS', 'POTENTIAL VIOLATION', and 'NEEDS VERIFICATION'. They serve strictly as assistive cues for inspecting officers."),
        ("Authorized Human Sign-Off", "Only an authorized official (Inspector or Deputy Controller) holding valid statutory credentials can mark a case as 'VERIFIED VIOLATION', 'NOT VERIFIED', 'ACTION TAKEN', or 'CLOSED'."),
        ("Tamper-Evident Digital Seal", "Official determinations generate an immutable verification hash (e.g. SEAL-LM-DIR-XXXX) logged in the permanent audit trail."),
        ("No Misleading Legal Scores", "Overall compliance percentages are presented strictly as supporting diagnostic metrics rather than final legal judgments.")
    ]

    for title, desc in guardrails:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    story.append(Spacer(1, 8))

    story.append(Paragraph("5. Technical Architecture & Endpoints", h1_style))
    
    tech_specs = [
        ["Layer", "Technology", "Description & Implementation"],
        ["Frontend UI", "React 18, TypeScript, Vite", "Ultra-fast Single Page App with sub-400ms production builds."],
        ["Styling Engine", "Tailwind CSS v4", "High-contrast governmental theme (Navy #0f172a, Saffron #f59e0b)."],
        ["Local Persistence", "IndexedDB & LocalStorage", "Resilient offline caching and automatic schema synchronization."],
        ["Offline PWA", "Vite PWA / Workbox", "Zero-downtime offline inspection recording with background sync."],
        ["API Services", "FastAPI REST Ready", "Structured endpoint client (/api/scans, /api/complaints, /api/reports)."],
        ["Internationalization", "Custom i18n Context", "Full trilingual localization support in English, Hindi, and Telugu."]
    ]

    t_tech = Table(tech_specs, colWidths=[85, 125, 294])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('LEADING', (0,0), (-1,-1), 9.5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_tech)

    story.append(PageBreak())

    # ── PAGE 3: DIRECTORY STRUCTURE & OPERATIONAL WORKFLOW ─────────────────────────
    story.append(Paragraph("6. Codebase Architecture & File Structure", h1_style))
    
    structure_text = """
    <b>src/pages/ (Core Page Views)</b><br/>
    &nbsp;&nbsp;• <b>HomePage.tsx:</b> Executive enforcement dashboard, 8-status metrics counters, 360° scanner spotlight.<br/>
    &nbsp;&nbsp;• <b>ScanPage.tsx:</b> 4-stage inspection wizard (Upload, Keyframe Extraction, Review, Rule Verification & Escalation).<br/>
    &nbsp;&nbsp;• <b>ComplaintsPage.tsx:</b> Complete complaint registry, status filtering, search bar, and clean empty state.<br/>
    &nbsp;&nbsp;• <b>ComplaintDetailPage.tsx:</b> Comprehensive dossier with AI evidence ROI boxes, official verification, and audit logs.<br/>
    &nbsp;&nbsp;• <b>TrackComplaintPage.tsx:</b> Public citizen grievance tracker with sanitized progress updates.<br/>
    &nbsp;&nbsp;• <b>ReportsPage.tsx:</b> Official statutory inspection and assessment reports catalogue.<br/>
    &nbsp;&nbsp;• <b>HistoryPage.tsx:</b> Field inspection history log with batch delete and report download options.<br/><br/>
    <b>src/components/ (Interactive Statutory UI Elements)</b><br/>
    &nbsp;&nbsp;• <b>RoleSwitcher.tsx:</b> Persona toggle (Inspector, Senior Official, Citizen).<br/>
    &nbsp;&nbsp;• <b>ForwardModal.tsx:</b> Departmental case escalation dialog.<br/>
    &nbsp;&nbsp;• <b>VerificationModal.tsx:</b> Statutory determination and digital seal signing dialog.<br/>
    &nbsp;&nbsp;• <b>EvidenceModal.tsx:</b> Cropped photographic evidence and OCR ROI bounding box inspector.<br/>
    &nbsp;&nbsp;• <b>NewComplaintModal.tsx:</b> Manual complaint docket filing modal.<br/>
    &nbsp;&nbsp;• <b>Navigation.tsx:</b> Top navigation bar with language picker, role badge, and route links.<br/><br/>
    <b>src/services/ & src/types/ (Business Logic & Types)</b><br/>
    &nbsp;&nbsp;• <b>complaintService.ts:</b> Data store, CRUD, timeline generator, and public tracking sanitizer.<br/>
    &nbsp;&nbsp;• <b>api.ts:</b> REST API client abstraction.<br/>
    &nbsp;&nbsp;• <b>complaint.ts:</b> Core TypeScript data models.
    """
    story.append(Paragraph(structure_text, body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("7. Operational Instructions for Demonstration", h1_style))
    instructions = [
        ("Conducting a Fresh Inspection", "Navigate to '/scan' -> Upload packaging images or record 360° video -> The AI pipeline extracts mandatory declarations -> If any Rule 6 breach occurs, click 'Create Complaint / Enquiry' to generate an official LM-2026-XXXXXX dossier."),
        ("Escalating to Higher Authority", "Open the Complaint Dossier -> Click 'Forward for Further Enquiry' -> Select target authority (Prosecution Cell, Laboratory Wing) and specify grounds -> Case transitions to 'Further Enquiry'."),
        ("Official Statutory Verification", "Switch persona to 'Senior Official' -> Open Complaint Dossier -> Click 'Official Verification' -> Select verdict ('Verified Violation' / 'Action Taken') -> Enter statutory observations -> Seal with digital signature hash."),
        ("Citizen Public Verification", "Navigate to '/track' -> Search using the Complaint ID -> Review sanitized, tamper-evident progression timeline without exposing confidential notes.")
    ]

    for title, desc in instructions:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    out_dir = r"C:\Users\Bathula Yashwanth\.gemini\antigravity-ide\scratch\LegalMetriX"
    out_file = os.path.join(out_dir, "LegalMetriX_Platform_Documentation.pdf")
    generate_pdf(out_file)
    print(f"PDF successfully generated at: {out_file}")
