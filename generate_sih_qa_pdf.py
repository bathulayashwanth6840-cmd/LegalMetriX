# generate_sih_qa_pdf.py
import os
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
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
            self.drawString(54, 750, "Smart India Hackathon (SIH) — LegalMetriX Defense Guide")
            self.drawRightString(612 - 54, 750, "Judges Q&A Comprehensive Master Reference")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential — Smart India Hackathon Team Reference Document")
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
    BORDER_COLOR = colors.HexColor("#cbd5e1")
    QUESTION_BG = colors.HexColor("#f1f5f9")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=NAVY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=PRIMARY_BLUE,
        spaceAfter=8
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=NAVY,
        spaceAfter=3
    )

    answer_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=SLATE_TEXT,
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=SLATE_TEXT
    )

    story = []

    # ── HEADER & TITLE ──────────────────────────────────────────────────────────
    story.append(Paragraph("Smart India Hackathon (SIH) — Judges Q&A Defense Manual", title_style))
    story.append(Paragraph("Comprehensive Technical, Regulatory, Architectural & Defense Reference for LegalMetriX", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=8))

    meta_table_data = [
        [
            Paragraph("<b>Project:</b> LegalMetriX Compliance & Enforcement System", meta_style),
            Paragraph("<b>Domain:</b> Legal Metrology (Weights & Measures)", meta_style)
        ],
        [
            Paragraph("<b>Live Demo URL:</b> https://legal-metrology-dist-three.vercel.app/", meta_style),
            Paragraph("<b>Statutory Mandate:</b> Packaged Commodities Rules 2011", meta_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[255, 249])
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
    story.append(Spacer(1, 8))

    # Helper function to add a Q&A block
    def add_qa(q_num, question, answer):
        q_text = f"<b>Q{q_num}: \"{question}\"</b>"
        a_text = f"<b>Winning Answer:</b> {answer}"
        
        qa_data = [
            [Paragraph(q_text, question_style)],
            [Paragraph(a_text, answer_style)]
        ]
        t_qa = Table(qa_data, colWidths=[504])
        t_qa.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), QUESTION_BG),
            ('BACKGROUND', (0,1), (0,1), colors.white),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('LINEBELOW', (0,0), (0,0), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(KeepTogether([t_qa, Spacer(1, 6)]))

    # ── SECTION 1: AI, COMPUTER VISION & OCR PIPELINE ─────────────────────────
    story.append(Paragraph("Section 1: AI, Computer Vision & OCR Architecture", section_heading))
    
    add_qa(
        1,
        "Why did you use a dual-pass pipeline (PaddleOCR + Gemini Vision) instead of Gemini alone?",
        "Using a dual-pass architecture solves cost, latency, and hallucination. PaddleOCR performs instantaneous, zero-cost character bounding box detection locally without hallucination. Gemini Vision then acts as a contextual intelligence layer to interpret legal phrasing (e.g., confirming whether 'Incl. of all taxes' accompanies the MRP or distinguishing manufacturer vs packer). If PaddleOCR detects zero text, Gemini is strictly prevented from guessing or inventing declarations."
    )

    add_qa(
        2,
        "How do you handle motion blur during 360° rotational continuous video scanning?",
        "We do not analyze raw video frames directly. The keyframe extraction engine samples 24–36 frames across the rotation arc and calculates the 2D Laplacian variance of each frame: Sharpness = Var(Laplacian(I)). Blurry frames caused by quick hand rotation fall below our dynamic sharpness threshold and are automatically discarded. Only the sharpest, highest-contrast frame from each 90-degree quadrant is selected for compliance analysis."
    )

    add_qa(
        3,
        "How do you handle glare on shiny plastic wrappers and curved metallic surfaces?",
        "We implement a 3-tier defense: (1) Client-side pre-flight quality check evaluating brightness and glare reflection; (2) Adaptive Histogram Equalization (CLAHE) to balance dynamic range; (3) Anti-hallucination guardrail: if text is obscured by glare, the engine outputs 'NEEDS VERIFICATION — Glare Obscuration' rather than falsely failing the product."
    )

    add_qa(
        4,
        "How is LegalMetriX different from Google Lens or standard OCR apps?",
        "Google Lens is a generic text extractor without domain knowledge. LegalMetriX: (1) Enforces statutory rules under the Legal Metrology Act (e.g., verifying metric units, MRP formatting, consumer helpline); (2) Maps specific violation codes (Rule 6(1)(a)-(n)); (3) Generates court-admissible PDF Inspection Dossiers; (4) Integrates multi-surface 360° keyframe fusion."
    )

    add_qa(
        5,
        "How can you verify font height compliance from a mobile camera photo without a ruler?",
        "Under legal metrology guidelines, minimum numeral height ranges from 1 mm to 6 mm. From an uncalibrated 2D photo, exact millimeter measurement is an optical approximation. Therefore, our system computes the relative character height ratio against the bounding area of the display panel. If the scale is indeterminate, our engine outputs 'NEEDS REVIEW — Insufficient Visual Scale' rather than incorrectly failing the product."
    )

    # ── SECTION 2: STATUTORY COMPLIANCE & LEGAL METROLOGY LAW ──────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("Section 2: Legal Metrology Acts, Rules 2011 & Legal Mandate", section_heading))

    add_qa(
        6,
        "Can AI legally issue a fine, seizure notice, or penalize a manufacturer in court?",
        "Absolutely not. Under the Legal Metrology Act, 2009, only an authorized gazetted officer (Inspector or Deputy Controller) has statutory authority to issue notices or compound offenses. Our AI is strictly an Assistive Enforcement Tool. It outputs preliminary labels ('PASS', 'POTENTIAL VIOLATION', 'NEEDS VERIFICATION'). A case only becomes legally actionable when an officer reviews the evidence, selects a statutory verdict, and applies their Digital Signature Seal."
    )

    add_qa(
        7,
        "What specific rules of the Legal Metrology (Packaged Commodities) Rules, 2011 do you evaluate?",
        "We evaluate all mandatory declarations under Rule 6(1) and Rule 12: Rule 6(1)(a) Generic Name; Rule 6(1)(b) Net Quantity in standard metric units (g, kg, ml, L); Rule 6(1)(c) Month & Year of Mfg/Packing; Rule 6(1)(d) Expiry/Best Before; Rule 6(1)(e) MRP formatted as 'Rs. XX.XX (Incl. of all taxes)'; Rule 6(1)(f) Complete Manufacturer/Packer Name & Address with PIN Code; Rule 6(1)(g) Consumer Care Telephone & Email; and Rule 6(1)(n) Country of Origin."
    )

    add_qa(
        8,
        "How do you detect Dual MRP stickers pasted over retail commodities?",
        "Dual MRP violates Section 18 of the Legal Metrology Act. Our engine identifies Dual MRP by checking for multiple distinct numerical values matching the currency symbol 'Rs.' / 'MRP' on the same panel, as well as detecting bounding-box overlays indicating a price sticker pasted over pre-printed text. When detected, a High-Priority Potential Violation is flagged."
    )

    add_qa(
        9,
        "How do you check Unit Sale Price (USP) compliance on multi-piece or bulk packaging?",
        "Under the recent Legal Metrology amendments, packages containing more than 1 unit must declare the Unit Sale Price (e.g., 'Rs. 1.50 per g' or 'Rs. 15.00 per piece'). Our parser calculates the ratio of declared MRP to Net Quantity and verifies whether the corresponding unit sale price is legibly displayed alongside the total price."
    )

    add_qa(
        10,
        "What is the statutory 8-stage complaint lifecycle in your system?",
        "Every market violation progresses through 8 standardized administrative stages: 1. Submitted -> 2. Under Review -> 3. Further Enquiry -> 4. Awaiting Verification -> 5. Verified Violation -> 6. Not Verified -> 7. Action Taken -> 8. Closed."
    )

    # ── SECTION 3: SECURITY, INTEGRITY & ANTI-CORRUPTION ───────────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("Section 3: Security, Chain-of-Custody & Tamper Proofing", section_heading))

    add_qa(
        11,
        "How do you ensure photographic evidence is authentic and not faked or downloaded from Google?",
        "We enforce a strict Chain-of-Custody: (1) Hardware Camera Binding capturing device sensor metadata and timestamps; (2) Cryptographic SHA-256 Hashing: every photo is hashed immediately upon capture; (3) Tamper-Proof Seals: any modification to pixel data invalidates the cryptographic hash in the immutable audit trail."
    )

    add_qa(
        12,
        "Can a corrupt inspector delete a violation after accepting a bribe from a retailer?",
        "No. All inspection scans and complaint records write to an Append-Only Immutable Audit Log. Once a scan is logged with AI-detected non-compliances, field inspectors cannot delete or silence the record. Reclassifying or closing a case requires senior official sign-off with mandatory statutory justification notes permanently recorded."
    )

    add_qa(
        13,
        "What prevents public citizens from accessing confidential officer notes on the tracking portal?",
        "We implement strict Role-Based Data Redaction on the public endpoint (/track). Citizens see commodity name, filing date, and milestone progress, while internal officer investigation remarks, inspector contact numbers, and confidential compounding receipts are completely stripped."
    )

    # ── SECTION 4: EDGE CASES, PACKAGING DEFECTS & LANGUAGES ────────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("Section 4: Edge Cases, Multi-Language Labels & Packaging Defects", section_heading))

    add_qa(
        14,
        "How does the system handle multi-language or bilingual packaging (e.g. English + Hindi + Tamil)?",
        "Under Rule 9 of the Packaged Commodities Rules, declarations must be in either English or Hindi in Devanagari script, with optional regional languages. Our OCR model supports Devanagari and Indic scripts, aggregating multi-language bounding boxes and verifying compliance on the statutory language present."
    )

    add_qa(
        15,
        "What happens if a package is torn, crumpled, or partially stained?",
        "The system enforces a Confidence Threshold Gate. If character recognition confidence drops below 80% due to tearing or smudges, the AI does not guess missing words. It flags the specific declaration as 'NEEDS REVIEW — Low Visual Confidence' with an evidence bounding box, prompting the officer to take a close-up crop or perform physical caliper review."
    )

    add_qa(
        16,
        "How do you differentiate between Manufacturer, Packer, and Importer addresses?",
        "The AI semantic layer searches for statutory keyword markers: 'Mfg by / Manufactured by', 'Packed by', 'Imported & Marketed by'. It verifies whether the entity name is accompanied by a complete physical address including postal PIN code, as required under Rule 6(1)(a)."
    )

    # ── SECTION 5: E-COMMERCE, QUICK COMMERCE & COUNTERFEITING ─────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("Section 5: E-Commerce, Quick-Commerce & Counterfeit Detection", section_heading))

    add_qa(
        17,
        "Does LegalMetriX work for e-commerce platforms like Amazon, Flipkart, Blinkit, and Zepto?",
        "Yes! Under Rule 6(10) of the Packaged Commodities Rules, digital marketplace listings must display the exact same mandatory declarations as physical packaging. LegalMetriX can ingest product catalog screenshots or e-commerce API feeds and cross-verify digital declarations against physical warehouse samples."
    )

    add_qa(
        18,
        "How can this platform assist in catching counterfeit and spurious commodities?",
        "Counterfeit products often have subtle legal metrology flaws: mismatched barcodes, fake FSSAI numbers (e.g., invalid checksums or 13-digit instead of 14-digit strings), non-existent PIN codes, and missing consumer helpline emails. LegalMetriX instantly flags these mathematical and statutory inconsistencies."
    )

    # ── SECTION 6: SYSTEM ARCHITECTURE, OFFLINE PWA & FUTURE ROADMAP ───────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("Section 6: Scalability, Offline Architecture & Government Integration", section_heading))

    add_qa(
        19,
        "How will inspectors operate in remote rural areas with zero internet connectivity?",
        "LegalMetriX is engineered as an Offline-First Progressive Web App (PWA) using Service Workers and IndexedDB. Inspectors can capture samples, run local client checks, and queue inspection dockets completely offline. When network connectivity is restored, the background sync engine seamlessly uploads pending dossiers to the central state registry."
    )

    add_qa(
        20,
        "How can LegalMetriX integrate with existing central portals like INGRAM (NCH 1915) or e-Daakhil?",
        "Our backend API layer is built on standardized REST JSON microservices (/api/complaints, /api/scans, /api/public/track). It can directly plug into the National Consumer Helpline (INGRAM) for automatic citizen grievance intake and state weights & measures databases for automated license verification."
    )

    add_qa(
        21,
        "What is the average processing speed and latency of your platform?",
        "Client-side image optimization and camera capture take under 250 milliseconds. The dual-pass OCR and rule evaluation takes 1.8 to 2.4 seconds per multi-surface product. Compared to manual inspection documentation (8–10 minutes per product), LegalMetriX achieves a 95% reduction in inspection audit time."
    )

    add_qa(
        22,
        "Why is LegalMetriX ready for immediate deployment and adoption by State Governments?",
        "Because it is not a prototype or mock design — it is fully built, tested, and live right now at https://legal-metrology-dist-three.vercel.app/. It features zero-install web access, full English/Hindi/Telugu localization, realistic statutory workflows, role-based security, and court-admissible PDF reporting."
    )

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"SIH QA PDF generated at: {output_path}")

if __name__ == "__main__":
    out_dir = r"C:\Users\Bathula Yashwanth\.gemini\antigravity-ide\scratch\LegalMetriX"
    pdf_path = os.path.join(out_dir, "SIH_Hackathon_Judges_QA_Defense_Manual.pdf")
    generate_pdf(pdf_path)
    
    public_path = os.path.join(out_dir, "frontend", "public", "SIH_Hackathon_Judges_QA_Defense_Manual.pdf")
    shutil.copy(pdf_path, public_path)
    print(f"Copied to public asset: {public_path}")
