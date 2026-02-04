from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Date, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    required_documents = Column(Text)  # JSON string of required doc types
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    employees = relationship("Employee", back_populates="position")

class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = {'extend_existing': True}
 
    employee_id = Column(String(50), primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
 
    department_id = Column(Integer, nullable=False)
    designation = Column(String(50), nullable=False)
    joining_date = Column(Date, nullable=False)
    reporting_manager = Column(String(50))
    email_id = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    location = Column(String(50))
    shift_id = Column(Integer, nullable=False)
    employment_type = Column(String(50), nullable=False)
    annual_ctc = Column(String(50), default="0")
    annual_leaves = Column(Integer, server_default='21')
    position_id = Column(Integer, ForeignKey('positions.id'))
   
    profile_photo = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
 
    # Relationships
    position = relationship("Position", back_populates="employees")
    documents = relationship("EmployeeDocuments", back_populates="employee")
 
    def delete(self, session):
        """Delete employee and all related records"""
        session.delete(self)
        session.commit()