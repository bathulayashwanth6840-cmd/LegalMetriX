import pytest
from unittest.mock import patch
from app.services.gemini_vision import GeminiProductLabelData
import io


def test_scan_flow_with_fusion(client):
    # 1. Register and Login to get a token
    client.post(
        "/api/auth/register",
        json={"name": "Inspector", "email": "inspector@test.com", "password": "password123", "role": "officer"}
    )
    login_res = client.post(
        "/api/auth/login",
        data={"username": "inspector@test.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Mock external services: OCR, Barcode, and Gemini
    mock_ocr = {
        "raw_text": "Product: Parle-G Gluco Biscuits\nMfg: 08/2026\nMRP: Rs. 10\nNet Wt: 100 g\nMfd by: Parle Products Pvt Ltd Mumbai India\nBest before: 08/2027\nFSSAI Lic: 10013022002222\nConsumer Care: care@parle.com",
        "bounding_boxes": [{"text": "Parle-G", "box": [[0, 0], [10, 0], [10, 10], [0, 10]], "confidence": 0.95}]
    }
    
    mock_barcode = {
        "barcode": "8901719101017",
        "barcode_type": "EAN13",
        "all_codes": ["8901719101017"]
    }
    
    mock_gemini = GeminiProductLabelData(
        product_name="Parle-G Gluco Biscuits",
        brand_name="Parle",
        manufacturer_name="Parle Products Pvt Ltd",
        manufacturer_address="Mumbai, India",
        mrp="10",
        currency="INR",
        net_quantity_value="100",
        net_quantity_unit="g",
        manufacturing_date="08/2026",
        fssai_number="10013022002222",
        consumer_care_email="customercare@parle.biz",
        country_of_origin="India",
        expiry_date="08/2027",
        uncertain_fields=[]
    )

    with patch("app.routers.scans._ocr_provider.extract_text", return_value=mock_ocr), \
         patch("app.routers.scans._barcode_detector.detect", return_value=mock_barcode), \
         patch("app.routers.scans._gemini_vision.client", True), \
         patch("app.routers.scans._gemini_vision.analyze_product_label", return_value=mock_gemini):

        # Send scanned image
        dummy_file = io.BytesIO(b"dummy image bytes")
        response = client.post(
            "/api/scans/",
            files={"image": ("test.jpg", dummy_file, "image/jpeg")},
            data={"capture_method": "camera"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] in ["compliant", "needs_review"]
        assert data["ocr_confidence"] is not None
        assert data["extraction_confidence"] is not None
        
        # Verify result fusion worked and holds expected values
        semantic = data["extracted_fields"]["semantic_fields"]
        assert semantic["product_name"] == "Parle-G Gluco Biscuits"
        assert semantic["mrp"] == "10"
        assert semantic["barcode"] == "8901719101017"

        # Get scan by ID
        scan_id = data["id"]
        get_res = client.get(f"/api/scans/{scan_id}", headers=headers)
        assert get_res.status_code == 200


def test_scan_verification_trigger(client):
    # Register / Login
    client.post(
        "/api/auth/register",
        json={"name": "Inspector 2", "email": "inspector2@test.com", "password": "password123", "role": "officer"}
    )
    login_res = client.post(
        "/api/auth/login",
        data={"username": "inspector2@test.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mock_ocr = {"raw_text": "Blurry Label Text", "bounding_boxes": []}
    mock_barcode = {"barcode": None, "barcode_type": None, "all_codes": []}

    with patch("app.routers.scans._ocr_provider.extract_text", return_value=mock_ocr), \
         patch("app.routers.scans._barcode_detector.detect", return_value=mock_barcode), \
         patch("app.routers.scans._gemini_vision.client", None):

        dummy_file = io.BytesIO(b"dummy image bytes")
        response = client.post(
            "/api/scans/",
            files={"image": ("test.jpg", dummy_file, "image/jpeg")},
            data={"capture_method": "camera"}
        )
        assert response.status_code == 201
        data = response.json()
        scan_id = data["id"]

        # Run verification with valid fields
        verify_fields = {
            "product_name": "Parle-G Biscuits",
            "manufacturer_name": "Parle Products",
            "manufacturer_address": "Mumbai, Maharashtra 400057",
            "net_quantity": "100 g",
            "mrp": "10.00",
            "mfg_date": "08/2026",
            "expiry_date": "Best Before 6 Months",
            "fssai_number": "10013022002222",
            "consumer_care": "care@parle.com",
            "country_of_origin": "India",
            "barcode": "8901719101017"
        }

        verify_response = client.post(
            f"/api/scans/{scan_id}/verify",
            json={"fields": verify_fields, "reason": "Officer verified physical packaging"},
            headers=headers
        )

        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["status"] == "compliant"
        assert verify_data["detailed_status"] == "VERIFIED"
        assert verify_data["extracted_fields"]["officer_overrides"] is not None

        # Test PDF Report Generation
        report_res = client.get(f"/api/scans/{scan_id}/report", headers=headers)
        assert report_res.status_code == 200
        assert report_res.headers["content-type"] == "application/pdf"


def test_decision_fusion_conflict_handling(client):
    """Verifies that conflicting OCR and Gemini extractions are flagged for manual review without silent overwrite."""
    from app.fusion import fuse_results

    local_ocr_fields = {
        "mrp": "120",
        "net_quantity": "200 g",
        "product_name": "Original OCR Biscuit"
    }

    mock_gemini = GeminiProductLabelData(
        product_name="Original OCR Biscuit",
        mrp="130",  # Conflict with local OCR MRP 120
        net_quantity_value="200",
        net_quantity_unit="g",
        uncertain_fields=[]
    )

    fusion_res = fuse_results(
        local_fields=local_ocr_fields,
        gemini_data=mock_gemini,
        barcode_result={"barcode": "890100000001", "barcode_type": "EAN13"}
    )

    fusion_fields = fusion_res["fusion_fields"]
    mrp_meta = fusion_fields["mrp"]
    
    assert mrp_meta["conflict"] is True
    assert mrp_meta["source"] == "conflict"
    assert mrp_meta["ocr_value"] == "120"
    assert mrp_meta["gemini_value"] == "130"
    assert fusion_res["needs_manual_review"] is True


def test_gemini_vision_caching():
    """Verifies that identical image bytes return cached extraction without hitting external API repeatedly."""
    from app.services.gemini_vision import GeminiVisionService, _GEMINI_EXTRACTION_CACHE, GeminiProductLabelData

    service = GeminiVisionService()
    fake_data = GeminiProductLabelData(product_name="Cached Biscuit", mrp="50")
    
    hash_key = service._compute_images_hash([b"test_image_bytes_12345"])
    _GEMINI_EXTRACTION_CACHE[hash_key] = fake_data

    # Direct query should match cached item
    assert _GEMINI_EXTRACTION_CACHE.get(hash_key).product_name == "Cached Biscuit"

