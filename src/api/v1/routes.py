from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
import uuid

from src.core.controller import ComplianceController
from src.core.blackboard import Blackboard
from src.tools.email_utils import send_email
from src.models.base import SessionLocal
from src.models.employees import Employee
from src.models.document_compliance_analysis import DocumentComplianceAnalysis
from src.models.document_reminders import DocumentReminder
from src.models.users import User
from src.services.compliance_analyzer import ComplianceAnalyzer
from src.auth.auth import verify_jwt_token, authenticate_user, create_access_token
from datetime import timedelta

router = APIRouter()

class RunScanRequest(BaseModel):
    employee_id: Optional[str] = None  # Changed to string to match your model
    batch: Optional[bool] = False
    limit: Optional[int] = 25

class TestEmailRequest(BaseModel):
    employee_id: Optional[str] = Field(None, description="Employee ID to fetch email automatically")
    to: Optional[str] = Field(None, description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")

class LoginRequest(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class EmployeeResponse(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email_id: str
    department_id: int
    designation: str
    employment_type: str

@router.get("/auth/available-users")
async def get_available_users() -> Dict[str, Any]:
    """Get all users available for login from database"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        return {
            "users": [
                {
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "employee_id": user.employee_id
                } for user in users
            ],
            "total": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")
    finally:
        db.close()

@router.post("/seed-documents")
async def seed_documents() -> Dict[str, Any]:
    """Seed employee documents data"""
    try:
        from src.scripts.seed_documents import seed_employee_documents
        seed_employee_documents()
        return {"message": "Documents seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")

@router.post("/calculate-compliance/{employee_id}")
async def calculate_compliance(employee_id: str, current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Calculate missing documents and store in compliance analysis table"""
    try:
        from src.services.document_compliance_service import DocumentComplianceService
        
        with DocumentComplianceService() as service:
            result = service.calculate_missing_documents(employee_id)
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance calculation failed: {str(e)}")

@router.post("/calculate-all-compliance")
async def calculate_all_compliance(current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Calculate compliance for all employees and store in database"""
    try:
        from src.services.document_compliance_service import DocumentComplianceService
        
        with DocumentComplianceService() as service:
            result = service.process_all_employees()
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch compliance calculation failed: {str(e)}")

@router.post("/auth/init-users")
async def initialize_users() -> Dict[str, Any]:
    """Initialize users from existing employees"""
    from src.auth.auth import get_password_hash
    
    db = SessionLocal()
    try:
        # Get all employees without user accounts
        employees = db.query(Employee).all()
        created_users = []
        existing_users = []
        
        for employee in employees:
            # Check if user already exists
            existing_user = db.query(User).filter(User.employee_id == employee.employee_id).first()
            if existing_user:
                existing_users.append({
                    "email": existing_user.email,
                    "full_name": existing_user.full_name,
                    "role": existing_user.role,
                    "employee_id": existing_user.employee_id
                })
                continue
            
            # Create user account with default password
            default_password = "hrms2024"
            hashed_password = get_password_hash(default_password)
            
            user = User(
                employee_id=employee.employee_id,
                email=employee.email_id,
                hashed_password=hashed_password,
                full_name=f"{employee.first_name} {employee.last_name}",
                role="USER" if employee.designation != "HR Manager" else "ADMIN",
                is_active=True
            )
            
            db.add(user)
            created_users.append({
                "employee_id": employee.employee_id,
                "email": employee.email_id,
                "full_name": f"{employee.first_name} {employee.last_name}",
                "role": user.role,
                "default_password": default_password
            })
        
        db.commit()
        
        return {
            "message": f"Created {len(created_users)} new users, {len(existing_users)} already exist",
            "created_users": created_users,
            "existing_users": existing_users
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"User initialization failed: {str(e)}")
    finally:
        db.close()

@router.post("/auth/login")
async def login(request: LoginRequest) -> Dict[str, Any]:
    """Login endpoint to get JWT token"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Return debug info for troubleshooting
            all_users = db.query(User).all()
            return {
                "error": "User not found",
                "searched_email": request.email,
                "available_emails": [u.email for u in all_users]
            }
        
        # Try multiple password formats
        from src.auth.auth import get_password_hash
        input_hash = get_password_hash(request.password)
        
        password_matches = [
            user.hashed_password == request.password,  # Plain text
            user.hashed_password == input_hash,        # Hashed
        ]
        
        if not any(password_matches):
            return {
                "error": "Password mismatch",
                "input_password": request.password,
                "input_hash": input_hash,
                "stored_password": user.hashed_password,
                "plain_match": password_matches[0],
                "hash_match": password_matches[1]
            }
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": str(user.id), 
                "employee_id": user.employee_id,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name
            }
        )
        
        refresh_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "type": "refresh"
            },
            expires_delta=timedelta(days=7)
        )
        
        # Determine redirect URL based on role
        redirect_url = "/hr-manager-dashboard" if "Manager" in user.role else "/employee-dashboard"
        
        return {
            "user_id": str(user.id),
            "employee_id": user.employee_id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "redirect_url": redirect_url,
            "token_type": "bearer",
            "expires_in": 86400
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@router.get("/employees")
async def get_employees(limit: int = 50, current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Get all employees"""
    db = SessionLocal()
    try:
        employees = db.query(Employee).limit(limit).all()
        return {
            "employees": [
                {
                    "employee_id": emp.employee_id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "email_id": emp.email_id,
                    "department_id": emp.department_id,
                    "designation": emp.designation,
                    "employment_type": emp.employment_type
                } for emp in employees
            ],
            "total": len(employees)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employees: {str(e)}")
    finally:
        db.close()

@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, current_user: dict = Depends(verify_jwt_token)) -> EmployeeResponse:
    """Get specific employee"""
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return EmployeeResponse(
            employee_id=employee.employee_id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            email_id=employee.email_id,
            department_id=employee.department_id,
            designation=employee.designation,
            employment_type=employee.employment_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employee: {str(e)}")
    finally:
        db.close()

@router.post("/run-docs-scan")
async def run_docs_scan(request: RunScanRequest, current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Trigger document compliance scan"""
    controller = ComplianceController()
    
    try:
        if request.employee_id:
            result = controller.run_for_employee(request.employee_id)
            return {
                "processed": 1,
                "created_analyses": 1 if result.get("success") else 0,
                "created_reminders": result.get("reminders_sent", 0),
                "emails_sent": result.get("reminders_sent", 0),
                "results": [result]
            }
        elif request.batch:
            return controller.run_batch(request.limit)
        else:
            raise HTTPException(status_code=400, detail="Must specify either employee_id or batch=true")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.get("/results/{employee_identifier}")
async def get_employee_documents(employee_identifier: str, current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Get missing and submitted documents for specific employee by ID or name"""
    try:
        from src.services.compliance_analyzer import ComplianceAnalyzer
        from src.models.employee_documents import EmployeeDocuments
        
        db = SessionLocal()
        analyzer = ComplianceAnalyzer()
        
        try:
            # Find employee by ID or name
            employee = db.query(Employee).filter(Employee.employee_id == employee_identifier).first()
            
            if not employee:
                # Search by name
                from sqlalchemy import func
                employee = db.query(Employee).filter(
                    func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{employee_identifier}%")
                ).first()
            
            if not employee:
                raise HTTPException(status_code=404, detail="Employee not found")
            
            # Get submitted documents
            submitted_docs = db.query(EmployeeDocuments).filter(
                EmployeeDocuments.employee_id == employee.employee_id
            ).all()
            
            submitted_doc_names = list(set([doc.document_name for doc in submitted_docs]))
            submitted_doc_names_set = set(submitted_doc_names)
            
            # Calculate missing documents
            missing_docs = [doc for doc in analyzer.REQUIRED_DOCUMENTS if doc not in submitted_doc_names_set]
            
            return {
                "employee_id": employee.employee_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "submitted_documents": submitted_doc_names,
                "missing_documents": missing_docs
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employee documents: {str(e)}")
    """Get employee ID and name only"""
    try:
        db = SessionLocal()
        
        try:
            # Get all employees
            employees = db.query(Employee).all()
            results = []
            
            for employee in employees:
                employee_result = {
                    "employee_id": employee.employee_id,
                    "employee_name": f"{employee.first_name} {employee.last_name}"
                }
                results.append(employee_result)
            
            return {
                "total_employees": len(results),
                "results": results
            }
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@router.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Get dashboard metrics"""
    try:
        with Blackboard() as bb:
            metrics = bb.get_dashboard_metrics()
            return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.post("/analyze-compliance/{employee_id}")
async def analyze_employee_compliance(employee_id: str, current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Analyze document compliance for a specific employee"""
    analyzer = ComplianceAnalyzer()
    try:
        result = analyzer.analyze_employee_compliance(employee_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/alerts")
async def get_alerts(current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Get alerts with Employee, Risk, Alert Type, Triggered By, Notification Status, Assigned HR Exec, SLA Timer"""
    try:
        with Blackboard() as bb:
            # Get all employees
            all_employees = bb.db.query(Employee).all()
            alerts = []
            
            for employee in all_employees:
                # Get compliance analysis if exists
                analysis = bb.db.query(DocumentComplianceAnalysis).filter(
                    DocumentComplianceAnalysis.employee_id == employee.employee_id
                ).first()
                
                if analysis:
                    # Employee has analysis - use analysis data
                    alert_types = []
                    if analysis.missing_documents and len(analysis.missing_documents) > 0:
                        alert_types.append("Missing Documents")
                    if analysis.expiring_documents and len(analysis.expiring_documents) > 0:
                        alert_types.append("Expiring Documents")
                    if not alert_types:
                        alert_types.append("Compliance Check")
                    
                    missing_docs = analysis.missing_documents or []
                    risk_level = analysis.priority_level
                else:
                    # Employee has no analysis - calculate missing docs
                    from src.services.compliance_analyzer import ComplianceAnalyzer
                    from src.models.employee_documents import EmployeeDocuments
                    analyzer = ComplianceAnalyzer()
                    
                    submitted_docs = bb.db.query(EmployeeDocuments).filter(
                        EmployeeDocuments.employee_id == employee.employee_id
                    ).all()
                    
                    submitted_doc_names = set([doc.document_name for doc in submitted_docs])
                    missing_docs = [doc for doc in analyzer.REQUIRED_DOCUMENTS if doc not in submitted_doc_names]
                    
                    alert_types = ["Documents Not Submitted"] if missing_docs else ["Compliant"]
                    risk_level = "High" if missing_docs else "Low"
                
                # Check if reminder was sent
                reminder = bb.db.query(DocumentReminder).filter(
                    DocumentReminder.employee_id == employee.employee_id
                ).order_by(DocumentReminder.created_at.desc()).first()
                
                notification_status = "Sent" if reminder and reminder.reminder_sent else "Pending"
                
                # Calculate SLA timer
                from datetime import datetime
                if analysis:
                    days_elapsed = (datetime.now() - analysis.created_at.replace(tzinfo=None)).days
                else:
                    days_elapsed = 0
                sla_timer = f"{days_elapsed} days"
                
                # Only add to alerts if employee has missing documents
                if missing_docs:
                    alerts.append({
                        "employee_id": employee.employee_id,
                        "employee": f"{employee.first_name} {employee.last_name}",
                        "risk": risk_level,
                        "alert_type": ", ".join(alert_types),
                        "triggered_by": "System Automated Scan",
                        "notification_status": notification_status,
                        "assigned_hr_exec": "HR Team",
                        "sla_timer": sla_timer,
                        "missing_documents": missing_docs
                    })
            
            return {
                "total_alerts": len(alerts),
                "alerts": alerts
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/compliance-filter")
async def get_compliance_filter(
    employee: Optional[str] = None,
    department: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: dict = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """Get filtered compliance summary"""
    analyzer = ComplianceAnalyzer()
    try:
        result = analyzer.get_filtered_compliance(employee, department, risk_level)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filtered compliance: {str(e)}")

@router.get("/compliance-summary")
async def get_compliance_summary(current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Get overall compliance summary"""
    analyzer = ComplianceAnalyzer()
    try:
        summary = analyzer.get_compliance_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.post("/send-test-email")
async def send_test_email(request: TestEmailRequest, current_user: dict = Depends(verify_jwt_token)) -> Dict[str, Any]:
    """Send test email with missing documents"""
    try:
        employee_id = request.employee_id
        subject = request.subject
        email_body = request.body
        recipient_email = request.to  # Use provided email or will be set from employee
        
        # Determine recipient email
        if request.employee_id:
            # Fetch email from employee table
            db = SessionLocal()
            try:
                employee = db.query(Employee).filter(Employee.employee_id == request.employee_id).first()
                if not employee:
                    raise HTTPException(status_code=404, detail="Employee not found")
                
                # Use employee's actual email
                recipient_email = employee.email_id
                
                # Get missing documents for this employee
                from src.services.compliance_analyzer import ComplianceAnalyzer
                from src.models.employee_documents import EmployeeDocuments
                analyzer = ComplianceAnalyzer()
                
                # Get submitted documents
                submitted_docs = db.query(EmployeeDocuments).filter(
                    EmployeeDocuments.employee_id == employee_id
                ).all()
                submitted_doc_names = {doc.document_name for doc in submitted_docs}
                
                # Calculate missing documents
                missing_docs = [doc for doc in analyzer.REQUIRED_DOCUMENTS if doc not in submitted_doc_names]
                
                # Create email body with missing documents
                if missing_docs:
                    missing_docs_text = "\n- ".join(missing_docs)
                    email_body = f"""Dear {employee.first_name} {employee.last_name},

Employee ID: {employee.employee_id}
Employee Name: {employee.first_name} {employee.last_name}

You have the following missing documents that need to be submitted:

- {missing_docs_text}

Please submit these documents as soon as possible to complete your compliance requirements.

Thank you,
HR Team"""
                    subject = f"URGENT: {len(missing_docs)} Missing Documents - {employee.employee_id} {employee.first_name} {employee.last_name}"
                else:
                    email_body = f"""Dear {employee.first_name} {employee.last_name},

Employee ID: {employee.employee_id}
Employee Name: {employee.first_name} {employee.last_name}

All your required documents have been submitted. Your compliance is up to date.

Thank you,
HR Team"""
                    subject = f"Document Compliance Complete - {employee.employee_id} {employee.first_name} {employee.last_name}"
                
            finally:
                db.close()
        elif request.to:
            recipient_email = request.to
        else:
            raise HTTPException(status_code=400, detail="Either employee_id or to email must be provided")
        
        status_code = send_email(recipient_email, subject, email_body)
        
        # Create reminder record if email sent successfully and employee_id exists
        if status_code in [200, 202] and employee_id:
            db = SessionLocal()
            try:
                reminder = DocumentReminder(
                    employee_id=employee_id,
                    document_type="Missing Documents Email",
                    reminder_type="manual",
                    reminder_sent=True,
                    reminder_count=1
                )
                db.add(reminder)
                db.commit()
            except Exception as e:
                print(f"Failed to create reminder record: {e}")
            finally:
                db.close()
        
        return {
            "status_code": status_code,
            "success": status_code in [200, 202],
            "message": "Email sent successfully" if status_code in [200, 202] else "Email send failed",
            "recipient": recipient_email,
            "subject": subject,
            "body": email_body
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send failed: {str(e)}")