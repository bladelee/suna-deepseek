"""
Test Docker Sandbox functionality.

This module tests the local Docker sandbox implementation.
"""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

# Test configuration
os.environ['USE_LOCAL_DOCKER_SANDBOX'] = 'true'
os.environ['SANDBOX_IMAGE_NAME'] = 'kortix/suna:0.1.3.6'

from sandbox.docker_sandbox import (
    DockerSandbox, 
    DockerSandboxFS, 
    DockerSandboxProcess,
    DockerSandboxManager,
    SessionExecuteRequest
)


class TestDockerSandbox:
    """Test DockerSandbox class."""
    
    def test_init(self):
        """Test DockerSandbox initialization."""
        mock_client = Mock()
        sandbox = DockerSandbox("test-container-id", mock_client)
        
        assert sandbox.container_id == "test-container-id"
        assert sandbox.client == mock_client
        assert sandbox._container is None
    
    def test_id_property(self):
        """Test id property."""
        mock_client = Mock()
        sandbox = DockerSandbox("test-container-id", mock_client)
        
        assert sandbox.id == "test-container-id"
    
    @patch('docker.Container')
    def test_container_property(self, mock_container_class):
        """Test container property."""
        mock_client = Mock()
        mock_container = Mock()
        mock_client.containers.get.return_value = mock_container
        
        sandbox = DockerSandbox("test-container-id", mock_client)
        container = sandbox.container
        
        assert container == mock_container
        mock_client.containers.get.assert_called_once_with("test-container-id")
        
        # Test caching
        container2 = sandbox.container
        assert container2 == mock_container
        # Should not call get again
        assert mock_client.containers.get.call_count == 1


class TestDockerSandboxFS:
    """Test DockerSandboxFS class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sandbox = Mock()
        self.mock_sandbox.container_id = "test-container-id"
        self.mock_sandbox.client = Mock()
        self.fs = DockerSandboxFS(self.mock_sandbox)
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.makedirs')
    @patch('os.unlink')
    def test_upload_file_success(self, mock_unlink, mock_makedirs, mock_temp_file):
        """Test successful file upload."""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_file"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # Mock Docker API response
        self.mock_sandbox.client.api.put_archive.return_value = True
        
        # Test upload
        content = b"test content"
        path = "/test/path/file.txt"
        
        asyncio.run(self.fs.upload_file(content, path))
        
        # Verify calls
        mock_temp.write.assert_called_once_with(content)
        mock_temp.flush.assert_called_once()
        mock_makedirs.assert_called_once()
        self.mock_sandbox.client.api.put_archive.assert_called_once()
        mock_unlink.assert_called_once_with("/tmp/test_file")
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.makedirs')
    @patch('os.unlink')
    def test_upload_file_failure(self, mock_unlink, mock_makedirs, mock_temp_file):
        """Test file upload failure."""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_file"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # Mock Docker API failure
        self.mock_sandbox.client.api.put_archive.return_value = False
        
        # Test upload failure
        content = b"test content"
        path = "/test/path/file.txt"
        
        with pytest.raises(Exception, match="Failed to copy file to container"):
            asyncio.run(self.fs.upload_file(content, path))
        
        # Verify cleanup
        mock_unlink.assert_called_once_with("/tmp/test_file")


class TestDockerSandboxProcess:
    """Test DockerSandboxProcess class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sandbox = Mock()
        self.mock_sandbox.container_id = "test-container-id"
        self.mock_sandbox.client = Mock()
        self.process = DockerSandboxProcess(self.mock_sandbox)
    
    def test_create_session(self):
        """Test session creation."""
        session_id = "test-session"
        
        self.process.create_session(session_id)
        
        assert session_id in self.process._sessions
        assert self.process._sessions[session_id] == session_id
    
    def test_execute_session_command_session_not_found(self):
        """Test executing command with non-existent session."""
        request = SessionExecuteRequest("echo 'test'")
        
        with pytest.raises(Exception, match="Session test-session not found"):
            asyncio.run(self.process.execute_session_command("test-session", request))
    
    def test_execute_session_command_success(self):
        """Test successful command execution."""
        session_id = "test-session"
        self.process.create_session(session_id)
        
        # Mock Docker exec API
        mock_exec_result = {"Id": "exec-123"}
        self.mock_sandbox.client.api.exec_create.return_value = mock_exec_result
        
        mock_output = b"test output"
        self.mock_sandbox.client.api.exec_start.return_value = mock_output
        
        request = SessionExecuteRequest("echo 'test'")
        
        result = asyncio.run(self.process.execute_session_command(session_id, request))
        
        assert result == "test output"
        self.mock_sandbox.client.api.exec_create.assert_called_once()
        self.mock_sandbox.client.api.exec_start.assert_called_once_with("exec-123")


class TestDockerSandboxManager:
    """Test DockerSandboxManager class."""
    
    @patch('docker.from_env')
    def test_init_success(self, mock_from_env):
        """Test successful manager initialization."""
        mock_client = Mock()
        mock_from_env.return_value = mock_client
        
        manager = DockerSandboxManager()
        
        assert manager.client == mock_client
        mock_from_env.assert_called_once()
    
    @patch('docker.from_env')
    def test_init_failure(self, mock_from_env):
        """Test manager initialization failure."""
        mock_from_env.side_effect = Exception("Docker not available")
        
        with pytest.raises(Exception, match="Docker not available"):
            DockerSandboxManager()
    
    @patch('docker.Container')
    def test_get_sandbox_success(self, mock_container_class):
        """Test successful sandbox retrieval."""
        mock_client = Mock()
        mock_container = Mock()
        mock_client.containers.get.return_value = mock_container
        
        manager = DockerSandboxManager()
        manager.client = mock_client
        
        sandbox = asyncio.run(manager.get_sandbox("test-id"))
        
        assert isinstance(sandbox, DockerSandbox)
        assert sandbox.container_id == "test-id"
        mock_client.containers.get.assert_called_once_with("test-id")
    
    @patch('docker.Container')
    def test_get_sandbox_not_found(self, mock_container_class):
        """Test sandbox retrieval when not found."""
        from docker.errors import NotFound
        
        mock_client = Mock()
        mock_client.containers.get.side_effect = NotFound("Container not found")
        
        manager = DockerSandboxManager()
        manager.client = mock_client
        
        with pytest.raises(Exception, match="Sandbox test-id not found"):
            asyncio.run(manager.get_sandbox("test-id"))


class TestSessionExecuteRequest:
    """Test SessionExecuteRequest class."""
    
    def test_init(self):
        """Test SessionExecuteRequest initialization."""
        request = SessionExecuteRequest("echo 'test'", var_async=True)
        
        assert request.command == "echo 'test'"
        assert request.var_async is True
    
    def test_init_defaults(self):
        """Test SessionExecuteRequest default values."""
        request = SessionExecuteRequest("echo 'test'")
        
        assert request.command == "echo 'test'"
        assert request.var_async is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
