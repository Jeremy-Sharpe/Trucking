"""
Simple test script to diagnose basic issues.
"""

print("Starting basic test")

try:
    # Test basic imports
    print("Testing imports...")
    import os
    import imaplib
    import json
    from datetime import datetime, timedelta
    print("Basic imports successful")
    
    # Test email module import
    print("Testing email module import...")
    import email
    print("Email module import successful")
    
    # Test config import
    print("Testing config import...")
    from config import EMAIL_USERNAME
    print(f"Email username from config: {EMAIL_USERNAME}")
    
    print("All tests passed!")
except Exception as e:
    print(f"Error during test: {e}")
    import traceback
    traceback.print_exc() 