"""
Docker Sandbox Manager for local deployment.

This module provides Docker-based sandbox management as an alternative to Daytona
for local development and deployment scenarios.
"""

import asyncio
import json
import os
import tempfile
import time
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import docker
from docker.errors import DockerException, NotFound, APIError
from utils.logger import logger
from utils.config import config


class DockerSandbox:
    """Docker-based sandbox implementation for local deployment."""
    
    def __init__(self, container_id: str, client: docker.DockerClient):
        self.container_id = container_id
        self.client = client
        self._container = None
        self._process_instance = None  # Cache the process instance
        self._fs_instance = None       # Cache the fs instance
        
    @property
    def container(self):
        """Get the Docker container object."""
        if self._container is None:
            self._container = self.client.containers.get(self.container_id)
        return self._container
    
    @property
    def id(self) -> str:
        """Get the sandbox ID (container ID)."""
        return self.container_id
    
    @property
    def state(self) -> str:
        """Get the container state."""
        try:
            container = self.container
            return container.status
        except Exception as e:
            logger.error(f"Error getting container state: {e}")
            return "unknown"
    
    async def start(self):
        """Start the Docker container."""
        try:
            if self.state != "running":
                self.container.start()
                logger.debug(f"Started Docker container {self.container_id}")
            return self
        except Exception as e:
            logger.error(f"Error starting Docker container {self.container_id}: {e}")
            raise
    
    async def stop(self):
        """Stop the Docker container."""
        try:
            if self.state == "running":
                self.container.stop(timeout=30)
                logger.debug(f"Stopped Docker container {self.container_id}")
        except Exception as e:
            logger.error(f"Error stopping Docker container {self.container_id}: {e}")
            raise
    
    async def delete(self):
        """Delete the Docker container."""
        try:
            if self.state == "running":
                await self.stop()
            self.container.remove(force=True)
            logger.debug(f"Deleted Docker container {self.container_id}")
        except Exception as e:
            logger.error(f"Error deleting Docker container {self.container_id}: {e}")
            raise
    
    @property
    def fs(self):
        """Get the filesystem interface."""
        if self._fs_instance is None:
            self._fs_instance = DockerSandboxFS(self)
        return self._fs_instance
    
    
    async def get_preview_link(self, port: int):
        """Get a preview link for the specified port using integrated daemon-proxy.
        
        For Docker sandboxes, this uses the integrated daemon-proxy API to create a real preview link
        that can be used to access services running in the container.
        """
        try:
            # Use the integrated daemon-proxy API
            preview_link = await self._get_preview_link_via_api(port)
            
            if preview_link:
                logger.info(f"Created daemon-proxy preview link for port {port}: {preview_link.url}")
                return preview_link
            else:
                logger.warning(f"Failed to create daemon-proxy preview link for port {port}, falling back to mock preview link")
                return self._create_mock_preview_link(port)
                
        except Exception as e:
            logger.error(f"Error creating daemon-proxy preview link for port {port}: {e}")
            logger.info(f"Falling back to mock preview link for port {port}")
            return self._create_mock_preview_link(port)
    
    async def _get_preview_link_via_api(self, port: int):
        """Get preview link via the integrated daemon-proxy API"""
        try:
            import aiohttp
            from utils.config import config
            
            # Get backend URL from config
            backend_url = getattr(config, 'BACKEND_URL', 'http://localhost:8001/api')
            
            async with aiohttp.ClientSession() as session:
                # First, ensure daemon is injected into this container
                inject_url = f"{backend_url}/daemon-proxy/container/{self.container_id}/inject"
                async with session.post(inject_url) as response:
                    if response.status not in [200, 409]:  # 409 = already injected
                        logger.warning(f"Failed to inject daemon into container {self.container_id}")
                        return None
                
                # Create preview link
                preview_url = f"{backend_url}/daemon-proxy/container/{self.container_id}/preview/{port}"
                async with session.post(preview_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Create a preview link object
                        class PreviewLink:
                            def __init__(self, data):
                                self.url = data['url']
                                self.token = data['token']
                                self.port = data['port']
                                self.expires_at = data['expires_at']
                        
                        return PreviewLink(data)
                    else:
                        logger.warning(f"Failed to create preview link: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling daemon-proxy API: {e}")
            return None
    
    def _create_mock_preview_link(self, port: int):
        """Create a mock preview link as fallback."""
        class MockPreviewLink:
            def __init__(self, port: int):
                self.port = port
                self.url = f"http://localhost:{port}"
                self.token = None
                self.expires_at = None
            
            def __str__(self):
                return f"MockPreviewLink(url='{self.url}', token='{self.token}')"
        
        return MockPreviewLink(port)
    
    
    async def inject_daytona_daemon(self, binary_source_path: str = None, injection_method: str = None) -> bool:
        """Inject and start daytona daemon in this container using existing daemon-proxy functionality."""
        try:
            from backend.extensions.daemon_proxy.daemon_proxy import DaemonManager, Config
            
            # Use provided binary path or default
            binary_path = binary_source_path or os.getenv('DAEMON_BINARY_PATH', '/app/daemon-proxy/daytona-daemon-static')
            
            # Use provided injection method or default from environment
            method = injection_method or os.getenv('DAEMON_INJECTION_METHOD', 'copy')
            
            # Create daemon manager with Docker injection mode
            daemon_config = Config()
            daemon_config.set("daemon.mode", "docker")
            daemon_config.set("daemon.port", 2080)
            daemon_config.set("daemon.container_name", self.container_id)
            daemon_config.set("daemon.injection_mode", "volume")
            daemon_config.set("daemon.injection_method", method)  # 使用配置的注入方式
            daemon_config.set("daemon.binary_source_path", binary_path)
            daemon_config.set("daemon.startup_timeout", 30)
            
            daemon_manager = DaemonManager(daemon_config)
            await daemon_manager.start()
            
            logger.info(f"Successfully injected daytona daemon into container {self.container_id} using {method} method")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting daytona daemon: {e}")
            return False
    
    async def stop_daytona_daemon(self) -> bool:
        """Stop daytona daemon in this container."""
        try:
            container = self.container
            # Use pkill to stop daytona daemon processes
            result = container.exec_run(['sh', '-c', 'pkill -f "daytona"'])
            
            if result.exit_code == 0:
                logger.info(f"Successfully stopped daytona daemon in container {self.container_id}")
                return True
            else:
                logger.warning(f"Failed to stop daytona daemon: {result.output.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping daytona daemon: {e}")
            return False
    
    async def is_daytona_daemon_running(self) -> bool:
        """Check if daytona daemon is running in this container."""
        try:
            container = self.container
            result = container.exec_run(['sh', '-c', 'pgrep -f "daytona"'])
            return result.exit_code == 0
        except Exception as e:
            logger.error(f"Error checking daytona daemon status: {e}")
            return False
    
    @property
    def process(self):
        """Get the process interface."""
        if self._process_instance is None:
            self._process_instance = DockerSandboxProcess(self)
        return self._process_instance


class DockerSandboxFS:
    """Filesystem interface for Docker sandbox."""
    
    def __init__(self, sandbox: DockerSandbox):
        self.sandbox = sandbox
    
    async def upload_file(self, content: bytes, path: str):
        """Upload a file to the sandbox."""
        try:
            logger.info(f"Starting file upload: {path}, content size: {len(content)} bytes")
            
            # Normalize the path and ensure it's relative to /workspace
            original_path = path
            if path.startswith('/'):
                path = path.lstrip('/')
            
            logger.info(f"Normalized path: '{original_path}' -> '{path}'")
            
            # Create a tar archive containing the file with proper structure
            import tarfile
            import io
            
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w:tar') as tar:
                # Add the file to the tar archive with full relative path
                tarinfo = tarfile.TarInfo(name=path)
                tarinfo.size = len(content)
                tar.addfile(tarinfo, io.BytesIO(content))
                logger.info(f"Added file to tar: name='{path}', size={len(content)}")
            
            tar_buffer.seek(0)
            tar_size = len(tar_buffer.getvalue())
            logger.info(f"Tar archive created: size={tar_size} bytes")
            
            # Determine the target directory in the container
            container_dir = "/workspace"
            logger.info(f"Target container directory: {container_dir}")
            
            # Ensure the target directory exists in the container
            try:
                if '/' in path:
                    dir_path = os.path.dirname(path)
                    if dir_path:
                        logger.info(f"Creating directory: /workspace/{dir_path}")
                        exec_result = self.sandbox.client.api.exec_create(
                            self.sandbox.container_id,
                            f"mkdir -p /workspace/{dir_path}"
                        )
                        self.sandbox.client.api.exec_start(exec_result['Id'])
                        logger.info(f"Successfully created directory /workspace/{dir_path}")
            except Exception as e:
                logger.warning(f"Could not create directory /workspace/{dir_path}: {e}")
            
            # Use put_archive with the tar buffer
            logger.info(f"Uploading tar archive to container {self.sandbox.container_id}")
            result = self.sandbox.client.api.put_archive(
                self.sandbox.container_id,
                container_dir,
                tar_buffer.getvalue()
            )
            
            if not result:
                raise Exception("Failed to copy file to container")
            
            logger.info(f"Successfully uploaded file to {path} in container {self.sandbox.container_id}")
            
            # Verify file was created by listing container contents
            try:
                exec_result = self.sandbox.client.api.exec_create(
                    self.sandbox.container_id,
                    f"ls -la /workspace/{path}"
                )
                ls_output = self.sandbox.client.api.exec_start(exec_result['Id'])
                logger.info(f"File verification - ls output: {ls_output.decode('utf-8') if ls_output else 'No output'}")
            except Exception as e:
                logger.warning(f"Could not verify file creation: {e}")
            
        except Exception as e:
            logger.error(f"Error uploading file {path}: {e}")
            raise
        finally:
            # Clean up tar buffer
            if 'tar_buffer' in locals():
                try:
                    tar_buffer.close()
                except Exception:
                    pass  # Ignore cleanup errors
    
    async def download_file(self, path: str) -> bytes:
        """Download a file from the sandbox."""
        try:
            container_path = os.path.join("/workspace", path.lstrip("/"))
            
            # Use docker cp to copy file from container
            archive, stat = self.sandbox.client.api.get_archive(
                self.sandbox.container_id,
                container_path
            )
            
            if not archive:
                raise Exception(f"File not found: {path}")
            
            # Read the tar archive and extract the file content
            import tarfile
            import io
            
            # Convert generator to bytes
            archive_data = b''.join(archive)
            tar_data = io.BytesIO(archive_data)
            
            with tarfile.open(fileobj=tar_data, mode='r:tar') as tar:
                # Get the first file in the archive
                member = tar.getmembers()[0]
                content = tar.extractfile(member).read()
                
            logger.debug(f"Downloaded file {path} from container {self.sandbox.container_id}")
            return content
            
        except Exception as e:
            logger.error(f"Error downloading file {path}: {e}")
            raise
    
    async def list_files(self, path: str) -> List['DockerFileInfo']:
        """List files in the sandbox directory."""
        try:
            container_path = os.path.join("/workspace", path.lstrip("/"))
            
            # Execute ls command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                f"ls -la {container_path}",
                workdir="/workspace"
            )
            
            output = self.sandbox.client.api.exec_start(exec_result['Id'])
            lines = output.decode('utf-8').strip().split('\n')
            
            files = []
            for line in lines[1:]:  # Skip total line
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        permissions = parts[0]
                        size = int(parts[4]) if parts[4].isdigit() else 0
                        name = parts[-1]
                        is_dir = permissions.startswith('d')
                        
                        files.append(DockerFileInfo(
                            name=name,
                            path=os.path.join(path, name).replace('\\', '/'),
                            is_dir=is_dir,
                            size=size,
                            mod_time=time.time(),
                            permissions=permissions
                        ))
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {path}: {e}")
            raise
    
    async def delete_file(self, path: str):
        """Delete a file from the sandbox."""
        try:
            container_path = os.path.join("/workspace", path.lstrip("/"))
            
            # Execute rm command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                f"rm -rf {container_path}"
            )
            
            output = self.sandbox.client.api.exec_start(exec_result['Id'])
            if output:
                logger.debug(f"Deleted file {path} from container {self.sandbox.container_id}")
                
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            raise

    async def create_folder(self, path: str, permissions: str = "755"):
        """Create a folder in the sandbox."""
        try:
            container_path = os.path.join("/workspace", path.lstrip("/"))
            
            # Execute mkdir command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                f"mkdir -p {container_path}"
            )
            
            output = self.sandbox.client.api.exec_start(exec_result['Id'])
            if output is not None:
                logger.debug(f"Created folder {path} in container {self.sandbox.container_id}")
            else:
                logger.debug(f"Folder {path} created or already exists in container {self.sandbox.container_id}")
            
            # Set permissions if specified
            if permissions and permissions != "755":
                try:
                    chmod_result = self.sandbox.client.api.exec_create(
                        self.sandbox.container_id,
                        f"chmod {permissions} {container_path}"
                    )
                    self.sandbox.client.api.exec_start(chmod_result['Id'])
                    logger.debug(f"Set permissions {permissions} on folder {path}")
                except Exception as e:
                    logger.warning(f"Could not set permissions {permissions} on folder {path}: {e}")
                
        except Exception as e:
            logger.error(f"Error creating folder {path}: {e}")
            raise

    async def set_file_permissions(self, path: str, permissions: str):
        """Set file permissions in the sandbox."""
        try:
            container_path = os.path.join("/workspace", path.lstrip("/"))
            
            # Execute chmod command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                f"chmod {permissions} {container_path}"
            )
            
            output = self.sandbox.client.api.exec_start(exec_result['Id'])
            if output is not None:
                logger.debug(f"Set permissions {permissions} on {path} in container {self.sandbox.container_id}")
            else:
                logger.debug(f"Permissions {permissions} set on {path} in container {self.sandbox.container_id}")
                
        except Exception as e:
            logger.error(f"Error setting permissions {permissions} on {path}: {e}")
            raise

    async def get_file_info(self, path: str) -> 'DockerFileInfo':
        """Get file information."""
        try:
            container_path = os.path.join("/workspace", path.lstrip("/"))
            
            # Execute stat command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                f"stat -c '%n|%s|%Y|%a' {container_path}"
            )
            
            # Execute the command and get the result
            output = self.sandbox.client.api.exec_start(exec_result['Id'])
            
            # Check if the command executed successfully by getting the exit code
            exit_code = self.sandbox.client.api.exec_inspect(exec_result['Id'])['ExitCode']
            
            if exit_code != 0:
                # File does not exist or stat command failed
                raise FileNotFoundError(f"File {path} does not exist (exit code: {exit_code})")
            
            if output:
                output_str = output.decode('utf-8').strip()
                if output_str and '|' in output_str:
                    parts = output_str.split('|')
                    if len(parts) == 4:
                        name, size_str, mtime_str, perms_str = parts
                        
                        try:
                            size = int(size_str)
                            mtime = float(mtime_str)
                            permissions = perms_str
                            
                            # Check if it's a directory
                            is_dir_result = self.sandbox.client.api.exec_create(
                                self.sandbox.container_id,
                                f"test -d {container_path} && echo 'dir' || echo 'file'"
                            )
                            is_dir_output = self.sandbox.client.api.exec_start(is_dir_result['Id'])
                            is_dir = is_dir_output.decode('utf-8').strip() == 'dir'
                            
                            return DockerFileInfo(
                                name=os.path.basename(path),
                                path=path,
                                is_dir=is_dir,
                                size=size,
                                mod_time=mtime,
                                permissions=permissions
                            )
                        except (ValueError, IndexError):
                            pass
            
            # If we reach here, the stat command succeeded but output parsing failed
            raise ValueError(f"Failed to parse stat output for {path}: {output}")
                
        except FileNotFoundError:
            # Re-raise FileNotFoundError as-is
            raise
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            raise


class DockerSandboxProcess:
    """Process interface for Docker sandbox."""
    
    def __init__(self, sandbox: DockerSandbox):
        self.sandbox = sandbox
        self._sessions: Dict[str, str] = {}
    
    async def create_session(self, session_id: str):
        """Create a new session."""
        try:
            # For Docker, we'll use the session_id as a key for tracking
            self._sessions[session_id] = {
                'id': session_id,
                'created_at': time.time(),
                'status': 'created'
            }
            logger.debug(f"Created session {session_id} in container {self.sandbox.container_id}")
            
            # Verify session was created successfully
            await asyncio.sleep(0.1)  # Small delay to ensure session is ready
            
            # Test session by trying to execute a simple command
            try:
                test_result = self.sandbox.client.api.exec_create(
                    self.sandbox.container_id,
                    "echo 'session_test'",
                    workdir="/workspace"
                )
                self.sandbox.client.api.exec_start(test_result['Id'])
                self._sessions[session_id]['status'] = 'ready'
                logger.debug(f"Session {session_id} verified and ready")
            except Exception as e:
                logger.warning(f"Session {session_id} verification failed: {e}")
                # Remove failed session
                if session_id in self._sessions:
                    del self._sessions[session_id]
                raise Exception(f"Session {session_id} creation failed: {e}")
                
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            raise
    
    async def execute_session_command(self, session_id: str, request: 'SessionExecuteRequest', timeout: int = None) -> 'CommandResponse':
        """Execute a command in a session."""
        try:
            if session_id not in self._sessions:
                raise Exception(f"Session {session_id} not found")
            
            session_info = self._sessions[session_id]
            if session_info.get('status') != 'ready':
                raise Exception(f"Session {session_id} is not ready (status: {session_info.get('status')})")
            
            # Execute command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                request.command,
                workdir="/workspace"
            )
            
            if request.var_async:
                # Start command asynchronously
                self.sandbox.client.api.exec_start(exec_result['Id'], detach=True)
                logger.debug(f"Started async command in session {session_id}")
                return CommandResponse(exec_result['Id'], 0, "") # Return a placeholder for async
            else:
                # Execute command synchronously
                output = self.sandbox.client.api.exec_start(exec_result['Id'])
                output_text = output.decode('utf-8') if output else ""
                logger.debug(f"Executed command in session {session_id}")
                
                # Store the command output for later retrieval
                if 'command_outputs' not in session_info:
                    session_info['command_outputs'] = {}
                session_info['command_outputs'][exec_result['Id']] = output_text
                
                return CommandResponse(exec_result['Id'], 0, output_text)
                
        except Exception as e:
            logger.error(f"Error executing command in session {session_id}: {e}")
            raise

    async def exec(self, command: str, timeout: int = None) -> str:
        """Execute a command directly in the container."""
        try:
            # Execute command in container
            exec_result = self.sandbox.client.api.exec_create(
                self.sandbox.container_id,
                command,
                workdir="/workspace"
            )
            
            # Execute command with timeout handling
            if timeout:
                # For timeout support, we need to handle it manually
                import asyncio
                try:
                    output = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: self.sandbox.client.api.exec_start(exec_result['Id'])
                        ),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    # Kill the process if it times out
                    try:
                        self.sandbox.client.api.exec_kill(exec_result['Id'])
                    except Exception:
                        pass
                    raise Exception(f"Command execution timed out after {timeout} seconds")
            else:
                output = self.sandbox.client.api.exec_start(exec_result['Id'])
            
            if output:
                return output.decode('utf-8')
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            raise

    async def delete_session(self, session: dict):
        """Delete a session."""
        try:
            session_id = session.get('id')
            if session_id and session_id in self._sessions:
                # Remove session from tracking
                del self._sessions[session_id]
                logger.debug(f"Deleted session {session_id} from container {self.sandbox.container_id}")
            else:
                logger.warning(f"Session {session_id} not found for deletion")
                
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            raise

    async def get_session_command_logs(self, session_id: str, command_id: str) -> str:
        """Get session command logs."""
        try:
            if session_id not in self._sessions:
                raise Exception(f"Session {session_id} not found")
            
            session_info = self._sessions[session_id]
            if session_info.get('status') != 'ready':
                raise Exception(f"Session {session_id} is not ready (status: {session_info.get('status')})")
            
            # Since we're executing commands synchronously, the output is already in the CommandResponse
            # We need to store the command output when executing commands
            if 'command_outputs' not in session_info:
                session_info['command_outputs'] = {}
            
            # Return the stored output for this command, or a default message if not found
            if command_id in session_info['command_outputs']:
                return session_info['command_outputs'][command_id]
            else:
                return f"Command {command_id} executed in session {session_id} (output not available)"
                
        except Exception as e:
            logger.error(f"Error getting logs for command {command_id} in session {session_id}: {e}")
            raise


class DockerFileInfo:
    """File information for Docker sandbox."""
    
    def __init__(self, name: str, path: str, is_dir: bool, size: int, mod_time: float, permissions: str = None):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.mod_time = mod_time
        self.permissions = permissions


class SessionExecuteRequest:
    """Request for executing a command in a session."""
    
    def __init__(self, command: str, var_async: bool = False):
        self.command = command
        self.var_async = var_async


class CommandResponse:
    """Response from executing a command in a session."""
    
    def __init__(self, cmd_id: str, exit_code: int = 0, output: str = ""):
        self.cmd_id = cmd_id
        self.exit_code = exit_code
        self.output = output


class DockerSandboxManager:
    """Manager for Docker-based sandboxes."""
    
    def __init__(self):
        self.client = None
        self._initialized = False
        try:
            # Try to get Docker configuration from environment
            docker_host = os.getenv('DOCKER_HOST')
            docker_cert_path = os.getenv('DOCKER_CERT_PATH')
            docker_tls_verify = os.getenv('DOCKER_TLS_VERIFY', 'false').lower() == 'true'
            
            # Auto-detect WSL2 environment
            if not docker_host:
                if self._is_wsl2_environment():
                    # WSL2 with Docker Desktop - try TCP first, fallback to Unix socket
                    try:
                        # Test TCP connection
                        test_client = docker.DockerClient(base_url='tcp://localhost:2375')
                        test_client.ping()
                        test_client.close()
                        docker_host = 'tcp://localhost:2375'
                        logger.info("Detected WSL2 environment, using Docker Desktop TCP connection")
                    except Exception:
                        # Fallback to Unix socket
                        docker_host = 'unix:///var/run/docker.sock'
                        logger.info("Detected WSL2 environment, TCP connection failed, using Unix socket")
                else:
                    # Standard Linux environment
                    docker_host = 'unix:///var/run/docker.sock'
            
            logger.debug(f"Initializing Docker client with host: {docker_host}")
            
            if docker_host.startswith('tcp://'):
                # TCP connection (WSL2 + Docker Desktop)
                if docker_tls_verify and docker_cert_path:
                    # TLS configuration
                    self.client = docker.DockerClient(
                        base_url=docker_host,
                        tls=docker.tls.TLSConfig(
                            ca_cert=os.path.join(docker_cert_path, 'ca.pem'),
                            client_cert=(os.path.join(docker_cert_path, 'cert.pem'), 
                                       os.path.join(docker_cert_path, 'key.pem')),
                            verify=True
                        )
                    )
                else:
                    # Non-TLS TCP connection
                    self.client = docker.DockerClient(base_url=docker_host)
            else:
                # Unix socket connection
                self.client = docker.from_env()
            
            # Test the connection
            self.client.ping()
            self._initialized = True
            logger.debug("Docker client initialized successfully")
            
        except docker.errors.DockerException as e:
            logger.warning(f"Docker client initialization failed (DockerException): {e}")
            self.client = None
            self._initialized = False
        except FileNotFoundError as e:
            logger.warning(f"Docker socket not found: {e}")
            logger.info("This usually means Docker is not running or the socket is not accessible")
            self.client = None
            self._initialized = False
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}")
            self.client = None
            self._initialized = False
    
    def _is_wsl2_environment(self) -> bool:
        """Check if running in WSL2 environment."""
        try:
            # Check for WSL2 specific files
            if os.path.exists('/proc/version'):
                with open('/proc/version', 'r') as f:
                    version_info = f.read().lower()
                    if 'microsoft' in version_info or 'wsl' in version_info:
                        return True
            
            # Check for WSL environment variable
            if os.getenv('WSL_DISTRO_NAME'):
                return True
                
            # Check for WSL2 specific mount points
            if os.path.exists('/mnt/c'):
                return True
                
            return False
        except Exception:
            return False
    
    @property
    def is_available(self) -> bool:
        """Check if Docker sandbox manager is available."""
        return self._initialized and self.client is not None
    
    async def create_sandbox(self, password: str, project_id: str = None, 
                           inject_daytona_daemon: bool = True) -> DockerSandbox:
        """Create a new Docker sandbox with optional daytona daemon injection."""
        if not self.is_available:
            raise Exception("Docker sandbox manager is not available")
            
        try:
            # Generate unique container name
            container_name = f"suna-sandbox-{project_id or 'default'}-{int(time.time())}"
            
            # Container configuration
            container_config = {
                'image': config.SANDBOX_IMAGE_NAME,
                'name': container_name,
                'detach': True,
                'environment': {
                    'VNC_PASSWORD': password,
                    'RESOLUTION': '1048x768x24',
                    'CHROME_PERSISTENT_SESSION': 'true',
                    'ANONYMIZED_TELEMETRY': 'false'
                },
                'ports': {
                    '5900/tcp': None,  # VNC port
                    '9222/tcp': None,  # Chrome debugging port
                    '2080/tcp': None,  # Daytona daemon port (for daemon-proxy)
                },
                'volumes': {
                    '/tmp/.X11-unix': {'bind': '/tmp/.X11-unix', 'mode': 'rw'},
                    '/dev/shm': {'bind': '/dev/shm', 'mode': 'rw'}
                },
                'working_dir': '/workspace',
                'command': config.SANDBOX_ENTRYPOINT,
                'labels': {'suna.sandbox': 'true', 'project_id': project_id or 'default'}
            }
            
            # Create and start container
            container = self.client.containers.run(**container_config)
            logger.debug(f"Created Docker sandbox container: {container.id}")
            
            # Wait for container to be ready
            await self._wait_for_container_ready(container.id)
            
            # Inject daytona daemon if requested
            if inject_daytona_daemon:
                try:
                    # Use existing daemon-proxy injection functionality
                    from backend.extensions.daemon_proxy.daemon_proxy import DaemonManager, Config
                    
                    # Get configuration from environment variables
                    binary_path = os.getenv('DAEMON_BINARY_PATH', '/app/daemon-proxy/daytona-daemon-static')
                    injection_method = os.getenv('DAEMON_INJECTION_METHOD', 'copy')
                    
                    # Create daemon manager with Docker injection mode
                    daemon_config = Config()
                    daemon_config.set("daemon.mode", "docker")
                    daemon_config.set("daemon.port", 2080)
                    daemon_config.set("daemon.container_name", container.id)
                    daemon_config.set("daemon.injection_mode", "volume")
                    daemon_config.set("daemon.injection_method", injection_method)  # 使用配置的注入方式
                    daemon_config.set("daemon.binary_source_path", binary_path)
                    daemon_config.set("daemon.startup_timeout", 30)
                    
                    daemon_manager = DaemonManager(daemon_config)
                    await daemon_manager.start()
                    
                    logger.info(f"Successfully injected daytona daemon into container {container.id} using {injection_method} method")
                except Exception as e:
                    logger.warning(f"Daytona daemon injection failed: {e}")
                    # Continue without daemon injection - sandbox will still work
            
            return DockerSandbox(container.id, self.client)
            
        except Exception as e:
            logger.error(f"Error creating Docker sandbox: {e}")
            raise
    
    async def get_sandbox(self, sandbox_id: str) -> DockerSandbox:
        """Get an existing sandbox by ID."""
        if not self.is_available:
            raise Exception("Docker sandbox manager is not available")
            
        try:
            container = self.client.containers.get(sandbox_id)
            return DockerSandbox(container.id, self.client)
        except NotFound:
            raise Exception(f"Sandbox {sandbox_id} not found")
        except Exception as e:
            logger.error(f"Error getting sandbox {sandbox_id}: {e}")
            raise
    
    async def list_sandboxes(self) -> List[DockerSandbox]:
        """List all sandboxes."""
        if not self.is_available:
            raise Exception("Docker sandbox manager is not available")
            
        try:
            containers = self.client.containers.list(
                filters={'label': 'suna.sandbox=true'},
                all=True
            )
            return [DockerSandbox(container.id, self.client) for container in containers]
        except Exception as e:
            logger.error(f"Error listing sandboxes: {e}")
            raise
    
    async def cleanup_sandboxes(self, max_age_hours: int = 24):
        """Clean up old sandboxes."""
        if not self.is_available:
            logger.warning("Docker sandbox manager is not available, skipping cleanup")
            return
            
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            containers = self.client.containers.list(
                filters={'label': 'suna.sandbox=true'},
                all=True
            )
            
            for container in containers:
                if container.attrs['Created'] < cutoff_time:
                    logger.debug(f"Cleaning up old sandbox: {container.id}")
                    try:
                        container.remove(force=True)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup sandbox {container.id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during sandbox cleanup: {e}")
    
    async def _wait_for_container_ready(self, container_id: str, timeout: int = 60):
        """Wait for container to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                container = self.client.containers.get(container_id)
                if container.status == 'running':
                    # Check if the container is responding
                    try:
                        exec_result = self.client.api.exec_create(
                            container_id,
                            "echo 'ready'"
                        )
                        output = self.client.api.exec_start(exec_result['Id'])
                        if output.decode('utf-8').strip() == 'ready':
                            logger.debug(f"Container {container_id} is ready")
                            return
                    except Exception:
                        pass
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Error checking container readiness: {e}")
                await asyncio.sleep(1)
        
        raise Exception(f"Container {container_id} failed to become ready within {timeout} seconds")


# Global Docker sandbox manager instance
docker_manager = None

def get_docker_manager() -> DockerSandboxManager:
    """Get the global Docker sandbox manager instance."""
    global docker_manager
    if docker_manager is None:
        docker_manager = DockerSandboxManager()
    return docker_manager
