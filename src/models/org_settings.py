from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base

class DocumentRequirement(Base):
    __tablename__ = "document_requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type = Column(String(100), nullable=False, unique=True)
    is_mandatory = Column(Boolean, default=True)
    description = Column(Text)
    expiry_applicable = Column(Boolean, default=False)
    grace_period_days = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ComplianceRequirement(Base):
    __tablename__ = "compliance_requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(100), nullable=False)
    department = Column(String(100))  # null means applies to all
    threshold_days = Column(Integer, default=30)  # days before expiry to trigger warning
    escalation_days = Column(Integer, default=7)  # days after expiry to escalate
    scoring_weight = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String(100), nullable=False, unique=True)
    setting_value = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())