import os
import uuid
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .. import schemas, models, auth, database, audit
from ..barcode import BarcodeDetector
from ..ocr import get_ocr_provider
from ..extractor import FieldExtractor
from ..rules_engine import RuleEngine
from ..services.gemini_vision import GeminiVisionService
from ..services.reconcile import reconcile_fields
from ..fusion import fuse_results

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/scans",
    tags=["Scans"]
)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Singletons initialized once to avoid reloading models on every request
_ocr_provider = get_ocr_provider()
_barcode_detector = BarcodeDetector()
_extractor = FieldExtractor()
_rule_engine = RuleEngine()
_gemini_vision = GeminiVisionService()


def calculate_compliance_score(extracted_fields: Dict[str, Any], violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates a realistic compliance score between 0 and 100 based on mandatory declarations and violations."""
    mandatory_fields = [
        "product_name", "manufacturer_name", "manufacturer_address",
        "net_quantity", "mrp", "mfg_date", "expiry_date",
        "consumer_care", "country_of_origin", "fssai_number"
    ]
    present_fields = [f for f in mandatory_fields if extracted_fields.get(f) and str(extracted_fields.get(f)).strip()]
    missing_fields = [f for f in mandatory_fields if f not in present_fields]
    
    # Base declaration coverage (0 to 100)
    coverage_ratio = len(present_fields) / len(mandatory_fields)
    base_score = coverage_ratio * 100.0

    fail_count = sum(1 for v in violations if v.get("status") == "FAIL" or v.get("severity") == "HIGH")
    review_count = sum(1 for v in violations if v.get("status") == "REVIEW" or v.get("severity") == "MEDIUM")
    low_count = sum(1 for v in violations if v.get("severity") == "LOW")

    deductions = (fail_count * 20) + (review_count * 8) + (low_count * 2)
    raw_score = base_score - deductions

    final_score = int(max(10, min(100, round(raw_score))))
    if not fail_count and len(present_fields) >= 7:
        final_score = max(final_score, 88)

    if final_score >= 90 and not fail_count:
        category = "Excellent / Compliant"
        grade = "A"
        color = "green"
    elif final_score >= 70 and not fail_count:
        category = "Good / Minor Issues"
        grade = "B"
        color = "yellow"
    elif final_score >= 40:
        category = "Needs Review"
        grade = "C"
        color = "orange"
    else:
        category = "High Risk / Non-Compliant"
        grade = "D"
        color = "red"

    return {
        "score": final_score,
        "max_score": 100,
        "grade": grade,
        "category": category,
        "color": color,
        "declarations_found": len(present_fields),
        "declarations_total": len(mandatory_fields),
        "missing_declarations": missing_fields,
        "violations_count": len(violations),
        "high_severity_count": fail_count,
        "medium_severity_count": review_count,
        "low_severity_count": low_count
    }


def compute_field_confidences(extracted_fields: Dict[str, Any], fusion_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Computes field-level confidence percentage and highlights critical fields needing review."""
    critical_fields = {"mrp", "net_quantity", "manufacturer_name", "manufacturer_address", "expiry_date"}
    field_confidences = {}

    for field_name, value in extracted_fields.items():
        if not value or not str(value).strip():
            field_confidences[field_name] = {
                "score": 0,
                "level": "LOW",
                "color": "red",
                "is_critical": field_name in critical_fields,
                "needs_review": field_name in critical_fields
            }
            continue

        fusion_info = fusion_fields.get(field_name, {}) if isinstance(fusion_fields, dict) else {}
        numeric_score = fusion_info.get("confidence_score")
        qual_conf = str(fusion_info.get("confidence", "")).lower()

        if numeric_score is None:
            if qual_conf == "high":
                numeric_score = 95
            elif qual_conf == "medium":
                numeric_score = 82
            else:
                numeric_score = 65

        if numeric_score >= 90:
            level = "HIGH"
            color = "green"
        elif numeric_score >= 70:
            level = "MEDIUM"
            color = "yellow"
        else:
            level = "LOW"
            color = "red"

        is_crit = field_name in critical_fields
        needs_review = is_crit and (level == "LOW" or numeric_score < 70)

        field_confidences[field_name] = {
            "score": numeric_score,
            "level": level,
            "color": color,
            "is_critical": is_crit,
            "needs_review": needs_review,
            "source_side": fusion_info.get("source_side", "front"),
            "bounding_box": fusion_info.get("bounding_box")
        }

    return field_confidences


def check_duplicate_product(db: Session, barcode: Optional[str], product_name: Optional[str], current_scan_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Checks the database for prior scans with matching barcode or product name."""
    prev_scan = None
    match_type = None

    if barcode and barcode.strip():
        query = db.query(models.Scan).filter(models.Scan.barcode == barcode.strip())
        if current_scan_id:
            query = query.filter(models.Scan.id != current_scan_id)
        prev_scan = query.order_by(models.Scan.created_at.desc()).first()
        if prev_scan:
            match_type = "barcode"

    if not prev_scan and product_name and product_name.strip() and len(product_name.strip()) >= 3:
        query = db.query(models.Scan)
        if current_scan_id:
            query = query.filter(models.Scan.id != current_scan_id)
        all_recent = query.order_by(models.Scan.created_at.desc()).limit(50).all()
        for s in all_recent:
            if s.extracted_fields and isinstance(s.extracted_fields, dict):
                sem = s.extracted_fields.get("semantic_fields", {})
                if sem and sem.get("product_name", "").strip().lower() == product_name.strip().lower():
                    prev_scan = s
                    match_type = "product_name"
                    break

    if prev_scan:
        sem = prev_scan.extracted_fields.get("semantic_fields", {}) if isinstance(prev_scan.extracted_fields, dict) else {}
        return {
            "is_duplicate": True,
            "match_type": match_type,
            "previous_scan_id": prev_scan.id,
            "product_name": sem.get("product_name") or product_name or f"Scan #{prev_scan.id}",
            "scanned_at": prev_scan.created_at.isoformat() if prev_scan.created_at else None,
            "previous_status": prev_scan.status.value.upper() if hasattr(prev_scan.status, "value") else str(prev_scan.status).upper(),
            "violations_count": len(prev_scan.violations) if prev_scan.violations else 0
        }

    return None


def _process_single_ocr(file_path: str) -> Dict[str, Any]:
    """Helper function to run OCR on a single image file with error isolation."""
    try:
        ocr_res = _ocr_provider.extract_text(file_path)
        if not ocr_res:
            return {"raw_text": "", "bounding_boxes": []}
        return ocr_res
    except Exception as e:
        logger.warning(f"OCR failed for image {file_path}: {e}")
        return {"raw_text": "", "bounding_boxes": [], "error": str(e)}


# =========================================================
# CREATE SCAN (Supports 1 to 4 Images: Front, Back, Left, Right)
# =========================================================

@router.post(
    "/",
    response_model=schemas.ScanResponse,
    status_code=status.HTTP_201_CREATED
)
def create_scan(
    image: Optional[UploadFile] = File(None),
    images: Optional[List[UploadFile]] = File(None),
    sides: Optional[str] = Form(None),
    product_id: Optional[int] = Form(None),
    capture_method: models.CaptureMethod = Form(models.CaptureMethod.camera),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(database.get_db),
):
    # -----------------------------------------------------
    # 1. COLLECT & VALIDATE UPLOADED IMAGES
    # -----------------------------------------------------
    upload_files: List[UploadFile] = []
    if images and len(images) > 0:
        upload_files = [f for f in images if f and f.filename]
    elif image and image.filename:
        upload_files = [image]

    if not upload_files:
        raise HTTPException(
            status_code=400,
            detail="No product label image file provided for scanning."
        )

    # Parse side labels if provided
    side_names: List[str] = []
    if sides:
        try:
            parsed = json.loads(sides)
            if isinstance(parsed, list):
                side_names = [str(s).lower() for s in parsed]
        except Exception:
            side_names = []

    default_side_order = ["front", "back", "left", "right"]
    if len(side_names) != len(upload_files):
        side_names = [
            default_side_order[i] if i < len(default_side_order) else f"side_{i+1}"
            for i in range(len(upload_files))
        ]

    saved_filenames: List[str] = []
    saved_filepaths: List[str] = []

    for file_item in upload_files:
        file_ext = (
            file_item.filename.split(".")[-1].lower()
            if file_item.filename and "." in file_item.filename
            else "jpg"
        )
        if file_ext not in {"jpg", "jpeg", "png", "webp"}:
            file_ext = "jpg"

        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            contents = file_item.file.read()
            if not contents:
                continue
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
            saved_filenames.append(unique_filename)
            saved_filepaths.append(file_path)
            logger.info(f"Saved upload image: {file_path}")
        except Exception as e:
            logger.exception(f"Failed to read/save uploaded image: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded image.")
        finally:
            file_item.file.close()

    if not saved_filepaths:
        raise HTTPException(status_code=400, detail="Uploaded image files were empty.")

    # -----------------------------------------------------
    # 2. RUN CONTROLLED CONCURRENCY OCR & PARALLEL GEMINI VISION
    # -----------------------------------------------------
    side_ocr_results: Dict[str, Any] = {}
    combined_text_parts: List[str] = []
    all_bounding_boxes: List[Dict[str, Any]] = []
    all_ocr_confs: List[float] = []

    gemini_future = None
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Launch Gemini Vision concurrently in the background while CPU processes local OCR
        if _gemini_vision.client:
            gemini_future = executor.submit(_gemini_vision.analyze_product_label, saved_filepaths)

        ocr_outputs = list(executor.map(_process_single_ocr, saved_filepaths))

    for idx, (side_label, ocr_res) in enumerate(zip(side_names, ocr_outputs)):
        raw_text = ocr_res.get("raw_text", "").strip()
        bboxes = ocr_res.get("bounding_boxes", [])

        # Add side tag to each bounding box
        for b in bboxes:
            b["side"] = side_label
            if "confidence" in b and isinstance(b["confidence"], (int, float)):
                all_ocr_confs.append(float(b["confidence"]))

        side_ocr_results[side_label] = {
            "image_path": saved_filenames[idx],
            "full_text": raw_text,
            "raw_text": raw_text,
            "bounding_boxes": bboxes,
            "error": ocr_res.get("error")
        }

        if raw_text:
            combined_text_parts.append(f"--- [{side_label.upper()} SIDE] ---\n{raw_text}")
        all_bounding_boxes.extend(bboxes)

    combined_full_text = "\n\n".join(combined_text_parts)
    avg_ocr_confidence = round(sum(all_ocr_confs) / len(all_ocr_confs) * 100, 1) if all_ocr_confs else 85.0

    # -----------------------------------------------------
    # 3. BARCODE DETECTION ACROSS IMAGES
    # -----------------------------------------------------
    barcode_result = {"barcode": None, "barcode_type": None, "all_codes": []}
    for file_path in saved_filepaths:
        try:
            detected = _barcode_detector.detect(file_path)
            if detected.get("barcode"):
                barcode_result = detected
                break
        except Exception as e:
            logger.warning(f"Barcode detection skipped on {file_path}: {e}")

    # -----------------------------------------------------
    # 4. MULTI-SIDE EXTRACTION WITH BOUNDING-BOX EVIDENCE
    # -----------------------------------------------------
    try:
        multi_side_extraction = _extractor.extract_from_multi_side_ocr(side_ocr_results, barcode_result)
        local_extracted_fields = multi_side_extraction.get("fields", {})
        evidence_map = multi_side_extraction.get("evidence", {})
        logger.info(f"Multi-side extracted fields: {local_extracted_fields}")
    except Exception as e:
        logger.exception(f"Multi-side field extraction failed: {e}")
        local_extracted_fields = {}
        evidence_map = {}

    # -----------------------------------------------------
    # 5. GEMINI VISION MULTIMODAL EXTRACTION & FUSION
    # -----------------------------------------------------
    gemini_data = None
    gemini_dict: Dict[str, Any] = {}
    fusion_fields: Dict[str, Any] = {}
    needs_manual_review = False
    local_ocr_fallback = False

    if gemini_future:
        try:
            logger.info("Awaiting concurrent multimodal Gemini Vision analysis result...")
            gemini_data = gemini_future.result(timeout=25)
            logger.info(f"Gemini extraction result: {gemini_data}")
            if gemini_data:
                gemini_dict = {
                    "product_name": gemini_data.product_name,
                    "brand_name": gemini_data.brand_name,
                    "manufacturer_name": gemini_data.manufacturer_name,
                    "manufacturer_address": gemini_data.manufacturer_address,
                    "packer_name": gemini_data.packer_name,
                    "packer_address": gemini_data.packer_address,
                    "importer_name": gemini_data.importer_name,
                    "importer_address": gemini_data.importer_address,
                    "mrp": gemini_data.mrp,
                    "currency": gemini_data.currency,
                    "tax_inclusive": gemini_data.tax_inclusive,
                    "net_quantity_value": gemini_data.net_quantity_value,
                    "net_quantity_unit": gemini_data.net_quantity_unit,
                    "unit_sale_price": gemini_data.unit_sale_price,
                    "manufacturing_date": gemini_data.manufacturing_date,
                    "packing_date": gemini_data.packing_date,
                    "expiry_date": gemini_data.expiry_date,
                    "best_before": gemini_data.best_before,
                    "customer_care_details": gemini_data.customer_care_details,
                    "country_of_origin": gemini_data.country_of_origin,
                    "consumer_care_email": gemini_data.consumer_care_email,
                    "consumer_care_phone": gemini_data.consumer_care_phone,
                    "fssai_number": gemini_data.fssai_number,
                    "barcode": gemini_data.barcode,
                    "declared_usp": gemini_data.declared_usp,
                    "raw_text": gemini_data.raw_text,
                    "uncertain_fields": gemini_data.uncertain_fields
                }
            else:
                local_ocr_fallback = True
        except Exception as e:
            logger.warning(f"Gemini Vision extraction failed: {e}. Falling back to LOCAL_OCR_ONLY.")
            local_ocr_fallback = True
    else:
        local_ocr_fallback = True

    # Fuse results from Local Multi-Side OCR, Gemini, and Barcode
    try:
        fusion_res = fuse_results(
            local_fields=local_extracted_fields,
            gemini_data=gemini_data,
            barcode_result=barcode_result,
            evidence_map=evidence_map
        )
        extracted_fields = fusion_res.get("flat_fields", {})
        fusion_fields = fusion_res.get("fusion_fields", {})
        needs_manual_review = fusion_res.get("needs_manual_review", False)
        extraction_confidence = fusion_res.get("extraction_confidence", 85.0)
        logger.info("Fused fields successfully resolved.")
    except Exception as e:
        logger.exception(f"Result fusion failed: {e}")
        extracted_fields = dict(local_extracted_fields)
        extracted_fields["barcode"] = barcode_result.get("barcode")
        extracted_fields["barcode_type"] = barcode_result.get("barcode_type")
        extraction_confidence = 75.0

    # -----------------------------------------------------
    # 6. LEGAL METROLOGY RULE EVALUATION (PASS / REVIEW / FAIL)
    # -----------------------------------------------------
    try:
        rule_eval_output = _rule_engine.evaluate_rules(
            extracted_fields=extracted_fields,
            images_count=len(saved_filenames),
            fusion_fields=fusion_fields,
            evidence_map=evidence_map,
            ocr_raw_text=combined_full_text
        )
        verdict_str = rule_eval_output["verdict"]
        rules_evaluated_list = rule_eval_output["rules_evaluated"]
        violations_data = rule_eval_output["violations_data"]
        compliance_score_num = rule_eval_output["score"]
    except Exception as e:
        logger.exception(f"Rule evaluation failed: {e}")
        verdict_str = "needs_review"
        rules_evaluated_list = []
        violations_data = []
        compliance_score_num = 75

    # -----------------------------------------------------
    # 7. 3-TIER CONFIDENCES & COMPLIANCE SCORE & DUPLICATE DETECTION
    # -----------------------------------------------------
    compliance_score_data = calculate_compliance_score(extracted_fields, violations_data)
    # Use accurate rule engine score
    compliance_score_data["score"] = compliance_score_num
    if verdict_str == "compliant":
        compliance_score_data["category"] = "Excellent / Compliant"
        compliance_score_data["color"] = "green"
    elif verdict_str == "needs_review":
        compliance_score_data["category"] = "Needs Review"
        compliance_score_data["color"] = "orange"
    else:
        compliance_score_data["category"] = "High Risk / Non-Compliant"
        compliance_score_data["color"] = "red"

    field_confidences_data = compute_field_confidences(extracted_fields, fusion_fields)
    duplicate_info = check_duplicate_product(
        db=db,
        barcode=barcode_result.get("barcode"),
        product_name=extracted_fields.get("product_name")
    )

    # -----------------------------------------------------
    # 8. COMBINED EXTRACTION DATA BLOB
    # -----------------------------------------------------
    combined_extraction_data = {
        "bounding_boxes": all_bounding_boxes,
        "semantic_fields": extracted_fields,
        "barcode_data": barcode_result,
        "fusion_fields": fusion_fields,
        "needs_manual_review": needs_manual_review,
        "evidence_map": evidence_map,
        "rules_evaluated": rules_evaluated_list,
        
        # 3-Tier Confidences
        "ocr_confidence": avg_ocr_confidence,
        "extraction_confidence": float(extraction_confidence),
        "compliance_confidence": float(compliance_score_num),
        
        # Extended fields for API Response & UI Multi-Side Viewer
        "local_ocr": local_extracted_fields,
        "gemini_extraction": gemini_dict,
        "confidence": "HIGH" if verdict_str == "compliant" else "MEDIUM",
        "detailed_status": verdict_str.upper(),
        "manual_review_required": verdict_str == "needs_review",
        "discrepancies": [],
        "sides_ocr": side_ocr_results,
        "images_count": len(saved_filenames),
        "images_paths": saved_filenames,
        "compliance_score": compliance_score_data,
        "field_confidences": field_confidences_data,
        "duplicate_product": duplicate_info
    }

    # -----------------------------------------------------
    # 9. DETERMINE COMPLIANCE STATUS ENUM
    # -----------------------------------------------------
    if verdict_str == "compliant":
        status_enum = models.ScanStatus.compliant
    elif verdict_str == "needs_review":
        status_enum = models.ScanStatus.needs_review
    else:
        status_enum = models.ScanStatus.non_compliant

    # -----------------------------------------------------
    # 10. PERSIST SCAN + VIOLATIONS TO DATABASE
    # -----------------------------------------------------
    primary_image_filename = saved_filenames[0] if saved_filenames else ""

    try:
        new_scan = models.Scan(
            product_id=product_id,
            image_path=primary_image_filename,
            capture_method=capture_method,
            barcode=barcode_result.get("barcode"),
            barcode_format=barcode_result.get("barcode_type"),
            latitude=latitude,
            longitude=longitude,
            ocr_raw_text=combined_full_text,
            ocr_confidence=avg_ocr_confidence,
            extracted_fields=combined_extraction_data,
            status=status_enum
        )
        db.add(new_scan)
        db.flush()

        for v_data in violations_data:
            db.add(models.Violation(
                scan_id=new_scan.id,
                rule_code=v_data["rule_code"],
                rule_description=v_data["rule_description"],
                severity=v_data["severity"],
                detail_text=v_data["detail_text"]
            ))

        db.commit()
        db.refresh(new_scan)
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Failed to save scan/violations: {e}")
        raise HTTPException(status_code=500, detail="Failed to save scan results.")

    return new_scan


# =========================================================
# GET ALL SCANS
# =========================================================

@router.get(
    "/",
    response_model=List[schemas.ScanResponse]
)
def get_scans(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    scans = (
        db.query(models.Scan)
        .order_by(models.Scan.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return scans


# =========================================================
# GET SINGLE SCAN
# =========================================================

@router.get(
    "/{scan_id}",
    response_model=schemas.ScanResponse
)
def get_scan(
    scan_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )

    return scan


# =========================================================
# VERIFY SCAN (OFFICER CONFIRMATION / EDITS)
# =========================================================

@router.post(
    "/{scan_id}/verify",
    response_model=schemas.ScanResponse
)
def verify_scan(
    scan_id: int,
    request: Dict[str, Any],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )

    fields = request.get("fields", {})
    reason = request.get("reason", "Officer manual inspection verification")
    images_count = scan.extracted_fields.get("images_count", 1) if isinstance(scan.extracted_fields, dict) else 1

    old_ext = dict(scan.extracted_fields or {})
    original_semantic = old_ext.get("semantic_fields", {})
    existing_overrides = old_ext.get("officer_overrides", {})
    new_overrides = dict(existing_overrides)

    from datetime import datetime, timezone

    # Record every field edited by the officer
    for f_key, new_val in fields.items():
        orig_val = original_semantic.get(f_key)
        if str(new_val).strip() != str(orig_val).strip():
            fusion_meta = old_ext.get("fusion_fields", {}).get(f_key, {})
            new_overrides[f_key] = {
                "field_name": f_key,
                "original_value": orig_val,
                "original_source": fusion_meta.get("source", "ocr/ai"),
                "officer_value": new_val,
                "officer_id": current_user.id,
                "officer_name": current_user.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": reason
            }

    # Re-evaluate rules with verified fields
    rule_eval = _rule_engine.evaluate_rules(
        fields,
        images_count=images_count,
        fusion_fields=old_ext.get("fusion_fields"),
        evidence_map=old_ext.get("evidence_map"),
        ocr_raw_text=scan.ocr_raw_text
    )
    verdict_str = rule_eval["verdict"]
    rules_evaluated_list = rule_eval["rules_evaluated"]
    violations_data = rule_eval["violations_data"]

    old_ext["semantic_fields"] = fields
    old_ext["officer_overrides"] = new_overrides
    old_ext["confidence"] = "HIGH"
    old_ext["detailed_status"] = "VERIFIED"
    old_ext["manual_review_required"] = False
    old_ext["rules_evaluated"] = rules_evaluated_list
    old_ext["compliance_confidence"] = float(rule_eval["score"])

    compliance_score_data = calculate_compliance_score(fields, violations_data)
    compliance_score_data["score"] = rule_eval["score"]
    field_confidences_data = compute_field_confidences(fields, old_ext.get("fusion_fields", {}))

    old_ext["compliance_score"] = compliance_score_data
    old_ext["field_confidences"] = field_confidences_data
    scan.extracted_fields = old_ext

    if verdict_str == "compliant":
        scan.status = models.ScanStatus.compliant
    elif verdict_str == "needs_review":
        scan.status = models.ScanStatus.needs_review
    else:
        scan.status = models.ScanStatus.non_compliant

    # Delete old violations & recreate
    (
        db.query(models.Violation)
        .filter(models.Violation.scan_id == scan.id)
        .delete()
    )

    if scan.report:
        db.delete(scan.report)

    for v_data in violations_data:
        db.add(models.Violation(
            scan_id=scan.id,
            rule_code=v_data["rule_code"],
            rule_description=v_data["rule_description"],
            severity=v_data["severity"],
            detail_text=v_data["detail_text"]
        ))

    # Record in Audit Log
    audit.log_audit(db, current_user.id, "VERIFY_SCAN", "scan", scan.id)

    db.commit()
    db.refresh(scan)

    return scan


# =========================================================
# GET SCAN REPORT (PDF GENERATION)
# =========================================================

@router.get(
    "/{scan_id}/report"
)
def get_scan_report(
    scan_id: int,
    db: Session = Depends(database.get_db),
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )

    # Check if report already exists on disk
    if scan.report and scan.report.pdf_path:
        report_dir = os.path.join(os.getcwd(), "reports")
        p = os.path.join(report_dir, os.path.basename(scan.report.pdf_path))
        if os.path.exists(p):
            from fastapi.responses import FileResponse
            return FileResponse(
                p,
                media_type="application/pdf",
                filename=f"legalmetrix_report_{scan.id}.pdf"
            )

    from ..reports import generate_pdf_report

    sem_fields = scan.extracted_fields.get("semantic_fields", {}) if isinstance(scan.extracted_fields, dict) else {}
    scan_data = {
        "id": scan.id,
        "product_name": sem_fields.get("product_name"),
        "barcode": scan.barcode,
        "status": scan.status.value if hasattr(scan.status, "value") else str(scan.status),
        "ocr_raw_text": scan.ocr_raw_text,
        "extracted_fields": scan.extracted_fields,
        "compliance_score": scan.extracted_fields.get("compliance_score", {}) if isinstance(scan.extracted_fields, dict) else {},
        "violations": [
            {
                "rule_code": v.rule_code,
                "rule_description": v.rule_description,
                "severity": v.severity,
                "detail_text": v.detail_text,
                "status": "FAIL" if v.severity == "HIGH" else "REVIEW"
            }
            for v in scan.violations
        ]
    }

    try:
        pdf_path = generate_pdf_report(scan_data)

        new_report = models.Report(
            scan_id=scan.id,
            pdf_path=os.path.basename(pdf_path)
        )
        db.add(new_report)
        db.commit()

        from fastapi.responses import FileResponse
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"legalmetrix_report_{scan.id}.pdf"
        )
    except Exception as e:
        logger.exception(f"Report generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate inspection report: {str(e)}"
        )


# =========================================================
# FILE CLEANUP HELPER
# =========================================================

def _cleanup_scan_files(scan: models.Scan):
    try:
        if scan.image_path:
            file_path = os.path.join(UPLOAD_DIR, scan.image_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        if scan.extracted_fields and isinstance(scan.extracted_fields, dict):
            extra_images = scan.extracted_fields.get("images_paths", [])
            for extra_img in extra_images:
                if extra_img and isinstance(extra_img, str):
                    p = os.path.join(UPLOAD_DIR, os.path.basename(extra_img))
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
        if scan.report and scan.report.pdf_path:
            report_dir = os.path.join(os.getcwd(), "reports")
            report_path = os.path.join(report_dir, os.path.basename(scan.report.pdf_path))
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Error cleaning up files for scan {scan.id}: {e}")


# =========================================================
# BATCH DELETE SCANS
# =========================================================

@router.post(
    "/batch-delete",
    response_model=schemas.BatchDeleteResponse
)
def batch_delete_scans(
    req: schemas.BatchDeleteRequest,
    db: Session = Depends(database.get_db),
):
    if not req.scan_ids:
        return schemas.BatchDeleteResponse(deleted_count=0, deleted_ids=[])

    scans = (
        db.query(models.Scan)
        .filter(models.Scan.id.in_(req.scan_ids))
        .all()
    )

    deleted_ids = []
    for scan in scans:
        _cleanup_scan_files(scan)
        if scan.violations:
            for v in scan.violations:
                db.delete(v)
        if scan.report:
            db.delete(scan.report)
        deleted_ids.append(scan.id)
        db.delete(scan)

    db.commit()

    return schemas.BatchDeleteResponse(
        deleted_count=len(deleted_ids),
        deleted_ids=deleted_ids
    )


# =========================================================
# DELETE SINGLE SCAN
# =========================================================

@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_scan(
    scan_id: int,
    db: Session = Depends(database.get_db),
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )

    _cleanup_scan_files(scan)
    if scan.violations:
        for v in scan.violations:
            db.delete(v)
    if scan.report:
        db.delete(scan.report)

    db.delete(scan)
    db.commit()

    return
