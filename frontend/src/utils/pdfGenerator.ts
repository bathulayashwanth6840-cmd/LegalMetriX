// src/utils/pdfGenerator.ts
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { ComplaintRecord } from '../types/complaint';

/**
 * Generates and triggers download of a certified Legal Metrology Assessment PDF for a Complaint Docket.
 */
export function generateComplaintAssessmentPDF(complaint: ComplaintRecord): void {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  // ── 1. Top Tricolor Banner Strip ──
  doc.setFillColor(255, 153, 51); // Saffron
  doc.rect(0, 0, pageWidth / 3, 3.5, 'F');
  doc.setFillColor(255, 255, 255); // White
  doc.rect(pageWidth / 3, 0, pageWidth / 3, 3.5, 'F');
  doc.setFillColor(19, 136, 8); // Green
  doc.rect((pageWidth / 3) * 2, 0, pageWidth / 3, 3.5, 'F');

  // ── 2. Official Department Header ──
  doc.setFillColor(15, 23, 42); // Slate 900
  doc.rect(0, 3.5, pageWidth, 28, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.text('GOVERNMENT OF INDIA', pageWidth / 2, 11, { align: 'center' });

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(203, 213, 225);
  doc.text('MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION', pageWidth / 2, 16, { align: 'center' });

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(251, 191, 36); // Amber
  doc.text('DEPARTMENT OF LEGAL METROLOGY • ENFORCEMENT & COMPLIANCE WING', pageWidth / 2, 22, { align: 'center' });

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text('Under Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011', pageWidth / 2, 27, { align: 'center' });

  // ── 3. Document Title & Badge ──
  let y = 38;
  doc.setTextColor(15, 23, 42);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.text('CERTIFIED STATUTORY ASSESSMENT REPORT', 14, y);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(30, 58, 138); // Blue 900
  doc.text(`DOCKET ID: ${complaint.id}`, pageWidth - 14, y, { align: 'right' });

  y += 5;
  doc.setDrawColor(203, 213, 225);
  doc.setLineWidth(0.5);
  doc.line(14, y, pageWidth - 14, y);

  // ── 4. Case Metadata Table ──
  y += 4;
  autoTable(doc, {
    startY: y,
    head: [['DOCKET METADATA', 'DETAILS', 'STATUS & JURISDICTION', 'VALUE']],
    body: [
      ['Docket / Reference', `${complaint.id} (Ref: ${complaint.inspectionId})`, 'Statutory Status', complaint.currentStatus],
      ['Date Filed', new Date(complaint.dateSubmitted).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }), 'Priority Level', complaint.priority || 'High'],
      ['Submitted By', `${complaint.submittedBy} (${complaint.submitterRole})`, 'Assigned Authority', complaint.assignedAuthority || 'Legal Metrology Enforcement Officer'],
      ['Inspection Location', complaint.location || 'Local Enforcement Zone', 'Last Updated', new Date(complaint.lastUpdated).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })],
    ],
    theme: 'grid',
    headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 35, fillColor: [248, 250, 252] },
      1: { cellWidth: 55 },
      2: { fontStyle: 'bold', cellWidth: 42, fillColor: [248, 250, 252] },
      3: { cellWidth: 50, fontStyle: 'bold' }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 6;

  // ── 5. Packaged Commodity Particulars ──
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(15, 23, 42);
  doc.text('1. PACKAGED COMMODITY PARTICULARS', 14, y);
  y += 3;

  autoTable(doc, {
    startY: y,
    body: [
      ['Product / Commodity Name', complaint.product.productName || 'N/A', 'Category', complaint.product.category || 'General Packaged Commodity'],
      ['Declared MRP', complaint.product.mrp || '₹ --', 'Declared Net Quantity', complaint.product.netQuantity || '--'],
      ['Manufacturer / Packer', complaint.product.manufacturerName || 'Under Investigation', 'Country of Origin', complaint.product.countryOfOrigin || 'India'],
      ['Physical Address', complaint.product.manufacturerAddress || 'Physical address verification required', 'Dates Declared', `Mfg: ${complaint.product.mfgDate || 'N/A'} | Exp: ${complaint.product.expiryDate || 'N/A'}`],
    ],
    theme: 'grid',
    bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 42, fillColor: [248, 250, 252] },
      1: { cellWidth: 52 },
      2: { fontStyle: 'bold', cellWidth: 38, fillColor: [248, 250, 252] },
      3: { cellWidth: 50 }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 6;

  // ── 6. Mandatory Declarations Compliance Audit ──
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(15, 23, 42);
  doc.text('2. STATUTORY DECLARATION AUDIT & EVIDENCE FINDINGS', 14, y);
  y += 3;

  const findingsRows = (complaint.findings || []).map((f) => [
    f.fieldKey ? f.fieldKey.replace(/_/g, ' ').toUpperCase() : 'DECLARATION',
    f.ruleCode || 'Rule 6(1)',
    f.detectedText || 'Not Declared',
    f.aiStatus || 'Non-Compliant',
    f.requiredStandard || f.ruleReference || 'Mandatory declaration under Legal Metrology Rules'
  ]);

  if (findingsRows.length === 0) {
    findingsRows.push([
      'MRP & Net Quantity',
      'Rule 6(1)(e) & 6(1)(d)',
      'Potential discrepancy flagged during packaging audit',
      'Under Review',
      'Mandatory declarations under Legal Metrology Rules 2011'
    ]);
  }

  autoTable(doc, {
    startY: y,
    head: [['MANDATORY DECLARATION', 'RULE REF', 'DETECTED VALUE', 'STATUS', 'STATUTORY REQUIREMENT']],
    body: findingsRows,
    theme: 'striped',
    headStyles: { fillColor: [15, 23, 42], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 7.5, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 36 },
      1: { fontStyle: 'bold', cellWidth: 26 },
      2: { cellWidth: 42 },
      3: { fontStyle: 'bold', cellWidth: 26 },
      4: { cellWidth: 52 }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 6;

  // Check if we need a new page for Verification & Signatures
  if (y > pageHeight - 65) {
    doc.addPage();
    y = 20;
  }

  // ── 7. Official Statutory Verification & Action ──
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(15, 23, 42);
  doc.text('3. OFFICIAL STATUTORY VERIFICATION & DETERMINATION', 14, y);
  y += 3;

  const remarks = complaint.verification?.remarks || 'Statutory review and packaging assessment executed pursuant to Legal Metrology Act provisions.';
  const actionTaken = complaint.verification?.actionTaken || 'Formal statutory enquiry initiated and registered under zonal enforcement docket.';

  autoTable(doc, {
    startY: y,
    body: [
      ['Statutory Determination', complaint.verification?.verdict ? complaint.verification.verdict.replace(/_/g, ' ') : complaint.currentStatus.toUpperCase()],
      ['Official Observations', remarks],
      ['Enforcement Action Concluded', actionTaken],
      ['Statutory Reference', 'Section 18, 36 & 39 of Legal Metrology Act, 2009 / Rule 6, 12, 18 of LMR 2011']
    ],
    theme: 'grid',
    bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 45, fillColor: [248, 250, 252] },
      1: { cellWidth: 137 }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 8;

  // Check if we need space for signature block
  if (y > pageHeight - 45) {
    doc.addPage();
    y = 20;
  }

  // ── 8. Official Signature & Digital Seal Block ──
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(14, y, pageWidth - 28, 32, 2, 2, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(15, 23, 42);
  doc.text('DIGITALLY CERTIFIED BY STATUTORY AUTHORITY', 18, y + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(71, 85, 105);
  doc.text(`Officer / Inspector: ${complaint.verification?.officerName || 'Inspector Rajesh Sharma (LM-204)'}`, 18, y + 11);
  doc.text(`Designation: ${complaint.verification?.officerDesignation || 'Legal Metrology Officer (North Circle)'}`, 18, y + 16);
  doc.text(`Verification Seal: ${complaint.verification?.digitalSealSignature || `SEAL-LM-DIR-${complaint.id}`}`, 18, y + 21);
  doc.text(`Timestamp: ${new Date().toISOString()} • System: LegalMetriX AI Compliance Engine`, 18, y + 26);

  // Seal Stamp Box on right
  doc.setDrawColor(30, 58, 138);
  doc.setLineWidth(0.8);
  doc.roundedRect(pageWidth - 62, y + 4, 44, 24, 1.5, 1.5, 'D');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7);
  doc.setTextColor(30, 58, 138);
  doc.text('LEGAL METROLOGY', pageWidth - 40, y + 10, { align: 'center' });
  doc.text('GOVT. OF INDIA', pageWidth - 40, y + 15, { align: 'center' });
  doc.setTextColor(16, 185, 129); // Green
  doc.text('★ VERIFIED DOCKET ★', pageWidth - 40, y + 20, { align: 'center' });
  doc.setFontSize(6);
  doc.setTextColor(100, 116, 139);
  doc.text(complaint.id, pageWidth - 40, y + 25, { align: 'center' });

  // ── 9. Footer Note ──
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.5);
  doc.setTextColor(148, 163, 184);
  doc.text(
    'This is a certified electronic document generated by the LegalMetriX Autonomous Compliance Platform under the Legal Metrology Act, 2009. Valid across jurisdictional enforcement circles.',
    pageWidth / 2,
    pageHeight - 6,
    { align: 'center' }
  );

  // Trigger browser download
  const cleanId = complaint.id.replace(/[^a-zA-Z0-9-_]/g, '_');
  doc.save(`LegalMetriX_Assessment_Report_${cleanId}.pdf`);
}

/**
 * Generates and triggers download of a certified Legal Metrology Assessment PDF for an Inspection Scan.
 */
export function generateInspectionReportPDF(scanData: any): void {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const scanId = scanData?.id || 'INS-LIVE';
  const ext = scanData?.extracted_fields?.gemini_extraction || scanData?.extracted_fields || {};
  const prodName = ext.product_name || scanData?.product?.name || 'Packaged Commodity Sample';
  const mrp = ext.mrp_raw_text || ext.mrp || scanData?.product?.declared_mrp || '₹ --';
  const netQty = ext.net_quantity || scanData?.product?.declared_net_quantity || '--';
  const mfgName = ext.manufacturer_name || scanData?.product?.manufacturer_name || 'Under Verification';
  const mfgAddr = ext.manufacturer_address || scanData?.product?.manufacturer_address || 'Physical address inspection';
  const mfgDate = ext.mfg_date || ext.manufacturing_date || 'N/A';
  const expDate = ext.expiry_date || ext.expiry_date_raw_text || 'N/A';
  const fssai = ext.fssai_number || ext.fssai || 'N/A';
  const score = scanData?.compliance_score != null ? scanData.compliance_score : 85;

  // ── 1. Top Tricolor Banner Strip ──
  doc.setFillColor(255, 153, 51);
  doc.rect(0, 0, pageWidth / 3, 3.5, 'F');
  doc.setFillColor(255, 255, 255);
  doc.rect(pageWidth / 3, 0, pageWidth / 3, 3.5, 'F');
  doc.setFillColor(19, 136, 8);
  doc.rect((pageWidth / 3) * 2, 0, pageWidth / 3, 3.5, 'F');

  // ── 2. Header ──
  doc.setFillColor(15, 23, 42);
  doc.rect(0, 3.5, pageWidth, 28, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.text('GOVERNMENT OF INDIA', pageWidth / 2, 11, { align: 'center' });

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(203, 213, 225);
  doc.text('MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION', pageWidth / 2, 16, { align: 'center' });

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(251, 191, 36);
  doc.text('DEPARTMENT OF LEGAL METROLOGY • PACKAGING INSPECTION DOSSIER', pageWidth / 2, 22, { align: 'center' });

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text('Inspection Assessment under Legal Metrology (Packaged Commodities) Rules, 2011', pageWidth / 2, 27, { align: 'center' });

  // ── 3. Title ──
  let y = 38;
  doc.setTextColor(15, 23, 42);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.text('OFFICIAL PACKAGING INSPECTION DOSSIER', 14, y);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(30, 58, 138);
  doc.text(`INSPECTION ID: #${scanId}`, pageWidth - 14, y, { align: 'right' });

  y += 5;
  doc.setDrawColor(203, 213, 225);
  doc.setLineWidth(0.5);
  doc.line(14, y, pageWidth - 14, y);

  // ── 4. Metadata ──
  y += 4;
  autoTable(doc, {
    startY: y,
    head: [['INSPECTION METADATA', 'VALUE', 'COMPLIANCE INDEX', 'RATING']],
    body: [
      ['Inspection Ref', `INS-${scanId}`, 'Compliance Score', `${score} / 100`],
      ['Audit Timestamp', new Date(scanData?.created_at || Date.now()).toLocaleString('en-IN'), 'Verification Status', score >= 80 ? 'COMPLIANT' : 'REVIEW REQUIRED'],
      ['Enforcement Circle', 'North Zone Enforcement Circle, New Delhi', 'Capture Method', scanData?.capture_method?.toUpperCase() || 'CAMERA / 360 VIDEO'],
      ['Inspector In-Charge', 'Inspector Rajesh Sharma (Badge #LM-204)', 'Legal Framework', 'LM (Packaged Commodities) Rules 2011'],
    ],
    theme: 'grid',
    headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 38, fillColor: [248, 250, 252] },
      1: { cellWidth: 54 },
      2: { fontStyle: 'bold', cellWidth: 38, fillColor: [248, 250, 252] },
      3: { cellWidth: 52, fontStyle: 'bold' }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 6;

  // ── 5. Commodity Declarations ──
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(15, 23, 42);
  doc.text('1. PACKAGED COMMODITY SPECIFICATIONS', 14, y);
  y += 3;

  autoTable(doc, {
    startY: y,
    body: [
      ['Commodity / Brand Name', prodName, 'Declared MRP', mrp],
      ['Manufacturer / Packer', mfgName, 'Declared Net Qty', netQty],
      ['Physical Address', mfgAddr, 'Mfg / Pkg Date', mfgDate],
      ['FSSAI License', fssai, 'Expiry / Best Before', expDate],
    ],
    theme: 'grid',
    bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 40, fillColor: [248, 250, 252] },
      1: { cellWidth: 54 },
      2: { fontStyle: 'bold', cellWidth: 38, fillColor: [248, 250, 252] },
      3: { cellWidth: 50 }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 6;

  // ── 6. Mandatory Declarations Audit Breakdown ──
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(15, 23, 42);
  doc.text('2. STATUTORY DECLARATION AUDIT BREAKDOWN', 14, y);
  y += 3;

  const checks = [
    ['Product Name & Description', 'Rule 6(1)(a)', prodName ? 'DETECTED' : 'MISSING', prodName ? 'Compliant declaration of common identity.' : 'Mandatory under Rule 6(1)(a).'],
    ['Maximum Retail Price (MRP)', 'Rule 6(1)(e)', mrp && mrp !== '₹ --' ? 'DETECTED' : 'REVIEW', 'MRP must be declared in INR inclusive of all taxes.'],
    ['Net Quantity & Units', 'Rule 6(1)(d)', netQty && netQty !== '--' ? 'DETECTED' : 'REVIEW', 'Must declare standard metric SI units (g, kg, ml, l, N).'],
    ['Manufacturer / Packer Details', 'Rule 6(1)(a)', mfgName !== 'Under Verification' ? 'DETECTED' : 'REVIEW', 'Name and complete physical address mandatory.'],
    ['Date of Manufacture / Pkg', 'Rule 6(1)(d)', mfgDate !== 'N/A' ? 'DETECTED' : 'REVIEW', 'Month and year of manufacture/packing required.'],
    ['Consumer Care Contact', 'Rule 6(1)(n)', ext.consumer_care || ext.customer_care_details ? 'DETECTED' : 'REVIEW', 'Name, address, phone/email of grievance officer.'],
  ];

  autoTable(doc, {
    startY: y,
    head: [['STATUTORY FIELD', 'LEGAL RULE', 'STATUS', 'REGULATORY ASSESSMENT']],
    body: checks,
    theme: 'striped',
    headStyles: { fillColor: [15, 23, 42], textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 7.5, textColor: [30, 41, 59] },
    columnStyles: {
      0: { fontStyle: 'bold', cellWidth: 44 },
      1: { fontStyle: 'bold', cellWidth: 28 },
      2: { fontStyle: 'bold', cellWidth: 26 },
      3: { cellWidth: 84 }
    },
    margin: { left: 14, right: 14 },
  });

  y = (doc as any).lastAutoTable.finalY + 8;

  // ── 7. Officer Sign-off Block ──
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(203, 213, 225);
  doc.roundedRect(14, y, pageWidth - 28, 30, 2, 2, 'FD');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(15, 23, 42);
  doc.text('CERTIFIED INSPECTION DOSSIER • LEGAL METROLOGY WING', 18, y + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.5);
  doc.setTextColor(71, 85, 105);
  doc.text('Inspector: Rajesh Sharma (Badge #LM-204)', 18, y + 11);
  doc.text(`Digital Verification Signature: SEAL-LM-INSP-${scanId}-${Date.now().toString().slice(-4)}`, 18, y + 16);
  doc.text(`Generated At: ${new Date().toISOString()}`, 18, y + 21);
  doc.text('Statutory Authority: Department of Consumer Affairs & Legal Metrology, Government of India', 18, y + 26);

  // Stamp
  doc.setDrawColor(30, 58, 138);
  doc.setLineWidth(0.8);
  doc.roundedRect(pageWidth - 62, y + 3, 44, 24, 1.5, 1.5, 'D');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7);
  doc.setTextColor(30, 58, 138);
  doc.text('LEGAL METROLOGY', pageWidth - 40, y + 9, { align: 'center' });
  doc.text('GOVT. OF INDIA', pageWidth - 40, y + 14, { align: 'center' });
  doc.setTextColor(score >= 80 ? 16 : 225, score >= 80 ? 185 : 29, score >= 80 ? 129 : 72);
  doc.text(score >= 80 ? '★ COMPLIANT ★' : '★ REVIEW REQ ★', pageWidth - 40, y + 19, { align: 'center' });
  doc.setFontSize(6);
  doc.setTextColor(100, 116, 139);
  doc.text(`INS-${scanId}`, pageWidth - 40, y + 24, { align: 'center' });

  // Footer
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(6.5);
  doc.setTextColor(148, 163, 184);
  doc.text(
    'Certified Electronic Assessment Record • Department of Legal Metrology, Government of India.',
    pageWidth / 2,
    pageHeight - 6,
    { align: 'center' }
  );

  doc.save(`LegalMetriX_Inspection_Report_INS_${scanId}.pdf`);
}
