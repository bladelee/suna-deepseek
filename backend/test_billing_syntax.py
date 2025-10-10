#!/usr/bin/env python3
"""
Minimal test script to verify the syntax of billing.py after fixing indentation issues.
This script will check if the file can be parsed without syntax errors.
"""
import sys
import os

# Path to the billing.py file
BILLING_FILE_PATH = '/home/debian/suna-deepseek/backend/services/billing.py'

print("Starting syntax check for billing.py...")
print("=====================================")

try:
    # Check if the file exists
    if not os.path.exists(BILLING_FILE_PATH):
        print(f"❌ Error: Could not find billing.py at {BILLING_FILE_PATH}")
        sys.exit(1)
    
    # Read the file content
    with open(BILLING_FILE_PATH, 'r') as f:
        file_content = f.read()
    
    # Try to parse the file content using Python's ast module
    # This will catch any syntax errors without actually executing the code
    import ast
    ast.parse(file_content)
    
    print("✅ Syntax check passed!")
    print(f"The file {BILLING_FILE_PATH} has no syntax errors.")
    print("This confirms that the indentation issues in get_user_credit_balance have been fixed.")
    
except SyntaxError as e:
    print(f"❌ Syntax error found in billing.py:")
    print(f"  Line: {e.lineno}")
    # Handle different error attribute names
    col_offset = getattr(e, 'col_offset', getattr(e, 'offset', 'N/A'))
    print(f"  Column: {col_offset}")
    print(f"  Error message: {e.msg}")
    if hasattr(e, 'text') and e.text:
        print(f"  Problematic code: {e.text.strip()}")
    print("The file still has syntax issues that need to be fixed.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error during syntax check: {str(e)}")
    sys.exit(1)

print("\nVerification complete!")
print("=====================================")