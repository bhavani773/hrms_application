from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from src.models.employees import Employee
from src.models.employee_documents import EmployeeDocuments
from src.models.document_compliance_analysis import DocumentComplianceAnalysis
from src.models.base import SessionLocal

class ComplianceAnalyzer:
    
    REQUIRED_DOCUMENTS = [
        "Aadhar Card", "PAN Card", "Passport", "Resume", "Educational Certificate",
        "Experience Letter", "Salary Slip", "Bank Statement", "Photo"
    ]
    
    DEPARTMENT_MAPPING = {
        1: "Engineering",
        2: "Human Resources", 
        3: "Sales",
        4: "Finance",
        5: "Marketing",
        6: "Operations",
        7: "Support",
        8: "IT",
        9: "Quality Assurance",
        10: "Research & Development"
    }
    
    def analyze_employee_compliance(self, employee_id: str) -> Dict[str, Any]:
        """Analyze document compliance for an employee and store results"""
        db = SessionLocal()
        try:
            # Get employee and documents
            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                return {"error": "Employee not found"}
            
            documents = db.query(EmployeeDocuments).filter(
                EmployeeDocuments.employee_id == employee_id
            ).all()
            
            # Analyze compliance
            analysis = self._perform_analysis(employee, documents)
            
            # Store in database
            compliance_record = DocumentComplianceAnalysis(
                employee_id=employee_id,
                compliance_score=analysis["compliance_score"],
                missing_documents=analysis["missing_documents"],
                expiring_documents=analysis["expiring_documents"],
                risk_assessment=analysis["risk_assessment"],
                action_plan=analysis["action_plan"],
                priority_level=analysis["priority_level"]
            )
            
            # Remove existing analysis for this employee
            db.query(DocumentComplianceAnalysis).filter(
                DocumentComplianceAnalysis.employee_id == employee_id
            ).delete()
            
            db.add(compliance_record)
            db.commit()
            
            return {
                "success": True,
                "employee_id": employee_id,
                "analysis": analysis
            }
            
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()
    
    def _perform_analysis(self, employee: Employee, documents: List[EmployeeDocuments]) -> Dict[str, Any]:
        """Perform the actual compliance analysis"""
        
        # Get document names that employee has submitted
        existing_docs = {doc.document_name for doc in documents if doc.status in ['verified', 'approved', 'submitted']}
        
        # Find missing documents (exclude submitted ones)
        missing_docs = [doc for doc in self.REQUIRED_DOCUMENTS if doc not in existing_docs]
        
        # Find expiring documents (within 30 days)
        expiring_docs = []
        thirty_days = datetime.now().date() + timedelta(days=30)
        
        for doc in documents:
            # Assuming documents have expiry logic based on upload date + 1 year
            if doc.upload_date:
                expiry_date = doc.upload_date + timedelta(days=365)
                if expiry_date <= thirty_days:
                    expiring_docs.append({
                        "document_name": doc.document_name,
                        "expiry_date": expiry_date.isoformat(),
                        "status": doc.status
                    })
        
        # Calculate compliance score
        total_required = len(self.REQUIRED_DOCUMENTS)
        total_missing = len(missing_docs)
        compliance_score = ((total_required - total_missing) / total_required) * 100
        
        # Determine priority level
        if compliance_score >= 90:
            priority_level = "Low"
        elif compliance_score >= 70:
            priority_level = "Medium"
        else:
            priority_level = "High"
        
        # Create risk assessment
        risk_assessment = {
            "compliance_percentage": compliance_score,
            "missing_count": total_missing,
            "expiring_count": len(expiring_docs),
            "risk_factors": []
        }
        
        if total_missing > 3:
            risk_assessment["risk_factors"].append("High number of missing documents")
        if len(expiring_docs) > 0:
            risk_assessment["risk_factors"].append("Documents expiring soon")
        
        # Create action plan
        action_plan = {
            "immediate_actions": [],
            "follow_up_actions": []
        }
        
        if missing_docs:
            action_plan["immediate_actions"].append(f"Collect missing documents: {', '.join(missing_docs)}")
        
        if expiring_docs:
            action_plan["follow_up_actions"].append("Renew expiring documents")
        
        return {
            "compliance_score": round(compliance_score, 2),
            "missing_documents": missing_docs,
            "expiring_documents": expiring_docs,
            "risk_assessment": risk_assessment,
            "action_plan": action_plan,
            "priority_level": priority_level
        }
    
    def get_filtered_compliance(self, employee: str = None, department: str = None, risk_level: str = None) -> Dict[str, Any]:
        """Get filtered compliance summary"""
        db = SessionLocal()
        try:
            # Build query with filters
            query = db.query(DocumentComplianceAnalysis, Employee).join(
                Employee, DocumentComplianceAnalysis.employee_id == Employee.employee_id
            )
            
            # Apply employee filter (works for both name and ID)
            if employee:
                query = query.filter(
                    or_(
                        Employee.employee_id == employee,
                        Employee.first_name.ilike(f"%{employee}%"),
                        Employee.last_name.ilike(f"%{employee}%"),
                        func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{employee}%")
                    )
                )
            
            # Apply department filter by name
            if department:
                # Find department ID by name
                dept_id = None
                for dept_id_key, dept_name in self.DEPARTMENT_MAPPING.items():
                    if dept_name.lower() == department.lower():
                        dept_id = dept_id_key
                        break
                if dept_id:
                    query = query.filter(Employee.department_id == dept_id)
            
            if risk_level:
                query = query.filter(DocumentComplianceAnalysis.priority_level == risk_level)
            
            analyses = query.all()
            
            if not analyses:
                return {
                    "total_employees": 0,
                    "compliance_summary": []
                }
            
            compliance_data = []
            
            # Process each analysis
            for analysis, employee in analyses:
                # Get last verified document date
                last_verified_doc = db.query(EmployeeDocuments).filter(
                    and_(
                        EmployeeDocuments.employee_id == employee.employee_id,
                        EmployeeDocuments.status == "Verified"
                    )
                ).order_by(EmployeeDocuments.updated_at.desc()).first()
                
                last_verified = last_verified_doc.updated_at.strftime("%Y-%m-%d") if last_verified_doc else "Never"
                
                # Count missing documents
                missing_docs_count = len(analysis.missing_documents) if analysis.missing_documents else 0
                
                employee_data = {
                    "employee": f"{employee.first_name} {employee.last_name}",
                    "role": employee.designation,
                    "department": self.DEPARTMENT_MAPPING.get(employee.department_id, f"Dept-{employee.department_id}"),
                    "compliance_score": f"{float(analysis.compliance_score):.1f}%",
                    "missing_docs": missing_docs_count,
                    "risk_level": analysis.priority_level,
                    "last_verified": last_verified
                }
                
                compliance_data.append(employee_data)
            
            return {
                "total_employees": len(compliance_data),
                "compliance_summary": compliance_data
            }
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary for ALL employees in database"""
        db = SessionLocal()
        try:
            # Get ALL employees from database
            all_employees = db.query(Employee).all()
            
            if not all_employees:
                return {"message": "No employees found"}
            
            compliance_data = []
            
            # Process each employee
            for employee in all_employees:
                # Try to get compliance analysis for this employee
                analysis = db.query(DocumentComplianceAnalysis).filter(
                    DocumentComplianceAnalysis.employee_id == employee.employee_id
                ).first()
                
                if analysis:
                    # Employee has compliance analysis
                    # Get last verified document date
                    last_verified_doc = db.query(EmployeeDocuments).filter(
                        and_(
                            EmployeeDocuments.employee_id == employee.employee_id,
                            EmployeeDocuments.status == "Verified"
                        )
                    ).order_by(EmployeeDocuments.updated_at.desc()).first()
                    
                    # Get submitted documents count and list
                    submitted_docs = db.query(EmployeeDocuments).filter(
                        EmployeeDocuments.employee_id == employee.employee_id
                    ).all()
                    
                    submitted_docs_list = list(set([doc.document_name for doc in submitted_docs]))
                    submitted_docs_count = len(submitted_docs_list)  # Use unique count
                    
                    # Calculate missing documents
                    submitted_doc_names = set(submitted_docs_list)
                    missing_docs_list = [doc for doc in self.REQUIRED_DOCUMENTS if doc not in submitted_doc_names]
                    missing_docs_count = len(missing_docs_list)
                    
                    # Calculate compliance score for analyzed employee (recalculate based on actual data)
                    total_required = len(self.REQUIRED_DOCUMENTS)
                    unique_submitted_count = len(submitted_doc_names)
                    calc_compliance_score = ((unique_submitted_count / total_required) * 100) if total_required > 0 else 0
                    compliance_score = f"{calc_compliance_score:.1f}%"
                    last_verified = last_verified_doc.updated_at.strftime("%Y-%m-%d") if last_verified_doc else "Never"
                    risk_level = analysis.priority_level
                else:
                    # Employee has no compliance analysis - calculate missing docs manually
                    submitted_docs = db.query(EmployeeDocuments).filter(
                        EmployeeDocuments.employee_id == employee.employee_id
                    ).all()
                    
                    submitted_docs_list = list(set([doc.document_name for doc in submitted_docs]))
                    submitted_docs_count = len(submitted_docs_list)  # Use unique count
                    
                    # Calculate missing docs for non-analyzed employee
                    submitted_doc_names = set(submitted_docs_list)
                    missing_docs_list = [doc for doc in self.REQUIRED_DOCUMENTS if doc not in submitted_doc_names]
                    missing_docs_count = len(missing_docs_list)
                    
                    # Calculate compliance score for non-analyzed employee
                    total_required = len(self.REQUIRED_DOCUMENTS)
                    unique_submitted_count = len(submitted_doc_names)  # Use unique count
                    calc_compliance_score = ((unique_submitted_count / total_required) * 100) if total_required > 0 else 0
                    compliance_score = f"{calc_compliance_score:.1f}%"
                    last_verified = "Not Analyzed"
                    risk_level = "Not Analyzed"
                
                employee_data = {
                    "employee": f"{employee.first_name} {employee.last_name}",
                    "role": employee.designation,
                    "department": self.DEPARTMENT_MAPPING.get(employee.department_id, f"Dept-{employee.department_id}"),
                    "compliance_score": compliance_score,
                    "missing_docs": missing_docs_count,
                    "missing_docs_list": missing_docs_list,
                    "submitted_docs": submitted_docs_count,
                    "submitted_docs_list": submitted_docs_list,
                    "risk_level": risk_level,
                    "last_verified": last_verified
                }
                
                compliance_data.append(employee_data)
            
            return {
                "total_employees": len(compliance_data),
                "compliance_summary": compliance_data
            }
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            db.close()