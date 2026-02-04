#!/usr/bin/env python3
"""
Seed basic employee data if database is empty
"""
from datetime import date, datetime
from src.models.base import SessionLocal
from src.models.employees import Employee, Position
from src.models.employee_documents import EmployeeDocuments
from src.models.org_settings import DocumentRequirement, ComplianceRequirement

def seed_basic_data():
    """Seed basic data if database is empty"""
    db = SessionLocal()
    try:
        # Check if employees already exist
        employee_count = db.query(Employee).count()
        if employee_count > 0:
            print(f"Database already has {employee_count} employees. Skipping seed.")
            return
        
        print("Seeding basic employee data...")
        
        # Create basic employees
        employees = [
            Employee(
                employee_id="EMP001",
                first_name="John",
                last_name="Doe",
                email_id="john.doe@company.com",
                department_id=1,
                designation="Software Engineer",
                employment_type="Full-time",
                joining_date=date(2023, 1, 15)
            ),
            Employee(
                employee_id="EMP002", 
                first_name="Jane",
                last_name="Smith",
                email_id="jane.smith@company.com",
                department_id=2,
                designation="HR Manager",
                employment_type="Full-time",
                joining_date=date(2022, 6, 10)
            ),
            Employee(
                employee_id="EMP003",
                first_name="Mike",
                last_name="Johnson",
                email_id="mike.johnson@company.com", 
                department_id=3,
                designation="Marketing Specialist",
                employment_type="Full-time",
                joining_date=date(2023, 3, 20)
            ),
            Employee(
                employee_id="EMP004",
                first_name="Sarah",
                last_name="Wilson",
                email_id="sarah.wilson@company.com",
                department_id=1,
                designation="Senior Developer",
                employment_type="Full-time",
                joining_date=date(2021, 11, 5)
            )
        ]
        
        for employee in employees:
            db.add(employee)
        
        # Create document requirements
        requirements = [
            DocumentRequirement(
                document_type="ID Proof",
                is_mandatory=True,
                description="Government issued ID proof"
            ),
            DocumentRequirement(
                document_type="Address Proof", 
                is_mandatory=True,
                description="Utility bill or bank statement"
            ),
            DocumentRequirement(
                document_type="Educational Certificate",
                is_mandatory=True,
                description="Degree or diploma certificate"
            ),
            DocumentRequirement(
                document_type="Experience Letter",
                is_mandatory=False,
                description="Previous employment experience letter"
            )
        ]
        
        for req in requirements:
            db.add(req)
        
        # Create compliance requirements
        compliance_rules = [
            ComplianceRequirement(
                rule_name="Document Expiry Warning",
                department="ALL",
                threshold_days=30,
                escalation_days=7,
                scoring_weight=0.3
            ),
            ComplianceRequirement(
                rule_name="Missing Document Alert",
                department="ALL", 
                threshold_days=0,
                escalation_days=3,
                scoring_weight=0.5
            )
        ]
        
        for rule in compliance_rules:
            db.add(rule)
        
        db.commit()
        print(f"Successfully seeded {len(employees)} employees and basic configuration")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_basic_data()