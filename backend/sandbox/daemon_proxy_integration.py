"""
Daemon Proxy Integration for Backend API

This module integrates daemon-proxy as FastAPI sub-application within the backend API service,
providing preview link functionality for Docker sandboxes.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, APIRouter, HTTPException
from aiohttp import web

from extensions.daemon_proxy.daemon_proxy import (
    DaemonProxy,
    DaemonManager, 
    Config, 
    PreviewLinkManager,
    PreviewHandler
)
from .docker_sandbox import DockerSandbox
from utils.logger import logger


class GlobalDaemonProxyService:
    """Global daemon-proxy service that manages multiple containers"""
    
    def __init__(self):
        self.daemon_proxy: Optional[DaemonProxy] = None
        self.preview_manager: Optional[PreviewLinkManager] = None
        self._is_running = False
        self._managed_containers: Dict[str, str] = {}  # container_id -> daemon_status
        self._daemon_managers: Dict[str, DaemonManager] = {}  # container_id -> DaemonManager
        
        # 从环境变量获取daemon二进制文件路径，支持容器化环境
        self.daemon_binary_path = os.getenv(
            'DAEMON_BINARY_PATH', 
            '/app/daemon-proxy/daytona-daemon-static'  # 容器内路径
        )
        
        # 从环境变量获取注入方式配置
        self.injection_method = os.getenv('DAEMON_INJECTION_METHOD', 'copy')  # 默认使用拷贝方式
        
        # 验证二进制文件是否存在
        if not os.path.exists(self.daemon_binary_path):
            logger.warning(f"Daemon binary not found at {self.daemon_binary_path}")
        else:
            logger.info(f"Daemon binary found at {self.daemon_binary_path}")
        
        logger.info(f"Using injection method: {self.injection_method}")
    
    async def start_global_service(self) -> bool:
        """Start the global daemon-proxy service"""
        try:
            if self._is_running:
                logger.warning("Global daemon-proxy service is already running")
                return True
            
            # Create global configuration for preview link management only
            daemon_config = Config()
            daemon_config.set("server.host", "127.0.0.1")  # Bind to localhost since it's part of backend
            daemon_config.set("server.port", 0)  # Let system assign a free port
            daemon_config.set("security.enabled", False)
            
            # Start only the preview link manager - NO daemon manager at startup
            self.preview_manager = PreviewLinkManager(daemon_config)
            await self.preview_manager.start()
            
            self._is_running = True
            logger.info("Global daemon-proxy service started (preview link manager only)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start global daemon-proxy service: {e}")
            return False
    
    async def stop_global_service(self):
        """Stop the global daemon-proxy service"""
        try:
            if not self._is_running:
                return
            
            # Stop all per-container daemon managers
            for container_id, daemon_manager in self._daemon_managers.items():
                try:
                    await daemon_manager.stop()
                    logger.info(f"Stopped daemon manager for container {container_id}")
                except Exception as e:
                    logger.error(f"Error stopping daemon manager for container {container_id}: {e}")
            
            # Stop the preview manager
            if self.preview_manager:
                try:
                    await self.preview_manager.stop()
                    logger.info("Stopped preview manager")
                except Exception as e:
                    logger.error(f"Error stopping preview manager: {e}")
            
            # Clear all tracking dictionaries
            self._daemon_managers.clear()
            self._managed_containers.clear()
            self._is_running = False
            
            logger.info("Global daemon-proxy service stopped")
        except Exception as e:
            logger.error(f"Error stopping global daemon-proxy service: {e}")
    
    async def inject_daemon_to_container(self, container_id: str, binary_source_path: str = None) -> bool:
        """Inject daemon into a specific container"""
        try:
            if not self._is_running:
                logger.error("Global daemon-proxy service is not running")
                return False
            
            # 使用配置的二进制文件路径
            actual_binary_path = binary_source_path or self.daemon_binary_path
            
            # 验证文件存在
            if not os.path.exists(actual_binary_path):
                logger.error(f"Daemon binary not found at {actual_binary_path}")
                return False
            
            # Check if container is already managed
            if container_id in self._daemon_managers:
                logger.warning(f"Container {container_id} is already managed by daemon-proxy")
                return True
            
            # Create per-container daemon manager
            daemon_config = Config()
            daemon_config.set("daemon.mode", "docker")
            daemon_config.set("daemon.port", 2080)
            daemon_config.set("daemon.container_name", container_id)
            daemon_config.set("daemon.injection_mode", "volume")
            daemon_config.set("daemon.injection_method", self.injection_method)  # 使用配置的注入方式
            daemon_config.set("daemon.binary_source_path", actual_binary_path)
            daemon_config.set("daemon.startup_timeout", 30)
            
            # Create and start daemon manager for this specific container
            daemon_manager = DaemonManager(daemon_config)
            await daemon_manager.start()  # This NOW happens per-container
            
            # Store the manager and update status
            self._daemon_managers[container_id] = daemon_manager
            self._managed_containers[container_id] = "running"
            logger.info(f"Injected daemon into container {container_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to inject daemon into container {container_id}: {e}")
            return False
    
    async def remove_daemon_from_container(self, container_id: str) -> bool:
        """Remove daemon from a specific container"""
        try:
            if container_id not in self._daemon_managers:
                logger.warning(f"Container {container_id} is not managed by daemon-proxy")
                return False
            
            # Retrieve and stop the DaemonManager for this container
            daemon_manager = self._daemon_managers[container_id]
            await daemon_manager.stop()
            
            # Remove from both tracking dictionaries
            del self._daemon_managers[container_id]
            del self._managed_containers[container_id]
            
            logger.info(f"Removed daemon from container {container_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error removing daemon from container {container_id}: {e}")
            return False
    
    async def get_preview_link(self, container_id: str, port: int):
        """Get preview link for a specific container and port"""
        if not self._is_running or not self.preview_manager:
            logger.error("Global daemon-proxy service is not running")
            return None
        
        if container_id not in self._daemon_managers:
            logger.error(f"Container {container_id} is not managed by daemon-proxy")
            return None
        
        try:
            # Use the preview manager to create preview link
            # The preview manager will use the daemon connection from the specific container's DaemonManager
            return await self.preview_manager.create_preview_link(port)
        except Exception as e:
            logger.error(f"Failed to get preview link for container {container_id}, port {port}: {e}")
            return None
    
    async def get_vnc_preview_link(self, container_id: str):
        """Get VNC preview link for a specific container"""
        return await self.get_preview_link(container_id, 6080)
    
    async def get_website_preview_link(self, container_id: str, port: int = 8080):
        """Get website preview link for a specific container"""
        return await self.get_preview_link(container_id, port)
    
    @property
    def is_running(self) -> bool:
        """Check if global daemon-proxy service is running"""
        return self._is_running
    
    @property
    def managed_containers(self) -> Dict[str, str]:
        """Get list of managed containers"""
        return self._managed_containers.copy()
    
    @property
    def service_url(self) -> Optional[str]:
        """Get the daemon-proxy service URL"""
        # Since we no longer use a full DaemonProxy with its own web server,
        # the service is integrated into the backend API
        if self._is_running:
            return "http://127.0.0.1:8000"  # Backend API URL
        return None


def create_daemon_proxy_router() -> APIRouter:
    """Create FastAPI router for daemon-proxy endpoints"""
    router = APIRouter(prefix="/daemon-proxy", tags=["daemon-proxy"])
    
    # Global daemon proxy service instance
    _global_service: Optional[GlobalDaemonProxyService] = None
    
    @router.on_event("startup")
    async def startup_daemon_proxy():
        """Start the global daemon-proxy service when the API starts"""
        global _global_service
        _global_service = GlobalDaemonProxyService()
        success = await _global_service.start_global_service()
        if not success:
            logger.error("Failed to start global daemon-proxy service")
    
    @router.on_event("shutdown")
    async def shutdown_daemon_proxy():
        """Stop the global daemon-proxy service when the API shuts down"""
        global _global_service
        if _global_service:
            await _global_service.stop_global_service()
            _global_service = None
    
    @router.post("/container/{container_id}/inject")
    async def inject_daemon_to_container(
        container_id: str,
        binary_source_path: Optional[str] = None
    ):
        """Inject daemon into a specific container"""
        try:
            global _global_service
            if not _global_service or not _global_service.is_running:
                raise HTTPException(status_code=503, detail="Global daemon-proxy service is not running")
            
            success = await _global_service.inject_daemon_to_container(container_id, binary_source_path)
            
            if success:
                return {"status": "injected", "container_id": container_id}
            else:
                raise HTTPException(status_code=500, detail="Failed to inject daemon into container")
                
        except Exception as e:
            logger.error(f"Error injecting daemon into container {container_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/container/{container_id}/remove")
    async def remove_daemon_from_container(container_id: str):
        """Remove daemon from a specific container"""
        try:
            global _global_service
            if not _global_service or not _global_service.is_running:
                raise HTTPException(status_code=503, detail="Global daemon-proxy service is not running")
            
            success = await _global_service.remove_daemon_from_container(container_id)
            
            if success:
                return {"status": "removed", "container_id": container_id}
            else:
                return {"status": "not_managed", "container_id": container_id}
                
        except Exception as e:
            logger.error(f"Error removing daemon from container {container_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/container/{container_id}/preview/{port}")
    async def create_preview_link(container_id: str, port: int):
        """Create a preview link for a specific port in a container"""
        try:
            global _global_service
            if not _global_service or not _global_service.is_running:
                raise HTTPException(status_code=503, detail="Global daemon-proxy service is not running")
            
            preview_link = await _global_service.get_preview_link(container_id, port)
            if preview_link:
                return {
                    "url": preview_link.url,
                    "token": preview_link.token,
                    "port": preview_link.port,
                    "expires_at": preview_link.expires_at
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create preview link")
                
        except Exception as e:
            logger.error(f"Error creating preview link for container {container_id}, port {port}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/container/{container_id}/status")
    async def get_container_daemon_status(container_id: str):
        """Get daemon status for a specific container"""
        try:
            global _global_service
            if not _global_service or not _global_service.is_running:
                return {
                    "status": "service_not_running",
                    "container_id": container_id,
                    "daemon_status": "unknown"
                }
            
            managed_containers = _global_service.managed_containers
            daemon_status = managed_containers.get(container_id, "not_managed")
            
            return {
                "status": "ok",
                "container_id": container_id,
                "daemon_status": daemon_status,
                "service_running": _global_service.is_running
            }
                
        except Exception as e:
            logger.error(f"Error getting daemon status for container {container_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/service/status")
    async def get_global_service_status():
        """Get global daemon-proxy service status"""
        try:
            global _global_service
            if not _global_service:
                return {
                    "status": "not_initialized",
                    "is_running": False,
                    "managed_containers": []
                }
            
            return {
                "status": "ok",
                "is_running": _global_service.is_running,
                "managed_containers": list(_global_service.managed_containers.keys()),
                "service_url": _global_service.service_url
            }
                
        except Exception as e:
            logger.error(f"Error getting global service status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


class DockerSandboxWithDaemonProxy:
    """Wrapper that adds daemon proxy functionality to Docker sandbox"""
    
    def __init__(self, docker_sandbox: DockerSandbox, daemon_proxy_config: Optional[Dict[str, Any]] = None):
        self.docker_sandbox = docker_sandbox
        self.daemon_proxy_manager = BackendDaemonProxyManager()
        self._daemon_proxy_config = daemon_proxy_config or {}
    
    async def start(self):
        """Start daemon proxy for this sandbox"""
        success = await self.daemon_proxy_manager.start_for_sandbox(
            self.docker_sandbox, 
            self._daemon_proxy_config
        )
        if not success:
            raise Exception("Failed to start daemon proxy")
    
    async def stop(self):
        """Stop daemon proxy"""
        await self.daemon_proxy_manager.stop()
    
    # Delegate Docker sandbox methods
    def __getattr__(self, name):
        return getattr(self.docker_sandbox, name)
    
    # Add daemon proxy methods
    async def get_preview_link(self, port: int):
        """Get preview link"""
        return await self.daemon_proxy_manager.get_preview_link(port)
    
    async def get_vnc_preview_link(self):
        """Get VNC preview link"""
        return await self.daemon_proxy_manager.get_vnc_preview_link()
    
    async def get_website_preview_link(self, port: int = 8080):
        """Get website preview link"""
        return await self.daemon_proxy_manager.get_website_preview_link(port)
    
    @property
    def daemon_proxy_running(self) -> bool:
        """Check if daemon proxy is running"""
        return self.daemon_proxy_manager.is_running


async def create_docker_sandbox_with_daemon_proxy(
    container_id: str, 
    daemon_proxy_config: Optional[Dict[str, Any]] = None
) -> Optional[DockerSandboxWithDaemonProxy]:
    """
    Create a Docker sandbox with integrated daemon proxy functionality
    
    Args:
        container_id: The Docker container ID
        daemon_proxy_config: Optional daemon proxy configuration
        
    Returns:
        DockerSandboxWithDaemonProxy instance or None if failed
    """
    try:
        # Get the Docker sandbox
        from .docker_sandbox import get_docker_manager
        docker_manager = get_docker_manager()
        
        if not docker_manager.is_available:
            logger.error("Docker is not available")
            return None
        
        docker_sandbox = await docker_manager.get_sandbox(container_id)
        
        if not docker_sandbox:
            logger.error(f"Failed to get Docker sandbox {container_id}")
            return None
        
        # Create wrapper with daemon proxy
        sandbox_with_proxy = DockerSandboxWithDaemonProxy(docker_sandbox, daemon_proxy_config)
        
        # Start daemon proxy
        await sandbox_with_proxy.start()
        
        logger.info(f"Created Docker sandbox with daemon proxy: {container_id}")
        return sandbox_with_proxy
        
    except Exception as e:
        logger.error(f"Failed to create Docker sandbox with daemon proxy: {e}")
        return None
