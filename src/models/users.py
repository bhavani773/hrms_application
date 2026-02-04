from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
   
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="EMPLOYEE")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=func.now(), server_default=func.now())
   
    def mark_onboarded(self):
        """Mark user as onboarded"""
        pass