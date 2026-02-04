#!/usr/bin/env python3
"""
Debug script to check employee data in database
"""
from src.models.base import SessionLocal
from src.models.employees import Employee

def check_employee_data():
    """Check what employee data is actually in the database"""
    db = SessionLocal()
    try:
        # Get all employees
        employees = db.query(Employee).all()
        
        print(f"Found {len(employees)} employees in database:")
        print("-" * 80)
        
        for emp in employees:
            print(f"ID: {emp.employee_id}")
            print(f"Name: {emp.first_name} {emp.last_name}")
            print(f"Email: {emp.email_id}")
            print(f"Department: {emp.department_id}")
            print(f"Designation: {emp.designation}")
            print("-" * 40)
        
        # Check specifically for EMP005
        emp005 = db.query(Employee).filter(Employee.employee_id == "EMP005").first()
        if emp005:
            print(f"\nEMP005 Details:")
            print(f"Name: {emp005.first_name} {emp005.last_name}")
            print(f"Email: {emp005.email_id}")
        else:
            print("\nEMP005 not found in database")
            
        # Check for Manikanta Karri
        manikanta = db.query(Employee).filter(Employee.first_name == "Manikanta").first()
        if manikanta:
            print(f"\nManikanta found:")
            print(f"ID: {manikanta.employee_id}")
            print(f"Name: {manikanta.first_name} {manikanta.last_name}")
            print(f"Email: {manikanta.email_id}")
        else:
            print("\nManikanta not found in database")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_employee_data()