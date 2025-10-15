"""
代理服务模块测试
"""

import pytest
import pytest_asyncio
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from aiohttp import web
from daemon_proxy.config import Config
from daemon_proxy.proxy import DaemonProxy


class TestDaemonProxy:
    """代理服务测试"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        config = Config()
        config.set("server.host", "127.0.0.1")
        config.set("server.port", 8080)
        config.set("daemon.mode", "host")
        config.set("daemon.port", 2280)
        config.set("security.enabled", False)
        config.set("proxy.timeout", 30)
        return config
    
    @pytest.fixture
    def secure_config(self):
        """安全配置"""
        config = Config()
        config.set("server.host", "127.0.0.1")
        config.set("server.port", 8080)
        config.set("daemon.mode", "host")
        config.set("daemon.port", 2280)
        config.set("security.enabled", True)
        config.set("security.api_key", "test-key")
        config.set("proxy.timeout", 30)
        return config
    
    @pytest.fixture
    def proxy(self, config):
        """代理服务实例"""
        return DaemonProxy(config)
    
    @pytest_asyncio.fixture
    async def started_proxy(self, config):
        """已启动的代理服务实例"""
        proxy = DaemonProxy(config)
        with patch.object(proxy.daemon_manager, 'start', new_callable=AsyncMock) as mock_start:
            await proxy.start()
            yield proxy
            await proxy.stop()
    
    def test_init(self, config):
        """测试初始化"""
        proxy = DaemonProxy(config)
        
        assert proxy.config == config
        assert proxy.daemon_manager is not None
        assert proxy.app is None
        assert proxy.runner is None
        assert proxy.site is None
        assert proxy._start_time > 0
        assert proxy._request_count == 0
        assert proxy._error_count == 0
    
    @pytest.mark.asyncio
    async def test_start(self, proxy):
        """测试启动服务"""
        with patch.object(proxy.daemon_manager, 'start', new_callable=AsyncMock) as mock_start:
            await proxy.start()
            
            assert proxy.app is not None
            assert proxy.runner is not None
            assert proxy.site is not None
            mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_proxy_handler_success(self, proxy):
        """测试代理处理器成功"""
        # 模拟请求
        request = Mock()
        request.match_info = {'port': '8080', 'path': 'api/data'}
        request.method = 'GET'
        request.headers = {'Content-Type': 'application/json'}
        request.can_read_body = False
        request.query_string = 'param=value'
        
        # 模拟daemon响应
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.read = AsyncMock(return_value=b'{"result": "success"}')
        
        with patch.object(proxy.daemon_manager, 'proxy_request', new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = mock_response
            
            response = await proxy.proxy_handler(request)
            
            assert isinstance(response, web.Response)
            assert response.status == 200
            assert response.body == b'{"result": "success"}'
            mock_proxy.assert_called_once_with(
                port='8080',
                path='api/data',
                method='GET',
                headers={'Content-Type': 'application/json'},
                data=None,
                query_string='param=value'
            )
    
    @pytest.mark.asyncio
    async def test_proxy_handler_with_body(self, proxy):
        """测试带请求体的代理处理器"""
        request = Mock()
        request.match_info = {'port': '8080', 'path': 'api/users'}
        request.method = 'POST'
        request.headers = {'Content-Type': 'application/json'}
        request.can_read_body = True
        request.read = AsyncMock(return_value=b'{"name": "test"}')
        request.query_string = ''
        
        mock_response = Mock()
        mock_response.status = 201
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.read = AsyncMock(return_value=b'{"id": 1}')
        
        with patch.object(proxy.daemon_manager, 'proxy_request', new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = mock_response
            
            response = await proxy.proxy_handler(request)
            
            assert response.status == 201
            assert response.body == b'{"id": 1}'
            mock_proxy.assert_called_once_with(
                port='8080',
                path='api/users',
                method='POST',
                headers={'Content-Type': 'application/json'},
                data=b'{"name": "test"}',
                query_string=''
            )
    
    @pytest.mark.asyncio
    async def test_proxy_handler_error(self, proxy):
        """测试代理处理器错误"""
        request = Mock()
        request.match_info = {'port': '8080', 'path': 'api/error'}
        request.method = 'GET'
        request.headers = {}
        request.can_read_body = False
        request.query_string = ''
        
        with patch.object(proxy.daemon_manager, 'proxy_request', new_callable=AsyncMock) as mock_proxy:
            mock_proxy.side_effect = Exception("Connection error")
            
            response = await proxy.proxy_handler(request)
            
            assert response.status == 502
            assert "Connection error" in response.text
    
    @pytest.mark.asyncio
    async def test_health_handler_healthy(self, started_proxy):
        """测试健康检查处理器 - 健康状态"""
        mock_status = {
            "status": "running",
            "version": "1.0.0",
            "url": "http://localhost:2280"
        }
        
        with patch.object(started_proxy.daemon_manager, 'get_daemon_status', new_callable=AsyncMock) as mock_status_func:
            mock_status_func.return_value = mock_status
            
            # 使用 aiohttp 测试客户端
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{started_proxy.site._server.sockets[0].getsockname()[1]}/health") as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data["status"] == "healthy"
                    assert data["daemon"] == mock_status
                    assert "uptime" in data
                    assert "request_count" in data
                    assert "error_count" in data
    
    @pytest.mark.asyncio
    async def test_health_handler_unhealthy(self, started_proxy):
        """测试健康检查处理器 - 不健康状态"""
        mock_status = {
            "status": "error",
            "error": "Connection failed",
            "url": "http://localhost:2280"
        }
        
        with patch.object(started_proxy.daemon_manager, 'get_daemon_status', new_callable=AsyncMock) as mock_status_func:
            mock_status_func.return_value = mock_status
            
            # 使用 aiohttp 测试客户端
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{started_proxy.site._server.sockets[0].getsockname()[1]}/health") as response:
                    assert response.status == 503
                    data = await response.json()
                    assert data["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_daemon_status_handler(self, started_proxy):
        """测试daemon状态处理器"""
        mock_status = {
            "status": "running",
            "version": "1.0.0",
            "url": "http://localhost:2280"
        }
        
        with patch.object(started_proxy.daemon_manager, 'get_daemon_status', new_callable=AsyncMock) as mock_status_func:
            mock_status_func.return_value = mock_status
            
            # 使用 aiohttp 测试客户端
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{started_proxy.site._server.sockets[0].getsockname()[1]}/daemon/status") as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data == mock_status
    
    @pytest.mark.asyncio
    async def test_metrics_handler(self, started_proxy):
        """测试指标处理器"""
        # 使用 aiohttp 测试客户端
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:{started_proxy.site._server.sockets[0].getsockname()[1]}/metrics") as response:
                assert response.status == 200
                assert response.headers['Content-Type'] == "text/plain; version=0.0.4; charset=utf-8"
                
                text = await response.text()
                assert "daemon_proxy_uptime_seconds" in text
                assert "daemon_proxy_requests_total" in text
                assert "daemon_proxy_errors_total" in text
                assert "daemon_proxy_daemon_running" in text
    
    @pytest.mark.asyncio
    async def test_root_handler(self, started_proxy):
        """测试根路径处理器"""
        # 使用 aiohttp 测试客户端
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:{started_proxy.site._server.sockets[0].getsockname()[1]}/") as response:
                assert response.status == 200
                data = await response.json()
                
                assert data["service"] == "Daemon Proxy"
                assert data["version"] == "1.0.0"
                assert "endpoints" in data
                assert "daemon_url" in data
    
    @pytest.mark.asyncio
    async def test_auth_middleware_success(self, secure_config):
        """测试认证中间件成功"""
        proxy = DaemonProxy(secure_config)
        
        request = Mock()
        request.path = "/proxy/8080/api"
        request.headers = {"Authorization": "Bearer test-key"}
        
        handler = AsyncMock(return_value=web.Response(text="OK"))
        
        middleware = proxy._auth_middleware
        response = await middleware(request, handler)
        
        assert response.text == "OK"
        handler.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_auth_middleware_failure(self, secure_config):
        """测试认证中间件失败"""
        proxy = DaemonProxy(secure_config)
        
        request = Mock()
        request.path = "/proxy/8080/api"
        request.headers = {"Authorization": "Bearer wrong-key"}
        
        handler = AsyncMock()
        
        middleware = proxy._auth_middleware
        response = await middleware(request, handler)
        
        assert response.status == 401
        assert "Unauthorized" in response.text
        handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auth_middleware_no_auth(self, secure_config):
        """测试认证中间件无认证头"""
        proxy = DaemonProxy(secure_config)
        
        request = Mock()
        request.path = "/proxy/8080/api"
        request.headers = {}
        
        handler = AsyncMock()
        
        middleware = proxy._auth_middleware
        response = await middleware(request, handler)
        
        assert response.status == 401
        handler.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auth_middleware_non_proxy_path(self, secure_config):
        """测试认证中间件非代理路径"""
        proxy = DaemonProxy(secure_config)
        
        request = Mock()
        request.path = "/health"
        request.headers = {}
        
        handler = AsyncMock(return_value=web.Response(text="OK"))
        
        middleware = proxy._auth_middleware
        response = await middleware(request, handler)
        
        assert response.text == "OK"
        handler.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_logging_middleware(self, proxy):
        """测试日志中间件"""
        request = Mock()
        request.method = "GET"
        request.path_qs = "/proxy/8080/api"
        
        handler = AsyncMock(return_value=web.Response(text="OK"))
        
        middleware = proxy._logging_middleware
        response = await middleware(request, handler)
        
        assert response.text == "OK"
        assert proxy._request_count == 1
        assert proxy._error_count == 0
        handler.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_logging_middleware_error(self, proxy):
        """测试日志中间件错误"""
        request = Mock()
        request.method = "GET"
        request.path_qs = "/proxy/8080/api"
        
        handler = AsyncMock(side_effect=Exception("Test error"))
        
        middleware = proxy._logging_middleware
        
        with pytest.raises(Exception, match="Test error"):
            await middleware(request, handler)
        
        assert proxy._request_count == 1
        assert proxy._error_count == 1
    
    @pytest.mark.asyncio
    async def test_error_middleware(self, proxy):
        """测试错误处理中间件"""
        request = Mock()
        handler = AsyncMock(side_effect=Exception("Test error"))
        
        middleware = proxy._error_middleware
        response = await middleware(request, handler)
        
        assert response.status == 500
        assert "Test error" in response.text
    
    @pytest.mark.asyncio
    async def test_stop(self, proxy):
        """测试停止服务"""
        proxy.site = AsyncMock()
        proxy.runner = AsyncMock()
        
        with patch.object(proxy.daemon_manager, 'stop', new_callable=AsyncMock) as mock_stop:
            await proxy.stop()
            
            proxy.site.stop.assert_called_once()
            proxy.runner.cleanup.assert_called_once()
            mock_stop.assert_called_once()
    
    def test_is_running_property(self, proxy):
        """测试is_running属性"""
        # 直接测试属性，不需要 patch
        assert proxy.is_running == proxy.daemon_manager.is_running

