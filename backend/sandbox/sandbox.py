import asyncio
from daytona_sdk import AsyncDaytona, DaytonaConfig, CreateSandboxFromSnapshotParams, AsyncSandbox, SessionExecuteRequest, Resources, SandboxState
from dotenv import load_dotenv
from utils.logger import logger
from utils.config import config
from utils.config import Configuration
from typing import Union, Optional, Dict, Any

load_dotenv()

# Initialize sandbox providers based on configuration
daytona = None
docker_manager = None

if config.USE_LOCAL_DOCKER_SANDBOX:
    logger.debug("Initializing local Docker sandbox configuration")
    try:
        from .docker_sandbox import get_docker_manager
        docker_manager = get_docker_manager()
        if docker_manager.is_available:
            logger.debug("Docker sandbox manager initialized successfully")
        else:
            logger.warning("Docker sandbox manager is not available (Docker daemon not accessible)")
            docker_manager = None
    except Exception as e:
        logger.warning(f"Failed to initialize Docker sandbox manager: {e}")
        docker_manager = None
else:
    logger.debug("Initializing Daytona sandbox configuration")
    if config.DAYTONA_API_KEY and config.DAYTONA_SERVER_URL and config.DAYTONA_TARGET:
        daytona_config = DaytonaConfig(
            api_key=config.DAYTONA_API_KEY,
            api_url=config.DAYTONA_SERVER_URL, 
            target=config.DAYTONA_TARGET,
        )
        daytona = AsyncDaytona(daytona_config)
        logger.debug("Daytona sandbox manager initialized successfully")
    else:
        logger.warning("Daytona configuration incomplete, sandbox functionality may be limited")

async def get_or_start_sandbox(sandbox_id: str) -> Union[AsyncSandbox, 'DockerSandbox']:
    """Retrieve a sandbox by ID, check its state, and start it if needed."""
    
    logger.debug(f"Getting or starting sandbox with ID: {sandbox_id}")

    try:
        if config.USE_LOCAL_DOCKER_SANDBOX and docker_manager and docker_manager.is_available:
            # Use Docker sandbox
            try:
                sandbox = await docker_manager.get_sandbox(sandbox_id)
                
                # Check if sandbox needs to be started
                if sandbox.state != "running":
                    logger.debug(f"Docker sandbox is in {sandbox.state} state. Starting...")
                    try:
                        await sandbox.start()
                        # Wait a moment for the sandbox to initialize
                        await asyncio.sleep(5)
                        # Refresh sandbox state after starting
                        sandbox = await docker_manager.get_sandbox(sandbox_id)
                        
                        # Start supervisord in a session when restarting
                        await start_supervisord_session(sandbox)
                    except Exception as e:
                        logger.error(f"Error starting Docker sandbox: {e}")
                        raise e
            except Exception as e:
                logger.error(f"Docker sandbox operation failed: {e}")
                # Fall back to Daytona if available
                if daytona:
                    logger.info("Falling back to Daytona sandbox")
                    raise Exception(f"Docker sandbox failed, falling back to Daytona: {e}")
                else:
                    raise Exception(f"Docker sandbox failed and no fallback available: {e}")
        else:
            # Use Daytona sandbox
            if not daytona:
                raise Exception("Daytona sandbox manager not available")
                
            sandbox = await daytona.get(sandbox_id)
            
            # Check if sandbox needs to be started
            if sandbox.state == SandboxState.ARCHIVED or sandbox.state == SandboxState.STOPPED:
                logger.debug(f"Sandbox is in {sandbox.state} state. Starting...")
                try:
                    await daytona.start(sandbox)
                    # Wait a moment for the sandbox to initialize
                    await asyncio.sleep(5)
                    # Refresh sandbox state after starting
                    sandbox = await daytona.get(sandbox_id)
                    
                    # Start supervisord in a session when restarting
                    await start_supervisord_session(sandbox)
                except Exception as e:
                    logger.error(f"Error starting sandbox: {e}")
                    raise e
        
        logger.debug(f"Sandbox {sandbox_id} is ready")
        return sandbox
        
    except Exception as e:
        logger.error(f"Error retrieving or starting sandbox: {str(e)}")
        raise e

async def start_supervisord_session(sandbox: Union[AsyncSandbox, 'DockerSandbox']):
    """Start supervisord in a session."""
    session_id = "supervisord-session"
    max_retries = 3
    retry_delay = 0.5  # 500ms
    
    try:
        logger.debug(f"Creating session {session_id} for supervisord")
        await sandbox.process.create_session(session_id)
        
        # Add a small delay to ensure session is fully initialized
        await asyncio.sleep(0.1)
        
        # Retry mechanism for executing supervisord command
        for attempt in range(max_retries):
            try:
                # Execute supervisord command
                # Use the appropriate SessionExecuteRequest class based on sandbox type
                if hasattr(sandbox, 'container_id'):  # Docker sandbox
                    from .docker_sandbox import SessionExecuteRequest as DockerSessionExecuteRequest
                    # Fix: Remove 'exec' prefix - it's a shell builtin, not an executable
                    # Use direct path to supervisord executable
                    request = DockerSessionExecuteRequest(
                        command="/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf",
                        var_async=True
                    )
                else:  # Daytona sandbox
                    request = SessionExecuteRequest(
                        command="/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf",
                        var_async=True
                    )
                
                await sandbox.process.execute_session_command(session_id, request)
                logger.debug(f"Supervisord started in session {session_id}")
                return  # Success, exit the function
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for session {session_id}: {e}, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Last attempt failed
                    logger.error(f"All {max_retries} attempts failed for session {session_id}: {e}")
                    raise e
                    
    except Exception as e:
        logger.error(f"Error starting supervisord session: {str(e)}")
        raise e

async def create_sandbox(password: str, project_id: str = None) -> Union[AsyncSandbox, 'DockerSandbox']:
    """Create a new sandbox with all required services configured and running."""
    
    try:
        if config.USE_LOCAL_DOCKER_SANDBOX and docker_manager and docker_manager.is_available:
            # Create Docker sandbox
            try:
                logger.debug("Creating new Docker sandbox environment")
                sandbox = await docker_manager.create_sandbox(password, project_id)
                logger.debug(f"Docker sandbox created with ID: {sandbox.id}")
                
                # Start supervisord in a session for new sandbox
                await start_supervisord_session(sandbox)
                
                logger.debug(f"Docker sandbox environment successfully initialized")
                return sandbox
            except Exception as e:
                logger.error(f"Docker sandbox creation failed: {e}")
                # Fall back to Daytona if available
                if daytona:
                    logger.info("Falling back to Daytona sandbox creation")
                else:
                    raise Exception(f"Docker sandbox creation failed and no fallback available: {e}")
        else:
            # Create Daytona sandbox
            if not daytona:
                raise Exception("Daytona sandbox manager not available")
                
            logger.debug("Creating new Daytona sandbox environment")
            logger.debug("Configuring sandbox with snapshot and environment variables")
            
            labels = None
            if project_id:
                logger.debug(f"Using sandbox_id as label: {project_id}")
                labels = {'id': project_id}
                
            params = CreateSandboxFromSnapshotParams(
                snapshot=Configuration.SANDBOX_SNAPSHOT_NAME,
                public=True,
                labels=labels,
                env_vars={
                    "CHROME_PERSISTENT_SESSION": "true",
                    "RESOLUTION": "1048x768x24",
                    "RESOLUTION_WIDTH": "1048",
                    "RESOLUTION_HEIGHT": "768",
                    "VNC_PASSWORD": password,
                    "ANONYMIZED_TELEMETRY": "false",
                    "CHROME_PATH": "",
                    "CHROME_USER_DATA": "",
                    "CHROME_DEBUGGING_PORT": "9222",
                    "CHROME_DEBUGGING_HOST": "localhost",
                    "CHROME_CDP": ""
                },
                resources=Resources(
                    cpu=2,
                    memory=4,
                    disk=5,
                ),
                auto_stop_interval=120,
                auto_archive_interval=2 * 60,
            )
            
            # Create the sandbox
            sandbox = await daytona.create(params)
            logger.debug(f"Sandbox created with ID: {sandbox.id}")
            
            # Start supervisord in a session for new sandbox
            await start_supervisord_session(sandbox)
            
            logger.debug(f"Sandbox environment successfully initialized")
            return sandbox
            
    except Exception as e:
        logger.error(f"Error creating sandbox: {e}")
        raise e

async def delete_sandbox(sandbox_id: str) -> bool:
    """Delete a sandbox by its ID."""
    logger.debug(f"Deleting sandbox with ID: {sandbox_id}")

    try:
        if config.USE_LOCAL_DOCKER_SANDBOX and docker_manager and docker_manager.is_available:
            # Delete Docker sandbox
            try:
                sandbox = await docker_manager.get_sandbox(sandbox_id)
                await sandbox.delete()
                logger.debug(f"Successfully deleted Docker sandbox {sandbox_id}")
            except Exception as e:
                logger.error(f"Failed to delete Docker sandbox {sandbox_id}: {e}")
                # Fall back to Daytona if available
                if daytona:
                    logger.info("Falling back to Daytona sandbox deletion")
                else:
                    raise Exception(f"Docker sandbox deletion failed and no fallback available: {e}")
        else:
            # Delete Daytona sandbox
            if not daytona:
                raise Exception("Daytona sandbox manager not available")
                
            sandbox = await daytona.get(sandbox_id)
            await daytona.delete(sandbox)
            logger.debug(f"Successfully deleted Daytona sandbox {sandbox_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error deleting sandbox {sandbox_id}: {str(e)}")
        raise e

def is_docker_sandbox_available() -> bool:
    """Check if Docker sandbox is available and working."""
    global docker_manager
    if not config.USE_LOCAL_DOCKER_SANDBOX:
        return False
    if docker_manager is None:
        return False
    return docker_manager.is_available

def get_available_sandbox_providers() -> list:
    """Get list of available sandbox providers."""
    providers = []
    
    if daytona:
        providers.append("daytona")
    
    if is_docker_sandbox_available():
        providers.append("docker")
    
    return providers


# Docker Sandbox Daemon Proxy Integration Functions

async def get_docker_sandbox_with_daemon_proxy(
    container_id: str, 
    daemon_proxy_config: Optional[Dict[str, Any]] = None
) -> Optional['DockerSandboxWithDaemonProxy']:
    """
    Get a Docker sandbox with integrated daemon proxy functionality
    
    Args:
        container_id: The Docker container ID
        daemon_proxy_config: Optional daemon proxy configuration
        
    Returns:
        DockerSandboxWithDaemonProxy instance or None if failed
    """
    try:
        from .daemon_proxy_integration import create_docker_sandbox_with_daemon_proxy
        return await create_docker_sandbox_with_daemon_proxy(container_id, daemon_proxy_config)
    except Exception as e:
        logger.error(f"Failed to get Docker sandbox with daemon proxy: {e}")
        return None


async def get_preview_link_for_docker_sandbox(
    container_id: str, 
    port: int, 
    daemon_proxy_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a preview link for a specific port in a Docker sandbox
    
    Args:
        container_id: The Docker container ID
        port: The port to create preview link for
        daemon_proxy_config: Optional daemon proxy configuration
        
    Returns:
        Preview link information or None if failed
    """
    try:
        import aiohttp
        from utils.config import config
        
        # Get backend URL from config
        backend_url = getattr(config, 'BACKEND_URL', 'http://localhost:8001/api')
        
        async with aiohttp.ClientSession() as session:
            # First, ensure daemon is injected into this container
            inject_url = f"{backend_url}/daemon-proxy/container/{container_id}/inject"
            async with session.post(inject_url, json=daemon_proxy_config) as response:
                if response.status not in [200, 409]:  # 409 = already injected
                    logger.warning(f"Failed to inject daemon into container {container_id}")
                    return None
            
            # Create preview link
            preview_url = f"{backend_url}/daemon-proxy/container/{container_id}/preview/{port}"
            async with session.post(preview_url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to create preview link: {response.status}")
                    return None
        
    except Exception as e:
        logger.error(f"Failed to get preview link for Docker sandbox {container_id}, port {port}: {e}")
        return None


async def get_vnc_preview_link_for_docker_sandbox(
    container_id: str, 
    daemon_proxy_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get VNC preview link for a Docker sandbox (port 6080)
    
    Args:
        container_id: The Docker container ID
        daemon_proxy_config: Optional daemon proxy configuration
        
    Returns:
        VNC preview link information or None if failed
    """
    return await get_preview_link_for_docker_sandbox(container_id, 6080, daemon_proxy_config)


async def get_website_preview_link_for_docker_sandbox(
    container_id: str, 
    port: int = 8080,
    daemon_proxy_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get website preview link for a Docker sandbox
    
    Args:
        container_id: The Docker container ID
        port: The website port (default: 8080)
        daemon_proxy_config: Optional daemon proxy configuration
        
    Returns:
        Website preview link information or None if failed
    """
    return await get_preview_link_for_docker_sandbox(container_id, port, daemon_proxy_config)


async def revoke_preview_link_for_docker_sandbox(
    container_id: str, 
    token: str,
    daemon_proxy_config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Revoke a preview link for a Docker sandbox
    
    Args:
        container_id: The Docker container ID
        token: The preview link token to revoke
        daemon_proxy_config: Optional daemon proxy configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sandbox_with_proxy = await get_docker_sandbox_with_daemon_proxy(container_id, daemon_proxy_config)
        if not sandbox_with_proxy:
            return False
        
        return await sandbox_with_proxy.revoke_preview_link(token)
        
    except Exception as e:
        logger.error(f"Failed to revoke preview link for Docker sandbox {container_id}, token {token}: {e}")
        return False
