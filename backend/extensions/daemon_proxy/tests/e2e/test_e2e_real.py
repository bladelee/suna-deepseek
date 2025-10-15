"""
第二组 E2E 测试：真实 Daemon 环境

使用真实编译的 daemon 进程和 mock HTTP 服务器进行端到端测试
重点测试预览链接功能与真实 daemon 的集成
"""

import pytest
import pytest_asyncio
import asyncio
import aiohttp
import time
import os
import subprocess
import signal
from pathlib import Path
from daemon_proxy import DaemonProxy
from daemon_proxy.client import DaemonProxyClient

from .fixtures.mock_services import MockVNCServer, MockWebServer
from .fixtures.daemon_manager import DaemonManager, daemon_manager, real_daemon_url
from .scenarios.preview_scenarios import PreviewLinkTestScenarios, run_preview_link_scenarios


@pytest.mark.e2e_real
class TestE2EReal:
    """真实 Daemon 环境 E2E 测试"""
    
    @pytest.fixture
    def check_daemon_requirements(self):
        """检查 daemon 环境要求"""
        # 优先使用编译的 daemon
        compiled_daemon = "/home/sa/agenthome/extentions/daemon-proxy/tests/e2e/bin/daytona-daemon"
        system_daemon = "/usr/local/bin/daytona"
        
        if os.path.exists(compiled_daemon) and os.access(compiled_daemon, os.X_OK):
            return compiled_daemon
        elif os.path.exists(system_daemon) and os.access(system_daemon, os.X_OK):
            return system_daemon
        else:
            pytest.skip(
                f"Neither compiled daemon ({compiled_daemon}) nor system daemon ({system_daemon}) found. "
                f"Run './tests/e2e/scripts/build_daemon.sh' to compile daemon."
            )
    
    @pytest_asyncio.fixture
    async def real_daemon_environment(self, real_daemon_config, daemon_manager, real_daemon_url):
        """真实 daemon 测试环境"""
        # 启动 mock 服务
        mock_vnc = MockVNCServer(6080)
        mock_web = MockWebServer(8080)
        
        vnc_url = await mock_vnc.start()
        web_url = await mock_web.start()
        
        # 配置 daemon-proxy 连接到真实 daemon
        real_daemon_config.set("daemon.mode", "host")
        real_daemon_config.set("daemon.port", 2280)
        real_daemon_config.set("daemon.path", daemon_manager.daemon_binary)
        
        # 启动 daemon-proxy
        proxy = DaemonProxy(real_daemon_config)
        
        try:
            await proxy.start()
            proxy_port = proxy.site._server.sockets[0].getsockname()[1]
            proxy_url = f"http://127.0.0.1:{proxy_port}"
            
            yield {
                'proxy': proxy,
                'proxy_url': proxy_url,
                'daemon_url': real_daemon_url,
                'daemon_manager': daemon_manager,
                'vnc': mock_vnc,
                'vnc_url': vnc_url,
                'web': mock_web,
                'web_url': web_url
            }
        finally:
            await proxy.stop()
            await mock_vnc.stop()
            await mock_web.stop()
    
    @pytest.mark.asyncio
    async def test_real_daemon_environment_setup(self, real_daemon_environment):
        """测试真实 daemon 环境设置"""
        env = real_daemon_environment
        
        # 验证所有服务都启动成功
        assert env['proxy'] is not None
        assert env['vnc'] is not None
        assert env['web'] is not None
        assert env['daemon_manager'] is not None
        
        # 验证端口
        assert env['proxy_url'].startswith('http://127.0.0.1:')
        assert env['vnc_url'].startswith('http://127.0.0.1:')
        assert env['web_url'].startswith('http://127.0.0.1:')
    
    @pytest.mark.asyncio
    async def test_real_daemon_health_check(self, real_daemon_environment):
        """测试真实 daemon 健康检查"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
                assert "uptime" in data
                assert "request_count" in data
                assert "daemon" in data
                
                # 验证 daemon 状态
                daemon_info = data["daemon"]
                assert daemon_info["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_real_daemon_status(self, real_daemon_environment):
        """测试真实 daemon 状态检查"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/daemon/status") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "running"
                assert "version" in data
                assert "url" in data
    
    @pytest.mark.asyncio
    async def test_real_daemon_proxy_functionality(self, real_daemon_environment):
        """测试真实 daemon 代理功能"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            # 测试代理到 VNC 服务
            async with session.get(f"{proxy_url}/proxy/6080/") as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "VNC"
                assert data["port"] == 6080
            
            # 测试代理到 Web 服务
            async with session.get(f"{proxy_url}/proxy/8080/") as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "Web"
                assert data["port"] == 8080
    
    @pytest.mark.asyncio
    async def test_real_daemon_preview_link_vnc(self, real_daemon_environment):
        """测试真实 daemon VNC 预览链接"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_create_and_access_preview_link(6080)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["port"] == 6080
        assert result["link"] is not None
        assert result["link"].port == 6080
        assert result["link"].url.startswith(f"{proxy_url}/preview/")
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_real_daemon_preview_link_web(self, real_daemon_environment):
        """测试真实 daemon Web 预览链接"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_create_and_access_preview_link(8080)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["port"] == 8080
        assert result["link"] is not None
        assert result["link"].port == 8080
        assert result["link"].url.startswith(f"{proxy_url}/preview/")
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_real_daemon_preview_link_lifecycle(self, real_daemon_environment):
        """测试真实 daemon 预览链接生命周期"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_preview_link_lifecycle(8080)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["revoked"] is True
        assert result["access_after_revoke"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_real_daemon_multiple_preview_links(self, real_daemon_environment):
        """测试真实 daemon 多个预览链接"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_multiple_preview_links([6080, 8080, 3000])
        
        assert len(result["created_links"]) >= 2
        assert result["stats"] is not None
        assert result["stats"]["total_links"] >= 2
        assert result["concurrent_access"]["successful"] >= 2
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_real_daemon_preview_link_performance(self, real_daemon_environment):
        """测试真实 daemon 预览链接性能"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        async with DaemonProxyClient(proxy_url) as client:
            # 测试创建多个预览链接的性能
            start_time = time.time()
            
            links = []
            for i in range(10):
                link = await client.get_preview_link(8080)
                links.append(link)
            
            creation_time = time.time() - start_time
            
            # 验证创建时间合理（应该在几秒内）
            assert creation_time < 10.0
            assert len(links) == 10
            
            # 测试并发访问性能
            async def access_link(session, link):
                start = time.time()
                async with session.get(link.url) as response:
                    return {
                        "status": response.status,
                        "response_time": time.time() - start
                    }
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                tasks = [access_link(session, link) for link in links[:5]]
                results = await asyncio.gather(*tasks)
            
            access_time = time.time() - start_time
            
            # 验证访问时间合理
            assert access_time < 5.0
            
            # 验证所有访问都成功
            for result in results:
                assert result["status"] == 200
                assert result["response_time"] < 2.0  # 单个请求应该在2秒内完成
    
    @pytest.mark.asyncio
    async def test_real_daemon_error_handling(self, real_daemon_environment):
        """测试真实 daemon 错误处理"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        async with aiohttp.ClientSession() as session:
            # 测试不存在的端口
            async with session.get(f"{proxy_url}/proxy/9999/") as response:
                # 应该返回 502 或 404（取决于 daemon 实现）
                assert response.status in [404, 502]
            
            # 测试无效的预览链接
            async with session.get(f"{proxy_url}/preview/invalid-token") as response:
                assert response.status == 404
    
    @pytest.mark.asyncio
    async def test_real_daemon_data_integrity(self, real_daemon_environment):
        """测试真实 daemon 数据传输完整性"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        # 测试 POST 请求的数据完整性
        test_data = {
            "test": "data",
            "number": 123,
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        async with aiohttp.ClientSession() as session:
            # 通过代理发送 POST 请求
            async with session.post(
                f"{proxy_url}/proxy/8080/api/data",
                json=test_data
            ) as response:
                assert response.status == 200
                response_data = await response.json()
                
                # 验证数据完整性
                assert response_data["received_data"] == test_data
                assert response_data["processed"] is True
    
    @pytest.mark.asyncio
    async def test_real_daemon_large_response(self, real_daemon_environment):
        """测试真实 daemon 大响应处理"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        # 创建一个较大的响应
        large_data = {"data": "x" * 10000}  # 10KB 数据
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{proxy_url}/proxy/8080/api/data",
                json=large_data
            ) as response:
                assert response.status == 200
                response_data = await response.json()
                
                # 验证大响应处理正确
                assert response_data["received_data"] == large_data
                assert response_data["processed"] is True
    
    @pytest.mark.asyncio
    async def test_real_daemon_concurrent_requests(self, real_daemon_environment):
        """测试真实 daemon 并发请求处理"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        async def make_request(session, i):
            async with session.get(f"{proxy_url}/proxy/8080/api/status") as response:
                return {
                    "request_id": i,
                    "status": response.status,
                    "data": await response.json() if response.status == 200 else None
                }
        
        # 并发发送 20 个请求
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, i) for i in range(20)]
            results = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            successful_requests = [r for r in results if r["status"] == 200]
            assert len(successful_requests) == 20
            
            # 验证响应数据一致性
            for result in successful_requests:
                assert result["data"]["service"] == "Web"
                assert result["data"]["port"] == 8080
    
    @pytest.mark.asyncio
    async def test_real_daemon_stability(self, real_daemon_environment):
        """测试真实 daemon 长时间运行稳定性"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        # 运行多个周期的预览链接创建和访问
        for cycle in range(3):
            async with DaemonProxyClient(proxy_url) as client:
                # 创建预览链接
                vnc_link = await client.get_preview_link(6080)
                web_link = await client.get_preview_link(8080)
                
                # 访问预览链接
                async with aiohttp.ClientSession() as session:
                    async with session.get(vnc_link.url) as response:
                        assert response.status == 200
                    
                    async with session.get(web_link.url) as response:
                        assert response.status == 200
                
                # 撤销链接
                await client.revoke_preview_link(vnc_link.token)
                await client.revoke_preview_link(web_link.token)
            
            # 短暂等待
            await asyncio.sleep(1)
    
    @pytest.mark.asyncio
    async def test_real_daemon_full_scenarios(self, real_daemon_environment):
        """运行真实 daemon 完整测试场景"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        # 运行所有预览链接测试场景
        results = await run_preview_link_scenarios(proxy_url)
        
        # 验证总体结果
        assert results["summary"]["total_scenarios"] > 0
        assert results["summary"]["successful_scenarios"] > 0
        assert results["summary"]["success_rate"] > 0.5
        
        # 验证关键场景
        assert "create_and_access" in results["scenarios"]
        assert "lifecycle" in results["scenarios"]
        assert "multiple_links" in results["scenarios"]
        assert "error_handling" in results["scenarios"]
    
    @pytest.mark.asyncio
    async def test_real_daemon_metrics(self, real_daemon_environment):
        """测试真实 daemon 指标收集"""
        env = real_daemon_environment
        proxy_url = env['proxy_url']
        
        # 生成一些请求
        async with aiohttp.ClientSession() as session:
            for _ in range(5):
                async with session.get(f"{proxy_url}/proxy/8080/") as response:
                    assert response.status == 200
        
        # 检查指标
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/metrics") as response:
                assert response.status == 200
                text = await response.text()
                
                # 验证指标存在
                assert "daemon_proxy_requests_total" in text
                assert "daemon_proxy_uptime_seconds" in text
                assert "daemon_proxy_daemon_running" in text
                
                # 验证请求计数
                lines = text.split('\n')
                for line in lines:
                    if 'daemon_proxy_requests_total' in line and not line.startswith('#'):
                        # 应该至少有我们发送的请求数
                        value = float(line.split()[-1])
                        assert value >= 5

    @pytest.mark.asyncio
    async def test_real_daemon_version(self, real_daemon_environment):
        """测试真实 daemon 版本信息"""
        env = real_daemon_environment
        daemon_url = env["daemon_url"]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{daemon_url}/version") as response:
                assert response.status == 200
                data = await response.json()
                assert "version" in data
                print(f"Real daemon version: {data['version']}")
    
    @pytest.mark.asyncio
    async def test_real_daemon_process_management(self, real_daemon_environment):
        """测试真实 daemon 进程管理"""
        env = real_daemon_environment
        daemon_manager = env["daemon_manager"]
        
        # 验证进程正在运行
        assert daemon_manager.is_running is True
        
        # 验证健康检查
        health = await daemon_manager.health_check()
        assert health["status"] == "healthy"
        assert health["running"] is True
        
        # 验证日志文件存在
        log_content = daemon_manager.get_log_content()
        assert len(log_content) > 0
        assert "daemon" in log_content.lower() or "started" in log_content.lower()

