from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    officer = "officer"

class CaptureMethod(str, enum.Enum):
    camera = "camera"
    upload = "upload"

class ScanStatus(str, enum.Enum):
    pending = "pending"
    compliant = "compliant"
    needs_review = "needs_review"
    non_compliant = "non_compliant"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.officer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    barcode = Column(String, unique=True, nullable=True, index=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    uploader = relationship("User")
    scans = relationship("Scan", back_populates="product")

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    image_path = Column(String, nullable=False)
    capture_method = Column(Enum(CaptureMethod), default=CaptureMethod.camera)
    
    barcode = Column(String, nullable=True, index=True)
    barcode_format = Column(String, nullable=True)
    
    ocr_raw_text = Column(String, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    status = Column(Enum(ScanStatus), default=ScanStatus.pending)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="scans")
    violations = relationship("Violation", back_populates="scan", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="scan", uselist=False)

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    rule_code = Column(String, nullable=False)
    rule_description = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    detail_text = Column(String, nullable=True)

    scan = relationship("Scan", back_populates="violations")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), unique=True)
    pdf_path = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="report")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False) # e.g., 'CREATE_SCAN', 'UPDATE_SCAN'
    entity_type = Column(String, nullable=False) # e.g., 'scan', 'report'
    entity_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
