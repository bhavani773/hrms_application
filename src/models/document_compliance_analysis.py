from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from .base import Base

class DocumentComplianceAnalysis(Base):
    __tablename__ = "document_compliance_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    compliance_score = Column(DECIMAL(5,2), nullable=False)
    missing_documents = Column(JSONB)
    expiring_documents = Column(JSONB)
    risk_assessment = Column(JSONB)
    action_plan = Column(JSONB)
    priority_level = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_compliance_analysis_employee_id', 'employee_id'),
        Index('idx_compliance_analysis_created_at', 'created_at'),
        Index('idx_compliance_analysis_priority', 'priority_level'),
    )