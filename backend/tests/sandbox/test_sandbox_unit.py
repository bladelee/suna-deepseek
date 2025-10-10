#!/usr/bin/env python3
"""
Unit tests for Docker sandbox fixes.
"""

import asyncio
import sys
import os
import unittest
from unittest.mock import Mock, AsyncMock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestDockerSandboxFixes(unittest.TestCase):
    """Test cases for Docker sandbox fixes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.container_id = "test-container-123"
        self.session_id = "supervisord-session"
        
    def test_session_verification_mechanism(self):
        """Test that session verification prevents race conditions."""
        from sandbox.docker_sandbox import DockerSandboxProcess, SessionExecuteRequest
        
        # Mock Docker client
        mock_client = Mock()
        mock_sandbox = Mock()
        mock_sandbox.container_id = self.container_id
        mock_sandbox.client = mock_client
        
        # Create process interface
        process = DockerSandboxProcess(mock_sandbox)
        
        # Mock exec_create and exec_start
        mock_exec_result = {'Id': 'exec-123'}
        mock_client.api.exec_create.return_value = mock_exec_result
        mock_client.api.exec_start.return_value = b'session_test\n'
        
        # Test session creation with verification
        async def test_session_creation():
            await process.create_session(self.session_id)
            
            # Verify session was created and marked as ready
            self.assertIn(self.session_id, process._sessions)
            session_info = process._sessions[self.session_id]
            self.assertEqual(session_info['status'], 'ready')
            
            # Verify verification command was executed
            mock_client.api.exec_create.assert_called_with(
                self.container_id,
                "echo 'session_test'",
                workdir="/workspace"
            )
            
        asyncio.run(test_session_creation())
    
    def test_session_status_check(self):
        """Test that commands are only executed on ready sessions."""
        from sandbox.docker_sandbox import DockerSandboxProcess, SessionExecuteRequest
        
        # Mock Docker client
        mock_client = Mock()
        mock_sandbox = Mock()
        mock_sandbox.container_id = self.container_id
        mock_sandbox.client = mock_client
        
        # Create process interface
        process = DockerSandboxProcess(mock_sandbox)
        
        # Add a session with 'created' status (not ready)
        process._sessions[self.session_id] = {
            'id': self.session_id,
            'status': 'created'
        }
        
        # Mock exec_create
        mock_exec_result = {'Id': 'exec-123'}
        mock_client.api.exec_create.return_value = mock_exec_result
        
        # Test that command execution fails for non-ready session
        async def test_command_execution_failure():
            request = SessionExecuteRequest("echo 'test'", var_async=False)
            
            with self.assertRaises(Exception) as context:
                await process.execute_session_command(self.session_id, request)
            
            self.assertIn("is not ready", str(context.exception))
            
        asyncio.run(test_command_execution_failure())
    
    def test_retry_mechanism(self):
        """Test the retry mechanism for supervisord startup."""
        from sandbox.sandbox import start_supervisord_session
        
        # Create a mock sandbox that fails twice then succeeds
        class MockSandbox:
            def __init__(self):
                self.fail_count = 0
                self.max_failures = 2
                
            @property
            def process(self):
                return self
                
            async def create_session(self, session_id: str):
                pass
                
            async def execute_session_command(self, session_id: str, request):
                self.fail_count += 1
                if self.fail_count <= self.max_failures:
                    raise Exception(f"Simulated failure {self.fail_count}")
                else:
                    return "Success"
        
        # Test retry mechanism
        async def test_retry():
            sandbox = MockSandbox()
            await start_supervisord_session(sandbox)
            
            # Verify that it failed twice before succeeding
            self.assertEqual(sandbox.fail_count, 3)
            
        asyncio.run(test_retry())
    
    def test_session_cleanup_on_failure(self):
        """Test that failed sessions are properly cleaned up."""
        from sandbox.docker_sandbox import DockerSandboxProcess
        
        # Mock Docker client that will fail
        mock_client = Mock()
        mock_sandbox = Mock()
        mock_sandbox.container_id = self.container_id
        mock_sandbox.client = mock_client
        
        # Create process interface
        process = DockerSandboxProcess(mock_sandbox)
        
        # Mock exec_create to fail
        mock_client.api.exec_create.side_effect = Exception("Docker API error")
        
        # Test session creation failure
        async def test_session_cleanup():
            with self.assertRaises(Exception):
                await process.create_session(self.session_id)
            
            # Verify session was cleaned up
            self.assertNotIn(self.session_id, process._sessions)
            
        asyncio.run(test_session_cleanup())
    
    def test_type_compatibility(self):
        """Test that both Docker and Daytona SessionExecuteRequest types work."""
        from sandbox.sandbox import start_supervisord_session
        
        # Test with Docker sandbox
        class DockerSandbox:
            def __init__(self):
                self.container_id = "docker-container"
                
            @property
            def process(self):
                return self
                
            async def create_session(self, session_id: str):
                pass
                
            async def execute_session_command(self, session_id: str, request):
                # Should work with Docker SessionExecuteRequest
                return "Docker success"
        
        # Test with Daytona sandbox
        class DaytonaSandbox:
            def __init__(self):
                pass
                
            @property
            def process(self):
                return self
                
            async def create_session(self, session_id: str):
                pass
                
            async def execute_session_command(self, session_id: str, request):
                # Should work with Daytona SessionExecuteRequest
                return "Daytona success"
        
        # Test both types
        async def test_type_compatibility():
            # Test Docker sandbox
            docker_sandbox = DockerSandbox()
            result = await start_supervisord_session(docker_sandbox)
            self.assertIsNone(result)  # Function returns None on success
            
            # Test Daytona sandbox
            daytona_sandbox = DaytonaSandbox()
            result = await start_supervisord_session(daytona_sandbox)
            self.assertIsNone(result)  # Function returns None on success
            
        asyncio.run(test_type_compatibility())

class TestSessionExecuteRequest(unittest.TestCase):
    """Test SessionExecuteRequest classes."""
    
    def test_docker_session_execute_request(self):
        """Test Docker SessionExecuteRequest."""
        from sandbox.docker_sandbox import SessionExecuteRequest
        
        request = SessionExecuteRequest("echo 'test'", var_async=True)
        self.assertEqual(request.command, "echo 'test'")
        self.assertTrue(request.var_async)
        
        request = SessionExecuteRequest("ls -la", var_async=False)
        self.assertEqual(request.command, "ls -la")
        self.assertFalse(request.var_async)
    
    def test_daytona_session_execute_request(self):
        """Test Daytona SessionExecuteRequest."""
        from daytona_sdk import SessionExecuteRequest
        
        request = SessionExecuteRequest("echo 'test'", var_async=True)
        self.assertEqual(request.command, "echo 'test'")
        self.assertTrue(request.var_async)

def run_tests():
    """Run all unit tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDockerSandboxFixes)
    suite.addTests(loader.loadTestsFromTestCase(TestSessionExecuteRequest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🧪 Running Docker sandbox fix unit tests...")
    
    success = run_tests()
    
    if success:
        print("\n🎉 All unit tests passed!")
        print("The Docker sandbox fixes are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some unit tests failed!")
        print("The fixes may need further investigation.")
        sys.exit(1)
