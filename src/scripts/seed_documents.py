from datetime import date, datetime
from src.models.base import SessionLocal
from src.models.employees import Employee
from src.models.employee_documents import EmployeeDocuments
import random

def seed_employee_documents():
    """Add sample documents to employee_documents table"""
    db = SessionLocal()
    try:
        # Check if documents already exist
        doc_count = db.query(EmployeeDocuments).count()
        if doc_count > 0:
            print(f"Documents already exist ({doc_count} records). Skipping seed.")
            return
        
        # Get all employees
        employees = db.query(Employee).all()
        
        # Document types
        document_types = [
            "Aadhar Card", "PAN Card", "Passport", "Resume", "Educational Certificate",
            "Experience Letter", "Salary Slip", "Bank Statement", "Photo"
        ]
        
        statuses = ["submitted", "verified", "approved", "pending", "rejected"]
        
        documents_added = 0
        
        for employee in employees:
            # Randomly assign 1-3 documents per employee
            num_docs = random.randint(1, 3)
            selected_docs = random.sample(document_types, num_docs)
            
            for doc_type in selected_docs:
                document = EmployeeDocuments(
                    employee_id=employee.employee_id,
                    document_name=doc_type,
                    file_name=f"{doc_type.replace(' ', '_').lower()}_{employee.employee_id}.pdf",
                    file_path=f"/uploads/{employee.employee_id}/{doc_type.replace(' ', '_').lower()}.pdf",
                    status=random.choice(statuses),
                    upload_date=date.today(),
                    category="Identity" if doc_type in ["Aadhar Card", "PAN Card", "Passport"] else "Professional"
                )
                db.add(document)
                documents_added += 1
        
        db.commit()
        print(f"Successfully added {documents_added} documents for {len(employees)} employees")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding documents: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_employee_documents()