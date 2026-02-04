#!/usr/bin/env python3
import json
import uuid
from datetime import datetime, timedelta
import random

# Generate 50+ employees with realistic data
employees = []
employee_documents = []

first_names = ["Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anita", "Rohit", "Kavya", "Arjun", "Deepika",
               "Sanjay", "Meera", "Karan", "Pooja", "Rahul", "Neha", "Suresh", "Divya", "Manoj", "Ritu",
               "Anil", "Sunita", "Ravi", "Geeta", "Ashok", "Seema", "Vinod", "Rekha", "Sunil", "Nisha",
               "Prakash", "Shweta", "Ramesh", "Preeti", "Ajay", "Sonia", "Mukesh", "Vandana", "Dinesh", "Kavita",
               "Yogesh", "Sapna", "Naresh", "Jyoti", "Mahesh", "Usha", "Rajesh", "Meena", "Sudhir", "Lata",
               "Kishore", "Radha", "Mohan", "Sushma", "Ganesh"]

last_names = ["Kumar", "Sharma", "Patel", "Gupta", "Singh", "Reddy", "Jain", "Nair", "Mehta", "Rao",
              "Verma", "Iyer", "Malhotra", "Agarwal", "Chopra", "Bansal", "Saxena", "Mishra", "Tiwari", "Pandey"]

departments = ["Engineering", "Human Resources", "Sales", "Finance", "Marketing", "Operations", "Support"]
position_ids = [
    "550e8400-e29b-41d4-a716-446655440001",  # Software Engineer
    "550e8400-e29b-41d4-a716-446655440002",  # HR Manager
    "550e8400-e29b-41d4-a716-446655440003",  # Sales Executive
    "550e8400-e29b-41d4-a716-446655440004",  # Finance Analyst
    "550e8400-e29b-41d4-a716-446655440005",  # Marketing Manager
    "550e8400-e29b-41d4-a716-446655440006",  # Operations Manager
    "550e8400-e29b-41d4-a716-446655440007",  # Data Scientist
    "550e8400-e29b-41d4-a716-446655440008"   # Customer Support
]

# Generate 55 employees
for i in range(55):
    emp_id = f"650e8400-e29b-41d4-a716-44665544{i+1:04d}"
    
    employee = {
        "id": emp_id,
        "employee_id": f"EMP{i+1:03d}",
        "first_name": random.choice(first_names),
        "last_name": random.choice(last_names),
        "email": f"employee{i+1:03d}@company.com",
        "phone": f"+91-987654{3210+i}",
        "department": random.choice(departments),
        "position_id": random.choice(position_ids),
        "hire_date": (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))).isoformat(),
        "status": "active"
    }
    employees.append(employee)
    
    # Generate documents for each employee
    doc_types = ["Aadhaar", "PAN", "Address Proof", "Bank Proof", "Education Certificate", "Experience Letter", "Photo", "UAN", "ESIC"]
    statuses = ["pending", "submitted", "verified", "expired"]
    
    # Each employee gets 3-6 random documents
    num_docs = random.randint(3, 6)
    selected_docs = random.sample(doc_types, num_docs)
    
    for doc_type in selected_docs:
        status = random.choice(statuses)
        
        # Generate realistic dates
        submitted_date = None
        verified_date = None
        expiry_date = None
        
        if status in ["submitted", "verified"]:
            submitted_date = (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 400))).isoformat()
            
        if status == "verified":
            verified_date = (datetime.fromisoformat(submitted_date) + timedelta(days=random.randint(1, 5))).isoformat()
        
        # Add expiry dates for applicable documents
        if doc_type in ["Address Proof", "Bank Proof", "Photo", "ESIC"]:
            if status == "expired":
                expiry_date = (datetime.now() - timedelta(days=random.randint(1, 90))).date().isoformat()
            else:
                expiry_date = (datetime.now() + timedelta(days=random.randint(30, 730))).date().isoformat()
        
        document = {
            "employee_id": emp_id,
            "document_type": doc_type,
            "status": status,
            "expiry_date": expiry_date,
            "submitted_date": submitted_date,
            "verified_date": verified_date
        }
        employee_documents.append(document)

# Print the data as JSON arrays
print("EMPLOYEES:")
print(json.dumps(employees, indent=2))
print("\nDOCUMENTS:")
print(json.dumps(employee_documents, indent=2))
print(f"\nGenerated {len(employees)} employees with {len(employee_documents)} documents")