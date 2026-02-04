from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base

class DocumentReminder(Base):
    __tablename__ = "document_reminders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False)
    document_type = Column(String(100), nullable=False)
    reminder_type = Column(String(50))  # missing, expiring, renewal
    due_date = Column(Date)
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_document_reminders_employee_id', 'employee_id'),
        Index('idx_document_reminders_due_date', 'due_date'),
        Index('idx_document_reminders_sent', 'reminder_sent', 'due_date'),
    )