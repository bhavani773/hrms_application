#!/usr/bin/env python3
from src.models.base import SessionLocal
from src.models.employees import Employee

db = SessionLocal()
try:
    # Update EMP005 with correct data
    emp005 = db.query(Employee).filter(Employee.employee_id == "EMP005").first()
    if emp005:
        print(f"Current EMP005: {emp005.first_name} {emp005.last_name} - {emp005.email_id}")
        
        # Update with correct data
        emp005.first_name = "Manikanta"
        emp005.last_name = "Karri"
        emp005.email_id = "manikantakarri508@gmail.com"
        
        db.commit()
        print(f"Updated EMP005: {emp005.first_name} {emp005.last_name} - {emp005.email_id}")
    else:
        print("EMP005 not found, creating new record")
        new_emp = Employee(
            employee_id="EMP005",
            first_name="Manikanta",
            last_name="Karri",
            email_id="manikantakarri508@gmail.com",
            department_id=1,
            designation="Software Engineer",
            employment_type="Full-time",
            phone_number="+91-9876543214",
            joining_date="2023-05-20",
            shift_id=1
        )
        db.add(new_emp)
        db.commit()
        print("Created new EMP005 record")
        
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()