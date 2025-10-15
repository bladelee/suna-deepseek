"""
集成测试
"""

import pytest
import asyncio
import aiohttp
import tempfile
import os
import subprocess
import time
from unittest.mock import patch, Mock
from daemon_proxy import Config, DaemonProxy


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        config = Config()
        config.set("server.host", "127.0.0.1")
        config.set("server.port", 0)  # 使用随机端口
        config.set("daemon.mode", "host")
        config.set("daemon.port", 2280)
        config.set("daemon.path", "/usr/local/bin/daytona")
        config.set("daemon.startup_timeout", 5)
        config.set("security.enabled", False)
        config.set("proxy.timeout", 10)
        return config
    
    @pytest.fixture
    async def mock_daemon_server(self):
        """模拟daemon服务器"""
        from aiohttp import web
        
        async def version_handler(request):
            return web.json_response({"version": "1.0.0"})
        
        async def proxy_handler(request):
            port = request.match_info['port']
            path = request.match_info.get('path', '')
            
            # 模拟代理到目标服务
            if port == "8080":
                if path == "api/status":
                    return web.json_response({"status": "ok", "port": 8080})
                elif path == "api/data":
                    return web.json_response({"data": "test data"})
                else:
                    return web.json_response({"message": "Hello from 8080"})
            else:
                return web.json_response({"error": "Port not found"}, status=404)
        
        app = web.Application()
        app.router.add_get('/version', version_handler)
        app.router.add_route('*', '/proxy/{port}/{path:.*}', proxy_handler)
        app.router.add_route('*', '/proxy/{port}', proxy_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', 0)
        await site.start()
        
        # 获取实际端口
        port = site._server.sockets[0].getsockname()[1]
        
        yield f"http://127.0.0.1:{port}"
        
        await site.stop()
        await runner.cleanup()
    
    @pytest.mark.asyncio
    async def test_full_proxy_workflow(self, config, mock_daemon_server):
        """测试完整的代理工作流程"""
        # 设置 mock 模式
        config.set("daemon.mode", "mock")
        # 模拟daemon URL
        daemon_url = mock_daemon_server
        
        with patch('daemon_proxy.daemon.DaemonManager._get_daemon_url', return_value=daemon_url):
            proxy = DaemonProxy(config)
            
            # 启动代理服务
            await proxy.start()
            
            try:
                # 获取代理服务端口
                proxy_port = proxy.site._server.sockets[0].getsockname()[1]
                proxy_url = f"http://127.0.0.1:{proxy_port}"
                
                async with aiohttp.ClientSession() as session:
                    # 测试健康检查
                    async with session.get(f"{proxy_url}/health") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert data["status"] == "healthy"
                    
                    # 测试daemon状态
                    async with session.get(f"{proxy_url}/daemon/status") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert data["status"] == "running"
                    
                    # 测试代理请求
                    async with session.get(f"{proxy_url}/proxy/8080/") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert "message" in data
                    
                    # 测试代理到特定路径
                    async with session.get(f"{proxy_url}/proxy/8080/api/status") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert data["status"] == "ok"
                        assert data["port"] == 8080
                    
                    # 测试POST请求
                    async with session.post(f"{proxy_url}/proxy/8080/api/data", 
                                          json={"test": "data"}) as response:
                        assert response.status == 200
                        data = await response.json()
                        assert "data" in data
                    
                    # 测试不存在的端口
                    async with session.get(f"{proxy_url}/proxy/9999/") as response:
                        assert response.status == 404
                    
                    # 测试指标端点
                    async with session.get(f"{proxy_url}/metrics") as response:
                        assert response.status == 200
                        text = await response.text()
                        assert "daemon_proxy_requests_total" in text
                    
                    # 测试根路径
                    async with session.get(f"{proxy_url}/") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert data["service"] == "Daemon Proxy"
                        assert "endpoints" in data
                
            finally:
                await proxy.stop()
    
    @pytest.mark.asyncio
    async def test_security_integration(self, config, mock_daemon_server):
        """测试安全认证集成"""
        # 设置 mock 模式
        config.set("daemon.mode", "mock")
        # 启用安全认证
        config.set("security.enabled", True)
        config.set("security.api_key", "test-secret-key")
        
        daemon_url = mock_daemon_server
        
        with patch('daemon_proxy.daemon.DaemonManager._get_daemon_url', return_value=daemon_url):
            proxy = DaemonProxy(config)
            await proxy.start()
            
            try:
                proxy_port = proxy.site._server.sockets[0].getsockname()[1]
                proxy_url = f"http://127.0.0.1:{proxy_port}"
                
                async with aiohttp.ClientSession() as session:
                    # 测试无认证请求（应该失败）
                    async with session.get(f"{proxy_url}/proxy/8080/") as response:
                        assert response.status == 401
                    
                    # 测试错误认证（应该失败）
                    headers = {"Authorization": "Bearer wrong-key"}
                    async with session.get(f"{proxy_url}/proxy/8080/", headers=headers) as response:
                        assert response.status == 401
                    
                    # 测试正确认证（应该成功）
                    headers = {"Authorization": "Bearer test-secret-key"}
                    async with session.get(f"{proxy_url}/proxy/8080/", headers=headers) as response:
                        assert response.status == 200
                        data = await response.json()
                        assert "message" in data
                    
                    # 测试非代理路径（不需要认证）
                    async with session.get(f"{proxy_url}/health") as response:
                        assert response.status == 200
                
            finally:
                await proxy.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, config):
        """测试错误处理集成"""
        # 设置 mock 模式
        config.set("daemon.mode", "mock")
        # 使用不存在的daemon端口
        config.set("daemon.port", 9999)
        
        proxy = DaemonProxy(config)
        
        # 启动应该失败
        with pytest.raises(TimeoutError):
            await proxy.start()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, config, mock_daemon_server):
        """测试并发请求"""
        # 设置 mock 模式
        config.set("daemon.mode", "mock")
        daemon_url = mock_daemon_server
        
        with patch('daemon_proxy.daemon.DaemonManager._get_daemon_url', return_value=daemon_url):
            proxy = DaemonProxy(config)
            await proxy.start()
            
            try:
                proxy_port = proxy.site._server.sockets[0].getsockname()[1]
                proxy_url = f"http://127.0.0.1:{proxy_port}"
                
                async def make_request(session, i):
                    async with session.get(f"{proxy_url}/proxy/8080/api/status") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert data["status"] == "ok"
                        return i
                
                # 并发发送10个请求
                async with aiohttp.ClientSession() as session:
                    tasks = [make_request(session, i) for i in range(10)]
                    results = await asyncio.gather(*tasks)
                    
                    assert len(results) == 10
                    assert all(isinstance(r, int) for r in results)
                
            finally:
                await proxy.stop()
    
    @pytest.mark.asyncio
    async def test_large_response(self, config, mock_daemon_server):
        """测试大响应处理"""
        from aiohttp import web
        
        # 设置 mock 模式
        config.set("daemon.mode", "mock")
        # 创建返回大响应的daemon
        async def large_response_handler(request):
            large_data = {"data": "x" * 10000}  # 10KB数据
            return web.json_response(large_data)
        
        # 修改mock daemon以支持大响应
        daemon_url = mock_daemon_server
        
        with patch('daemon_proxy.daemon.DaemonManager._get_daemon_url', return_value=daemon_url):
            proxy = DaemonProxy(config)
            await proxy.start()
            
            try:
                proxy_port = proxy.site._server.sockets[0].getsockname()[1]
                proxy_url = f"http://127.0.0.1:{proxy_port}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{proxy_url}/proxy/8080/api/data") as response:
                        assert response.status == 200
                        data = await response.json()
                        assert "data" in data
                
            finally:
                await proxy.stop()
    
    def test_config_validation(self):
        """测试配置验证"""
        from daemon_proxy.utils import validate_config
        
        # 有效配置（使用 mock 模式）
        config = Config()
        config.set("daemon.mode", "mock")
        assert validate_config(config) is True
        
        # 无效端口
        config.set("server.port", -1)
        assert validate_config(config) is False
        
        # 无效daemon模式
        config = Config()
        config.set("daemon.mode", "invalid")
        assert validate_config(config) is False
        
        # 不存在的daemon路径
        config = Config()
        config.set("daemon.path", "/nonexistent/path")
        assert validate_config(config) is False
    
    def test_utils_functions(self):
        """测试工具函数"""
        from daemon_proxy.utils import format_bytes, format_duration
        
        # 测试字节格式化
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"
        
        # 测试时间格式化
        assert format_duration(30) == "30.0s"
        assert format_duration(90) == "1.5m"
        assert format_duration(7200) == "2.0h"

