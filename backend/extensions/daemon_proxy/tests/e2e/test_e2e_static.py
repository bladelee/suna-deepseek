"""
第四组 E2E 测试：静态网站预览测试

测试 daemon-proxy 服务能够通过预览链接在浏览器中正确显示容器中的静态网站内容
使用 curl 等简单命令模拟浏览器访问，验证静态资源加载
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
from daemon_proxy.client import DaemonProxyClient


@pytest.mark.e2e_static
class TestE2EStaticWebsite:
    """静态网站预览 E2E 测试"""
    
    @pytest.fixture
    def check_static_requirements(self):
        """检查静态网站测试环境要求"""
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
    async def static_environment(self, check_static_requirements):
        """静态网站测试环境"""
        env = DockerTestEnvironment()
        
        # 使用静态网站专用的 compose 文件
        compose_file = "/home/sa/agenthome/extentions/daemon-proxy/docker-compose-static-e2e.yml"
        
        try:
            await env.start_environment(compose_file)
            yield env
        finally:
            await env.cleanup()
    
    @pytest_asyncio.fixture
    async def static_services(self, static_environment):
        """静态网站服务"""
        env = static_environment
        
        # 等待服务启动
        await asyncio.sleep(10)
        
        services = {
            'daemon-proxy': 'http://localhost:8080',
            'static-simple': 'http://localhost:3001',
            'static-complete': 'http://localhost:3002',
            'vnc-service': 'http://localhost:6080',
            'web-service': 'http://localhost:8081'
        }
        
        return services
    
    @pytest.mark.asyncio
    async def test_static_website_simple_html(self, static_services):
        """测试简单 HTML 页面预览"""
        services = static_services
        proxy_url = services['daemon-proxy']
        static_url = services['static-simple']
        
        # 解析静态网站端口
        static_port = 3001
        
        try:
            # 创建预览链接
            async with DaemonProxyClient(proxy_url) as client:
                preview_link = await client.get_preview_link(static_port)
            assert preview_link is not None
            assert preview_link.url.startswith(f"{proxy_url}/preview/")
            assert preview_link.port == static_port
            
            print(f"✅ 预览链接创建成功: {preview_link.url}")
            
            # 使用 curl 测试 HTML 页面访问
            result = await self._test_with_curl(preview_link.url)
            assert result['status_code'] == 200
            assert 'text/html' in result['content_type']
            assert 'Daemon Proxy 静态网站预览测试' in result['content']
            
            print(f"✅ HTML 页面访问成功")
            
            # 测试 CSS 文件加载
            css_url = preview_link.url.rstrip('/') + '/style.css'
            css_result = await self._test_with_curl(css_url)
            assert css_result['status_code'] == 200
            assert 'text/css' in css_result['content_type']
            assert 'body' in css_result['content']
            
            print(f"✅ CSS 文件加载成功")
            
            # 测试 JavaScript 文件加载
            js_url = preview_link.url.rstrip('/') + '/script.js'
            js_result = await self._test_with_curl(js_url)
            assert js_result['status_code'] == 200
            assert 'application/javascript' in js_result['content_type'] or 'text/javascript' in js_result['content_type']
            assert 'document.addEventListener' in js_result['content']
            
            print(f"✅ JavaScript 文件加载成功")
            
        except Exception as e:
            pytest.fail(f"简单 HTML 页面测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_static_website_complete_site(self, static_services):
        """测试完整静态网站预览"""
        services = static_services
        proxy_url = services['daemon-proxy']
        static_url = services['static-complete']
        
        static_port = 3002
        
        try:
            # 创建预览链接
            async with DaemonProxyClient(proxy_url) as client:
                preview_link = await client.get_preview_link(static_port)
            assert preview_link is not None
            assert preview_link.url.startswith(f"{proxy_url}/preview/")
            assert preview_link.port == static_port
            
            print(f"✅ 完整网站预览链接创建成功: {preview_link.url}")
            
            # 测试主页访问
            result = await self._test_with_curl(preview_link.url)
            assert result['status_code'] == 200
            assert 'text/html' in result['content_type']
            assert '完整的静态网站预览' in result['content']
            
            print(f"✅ 主页访问成功")
            
            # 测试 CSS 文件加载
            css_url = preview_link.url.rstrip('/') + '/css/main.css'
            css_result = await self._test_with_curl(css_url)
            assert css_result['status_code'] == 200
            assert 'text/css' in css_result['content_type']
            assert '.navbar' in css_result['content']
            
            print(f"✅ 主样式文件加载成功")
            
            # 测试响应式 CSS 文件加载
            responsive_css_url = preview_link.url.rstrip('/') + '/css/responsive.css'
            responsive_result = await self._test_with_curl(responsive_css_url)
            assert responsive_result['status_code'] == 200
            assert 'text/css' in responsive_result['content_type']
            assert '@media' in responsive_result['content']
            
            print(f"✅ 响应式样式文件加载成功")
            
            # 测试 JavaScript 文件加载
            js_url = preview_link.url.rstrip('/') + '/js/main.js'
            js_result = await self._test_with_curl(js_url)
            assert js_result['status_code'] == 200
            assert 'application/javascript' in js_result['content_type'] or 'text/javascript' in js_result['content_type']
            assert 'document.addEventListener' in js_result['content']
            
            print(f"✅ JavaScript 文件加载成功")
            
        except Exception as e:
            pytest.fail(f"完整静态网站测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_static_website_resource_loading(self, static_services):
        """测试静态资源加载功能"""
        services = static_services
        proxy_url = services['daemon-proxy']
        
        static_port = 3001
        
        try:
            # 创建预览链接
            async with DaemonProxyClient(proxy_url) as client:
                preview_link = await client.get_preview_link(static_port)
            
            # 测试各种资源类型的加载
            resources = [
                ('/', 'text/html', 'Daemon Proxy 静态网站预览测试'),
                ('/style.css', 'text/css', 'body'),
                ('/script.js', 'application/javascript', 'document.addEventListener'),
            ]
            
            for path, expected_type, expected_content in resources:
                url = preview_link.url.rstrip('/') + path
                result = await self._test_with_curl(url)
                
                assert result['status_code'] == 200, f"资源 {path} 加载失败: {result['status_code']}"
                assert expected_type in result['content_type'], f"资源 {path} 内容类型错误: {result['content_type']}"
                assert expected_content in result['content'], f"资源 {path} 内容不匹配"
                
                print(f"✅ 资源 {path} 加载成功")
            
        except Exception as e:
            pytest.fail(f"静态资源加载测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_static_website_preview_link_lifecycle(self, static_services):
        """测试静态网站预览链接生命周期"""
        services = static_services
        proxy_url = services['daemon-proxy']

        static_port = 3001

        try:
            # 创建预览链接
            async with DaemonProxyClient(proxy_url) as client:
                preview_link = await client.get_preview_link(static_port)
            assert preview_link is not None
            
            # 测试链接访问
            result = await self._test_with_curl(preview_link.url)
            assert result['status_code'] == 200
            
            print(f"✅ 预览链接访问成功")
            
                # 撤销链接
                revoked = await client.revoke_preview_link(preview_link.token)
                assert revoked is True

                print(f"✅ 预览链接撤销成功")

            # 测试撤销后访问
            result = await self._test_with_curl(preview_link.url)
            assert result['status_code'] in [404, 403, 401]  # 撤销后应该无法访问

            print(f"✅ 撤销后访问被正确拒绝")
            
        except Exception as e:
            pytest.fail(f"预览链接生命周期测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_static_website_multiple_ports(self, static_services):
        """测试多个静态网站端口"""
        services = static_services
        proxy_url = services['daemon-proxy']

        # 测试两个不同的静态网站端口
        ports = [3001, 3002]

        try:
            async with DaemonProxyClient(proxy_url) as client:
                for port in ports:
                    # 创建预览链接
                    preview_link = await client.get_preview_link(port)
                    assert preview_link is not None
                    assert preview_link.port == port
                    
                    # 测试访问
                    result = await self._test_with_curl(preview_link.url)
                    assert result['status_code'] == 200
                    assert 'text/html' in result['content_type']

                    print(f"✅ 端口 {port} 预览链接测试成功")
            
        except Exception as e:
            pytest.fail(f"多端口静态网站测试失败: {e}")
    
    async def _test_with_curl(self, url: str) -> Dict[str, Any]:
        """使用 curl 测试 URL 访问"""
        try:
            # 使用 curl 获取页面内容
            cmd = [
                'curl', '-s', '-w', 
                'HTTP_CODE:%{http_code}\nCONTENT_TYPE:%{content_type}\n',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"curl 命令执行失败: {result.stderr}")
            
            # 解析输出
            lines = result.stdout.strip().split('\n')
            content_lines = []
            status_code = None
            content_type = None
            
            for line in lines:
                if line.startswith('HTTP_CODE:'):
                    status_code = int(line.split(':', 1)[1])
                elif line.startswith('CONTENT_TYPE:'):
                    content_type = line.split(':', 1)[1]
                else:
                    content_lines.append(line)
            
            content = '\n'.join(content_lines)
            
            return {
                'status_code': status_code,
                'content_type': content_type,
                'content': content,
                'headers': {}  # curl 输出中不包含详细 headers
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("curl 请求超时")
        except Exception as e:
            raise Exception(f"curl 测试失败: {e}")
    
    @pytest.mark.asyncio
    async def test_static_website_performance(self, static_services):
        """测试静态网站性能"""
        services = static_services
        proxy_url = services['daemon-proxy']

        static_port = 3001

        try:
            # 创建预览链接
            async with DaemonProxyClient(proxy_url) as client:
                preview_link = await client.get_preview_link(static_port)
            
            # 测试页面加载时间
            start_time = time.time()
            result = await self._test_with_curl(preview_link.url)
            load_time = time.time() - start_time
            
            assert result['status_code'] == 200
            assert load_time < 5.0, f"页面加载时间过长: {load_time:.2f}秒"
            
            print(f"✅ 页面加载时间: {load_time:.2f}秒")
            
            # 测试并发访问
            tasks = []
            for i in range(5):
                task = self._test_with_curl(preview_link.url)
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time
            
            # 验证所有请求都成功
            for result in results:
                assert result['status_code'] == 200
            
            print(f"✅ 并发访问测试成功，5个请求耗时: {concurrent_time:.2f}秒")
            
        except Exception as e:
            pytest.fail(f"静态网站性能测试失败: {e}")
