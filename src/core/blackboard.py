from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Optional, Any
from datetime import date, datetime
import uuid

from src.models.base import SessionLocal
from src.models.employees import Employee, Position
from src.models.employee_documents import EmployeeDocuments
from src.models.org_settings import DocumentRequirement, ComplianceRequirement, SystemSetting
from src.models.document_compliance_analysis import DocumentComplianceAnalysis
from src.models.document_reminders import DocumentReminder

class Blackboard:
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def insert_analysis_record(self, employee_id: uuid.UUID, compliance_score: float, 
                             missing_documents: List[str], expiring_documents: List[Dict],
                             risk_assessment: Dict, action_plan: Dict, priority_level: str) -> uuid.UUID:
        """Insert compliance analysis record"""
        record = DocumentComplianceAnalysis(
            employee_id=employee_id,
            compliance_score=compliance_score,
            missing_documents=missing_documents,
            expiring_documents=expiring_documents,
            risk_assessment=risk_assessment,
            action_plan=action_plan,
            priority_level=priority_level
        )
        self.db.add(record)
        self.db.commit()
        return record.id
    
    def upsert_reminder(self, employee_id: uuid.UUID, document_type: str, 
                       reminder_type: str, due_date: Optional[date] = None) -> uuid.UUID:
        """Insert or update document reminder"""
        existing = self.db.query(DocumentReminder).filter(
            and_(
                DocumentReminder.employee_id == employee_id,
                DocumentReminder.document_type == document_type,
                DocumentReminder.reminder_type == reminder_type
            )
        ).first()
        
        if existing:
            existing.due_date = due_date
            self.db.commit()
            return existing.id
        else:
            reminder = DocumentReminder(
                employee_id=employee_id,
                document_type=document_type,
                reminder_type=reminder_type,
                due_date=due_date
            )
            self.db.add(reminder)
            self.db.commit()
            return reminder.id
    
    def mark_reminder_sent(self, reminder_id: uuid.UUID, success: bool) -> None:
        """Mark reminder as sent and increment count"""
        reminder = self.db.query(DocumentReminder).filter(DocumentReminder.id == reminder_id).first()
        if reminder:
            reminder.reminder_sent = success
            reminder.reminder_count += 1
            self.db.commit()
    
    def get_results_by_identifier(self, identifier: str) -> Dict[str, Any]:
        """Get analysis and reminder results for employee by ID or name"""
        # Try to find employee by ID first, then by name
        employee = self.db.query(Employee).filter(Employee.employee_id == identifier).first()
        
        if not employee:
            # Search by full name only
            employee = self.db.query(Employee).filter(
                func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{identifier}%")
            ).first()
        
        if not employee:
            return {"error": "Employee not found"}
        
        analysis = self.db.query(DocumentComplianceAnalysis).filter(
            DocumentComplianceAnalysis.employee_id == employee.employee_id
        ).order_by(DocumentComplianceAnalysis.created_at.desc()).all()
        
        reminders = self.db.query(DocumentReminder).filter(
            DocumentReminder.employee_id == employee.employee_id
        ).order_by(DocumentReminder.created_at.desc()).all()
        
        return {
            "employee_id": employee.employee_id,
            "employee_name": f"{employee.first_name} {employee.last_name}",
            "analysis": [self._analysis_to_dict(a) for a in analysis],
            "reminders": [self._reminder_to_dict(r) for r in reminders]
        }
    
    def get_employee_profile(self, employee_id: str) -> Optional[Dict]:
        """Get employee profile with position"""
        employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            return None
        
        return {
            "employee_id": employee.employee_id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "email": employee.email_id,
            "department": employee.department_id,
            "designation": employee.designation,
            "joining_date": employee.joining_date
        }
    
    def get_employee_documents(self, employee_id: str) -> List[Dict]:
        """Get employee documents"""
        docs = self.db.query(EmployeeDocuments).filter(
            EmployeeDocuments.employee_id == employee_id
        ).all()
        
        return [self._document_to_dict(doc) for doc in docs]
    
    def get_requirements_for_role(self, role_id: uuid.UUID) -> List[str]:
        """Get document requirements for specific role"""
        position = self.db.query(Position).filter(Position.id == role_id).first()
        if position and position.required_documents:
            import json
            try:
                return json.loads(position.required_documents)
            except:
                return []
        return []
    
    def get_mandatory_requirements(self) -> List[str]:
        """Get mandatory document requirements"""
        reqs = self.db.query(DocumentRequirement).filter(
            DocumentRequirement.is_mandatory == True
        ).all()
        return [req.document_type for req in reqs]
    
    def get_org_compliance_policies(self) -> Dict[str, Any]:
        """Get organization compliance policies"""
        policies = self.db.query(ComplianceRequirement).all()
        return {
            policy.rule_name: {
                "department": policy.department,
                "threshold_days": policy.threshold_days,
                "escalation_days": policy.escalation_days,
                "scoring_weight": policy.scoring_weight
            }
            for policy in policies
        }
    
    def get_all_employees(self, limit: Optional[int] = None) -> List[str]:
        """Get all employee IDs"""
        query = self.db.query(Employee.employee_id)
        if limit:
            query = query.limit(limit)
        return [row[0] for row in query.all()]
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics - only show employees with missing documents"""
        from datetime import date
        from src.services.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        
        # Employee tracked - total employees in database
        employees_tracked = self.db.query(func.count(Employee.employee_id)).scalar() or 0
        
        # Get all employees and check their document status
        all_employees = self.db.query(Employee).all()
        employees_with_missing_docs = 0
        fully_compliant_count = 0
        history = []
        
        for employee in all_employees:
            # Get submitted documents
            submitted_docs = self.db.query(EmployeeDocuments).filter(
                EmployeeDocuments.employee_id == employee.employee_id
            ).all()
            
            submitted_doc_names = set([doc.document_name for doc in submitted_docs])
            missing_docs = [doc for doc in analyzer.REQUIRED_DOCUMENTS if doc not in submitted_doc_names]
            
            if missing_docs:
                employees_with_missing_docs += 1
                
                # Get compliance analysis if exists for risk level only
                analysis = self.db.query(DocumentComplianceAnalysis).filter(
                    DocumentComplianceAnalysis.employee_id == employee.employee_id
                ).first()
                
                if analysis:
                    risk_level = analysis.priority_level
                else:
                    risk_level = "High"
                
                action = "Monitor" if risk_level == "Low" else "Follow Up Required" if risk_level == "Medium" else "Immediate Action"
                
                # Add to history only if employee has missing documents
                history.append({
                    "employee": f"{employee.first_name} {employee.last_name}",
                    "risk": risk_level,
                    "issue_type": "Missing Documents",
                    "triggered_by": "System Automated Scan",
                    "action": action
                })
            else:
                # Employee is fully compliant
                fully_compliant_count += 1
        
        # Alerts sent today - reminders sent today
        today = date.today()
        alerts_sent_today = self.db.query(func.count(DocumentReminder.id)).filter(
            and_(
                func.date(DocumentReminder.created_at) == today,
                DocumentReminder.reminder_sent == True
            )
        ).scalar() or 0
        
        return {
            "employees_tracked": employees_tracked,
            "fully_compliant": fully_compliant_count,
            "missing_documents": employees_with_missing_docs,
            "alerts_sent_today": alerts_sent_today,
            "history": history
        }
    
    def _analysis_to_dict(self, analysis: DocumentComplianceAnalysis) -> Dict:
        return {
            "id": str(analysis.id),
            "employee_id": str(analysis.employee_id),
            "compliance_score": float(analysis.compliance_score),
            "missing_documents": analysis.missing_documents
        }
    
    def _reminder_to_dict(self, reminder: DocumentReminder) -> Dict:
        return {
            "id": str(reminder.id),
            "employee_id": str(reminder.employee_id),
            "document_type": reminder.document_type,
            "reminder_type": reminder.reminder_type,
            "due_date": reminder.due_date.isoformat() if reminder.due_date else None,
            "reminder_sent": reminder.reminder_sent,
            "reminder_count": reminder.reminder_count,
            "created_at": reminder.created_at.isoformat()
        }
    
    def _document_to_dict(self, doc: EmployeeDocuments) -> Dict:
        return {
            "id": str(doc.document_id),
            "document_type": doc.document_name,
            "status": doc.status,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "file_name": doc.file_name,
            "category": doc.category
        }