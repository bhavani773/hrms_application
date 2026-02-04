from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Text, Index, Integer, TIMESTAMP, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base

class EmployeeDocuments(Base):
    __tablename__ = "employee_documents"
    __table_args__ = {'extend_existing': True}
 
    document_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id", ondelete="CASCADE"))
    document_name = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    upload_date = Column(Date, nullable=False)
    status = Column(String(50), default="Pending")
    uploaded_document = Column(LargeBinary)
 
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
 
    employee = relationship("Employee", back_populates="documents")