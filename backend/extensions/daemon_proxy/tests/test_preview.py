"""
预览链接模块测试
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from daemon_proxy.preview import PreviewLinkManager, PreviewHandler, PreviewLink
from daemon_proxy.client import DaemonProxyClient, PreviewLinkResult
from daemon_proxy.config import Config


class TestPreviewLink:
    """预览链接测试"""
    
    def test_init(self):
        """测试初始化"""
        link = PreviewLink(
            url="http://localhost:8080/preview/token123",
            token="token123",
            port=8080,
            expires_at=time.time() + 3600
        )
        
        assert link.url == "http://localhost:8080/preview/token123"
        assert link.token == "token123"
        assert link.port == 8080
        assert not link.is_expired()
    
    def test_expired(self):
        """测试过期检查"""
        # 未过期的链接
        link1 = PreviewLink(
            url="http://localhost:8080/preview/token123",
            token="token123",
            port=8080,
            expires_at=time.time() + 3600
        )
        assert not link1.is_expired()
        
        # 已过期的链接
        link2 = PreviewLink(
            url="http://localhost:8080/preview/token123",
            token="token123",
            port=8080,
            expires_at=time.time() - 3600
        )
        assert link2.is_expired()
        
        # 永不过期的链接
        link3 = PreviewLink(
            url="http://localhost:8080/preview/token123",
            token="token123",
            port=8080,
            expires_at=None
        )
        assert not link3.is_expired()


class TestPreviewLinkManager:
    """预览链接管理器测试"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        config = Config()
        config.set("server.host", "127.0.0.1")
        config.set("server.port", 8080)
        return config
    
    @pytest.fixture
    def manager(self, config):
        """预览链接管理器实例"""
        return PreviewLinkManager(config)
    
    @pytest.mark.asyncio
    async def test_init(self, manager):
        """测试初始化"""
        assert manager.links == {}
        assert manager.token_to_link == {}
        assert manager._cleanup_task is None
    
    @pytest.mark.asyncio
    async def test_get_preview_link(self, manager):
        """测试获取预览链接"""
        link = await manager.get_preview_link(8080)
        
        assert isinstance(link, PreviewLink)
        assert link.port == 8080
        assert link.token in manager.links
        assert link.url.startswith("http://127.0.0.1:8080/preview/")
        assert not link.is_expired()
    
    @pytest.mark.asyncio
    async def test_get_preview_link_custom_base_url(self, manager):
        """测试使用自定义基础URL获取预览链接"""
        custom_url = "https://example.com:9000"
        link = await manager.get_preview_link(8080, custom_url)
        
        assert link.url.startswith("https://example.com:9000/preview/")
    
    @pytest.mark.asyncio
    async def test_get_link_by_token(self, manager):
        """测试根据token获取链接"""
        link = await manager.get_preview_link(8080)
        
        retrieved_link = manager.get_link_by_token(link.token)
        assert retrieved_link == link
        
        # 测试不存在的token
        assert manager.get_link_by_token("nonexistent") is None
    
    @pytest.mark.asyncio
    async def test_revoke_link(self, manager):
        """测试撤销链接"""
        link = await manager.get_preview_link(8080)
        token = link.token
        
        assert token in manager.links
        assert manager.revoke_link(token) is True
        assert token not in manager.links
        
        # 测试撤销不存在的链接
        assert manager.revoke_link("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """测试获取统计信息"""
        # 创建一些链接
        link1 = await manager.get_preview_link(8080)
        link2 = await manager.get_preview_link(6080)
        
        stats = manager.get_stats()
        
        assert stats["total_links"] == 2
        assert stats["active_links"] == 2
        assert stats["expired_links"] == 0
        
        # 撤销一个链接
        manager.revoke_link(link1.token)
        
        stats = manager.get_stats()
        assert stats["total_links"] == 1
        assert stats["active_links"] == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_links(self, manager):
        """测试清理过期链接"""
        # 创建过期的链接
        expired_link = PreviewLink(
            url="http://localhost:8080/preview/expired",
            token="expired",
            port=8080,
            expires_at=time.time() - 3600
        )
        manager.links["expired"] = expired_link
        manager.token_to_link["expired"] = "expired"
        
        # 创建正常的链接
        normal_link = await manager.get_preview_link(8080)
        
        # 启动清理任务
        await manager.start()
        
        # 等待清理任务运行
        await asyncio.sleep(0.2)
        
        # 手动触发清理
        await manager._cleanup_expired_links()
        
        # 检查过期链接被清理
        assert "expired" not in manager.links
        assert normal_link.token in manager.links
        
        await manager.stop()


class TestPreviewHandler:
    """预览处理器测试"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        config = Config()
        return config
    
    @pytest.fixture
    def manager(self, config):
        """预览链接管理器"""
        return PreviewLinkManager(config)
    
    @pytest.fixture
    def daemon_manager(self):
        """模拟daemon管理器"""
        daemon_manager = Mock()
        daemon_manager.proxy_request = AsyncMock()
        return daemon_manager
    
    @pytest.fixture
    def handler(self, manager, daemon_manager):
        """预览处理器"""
        return PreviewHandler(manager, daemon_manager)
    
    @pytest.mark.asyncio
    async def test_handle_preview_request_success(self, handler, manager):
        """测试处理预览请求成功"""
        # 创建预览链接
        link = await manager.get_preview_link(8080)
        
        # 模拟请求
        request = Mock()
        request.match_info = {'token': link.token, 'path': 'api/data'}
        request.method = 'GET'
        request.headers = {}
        request.can_read_body = False
        request.query_string = ''
        
        # 模拟daemon响应
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.read = AsyncMock(return_value=b'{"result": "success"}')
        
        handler.daemon_manager.proxy_request.return_value = mock_response
        
        # 处理请求
        response = await handler.handle_preview_request(request)
        
        assert response.status == 200
        assert response.body == b'{"result": "success"}'
        handler.daemon_manager.proxy_request.assert_called_once_with(
            port='8080',
            path='api/data',
            method='GET',
            headers={},
            data=None,
            query_string=''
        )
    
    @pytest.mark.asyncio
    async def test_handle_preview_request_not_found(self, handler):
        """测试处理预览请求 - 链接不存在"""
        request = Mock()
        request.match_info = {'token': 'nonexistent', 'path': ''}
        
        response = await handler.handle_preview_request(request)
        
        assert response.status == 404
        assert "not found" in response.text
    
    @pytest.mark.asyncio
    async def test_handle_preview_request_expired(self, handler, manager):
        """测试处理预览请求 - 链接过期"""
        # 创建过期的链接
        expired_link = PreviewLink(
            url="http://localhost:8080/preview/expired",
            token="expired",
            port=8080,
            expires_at=time.time() - 3600
        )
        manager.links["expired"] = expired_link
        
        request = Mock()
        request.match_info = {'token': 'expired', 'path': ''}
        
        response = await handler.handle_preview_request(request)
        
        assert response.status == 410
        assert "expired" in response.text
        assert "expired" not in manager.links  # 应该被清理


class TestDaemonProxyClient:
    """Daemon Proxy客户端测试"""
    
    @pytest.mark.asyncio
    async def test_get_preview_link_success(self):
        """测试获取预览链接成功"""
        mock_response_data = {
            "url": "http://localhost:8080/preview/token123",
            "token": "token123",
            "port": 8080,
            "expires_at": time.time() + 3600
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with DaemonProxyClient("http://localhost:8080") as client:
                result = await client.get_preview_link(8080)
                
                assert isinstance(result, PreviewLinkResult)
                assert result.url == "http://localhost:8080/preview/token123"
                assert result.token == "token123"
                assert result.port == 8080
    
    @pytest.mark.asyncio
    async def test_get_preview_link_failure(self):
        """测试获取预览链接失败"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with DaemonProxyClient("http://localhost:8080") as client:
                with pytest.raises(Exception, match="Failed to create preview link"):
                    await client.get_preview_link(8080)
    
    @pytest.mark.asyncio
    async def test_revoke_preview_link(self):
        """测试撤销预览链接"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.delete.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with DaemonProxyClient("http://localhost:8080") as client:
                result = await client.revoke_preview_link("token123")
                assert result is True
    
    @pytest.mark.asyncio
    async def test_get_preview_stats(self):
        """测试获取预览统计"""
        mock_stats = {
            "total_links": 5,
            "active_links": 3,
            "expired_links": 2
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_stats)
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with DaemonProxyClient("http://localhost:8080") as client:
                stats = await client.get_preview_stats()
                assert stats == mock_stats
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        mock_health = {
            "status": "healthy",
            "uptime": 123.45
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_health)
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            async with DaemonProxyClient("http://localhost:8080") as client:
                health = await client.health_check()
                assert health == mock_health

