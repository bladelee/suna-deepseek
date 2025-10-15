"""
Mock Daemon 服务器

模拟真实的 daytona daemon 行为，用于 E2E 测试
"""

import asyncio
import aiohttp
from aiohttp import web
import logging
from typing import Dict, Any, Optional
import json
import pytest


class MockDaemonServer:
    """Mock Daemon 服务器"""
    
    def __init__(self, port: int = 0):
        self.port = port
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._target_services: Dict[int, str] = {}  # port -> service_url
        self._request_count = 0
        self._error_count = 0
    
    def register_target_service(self, port: int, service_url: str):
        """注册目标服务"""
        self._target_services[port] = service_url
        logging.info(f"Registered target service: port {port} -> {service_url}")
    
    def unregister_target_service(self, port: int):
        """注销目标服务"""
        if port in self._target_services:
            del self._target_services[port]
            logging.info(f"Unregistered target service: port {port}")
        
    async def start(self):
        """启动 mock daemon 服务器"""
        self.app = web.Application()
        self._setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(
            self.runner, 
            '127.0.0.1', 
            self.port
        )
        
        await self.site.start()
        
        # 获取实际端口
        self.port = self.site._server.sockets[0].getsockname()[1]
        
        logging.info(f"Mock daemon started on port {self.port}")
        return f"http://127.0.0.1:{self.port}"
    
    def _setup_routes(self):
        """设置路由"""
        # Daemon 版本信息
        self.app.router.add_get('/version', self.version_handler)
        
        # 代理路由
        self.app.router.add_route('*', '/proxy/{port}/{path:.*}', self.proxy_handler)
        self.app.router.add_route('*', '/proxy/{port}', self.proxy_handler)
        
        # 健康检查
        self.app.router.add_get('/health', self.health_handler)
        
        # 统计信息
        self.app.router.add_get('/stats', self.stats_handler)
    
    async def version_handler(self, request: web.Request) -> web.Response:
        """版本信息处理器"""
        return web.json_response({
            "version": "1.0.0-mock",
            "build": "mock-build",
            "commit": "mock-commit"
        })
    
    async def proxy_handler(self, request: web.Request) -> web.Response:
        """代理请求处理器"""
        self._request_count += 1
        
        port = request.match_info['port']
        path = request.match_info.get('path', '')
        
        try:
            # 检查是否有注册的目标服务
            port_int = int(port)
            if port_int in self._target_services:
                target_url = self._target_services[port_int]
                return await self._proxy_to_target(request, target_url, path)
            else:
                # 对于未注册的端口，返回 404
                return web.json_response(
                    {"error": f"Port {port} not found or not registered"}, 
                    status=404
                )
                
        except Exception as e:
            self._error_count += 1
            logging.error(f"Proxy error: {e}")
            return web.json_response(
                {"error": f"Proxy error: {str(e)}"}, 
                status=502
            )
    
    async def _proxy_to_target(self, request: web.Request, target_url: str, path: str) -> web.Response:
        """代理到真实目标服务"""
        # 构建目标URL
        target_path = f"{target_url}/{path}" if path else target_url
        
        # 准备请求数据
        headers = dict(request.headers)
        headers.pop('Host', None)
        headers.pop('Content-Length', None)
        
        body = None
        if request.can_read_body:
            body = await request.read()
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            response_cm = await session.request(
                method=request.method,
                url=target_path,
                headers=headers,
                data=body,
                params=request.query
            )
            async with response_cm as response:
                response_body = await response.read()
                
                return web.Response(
                    body=response_body,
                    status=response.status,
                    headers=dict(response.headers)
                )
    
    async def _mock_response(self, request: web.Request, port: str, path: str) -> web.Response:
        """返回模拟响应"""
        if port == "6080":  # VNC 端口
            return await self._mock_vnc_response(request, path)
        elif port == "8080":  # Web 端口
            return await self._mock_web_response(request, path)
        else:
            return await self._mock_generic_response(request, port, path)
    
    async def _mock_vnc_response(self, request: web.Request, path: str) -> web.Response:
        """模拟 VNC 响应"""
        if path == "status" or path == "":
            return web.json_response({
                "service": "VNC",
                "port": 6080,
                "status": "running",
                "protocol": "RFB",
                "version": "3.8"
            })
        elif path == "connect":
            return web.json_response({
                "connection": "established",
                "resolution": "1920x1080",
                "color_depth": 24
            })
        else:
            return web.json_response({
                "message": "VNC service response",
                "path": path,
                "timestamp": asyncio.get_event_loop().time()
            })
    
    async def _mock_web_response(self, request: web.Request, path: str) -> web.Response:
        """模拟 Web 响应"""
        if path == "api/status" or path == "status":
            return web.json_response({
                "service": "Web",
                "port": 8080,
                "status": "running",
                "version": "1.0.0"
            })
        elif path == "api/data":
            return web.json_response({
                "data": "test data from mock web service",
                "items": [1, 2, 3, 4, 5],
                "timestamp": asyncio.get_event_loop().time()
            })
        elif path == "" or path == "index.html":
            html_content = """
            <!DOCTYPE html>
            <html>
            <head><title>Mock Web Service</title></head>
            <body>
                <h1>Mock Web Service</h1>
                <p>Port: 8080</p>
                <p>Status: Running</p>
                <p>This is a mock response for E2E testing.</p>
            </body>
            </html>
            """
            return web.Response(text=html_content, content_type="text/html")
        else:
            return web.json_response({
                "message": "Web service response",
                "path": path,
                "method": request.method,
                "timestamp": asyncio.get_event_loop().time()
            })
    
    async def _mock_generic_response(self, request: web.Request, port: str, path: str) -> web.Response:
        """模拟通用响应"""
        return web.json_response({
            "service": "Generic",
            "port": port,
            "path": path,
            "method": request.method,
            "message": f"Mock response for port {port}",
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """健康检查处理器"""
        return web.json_response({
            "status": "healthy",
            "uptime": 0,
            "requests": self._request_count,
            "errors": self._error_count
        })
    
    async def stats_handler(self, request: web.Request) -> web.Response:
        """统计信息处理器"""
        return web.json_response({
            "requests_total": self._request_count,
            "errors_total": self._error_count,
            "target_services": len(self._target_services),
            "registered_ports": list(self._target_services.keys())
        })
    
    def register_target_service(self, port: str, service_url: str):
        """注册目标服务"""
        self._target_services[port] = service_url
        logging.info(f"Registered target service: port {port} -> {service_url}")
    
    def unregister_target_service(self, port: str):
        """取消注册目标服务"""
        if port in self._target_services:
            del self._target_services[port]
            logging.info(f"Unregistered target service: port {port}")
    
    async def stop(self):
        """停止服务器"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logging.info("Mock daemon stopped")


# Pytest fixtures
@pytest.fixture
async def mock_daemon_server():
    """Mock daemon 服务器 fixture"""
    server = MockDaemonServer()
    daemon_url = await server.start()
    
    yield server, daemon_url
    
    await server.stop()


@pytest.fixture
async def mock_daemon_url(mock_daemon_server):
    """Mock daemon URL fixture"""
    server, daemon_url = mock_daemon_server
    return daemon_url
