"""
第一组 E2E 测试：Mock 环境

使用 mock daemon 和 mock HTTP 服务器进行端到端测试
重点测试预览链接功能
"""

import pytest
import pytest_asyncio
import asyncio
import aiohttp
import time
from unittest.mock import patch, Mock
from daemon_proxy import DaemonProxy
from daemon_proxy.client import DaemonProxyClient

from .fixtures.mock_daemon import MockDaemonServer
from .fixtures.mock_services import MockVNCServer, MockWebServer
from .scenarios.preview_scenarios import PreviewLinkTestScenarios, run_preview_link_scenarios


@pytest.mark.e2e_mock
class TestE2EMock:
    """Mock 环境 E2E 测试"""
    
    @pytest_asyncio.fixture
    async def mock_environment(self, mock_config):
        """Mock 测试环境"""
        # 启动 mock daemon
        mock_daemon = MockDaemonServer()
        daemon_url = await mock_daemon.start()
        
        # 启动 mock 服务（使用随机端口）
        mock_vnc = MockVNCServer()
        mock_web = MockWebServer()
        
        vnc_url = await mock_vnc.start()
        web_url = await mock_web.start()
        
        # 注册目标服务到 mock daemon
        mock_daemon.register_target_service(mock_vnc.port, vnc_url)
        mock_daemon.register_target_service(mock_web.port, web_url)
        
        # 启动 daemon-proxy
        with patch('daemon_proxy.daemon.DaemonManager._get_daemon_url', return_value=daemon_url):
            proxy = DaemonProxy(mock_config)
            await proxy.start()
            
            try:
                proxy_port = proxy.site._server.sockets[0].getsockname()[1]
                proxy_url = f"http://127.0.0.1:{proxy_port}"
                
                yield {
                    'proxy': proxy,
                    'proxy_url': proxy_url,
                    'daemon': mock_daemon,
                    'daemon_url': daemon_url,
                    'vnc': mock_vnc,
                    'vnc_url': vnc_url,
                    'web': mock_web,
                    'web_url': web_url
                }
            finally:
                await proxy.stop()
                await mock_daemon.stop()
                await mock_vnc.stop()
                await mock_web.stop()
    
    @pytest.mark.asyncio
    async def test_mock_environment_setup(self, mock_environment):
        """测试 Mock 环境设置"""
        env = mock_environment
        
        # 验证所有服务都启动成功
        assert env['proxy'] is not None
        assert env['daemon'] is not None
        assert env['vnc'] is not None
        assert env['web'] is not None
        
        # 验证端口
        assert env['proxy_url'].startswith('http://127.0.0.1:')
        assert env['daemon_url'].startswith('http://127.0.0.1:')
        assert env['vnc_url'].startswith('http://127.0.0.1:')
        assert env['web_url'].startswith('http://127.0.0.1:')
    
    @pytest.mark.asyncio
    async def test_daemon_proxy_health_check(self, mock_environment):
        """测试 daemon-proxy 健康检查"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
                assert "uptime" in data
                assert "request_count" in data
                assert "daemon" in data
    
    @pytest.mark.asyncio
    async def test_daemon_status(self, mock_environment):
        """测试 daemon 状态检查"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/daemon/status") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "running"
                assert "version" in data
                assert "url" in data
    
    @pytest.mark.asyncio
    async def test_proxy_basic_functionality(self, mock_environment):
        """测试基本代理功能"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            # 测试代理到 VNC 服务
            vnc_port = env['vnc'].port
            async with session.get(f"{proxy_url}/proxy/{vnc_port}/") as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "VNC"
                assert data["port"] == vnc_port
            
            # 测试代理到 Web 服务
            web_port = env['web'].port
            async with session.get(f"{proxy_url}/proxy/{web_port}/") as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "Web"
                assert data["port"] == web_port
    
    @pytest.mark.asyncio
    async def test_preview_link_creation_vnc(self, mock_environment):
        """测试 VNC 预览链接创建"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        vnc_port = env['vnc'].port
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_create_and_access_preview_link(vnc_port)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["port"] == vnc_port
        assert result["link"] is not None
        assert result["link"].port == vnc_port
        assert result["link"].url.startswith(f"{proxy_url}/preview/")
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_preview_link_creation_web(self, mock_environment):
        """测试 Web 预览链接创建"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        web_port = env['web'].port
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_create_and_access_preview_link(web_port)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["port"] == web_port
        assert result["link"] is not None
        assert result["link"].port == web_port
        assert result["link"].url.startswith(f"{proxy_url}/preview/")
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_preview_link_lifecycle(self, mock_environment):
        """测试预览链接生命周期"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        web_port = env['web'].port
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_preview_link_lifecycle(web_port)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["revoked"] is True
        assert result["access_after_revoke"] is True  # 撤销后应该无法访问
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_preview_links(self, mock_environment):
        """测试多个预览链接管理"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        vnc_port = env['vnc'].port
        web_port = env['web'].port
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_multiple_preview_links([vnc_port, web_port, 3000])
        
        assert len(result["created_links"]) >= 2  # 至少 VNC 和 Web 应该成功
        assert result["stats"] is not None
        assert result["stats"]["total_links"] >= 2
        assert result["concurrent_access"]["successful"] >= 2
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_preview_link_error_handling(self, mock_environment):
        """测试预览链接错误处理"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_preview_link_error_handling()
        
        assert result["invalid_token_access"] is True
        assert result["nonexistent_port"] is True
        assert result["malformed_requests"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_preview_link_different_ports(self, mock_environment):
        """测试不同端口的预览链接"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_preview_link_with_different_ports()
        
        # 至少 VNC 和 Web 端口应该成功
        assert result["summary"]["successful"] >= 2
        vnc_port = env['vnc'].port
        web_port = env['web'].port
        assert result["summary"]["total"] == 5
        assert vnc_port in result["port_results"]
        assert web_port in result["port_results"]
        assert result["port_results"][vnc_port]["created"] is True
        assert result["port_results"][web_port]["created"] is True
    
    @pytest.mark.asyncio
    async def test_preview_link_stats(self, mock_environment):
        """测试预览链接统计功能"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            # 创建一些预览链接
            vnc_port = env['vnc'].port
            web_port = env['web'].port
            async with DaemonProxyClient(proxy_url) as client:
                vnc_link = await client.get_preview_link(vnc_port)
                web_link = await client.get_preview_link(web_port)
                
                # 获取统计信息
                stats = await client.get_preview_stats()
                
                assert stats["total_links"] >= 2
                assert stats["active_links"] >= 2
                assert stats["expired_links"] >= 0
                
                # 撤销一个链接
                await client.revoke_preview_link(vnc_link.token)
                
                # 再次获取统计信息
                stats_after = await client.get_preview_stats()
                assert stats_after["total_links"] < stats["total_links"]
    
    @pytest.mark.asyncio
    async def test_preview_link_concurrent_access(self, mock_environment):
        """测试预览链接并发访问"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with DaemonProxyClient(proxy_url) as client:
            # 创建预览链接
            vnc_port = env['vnc'].port
            web_port = env['web'].port
            vnc_link = await client.get_preview_link(vnc_port)
            web_link = await client.get_preview_link(web_port)
            
            # 并发访问
            async def access_link(session, link):
                async with session.get(link.url) as response:
                    return {
                        "port": link.port,
                        "status": response.status,
                        "success": response.status == 200
                    }
            
            async with aiohttp.ClientSession() as session:
                tasks = [
                    access_link(session, vnc_link),
                    access_link(session, web_link),
                    access_link(session, vnc_link),  # 重复访问
                    access_link(session, web_link)   # 重复访问
                ]
                
                results = await asyncio.gather(*tasks)
                
                # 验证所有访问都成功
                for result in results:
                    assert result["success"] is True
                    assert result["status"] == 200
    
    @pytest.mark.asyncio
    async def test_preview_link_with_authentication(self, base_config):
        """测试带认证的预览链接"""
        # 设置 mock 模式
        base_config.set("daemon.mode", "mock")
        # 启用认证
        base_config.set("security.enabled", True)
        base_config.set("security.api_key", "test-secret-key")
        
        # 启动新的带认证的环境
        mock_daemon = MockDaemonServer()
        daemon_url = await mock_daemon.start()
        
        mock_vnc = MockVNCServer()
        mock_web = MockWebServer()
        
        vnc_url = await mock_vnc.start()
        web_url = await mock_web.start()
        
        mock_daemon.register_target_service(mock_vnc.port, vnc_url)
        mock_daemon.register_target_service(mock_web.port, web_url)
        
        with patch('daemon_proxy.daemon.DaemonManager._get_daemon_url', return_value=daemon_url):
            proxy = DaemonProxy(base_config)
            await proxy.start()
            
            try:
                proxy_port = proxy.site._server.sockets[0].getsockname()[1]
                proxy_url = f"http://127.0.0.1:{proxy_port}"
                
                # 测试无认证访问（应该失败）
                web_port = mock_web.port
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{proxy_url}/proxy/{web_port}/") as response:
                        assert response.status == 401
                
                # 测试带认证访问（应该成功）
                async with DaemonProxyClient(proxy_url, "test-secret-key") as client:
                    link = await client.get_preview_link(web_port)
                    assert link is not None
                    assert link.port == web_port
                    
            finally:
                await proxy.stop()
                await mock_daemon.stop()
                await mock_vnc.stop()
                await mock_web.stop()
    
    @pytest.mark.asyncio
    async def test_full_preview_link_scenarios(self, mock_environment):
        """运行完整的预览链接测试场景"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        # 运行所有预览链接测试场景
        results = await run_preview_link_scenarios(proxy_url)
        
        # 验证总体结果
        assert results["summary"]["total_scenarios"] > 0
        assert results["summary"]["successful_scenarios"] > 0
        assert results["summary"]["success_rate"] > 0.5  # 至少50%成功率
        
        # 验证关键场景
        assert "create_and_access" in results["scenarios"]
        assert "lifecycle" in results["scenarios"]
        assert "multiple_links" in results["scenarios"]
        assert "error_handling" in results["scenarios"]
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, mock_environment):
        """测试指标端点"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/metrics") as response:
                assert response.status == 200
                text = await response.text()
                
                # 验证 Prometheus 格式的指标
                assert "daemon_proxy_uptime_seconds" in text
                assert "daemon_proxy_requests_total" in text
                assert "daemon_proxy_errors_total" in text
                assert "daemon_proxy_daemon_running" in text
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, mock_environment):
        """测试根端点"""
        env = mock_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/") as response:
                assert response.status == 200
                data = await response.json()
                
                assert data["service"] == "Daemon Proxy"
                assert data["version"] == "1.0.0"
                assert "endpoints" in data
                assert "daemon_url" in data
                
                # 验证端点列表
                endpoints = data["endpoints"]
                assert "proxy" in endpoints
                assert "preview" in endpoints
                assert "health" in endpoints
                assert "metrics" in endpoints
