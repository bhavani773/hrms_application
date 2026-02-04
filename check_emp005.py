#!/usr/bin/env python3
from src.models.base import SessionLocal
from src.models.employees import Employee

db = SessionLocal()
try:
    emp005 = db.query(Employee).filter(Employee.employee_id == "EMP005").first()
    if emp005:
        print(f"EMP005 Database Data:")
        print(f"Name: {emp005.first_name} {emp005.last_name}")
        print(f"Email: {emp005.email_id}")
        print(f"Department: {emp005.department_id}")
        print(f"Designation: {emp005.designation}")
    else:
        print("EMP005 not found in database")
        
    # Check if Manikanta exists
    manikanta = db.query(Employee).filter(Employee.first_name.ilike("%manikanta%")).first()
    if manikanta:
        print(f"\nManikanta found:")
        print(f"ID: {manikanta.employee_id}")
        print(f"Name: {manikanta.first_name} {manikanta.last_name}")
        print(f"Email: {manikanta.email_id}")
        
finally:
    db.close()