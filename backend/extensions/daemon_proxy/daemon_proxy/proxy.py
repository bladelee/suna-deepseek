"""
代理服务模块
"""

import asyncio
import aiohttp
import logging
import time
from typing import Optional, Dict, Any
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response
from .config import Config
from .daemon import DaemonManager
from .preview import PreviewLinkManager, PreviewHandler


class DaemonProxy:
    """Daemon代理服务"""
    
    def __init__(self, config: Config):
        self.config = config
        self.daemon_manager = DaemonManager(config)
        self.preview_manager = PreviewLinkManager(config)
        self.preview_handler = PreviewHandler(self.preview_manager, self.daemon_manager)
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        
    async def start(self):
        """启动代理服务"""
        # 启动daemon
        await self.daemon_manager.start()
        
        # 启动预览链接管理器
        await self.preview_manager.start()
        
        # 创建web应用
        self.app = web.Application()
        self._setup_routes()
        self._setup_middleware()
        
        # 启动web服务器
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(
            self.runner, 
            self.config.server_host, 
            self.config.server_port
        )
        
        await self.site.start()
        
        # 获取实际端口并更新预览链接管理器
        actual_port = self.site._server.sockets[0].getsockname()[1]
        self.preview_manager.config.set("server.port", actual_port)
        
        logging.info(f"Daemon proxy started on {self.config.server_host}:{actual_port}")
    
    def _setup_routes(self):
        """设置路由"""
        # 代理路由
        self.app.router.add_route('*', '/proxy/{port}/{path:.*}', self.proxy_handler)
        self.app.router.add_route('*', '/proxy/{port}', self.proxy_handler)
        
        # 预览链接路由
        self.app.router.add_route('*', '/preview/{token}/{path:.*}', self.preview_handler.handle_preview_request)
        self.app.router.add_route('*', '/preview/{token}', self.preview_handler.handle_preview_request)
        
        # 预览链接管理路由
        self.app.router.add_post('/api/preview/create', self.create_preview_link_handler)
        self.app.router.add_get('/api/preview/stats', self.preview_stats_handler)
        self.app.router.add_delete('/api/preview/{token}', self.revoke_preview_link_handler)
        
        # 健康检查路由
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/daemon/status', self.daemon_status_handler)
        self.app.router.add_get('/metrics', self.metrics_handler)
        
        # 根路径
        self.app.router.add_get('/', self.root_handler)
    
    def _setup_middleware(self):
        """设置中间件"""
        # 认证中间件
        if self.config.security_enabled:
            self.app.middlewares.append(self._auth_middleware)
        
        # 日志中间件
        self.app.middlewares.append(self._logging_middleware)
        
        # 错误处理中间件
        self.app.middlewares.append(self._error_middleware)
    
    @web.middleware
    async def _auth_middleware(self, request: Request, handler):
        """认证中间件"""
        if request.path.startswith('/proxy/'):
            auth_header = request.headers.get('Authorization')
            expected_auth = f"Bearer {self.config.security_api_key}"
            
            if not auth_header or auth_header != expected_auth:
                return web.Response(
                    text="Unauthorized",
                    status=401,
                    headers={'WWW-Authenticate': 'Bearer'}
                )
        
        return await handler(request)
    
    @web.middleware
    async def _logging_middleware(self, request: Request, handler):
        """日志中间件"""
        start_time = time.time()
        self._request_count += 1
        
        # 记录请求
        logging.info(f"Request: {request.method} {request.path_qs}")
        
        try:
            response = await handler(request)
            
            # 记录响应
            duration = time.time() - start_time
            logging.info(f"Response: {response.status} in {duration:.3f}s")
            
            return response
            
        except Exception as e:
            self._error_count += 1
            duration = time.time() - start_time
            logging.error(f"Error: {e} in {duration:.3f}s")
            raise
    
    @web.middleware
    async def _error_middleware(self, request: Request, handler):
        """错误处理中间件"""
        try:
            return await handler(request)
        except Exception as e:
            logging.error(f"Unhandled error: {e}")
            return web.Response(
                text=f"Internal Server Error: {str(e)}",
                status=500
            )
    
    async def proxy_handler(self, request: Request) -> Response:
        """代理请求处理器"""
        port = request.match_info['port']
        path = request.match_info.get('path', '')
        
        # 准备请求数据
        headers = dict(request.headers)
        body = None
        if request.can_read_body:
            body = await request.read()
        
        # 直接使用请求的端口，不需要端口映射
        target_port = port
        
        try:
            # 代理请求到daemon
            response = await self.daemon_manager.proxy_request(
                port=target_port,
                path=path,
                method=request.method,
                headers=headers,
                data=body,
                query_string=request.query_string
            )
            
            # 读取响应体
            response_body = await response.read()
            
            # 创建响应
            return web.Response(
                body=response_body,
                status=response.status,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            logging.error(f"Proxy error for {port}/{path}: {e}")
            return web.Response(
                text=f"Proxy error: {str(e)}",
                status=502
            )
    
    async def health_handler(self, request: Request) -> Response:
        """健康检查处理器"""
        daemon_status = await self.daemon_manager.get_daemon_status()
        
        health_data = {
            "status": "healthy" if daemon_status["status"] == "running" else "unhealthy",
            "uptime": time.time() - self._start_time,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "daemon": daemon_status
        }
        
        status_code = 200 if health_data["status"] == "healthy" else 503
        
        return web.json_response(health_data, status=status_code)
    
    async def daemon_status_handler(self, request: Request) -> Response:
        """Daemon状态处理器"""
        status = await self.daemon_manager.get_daemon_status()
        return web.json_response(status)
    
    async def metrics_handler(self, request: Request) -> Response:
        """指标处理器"""
        metrics = {
            "daemon_proxy_uptime_seconds": time.time() - self._start_time,
            "daemon_proxy_requests_total": self._request_count,
            "daemon_proxy_errors_total": self._error_count,
            "daemon_proxy_daemon_running": 1 if self.daemon_manager.is_running else 0
        }
        
        # 简单的Prometheus格式
        metrics_text = "\n".join([
            f"# HELP {key} {key.replace('_', ' ').title()}"
            f"# TYPE {key} gauge"
            f"{key} {value}"
            for key, value in metrics.items()
        ])
        
        response = web.Response(
            text=metrics_text,
            content_type="text/plain; version=0.0.4"
        )
        response.charset = 'utf-8'
        return response
    
    async def create_preview_link_handler(self, request: Request) -> Response:
        """创建预览链接处理器"""
        try:
            data = await request.json()
            port = data.get('port')
            
            if not port:
                return web.json_response(
                    {"error": "Port is required"}, 
                    status=400
                )
            
            # 创建预览链接
            link = await self.preview_manager.get_preview_link(port)
            
            return web.json_response({
                "url": link.url,
                "token": link.token,
                "port": link.port,
                "expires_at": link.expires_at
            })
            
        except Exception as e:
            logging.error(f"Error creating preview link: {e}")
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )
    
    async def preview_stats_handler(self, request: Request) -> Response:
        """预览链接统计处理器"""
        stats = self.preview_manager.get_stats()
        return web.json_response(stats)
    
    async def revoke_preview_link_handler(self, request: Request) -> Response:
        """撤销预览链接处理器"""
        token = request.match_info['token']
        
        if self.preview_manager.revoke_link(token):
            return web.json_response({"message": "Preview link revoked"})
        else:
            return web.json_response(
                {"error": "Preview link not found"}, 
                status=404
            )
    
    async def root_handler(self, request: Request) -> Response:
        """根路径处理器"""
        info = {
            "service": "Daemon Proxy",
            "version": "1.0.0",
            "endpoints": {
                "proxy": "/proxy/{port}/{path}",
                "preview": "/preview/{token}/{path}",
                "preview_create": "/api/preview/create",
                "preview_stats": "/api/preview/stats",
                "health": "/health",
                "daemon_status": "/daemon/status",
                "metrics": "/metrics"
            },
            "daemon_url": self.daemon_manager.daemon_url
        }
        
        return web.json_response(info)
    
    async def stop(self):
        """停止代理服务"""
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        await self.preview_manager.stop()
        await self.daemon_manager.stop()
        
        logging.info("Daemon proxy stopped")
    
    @property
    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self.daemon_manager.is_running
