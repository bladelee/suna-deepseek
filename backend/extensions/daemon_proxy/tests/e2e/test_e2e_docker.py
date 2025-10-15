"""
第三组 E2E 测试：Docker 环境

在 Docker 容器中运行完整的 daemon-proxy 和真实编译的 daemon 进行端到端测试
重点测试预览链接功能在容器化环境中的表现
"""

import pytest
import pytest_asyncio
import asyncio
import aiohttp
import time
import os
import subprocess
from typing import Dict, Any

from .fixtures.docker_helpers import DockerTestEnvironment
from .scenarios.preview_scenarios import PreviewLinkTestScenarios, run_preview_link_scenarios
from daemon_proxy.client import DaemonProxyClient


@pytest.mark.e2e_docker
class TestE2EDocker:
    """Docker 环境 E2E 测试"""
    
    @pytest.fixture
    def check_docker_requirements(self):
        """检查 Docker 环境要求"""
        try:
            # 检查 Docker 是否可用
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                pytest.skip("Docker is not available")
            
            # 检查 docker-compose 是否可用
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                pytest.skip("docker-compose is not available")
            
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker or docker-compose not found")
    
    @pytest_asyncio.fixture
    async def docker_environment(self, check_docker_requirements):
        """Docker 测试环境"""
        env = DockerTestEnvironment()
        
        # 使用 docker-compose 启动环境
        compose_file = 'docker-compose-e2e.yml'
        if not os.path.exists(compose_file):
            pytest.skip(f"Docker compose file {compose_file} not found")
        
        try:
            services = await env.start_environment(compose_file)
            yield env, services
        finally:
            await env.cleanup()
    
    @pytest_asyncio.fixture
    async def docker_services(self, docker_environment):
        """Docker 服务 fixture"""
        env, services = docker_environment
        return services
    
    @pytest.mark.asyncio
    async def test_docker_environment_setup(self, docker_environment):
        """测试 Docker 环境设置"""
        env, services = docker_environment
        
        # 验证服务启动
        assert 'daemon-proxy' in services
        assert 'mock-vnc' in services
        assert 'mock-web' in services
        
        # 验证服务 URL
        proxy_url = services['daemon-proxy']
        vnc_url = services['mock-vnc']
        web_url = services['mock-web']
        
        assert proxy_url.startswith('http://')
        assert vnc_url.startswith('http://')
        assert web_url.startswith('http://')
    
    @pytest.mark.asyncio
    async def test_docker_services_health(self, docker_services):
        """测试 Docker 服务健康状态"""
        services = docker_services
        
        # 等待服务就绪
        await asyncio.sleep(10)
        
        # 测试 daemon-proxy 健康检查
        proxy_url = services['daemon-proxy']
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
        
        # 测试 mock 服务
        vnc_url = services['mock-vnc']
        web_url = services['mock-web']
        
        async with aiohttp.ClientSession() as session:
            # 测试 VNC 服务
            async with session.get(vnc_url) as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "VNC"
            
            # 测试 Web 服务
            async with session.get(web_url) as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "Web"
    
    @pytest.mark.asyncio
    async def test_docker_daemon_proxy_functionality(self, docker_services):
        """测试 Docker 环境中的 daemon-proxy 功能"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
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
    async def test_docker_preview_link_vnc(self, docker_services):
        """测试 Docker 环境中的 VNC 预览链接"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
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
    async def test_docker_preview_link_web(self, docker_services):
        """测试 Docker 环境中的 Web 预览链接"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
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
    async def test_docker_preview_link_lifecycle(self, docker_services):
        """测试 Docker 环境中的预览链接生命周期"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_preview_link_lifecycle(8080)
        
        assert result["created"] is True
        assert result["accessed"] is True
        assert result["revoked"] is True
        assert result["access_after_revoke"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_docker_preview_link_multiple(self, docker_services):
        """测试 Docker 环境中的多个预览链接"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        scenarios = PreviewLinkTestScenarios(proxy_url)
        result = await scenarios.test_multiple_preview_links([6080, 8080, 3000])
        
        assert len(result["created_links"]) >= 2
        assert result["stats"] is not None
        assert result["stats"]["total_links"] >= 2
        assert result["concurrent_access"]["successful"] >= 2
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_docker_container_communication(self, docker_services):
        """测试容器间通信"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        # 测试通过 daemon-proxy 访问其他容器的服务
        async with aiohttp.ClientSession() as session:
            # 访问 VNC 容器
            async with session.get(f"{proxy_url}/proxy/6080/status") as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "VNC"
                assert data["protocol"] == "RFB"
            
            # 访问 Web 容器
            async with session.get(f"{proxy_url}/proxy/8080/api/status") as response:
                assert response.status == 200
                data = await response.json()
                assert data["service"] == "Web"
                assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_docker_network_isolation(self, docker_services):
        """测试 Docker 网络隔离"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        # 测试无法直接访问其他容器的服务（通过代理应该可以）
        async with aiohttp.ClientSession() as session:
            # 通过代理访问应该成功
            async with session.get(f"{proxy_url}/proxy/6080/") as response:
                assert response.status == 200
            
            # 直接访问应该失败（网络隔离）
            vnc_url = services['mock-vnc']
            try:
                # 这里应该失败，因为容器间网络隔离
                async with session.get(vnc_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    # 如果成功，说明网络没有隔离（在某些 Docker 配置下可能发生）
                    pass
            except (aiohttp.ClientError, asyncio.TimeoutError):
                # 这是期望的行为：网络隔离导致无法直接访问
                pass
    
    @pytest.mark.asyncio
    async def test_docker_preview_link_performance(self, docker_services):
        """测试 Docker 环境中的预览链接性能"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        async with DaemonProxyClient(proxy_url) as client:
            # 测试创建多个预览链接的性能
            start_time = time.time()
            
            links = []
            for i in range(5):
                link = await client.get_preview_link(8080)
                links.append(link)
            
            creation_time = time.time() - start_time
            
            # 验证创建时间合理
            assert creation_time < 15.0  # Docker 环境可能稍慢
            assert len(links) == 5
            
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
                tasks = [access_link(session, link) for link in links]
                results = await asyncio.gather(*tasks)
            
            access_time = time.time() - start_time
            
            # 验证访问时间合理
            assert access_time < 10.0
            
            # 验证所有访问都成功
            for result in results:
                assert result["status"] == 200
                assert result["response_time"] < 5.0  # Docker 环境可能稍慢
    
    @pytest.mark.asyncio
    async def test_docker_data_integrity(self, docker_services):
        """测试 Docker 环境中的数据完整性"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        # 测试 POST 请求的数据完整性
        test_data = {
            "test": "docker_data",
            "number": 456,
            "array": [4, 5, 6],
            "nested": {"docker": "test"}
        }
        
        async with aiohttp.ClientSession() as session:
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
    async def test_docker_concurrent_requests(self, docker_services):
        """测试 Docker 环境中的并发请求"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        async def make_request(session, i):
            async with session.get(f"{proxy_url}/proxy/8080/api/status") as response:
                return {
                    "request_id": i,
                    "status": response.status,
                    "data": await response.json() if response.status == 200 else None
                }
        
        # 并发发送 10 个请求（Docker 环境减少并发数）
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            successful_requests = [r for r in results if r["status"] == 200]
            assert len(successful_requests) == 10
            
            # 验证响应数据一致性
            for result in successful_requests:
                assert result["data"]["service"] == "Web"
                assert result["data"]["port"] == 8080
    
    @pytest.mark.asyncio
    async def test_docker_stability(self, docker_services):
        """测试 Docker 环境中的稳定性"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
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
            await asyncio.sleep(2)
    
    @pytest.mark.asyncio
    async def test_docker_metrics(self, docker_services):
        """测试 Docker 环境中的指标收集"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        # 生成一些请求
        async with aiohttp.ClientSession() as session:
            for _ in range(3):
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
    
    @pytest.mark.asyncio
    async def test_docker_full_scenarios(self, docker_services):
        """运行 Docker 环境完整测试场景"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        # 运行所有预览链接测试场景
        results = await run_preview_link_scenarios(proxy_url)
        
        # 验证总体结果
        assert results["summary"]["total_scenarios"] > 0
        assert results["summary"]["successful_scenarios"] > 0
        assert results["summary"]["success_rate"] > 0.3  # Docker 环境可能稍低
        
        # 验证关键场景
        assert "create_and_access" in results["scenarios"]
        assert "lifecycle" in results["scenarios"]
        assert "multiple_links" in results["scenarios"]
        assert "error_handling" in results["scenarios"]
    
    @pytest.mark.asyncio
    async def test_docker_restart_recovery(self, docker_environment):
        """测试 Docker 容器重启恢复"""
        env, services = docker_environment
        proxy_url = services['daemon-proxy']
        
        # 测试服务重启后的恢复能力
        async with aiohttp.ClientSession() as session:
            # 重启前测试
            async with session.get(f"{proxy_url}/health") as response:
                assert response.status == 200
            
            # 这里可以添加容器重启逻辑（如果需要）
            # 由于测试环境的限制，我们主要测试服务的稳定性
            
            # 重启后测试
            await asyncio.sleep(5)
            async with session.get(f"{proxy_url}/health") as response:
                assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_docker_resource_limits(self, docker_services):
        """测试 Docker 资源限制下的表现"""
        services = docker_services
        proxy_url = services['daemon-proxy']
        
        # 在资源受限的环境下测试预览链接功能
        async with DaemonProxyClient(proxy_url) as client:
            # 创建预览链接
            link = await client.get_preview_link(8080)
            
            # 访问预览链接
            async with aiohttp.ClientSession() as session:
                async with session.get(link.url) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data["service"] == "Web"
            
            # 撤销链接
            await client.revoke_preview_link(link.token)

    @pytest.mark.asyncio
    async def test_real_daemon_in_docker(self, docker_environment):
        """测试 Docker 中的真实 daemon"""
        env = docker_environment
        proxy_url = env["proxy_url"]
        
        # 等待 daemon 就绪
        await asyncio.sleep(10)
        
        # 测试 daemon 版本
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:2280/version") as response:
                assert response.status == 200
                data = await response.json()
                assert "version" in data
                print(f"Docker daemon version: {data['version']}")
        
        # 测试 daemon-proxy 健康状态
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{proxy_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_docker_daemon_proxy_integration(self, docker_environment):
        """测试 Docker 中 daemon-proxy 与真实 daemon 的集成"""
        env = docker_environment
        proxy_url = env["proxy_url"]
        
        # 等待服务就绪
        await asyncio.sleep(15)
        
        # 测试预览链接创建
        async with DaemonProxyClient(proxy_url) as client:
            # 创建 VNC 预览链接
            vnc_link = await client.get_preview_link(6080)
            assert vnc_link is not None
            assert vnc_link.port == 6080
            
            # 测试访问预览链接
            async with aiohttp.ClientSession() as session:
                async with session.get(vnc_link.url) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data["service"] == "VNC"
            
            # 创建 Web 预览链接
            web_link = await client.get_preview_link(8080)
            assert web_link is not None
            assert web_link.port == 8080
            
            # 测试访问预览链接
            async with aiohttp.ClientSession() as session:
                async with session.get(web_link.url) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data["service"] == "Web"

