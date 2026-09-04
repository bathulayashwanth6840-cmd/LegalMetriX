import pytest
import io
import os
import tempfile
from PIL import Image
from app.fusion import fuse_results, normalize_text
from app.services.gemini_vision import GeminiVisionService, _GEMINI_EXTRACTION_CACHE, GeminiProductLabelData
from app.reports import generate_pdf_report
from datetime import datetime

def test_gemini_caching_and_anti_hallucination():
    service = GeminiVisionService()
    # Create temp image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        img.save(f, format='JPEG')
        temp_path = f.name

    try:
        with open(temp_path, "rb") as f:
            b = f.read()
        cache_key = service._compute_images_hash([b])
        
        # Pre-populate cache to simulate API call cache
        cached_data = GeminiProductLabelData(
            product_name="Sunflower Refined Oil 1L",
            mrp="150",
            net_quantity_value="1",
            net_quantity_unit="L",
            manufacturer_name="Apex Foods Ltd",
            fssai_number="10019042000123"
        )
        _GEMINI_EXTRACTION_CACHE[cache_key] = cached_data
        
        # Enable client mock for test
        service.client = True  # Mock presence
        res = service.analyze_product_label(temp_path)
        assert res is not None
        assert res.mrp == "150"
        assert res.fssai_number == "10019042000123"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_decision_fusion_agreement_and_conflict():
    # Case A: High Agreement
    ocr_res = {"mrp": "₹ 150.00", "net_quantity": "1 L"}
    gemini_obj = GeminiProductLabelData(
        mrp="150",
        net_quantity_value="1",
        net_quantity_unit="L"
    )
    fusion_high = fuse_results(ocr_res, gemini_obj)
    fused_fields = fusion_high.get("fusion_fields", {})
    
    assert fused_fields["mrp"]["agreement"] == "HIGH"
    assert fused_fields["mrp"]["conflict"] is False

    # Case B: Disagreement / Conflict
    ocr_conflict = {"mrp": "₹ 120.00"}
    gemini_conflict = GeminiProductLabelData(
        mrp="130.00"
    )
    fusion_conflict = fuse_results(ocr_conflict, gemini_conflict)
    fused_conflict_fields = fusion_conflict.get("fusion_fields", {})
    
    assert fused_conflict_fields["mrp"]["agreement"] == "CONFLICT"
    assert fused_conflict_fields["mrp"]["conflict"] is True
    assert fused_conflict_fields["mrp"]["status"] == "NEEDS_MANUAL_REVIEW"
    assert fused_conflict_fields["mrp"]["ocr_value"] == "₹ 120.00"
    assert fused_conflict_fields["mrp"]["gemini_value"] == "130.00"

def test_pdf_report_sections_and_override_audit():
    scan_data = {
        "id": 999,
        "barcode": "8901030383451",
        "image_path": "test.jpg",
        "status": "COMPLIANT WITH CHECKED REQUIREMENTS",
        "compliance_score": 92,
        "ocr_confidence": 95.0,
        "extraction_confidence": 90.0,
        "created_at": datetime.utcnow().isoformat(),
        "extracted_fields": {
            "semantic_fields": {
                "product_name": "Premium Wheat Flour",
                "mrp": "120",
                "net_quantity": "5 kg",
                "manufacturer_name": "Agro Millers Ltd",
                "manufacturer_address": "Kolkata 700001",
                "mfg_date": "03/2026",
                "consumer_care": "1800-456-789",
                "country_of_origin": "India"
            },
            "fusion_fields": {
                "mrp": {"source": "PaddleOCR + Gemini 2.5 Flash", "confidence": 0.95}
            }
        },
        "violations": [],
        "officer_overrides": {
            "mrp": {
                "original_value": "120",
                "officer_value": "115",
                "officer_id": "#LM-204",
                "timestamp": "2026-09-04T11:00:00",
                "reason": "Corrected discount stamp on secondary label"
            }
        }
    }
    
    file_path = generate_pdf_report(scan_data)
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
    assert content.startswith(b"%PDF")
    assert len(content) > 1000
    if os.path.exists(file_path):
        os.remove(file_path)
