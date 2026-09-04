from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import UserRole, CaptureMethod, ScanStatus

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.officer

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    uploaded_by_user_id: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

# --- Violation Schemas ---
class ViolationBase(BaseModel):
    rule_code: str
    rule_description: str
    severity: str
    detail_text: Optional[str] = None

class ViolationResponse(ViolationBase):
    id: int
    scan_id: int
    class Config:
        from_attributes = True

# --- Scan Schemas ---
class ScanBase(BaseModel):
    product_id: Optional[int] = None
    capture_method: CaptureMethod
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    captured_at: Optional[datetime] = None

class ScanCreate(ScanBase):
    pass

class ScanResponse(ScanBase):
    id: int
    image_path: str
    ocr_raw_text: Optional[str] = None
    extracted_fields: Optional[Dict[str, Any]] = None
    status: ScanStatus
    synced_at: Optional[datetime] = None
    created_at: datetime
    violations: List[ViolationResponse] = []
    
    # Extended fields for API Response:
    local_ocr: Optional[Dict[str, Any]] = None
    gemini_extraction: Optional[Dict[str, Any]] = None
    detailed_status: Optional[str] = None
    confidence: Optional[str] = None
    manual_review_required: Optional[bool] = False
    barcode_data: Optional[Any] = None
    discrepancies: Optional[List[str]] = []
    compliance_score: Optional[Dict[str, Any]] = None
    field_confidences: Optional[Dict[str, Any]] = None
    duplicate_product: Optional[Dict[str, Any]] = None
    ocr_confidence: Optional[float] = None
    extraction_confidence: Optional[float] = None
    compliance_confidence: Optional[float] = None
    evidence_map: Optional[Dict[str, Any]] = None
    rules_evaluated: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode='before')
    @classmethod
    def populate_dynamic_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            ext = data.get("extracted_fields") or {}
            data["local_ocr"] = ext.get("local_ocr")
            data["gemini_extraction"] = ext.get("gemini_extraction")
            data["confidence"] = ext.get("confidence", "LOW")
            data["manual_review_required"] = ext.get("manual_review_required", False)
            data["detailed_status"] = ext.get("detailed_status", "LOCAL_OCR_ONLY")
            data["discrepancies"] = ext.get("discrepancies", [])
            data["compliance_score"] = ext.get("compliance_score")
            data["field_confidences"] = ext.get("field_confidences")
            data["duplicate_product"] = ext.get("duplicate_product")
            data["ocr_confidence"] = ext.get("ocr_confidence") or data.get("ocr_confidence")
            data["extraction_confidence"] = ext.get("extraction_confidence")
            data["compliance_confidence"] = ext.get("compliance_confidence")
            data["evidence_map"] = ext.get("evidence_map")
            data["rules_evaluated"] = ext.get("rules_evaluated")
            
            b_data = ext.get("barcode_data", {})
            all_codes = b_data.get("all_codes", []) if isinstance(b_data, dict) else []
            data["barcode_data"] = all_codes
        elif hasattr(data, "extracted_fields"):
            ext = data.extracted_fields or {}
            object.__setattr__(data, "local_ocr", ext.get("local_ocr"))
            object.__setattr__(data, "gemini_extraction", ext.get("gemini_extraction"))
            object.__setattr__(data, "confidence", ext.get("confidence", "LOW"))
            object.__setattr__(data, "manual_review_required", ext.get("manual_review_required", False))
            object.__setattr__(data, "detailed_status", ext.get("detailed_status", "LOCAL_OCR_ONLY"))
            object.__setattr__(data, "discrepancies", ext.get("discrepancies", []))
            object.__setattr__(data, "compliance_score", ext.get("compliance_score"))
            object.__setattr__(data, "field_confidences", ext.get("field_confidences"))
            object.__setattr__(data, "duplicate_product", ext.get("duplicate_product"))
            object.__setattr__(data, "ocr_confidence", ext.get("ocr_confidence") or getattr(data, "ocr_confidence", None))
            object.__setattr__(data, "extraction_confidence", ext.get("extraction_confidence"))
            object.__setattr__(data, "compliance_confidence", ext.get("compliance_confidence"))
            object.__setattr__(data, "evidence_map", ext.get("evidence_map"))
            object.__setattr__(data, "rules_evaluated", ext.get("rules_evaluated"))
            
            b_data = ext.get("barcode_data", {})
            all_codes = b_data.get("all_codes", []) if isinstance(b_data, dict) else []
            object.__setattr__(data, "barcode_data", all_codes)
        return data

    class Config:
        from_attributes = True

class BatchDeleteRequest(BaseModel):
    scan_ids: List[int]

class BatchDeleteResponse(BaseModel):
    deleted_count: int
    deleted_ids: List[int]

