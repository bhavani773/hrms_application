#!/usr/bin/env python3
"""
Quick test runner for the HR Documents Compliance system
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def main():
    """Run the acceptance tests"""
    try:
        from src.scripts.test_system import run_all_tests
        success = run_all_tests()
        
        if success:
            print("\n🎉 System is ready! You can now run:")
            print("   uvicorn api.server:app --reload")
            print("\nOr test locally with:")
            print("   python main.py")
        else:
            print("\n❌ Some tests failed. Check the output above.")
            
        return success
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)