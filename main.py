#!/usr/bin/env python3
"""
Local runner for the HR Documents Compliance system
"""
import os
from dotenv import load_dotenv
from src.core.controller import ComplianceController
from src.models.base import Base, engine

def main():
    """Run compliance analysis locally"""
    load_dotenv()
    
    print("=== Agentic HR Documents Compliance System ===")
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Run compliance analysis
    controller = ComplianceController()
    
    print("\nRunning batch compliance analysis (limit: 10)...")
    results = controller.run_batch(limit=10)
    
    print(f"\n=== RESULTS ===")
    print(f"Processed: {results['processed']} employees")
    print(f"Created analyses: {results['created_analyses']}")
    print(f"Created reminders: {results['created_reminders']}")
    print(f"Emails sent: {results['emails_sent']}")
    
    print("\n=== Individual Results ===")
    for result in results['results']:
        if result.get('success'):
            print(f"Employee {result['employee_id']}: Score {result['compliance_score']:.1f}%, Risk: {result['risk_level']}, Reminders: {result['reminders_sent']}")
        else:
            print(f"Employee {result['employee_id']}: FAILED - {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()