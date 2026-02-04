from sqlalchemy.orm import Session
from src.models.base import SessionLocal
from src.models.employees import Employee
from src.models.employee_documents import EmployeeDocuments
from src.models.org_settings import DocumentRequirement
from src.models.document_compliance_analysis import DocumentComplianceAnalysis
from datetime import datetime, date
from typing import List, Dict, Any

class DocumentComplianceService:
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def calculate_missing_documents(self, employee_id: str) -> Dict[str, Any]:
        """Calculate missing documents for an employee and store in compliance analysis table"""
        
        # Get employee
        employee = self.db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            return {"error": "Employee not found"}
        
        # Get all required documents
        required_docs = self.db.query(DocumentRequirement).filter(
            DocumentRequirement.is_mandatory == True
        ).all()
        required_doc_types = [doc.document_type for doc in required_docs]
        
        # Get employee's submitted documents with verified status
        submitted_docs = self.db.query(EmployeeDocuments).filter(
            EmployeeDocuments.employee_id == employee_id,
            EmployeeDocuments.status.in_(['verified', 'approved', 'submitted'])
        ).all()
        submitted_doc_types = [doc.document_name for doc in submitted_docs]
        
        # Calculate missing documents (exclude already submitted ones)
        missing_documents = [doc for doc in required_doc_types if doc not in submitted_doc_types]
        
        # Calculate expiring documents (within 30 days)
        expiring_documents = []
        for doc in submitted_docs:
            if doc.expiry_date and doc.expiry_date <= date.today().replace(day=date.today().day + 30):
                expiring_documents.append({
                    "document_type": doc.document_name,
                    "expiry_date": doc.expiry_date.isoformat(),
                    "days_remaining": (doc.expiry_date - date.today()).days
                })
        
        # Calculate compliance score
        total_required = len(required_doc_types)
        submitted_count = len([doc for doc in required_doc_types if doc in submitted_doc_types])
        compliance_score = (submitted_count / total_required * 100) if total_required > 0 else 100
        
        # Determine priority level
        if compliance_score < 50:
            priority_level = "High"
        elif compliance_score < 80:
            priority_level = "Medium"
        else:
            priority_level = "Low"
        
        # Create risk assessment
        risk_assessment = {
            "compliance_score": compliance_score,
            "missing_count": len(missing_documents),
            "expiring_count": len(expiring_documents),
            "risk_factors": []
        }
        
        if len(missing_documents) > 3:
            risk_assessment["risk_factors"].append("Multiple missing documents")
        if len(expiring_documents) > 0:
            risk_assessment["risk_factors"].append("Documents expiring soon")
        
        # Create action plan
        action_plan = {
            "immediate_actions": [],
            "follow_up_actions": []
        }
        
        if missing_documents:
            action_plan["immediate_actions"].append("Request missing documents from employee")
        if expiring_documents:
            action_plan["follow_up_actions"].append("Send renewal reminders for expiring documents")
        
        # Store in document_compliance_analysis table
        existing_analysis = self.db.query(DocumentComplianceAnalysis).filter(
            DocumentComplianceAnalysis.employee_id == employee_id
        ).first()
        
        if existing_analysis:
            # Update existing record
            existing_analysis.compliance_score = compliance_score
            existing_analysis.missing_documents = missing_documents
            existing_analysis.expiring_documents = expiring_documents
            existing_analysis.risk_assessment = risk_assessment
            existing_analysis.action_plan = action_plan
            existing_analysis.priority_level = priority_level
            existing_analysis.created_at = datetime.now()
        else:
            # Create new record
            analysis = DocumentComplianceAnalysis(
                employee_id=employee_id,
                compliance_score=compliance_score,
                missing_documents=missing_documents,
                expiring_documents=expiring_documents,
                risk_assessment=risk_assessment,
                action_plan=action_plan,
                priority_level=priority_level
            )
            self.db.add(analysis)
        
        self.db.commit()
        
        # Create submitted documents list with details
        submitted_documents = []
        for doc in submitted_docs:
            submitted_documents.append({
                "document_type": doc.document_name,
                "status": doc.status,
                "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                "file_name": doc.file_name
            })
        
        return {
            "employee_id": employee_id,
            "compliance_score": compliance_score,
            "missing_documents": missing_documents,
            "submitted_documents": submitted_documents,
            "expiring_documents": expiring_documents,
            "priority_level": priority_level,
            "stored_in_db": True
        }
    
    def process_all_employees(self) -> Dict[str, Any]:
        """Process compliance analysis for all employees"""
        employees = self.db.query(Employee).all()
        results = []
        
        for employee in employees:
            result = self.calculate_missing_documents(employee.employee_id)
            results.append(result)
        
        return {
            "processed_count": len(results),
            "results": results
        }