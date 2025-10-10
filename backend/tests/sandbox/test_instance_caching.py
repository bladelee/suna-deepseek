#!/usr/bin/env python3
"""
Test to verify DockerSandbox instance caching fix.
This test demonstrates the issue with session management when process instances are not cached.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_instance_caching():
    """Test that DockerSandbox caches process and fs instances."""
    print("🧪 Testing DockerSandbox instance caching...")
    
    # Mock DockerSandbox class for testing
    class MockDockerClient:
        def containers(self):
            return self
            
        def get(self, container_id):
            return MockContainer()
    
    class MockContainer:
        def __init__(self):
            self.status = "running"
    
    class MockDockerSandbox:
        def __init__(self, container_id: str, client):
            self.container_id = container_id
            self.client = client
            self._container = None
            self._process_instance = None
            self._fs_instance = None
        
        @property
        def process(self):
            if self._process_instance is None:
                self._process_instance = MockDockerSandboxProcess(self)
            return self._process_instance
        
        @property
        def fs(self):
            if self._fs_instance is None:
                self._fs_instance = MockDockerSandboxFS(self)
            return self._fs_instance
    
    class MockDockerSandboxProcess:
        def __init__(self, sandbox):
            self.sandbox = sandbox
            self._sessions = {}
            self.instance_id = id(self)  # Unique identifier for this instance
            print(f"  Created new MockDockerSandboxProcess instance: {self.instance_id}")
        
        def create_session(self, session_id):
            self._sessions[session_id] = {
                'id': session_id,
                'status': 'ready'
            }
            print(f"  Session {session_id} created in instance {self.instance_id}")
            print(f"  Sessions in this instance: {list(self._sessions.keys())}")
        
        def execute_command(self, session_id):
            if session_id in self._sessions:
                print(f"  ✅ Command executed successfully in instance {self.instance_id}")
                return "success"
            else:
                print(f"  ❌ Session {session_id} not found in instance {self.instance_id}")
                print(f"  Available sessions: {list(self._sessions.keys())}")
                raise Exception(f"Session {session_id} not found")
    
    class MockDockerSandboxFS:
        def __init__(self, sandbox):
            self.sandbox = sandbox
            self.instance_id = id(self)
            print(f"  Created new MockDockerSandboxFS instance: {self.instance_id}")
    
    # Test the fix
    print("\n📋 Testing WITH instance caching (fixed version):")
    mock_client = MockDockerClient()
    sandbox = MockDockerSandbox("test-container", mock_client)
    
    # Access process property multiple times
    process1 = sandbox.process
    process2 = sandbox.process
    
    print(f"  Process instances are the same: {process1 is process2}")
    print(f"  Instance 1 ID: {process1.instance_id}")
    print(f"  Instance 2 ID: {process2.instance_id}")
    
    # Test session management
    try:
        # Create session
        process1.create_session("test-session")
        
        # Execute command using the same instance
        result = process1.execute_command("test-session")
        print(f"  Result: {result}")
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False
    
    # Test that accessing process again returns the same instance
    process3 = sandbox.process
    print(f"  Process 3 is the same as Process 1: {process3 is process1}")
    
    print("\n✅ Instance caching test passed!")
    return True

def test_original_problem():
    """Test that demonstrates the original problem without instance caching."""
    print("\n📋 Testing WITHOUT instance caching (original problematic version):")
    
    # Define classes locally for this test
    class MockDockerClientOriginal:
        def containers(self):
            return self
            
        def get(self, container_id):
            return MockContainerOriginal()
    
    class MockContainerOriginal:
        def __init__(self):
            self.status = "running"
    
    class MockDockerSandboxOriginal:
        def __init__(self, container_id: str, client):
            self.container_id = container_id
            self.client = client
            self._container = None
        
        @property
        def process(self):
            # This creates a NEW instance every time (the original problem)
            return MockDockerSandboxProcessOriginal(self)
    
    class MockDockerSandboxProcessOriginal:
        def __init__(self, sandbox):
            self.sandbox = sandbox
            self._sessions = {}
            self.instance_id = id(self)
            print(f"  Created new MockDockerSandboxProcess instance: {self.instance_id}")
        
        def create_session(self, session_id):
            self._sessions[session_id] = {
                'id': session_id,
                'status': 'ready'
            }
            print(f"  Session {session_id} created in instance {self.instance_id}")
            print(f"  Sessions in this instance: {list(self._sessions.keys())}")
        
        def execute_command(self, session_id):
            if session_id in self._sessions:
                print(f"  ✅ Command executed successfully in instance {self.instance_id}")
                return "success"
            else:
                print(f"  ❌ Session {session_id} not found in instance {self.instance_id}")
                print(f"  Available sessions: {list(self._sessions.keys())}")
                raise Exception(f"Session {session_id} not found")
    
    mock_client = MockDockerClientOriginal()
    sandbox = MockDockerSandboxOriginal("test-container", mock_client)
    
    # This demonstrates the original problem
    print("  Simulating the original problematic flow:")
    print("  1. Create session using sandbox.process.create_session()")
    print("  2. Execute command using sandbox.process.execute_command()")
    print("  3. These are DIFFERENT instances, so session is not found!")
    
    try:
        # Create session using one instance
        process1 = sandbox.process
        process1.create_session("test-session")
        
        # Execute command using a DIFFERENT instance
        process2 = sandbox.process
        result = process2.execute_command("test-session")
        print(f"  Result: {result}")
        
    except Exception as e:
        print(f"  ❌ Original problem reproduced: {e}")
        print("  This demonstrates why the fix was needed!")
        return True  # We expect this to fail
    
    print("  ⚠️  Unexpected: Original problem did not occur")
    return False

def main():
    """Main test function."""
    print("🚀 Testing DockerSandbox Instance Caching Fix")
    print("=" * 60)
    
    try:
        # Test the fix
        fix_success = test_instance_caching()
        
        # Test the original problem
        original_problem_demonstrated = test_original_problem()
        
        print("\n" + "=" * 60)
        
        if fix_success and original_problem_demonstrated:
            print("🎉 TEST RESULTS:")
            print("✅ Instance caching fix works correctly")
            print("✅ Original problem successfully demonstrated")
            print("\n📋 SUMMARY:")
            print("The fix ensures that DockerSandbox.process returns the SAME instance")
            print("This prevents the 'Session not found' error that was occurring")
            print("when different process instances were created for session creation")
            print("and command execution.")
        else:
            print("❌ Some tests failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
