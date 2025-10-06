#!/usr/bin/env python3
"""
Simplified test script to verify the billing.py fixes, specifically the indentation issues
in the get_user_credit_balance function.
"""
import asyncio
import sys
from typing import Optional, Dict, Any

# Add the project root to the Python path
sys.path.append('/home/debian/suna-deepseek/backend')

# Mock the Supabase client to avoid actual database calls
class MockSupabaseClient:
    def __init__(self, mock_data: Optional[Dict[str, Any]] = None):
        self.mock_data = mock_data or {}
        
    async def table(self, table_name: str):
        return MockTable(self, table_name)

class MockTable:
    def __init__(self, client: MockSupabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self._filters = {}
        
    def select(self, columns: str):
        self._columns = columns
        return self
        
    def eq(self, column: str, value: Any):
        self._filters[column] = value
        return self
        
    async def execute(self):
        # Mock response based on table name and filters
        if self.table_name == 'credit_balance' and 'user_id' in self._filters:
            user_id = self._filters['user_id']
            # Return mock data if available, otherwise empty result
            if user_id in self.client.mock_data.get('credit_balance', {}):
                return MockResult({
                    'data': [self.client.mock_data['credit_balance'][user_id]]
                })
            else:
                return MockResult({'data': []})
        return MockResult({'data': []})

class MockResult:
    def __init__(self, data: Dict[str, Any]):
        self.data = data.get('data', [])

# Mock the logger to capture log messages
class MockLogger:
    def __init__(self):
        self.logs = {
            'debug': [],
            'info': [], 
            'warning': [],
            'error': [],
            'exception': []
        }
    
    def debug(self, msg: str):
        self.logs['debug'].append(msg)
        print(f"DEBUG: {msg}")
    
    def info(self, msg: str):
        self.logs['info'].append(msg)
        print(f"INFO: {msg}")
    
    def warning(self, msg: str):
        self.logs['warning'].append(msg)
        print(f"WARNING: {msg}")
    
    def error(self, msg: str):
        self.logs['error'].append(msg)
        print(f"ERROR: {msg}")
    
    def exception(self, msg: str):
        self.logs['exception'].append(msg)
        print(f"EXCEPTION: {msg}")

# Monkey patch the logger and other imports
import utils.logger
utils.logger.logger = MockLogger()

# Simple test to verify the import works
print("Starting billing.py fix verification test...")
print("=====================================")

successfully_imported = False
try:
    # Try to import the function - this will fail if there are syntax errors
    from services.billing import get_user_credit_balance
    successfully_imported = True
    print("✓ Successfully imported get_user_credit_balance function")
    
    # Define a simple mock for the client
    class SimpleMockClient:
        async def table(self, table_name):
            return self
            
        def select(self, columns):
            return self
            
        def eq(self, column, value):
            return self
            
        async def execute(self):
            # Return empty data to test the default path
            return type('obj', (object,), {'data': []})
    
    # Create a coroutine to test the function
    async def test_function():
        try:
            # This will test the error handling and default path in get_user_credit_balance
            mock_client = SimpleMockClient()
            result = await get_user_credit_balance(mock_client, 'test_user')
            print("✓ Successfully called get_user_credit_balance function")
            print(f"Result type: {type(result)}")
            print("\n✅ All tests passed!")
            print("This confirms that the indentation issues in get_user_credit_balance have been fixed.")
        except Exception as e:
            print(f"❌ Function call failed with error: {str(e)}")
            print("There might still be issues with the billing.py code.")
    
    # Run the coroutine
    asyncio.run(test_function())
    
except Exception as e:
    print(f"✗ Failed to import billing functions: {str(e)}")
    print("This indicates there might still be syntax errors in the code.")

print("\nVerification complete!")
print("=====================================")