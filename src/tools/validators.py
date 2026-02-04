from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

class EmployeeProfileState(BaseModel):
    employee_id: UUID
    first_name: str
    last_name: str
    email: str
    department: str
    position_title: str
    hire_date: Optional[datetime] = None

class DocumentState(BaseModel):
    document_type: str
    status: str
    expiry_date: Optional[date] = None
    submitted_date: Optional[datetime] = None

class ComplianceEvalState(BaseModel):
    missing_documents: List[str]
    expiring_documents: List[Dict[str, Any]]
    expired_documents: List[Dict[str, Any]]
    base_score: float
    priority_hint: str

class WorkflowState(BaseModel):
    candidate_id: UUID
    profile: Optional[EmployeeProfileState] = None
    documents: Optional[List[DocumentState]] = None
    requirements: Optional[List[str]] = None
    policies: Optional[Dict[str, Any]] = None
    compliance_eval: Optional[ComplianceEvalState] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    reminder_summary: Optional[Dict[str, int]] = None
    finalized: bool = False

def clamp_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamp score to valid range"""
    return max(min_val, min(max_val, score))

def validate_enum(value: str, valid_values: List[str]) -> str:
    """Validate enum value"""
    if value not in valid_values:
        return valid_values[0]
    return value

def coerce_date(value: Any) -> Optional[date]:
    """Coerce value to date"""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except:
            return None
    return None