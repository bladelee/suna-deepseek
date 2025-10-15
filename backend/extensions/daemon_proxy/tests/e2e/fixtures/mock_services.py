"""
Mock 服务

模拟各种目标服务（VNC、Web等），用于 E2E 测试
"""

import asyncio
import aiohttp
from aiohttp import web
import logging
from typing import Dict, Any, Optional
import json
import pytest
import socket


def get_unused_port():
    """获取一个未使用的端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class MockVNCServer:
    """Mock VNC 服务器"""
    
    def __init__(self, port: Optional[int] = None):
        self.port = port or get_unused_port()
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._connections = 0
        
    async def start(self):
        """启动 VNC 服务器"""
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
        
        logging.info(f"Mock VNC server started on port {self.port}")
        return f"http://127.0.0.1:{self.port}"
    
    def _setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/status', self.status_handler)
        self.app.router.add_post('/connect', self.connect_handler)
        self.app.router.add_get('/screen', self.screen_handler)
        self.app.router.add_post('/key', self.key_handler)
        self.app.router.add_post('/mouse', self.mouse_handler)
    
    async def index_handler(self, request: web.Request) -> web.Response:
        """首页处理器"""
        return web.json_response({
            "service": "VNC",
            "port": self.port,
            "status": "running",
            "protocol": "RFB",
            "version": "3.8",
            "connections": self._connections
        })
    
    async def status_handler(self, request: web.Request) -> web.Response:
        """状态处理器"""
        return web.json_response({
            "service": "VNC",
            "port": self.port,
            "status": "running",
            "protocol": "RFB",
            "version": "3.8",
            "connections": self._connections,
            "resolution": "1920x1080",
            "color_depth": 24,
            "compression": "Tight"
        })
    
    async def connect_handler(self, request: web.Request) -> web.Response:
        """连接处理器"""
        self._connections += 1
        return web.json_response({
            "connection": "established",
            "connection_id": self._connections,
            "resolution": "1920x1080",
            "color_depth": 24,
            "compression": "Tight",
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def screen_handler(self, request: web.Request) -> web.Response:
        """屏幕数据处理器"""
        return web.json_response({
            "screen_data": "mock_screen_data_base64_encoded",
            "width": 1920,
            "height": 1080,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def key_handler(self, request: web.Request) -> web.Response:
        """键盘事件处理器"""
        data = await request.json()
        return web.json_response({
            "key_event": "processed",
            "key": data.get("key"),
            "action": data.get("action"),
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def mouse_handler(self, request: web.Request) -> web.Response:
        """鼠标事件处理器"""
        data = await request.json()
        return web.json_response({
            "mouse_event": "processed",
            "x": data.get("x"),
            "y": data.get("y"),
            "button": data.get("button"),
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def stop(self):
        """停止服务器"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logging.info("Mock VNC server stopped")


class MockWebServer:
    """Mock Web 服务器"""
    
    def __init__(self, port: Optional[int] = None):
        self.port = port or get_unused_port()
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._request_count = 0
        
    async def start(self):
        """启动 Web 服务器"""
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
        
        logging.info(f"Mock Web server started on port {self.port}")
        return f"http://127.0.0.1:{self.port}"
    
    def _setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/index.html', self.index_handler)
        self.app.router.add_get('/api/status', self.status_handler)
        self.app.router.add_get('/api/data', self.data_handler)
        self.app.router.add_post('/api/data', self.post_data_handler)
        self.app.router.add_get('/api/users', self.users_handler)
        self.app.router.add_post('/api/users', self.create_user_handler)
        self.app.router.add_get('/health', self.health_handler)
    
    async def index_handler(self, request: web.Request) -> web.Response:
        """首页处理器"""
        self._request_count += 1
        return web.json_response({
            "service": "Web",
            "port": self.port,
            "status": "running",
            "version": "1.0.0",
            "requests": self._request_count
        })
    
    async def status_handler(self, request: web.Request) -> web.Response:
        """状态处理器"""
        return web.json_response({
            "service": "Web",
            "port": self.port,
            "status": "running",
            "version": "1.0.0",
            "requests": self._request_count,
            "uptime": asyncio.get_event_loop().time(),
            "endpoints": [
                "/api/status",
                "/api/data", 
                "/api/users",
                "/health"
            ]
        })
    
    async def data_handler(self, request: web.Request) -> web.Response:
        """数据处理器"""
        return web.json_response({
            "data": "test data from mock web service",
            "items": [
                {"id": 1, "name": "Item 1", "value": 100},
                {"id": 2, "name": "Item 2", "value": 200},
                {"id": 3, "name": "Item 3", "value": 300}
            ],
            "count": 3,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def post_data_handler(self, request: web.Request) -> web.Response:
        """POST 数据处理器"""
        try:
            data = await request.json()
            return web.json_response({
                "message": "Data received successfully",
                "received_data": data,
                "processed": True,
                "timestamp": asyncio.get_event_loop().time()
            })
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to process data: {str(e)}"}, 
                status=400
            )
    
    async def users_handler(self, request: web.Request) -> web.Response:
        """用户列表处理器"""
        return web.json_response({
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
            ],
            "total": 3,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def create_user_handler(self, request: web.Request) -> web.Response:
        """创建用户处理器"""
        try:
            data = await request.json()
            user_id = 100 + self._request_count  # 简单的ID生成
            
            return web.json_response({
                "message": "User created successfully",
                "user": {
                    "id": user_id,
                    "name": data.get("name"),
                    "email": data.get("email")
                },
                "timestamp": asyncio.get_event_loop().time()
            }, status=201)
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to create user: {str(e)}"}, 
                status=400
            )
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """健康检查处理器"""
        return web.json_response({
            "status": "healthy",
            "service": "Mock Web Server",
            "port": self.port,
            "requests": self._request_count,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def stop(self):
        """停止服务器"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logging.info("Mock Web server stopped")


# Pytest fixtures
@pytest.fixture
async def mock_vnc_server():
    """Mock VNC 服务器 fixture"""
    server = MockVNCServer()
    server_url = await server.start()
    
    yield server, server_url
    
    await server.stop()


@pytest.fixture
async def mock_web_server():
    """Mock Web 服务器 fixture"""
    server = MockWebServer()
    server_url = await server.start()
    
    yield server, server_url
    
    await server.stop()


@pytest.fixture
async def mock_services():
    """多个 mock 服务 fixture"""
    vnc_server = MockVNCServer()  # 使用随机端口
    web_server = MockWebServer()  # 使用随机端口
    
    vnc_url = await vnc_server.start()
    web_url = await web_server.start()
    
    yield {
        'vnc': (vnc_server, vnc_url),
        'web': (web_server, web_url)
    }
    
    await vnc_server.stop()
    await web_server.stop()
