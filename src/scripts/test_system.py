#!/usr/bin/env python3
"""
Acceptance tests for the HR Documents Compliance system
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.models.base import Base, engine, SessionLocal
from src.models.employees import Employee
from src.core.controller import ComplianceController
from src.core.blackboard import Blackboard
from src.tools.email_utils import send_email

def test_data_loading():
    """Test that dummy data is loaded correctly"""
    print("Testing data loading...")
    
    db = SessionLocal()
    try:
        employee_count = db.query(Employee).count()
        print(f"✓ Found {employee_count} employees in database")
        assert employee_count >= 10, f"Expected at least 10 employees, found {employee_count}"
        return True
    except Exception as e:
        print(f"✗ Data loading test failed: {e}")
        return False
    finally:
        db.close()

def test_compliance_analysis():
    """Test compliance analysis workflow"""
    print("Testing compliance analysis...")
    
    try:
        controller = ComplianceController()
        
        # Get first employee
        with Blackboard() as bb:
            employee_ids = bb.get_all_employees(limit=1)
            if not employee_ids:
                print("✗ No employees found for testing")
                return False
            
            employee_id = employee_ids[0]
        
        # Run analysis
        result = controller.run_for_employee(employee_id)
        
        print(f"✓ Analysis completed for employee {employee_id}")
        print(f"  Success: {result.get('success')}")
        print(f"  Compliance Score: {result.get('compliance_score')}")
        print(f"  Risk Level: {result.get('risk_level')}")
        print(f"  Reminders Sent: {result.get('reminders_sent')}")
        
        assert result.get('success'), "Analysis should succeed"
        return True
        
    except Exception as e:
        print(f"✗ Compliance analysis test failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing"""
    print("Testing batch processing...")
    
    try:
        controller = ComplianceController()
        results = controller.run_batch(limit=5)
        
        print(f"✓ Batch processing completed")
        print(f"  Processed: {results['processed']}")
        print(f"  Created Analyses: {results['created_analyses']}")
        print(f"  Created Reminders: {results['created_reminders']}")
        print(f"  Emails Sent: {results['emails_sent']}")
        
        assert results['processed'] > 0, "Should process at least one employee"
        return True
        
    except Exception as e:
        print(f"✗ Batch processing test failed: {e}")
        return False

def test_dashboard_metrics():
    """Test dashboard metrics"""
    print("Testing dashboard metrics...")
    
    try:
        with Blackboard() as bb:
            metrics = bb.get_dashboard_metrics()
        
        print(f"✓ Dashboard metrics retrieved")
        print(f"  Total Employees: {metrics['total_employees']}")
        print(f"  Completion Rate: {metrics['completion_rates']['overall']:.1f}%")
        print(f"  Overdue Documents: {metrics['overdue_statistics']['overdue_documents']}")
        
        assert metrics['total_employees'] > 0, "Should have employees"
        return True
        
    except Exception as e:
        print(f"✗ Dashboard metrics test failed: {e}")
        return False

def test_email_functionality():
    """Test email sending"""
    print("Testing email functionality...")
    
    try:
        status_code = send_email(
            to_email="test@example.com",
            subject="Test Email",
            body="This is a test email from the compliance system."
        )
        
        print(f"✓ Email test completed with status code: {status_code}")
        assert status_code in [200, 202], f"Expected success status code, got {status_code}"
        return True
        
    except Exception as e:
        print(f"✗ Email functionality test failed: {e}")
        return False

def run_all_tests():
    """Run all acceptance tests"""
    print("=== HR Documents Compliance System - Acceptance Tests ===\n")
    
    # Load environment
    load_dotenv()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Load dummy data
    from src.api.v1.server import load_dummy_data
    load_dummy_data()
    
    tests = [
        test_data_loading,
        test_compliance_analysis,
        test_batch_processing,
        test_dashboard_metrics,
        test_email_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}\n")
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All acceptance tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)