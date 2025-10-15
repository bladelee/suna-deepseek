"""
Daemon管理模块测试
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from daemon_proxy.config import Config
from daemon_proxy.daemon import DaemonManager


class TestDaemonManager:
    """Daemon管理器测试"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        config = Config()
        config.set("daemon.mode", "host")
        config.set("daemon.port", 2280)
        config.set("daemon.path", "/usr/local/bin/daytona")
        config.set("daemon.startup_timeout", 5)
        config.set("proxy.timeout", 30)
        return config
    
    @pytest.fixture
    def docker_config(self):
        """Docker模式配置"""
        config = Config()
        config.set("daemon.mode", "docker")
        config.set("daemon.port", 2280)
        config.set("daemon.container_name", "test-container")
        config.set("daemon.startup_timeout", 5)
        config.set("proxy.timeout", 30)
        return config
    
    @pytest.fixture
    def daemon_manager(self, config):
        """Daemon管理器实例"""
        return DaemonManager(config)
    
    def test_init(self, config):
        """测试初始化"""
        manager = DaemonManager(config)
        
        assert manager.config == config
        assert manager.docker_client is None
        assert manager.container_ip is None
        assert manager.daemon_process is None
        assert manager.session is None
        assert manager._is_running is False
    
    @pytest.mark.asyncio
    async def test_start_host_daemon_success(self, daemon_manager):
        """测试成功启动宿主机daemon"""
        with patch('subprocess.Popen') as mock_popen, \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch.object(daemon_manager, '_wait_for_daemon', new_callable=AsyncMock) as mock_wait:
            
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            await daemon_manager.start()
            
            assert daemon_manager.daemon_process == mock_process
            assert daemon_manager._is_running is True
            mock_popen.assert_called_once()
            mock_wait.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_host_daemon_file_not_found(self, daemon_manager):
        """测试daemon文件不存在"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                await daemon_manager.start()
    
    @pytest.mark.asyncio
    async def test_start_host_daemon_not_executable(self, daemon_manager):
        """测试daemon文件不可执行"""
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=False):
            with pytest.raises(PermissionError):
                await daemon_manager.start()
    
    @pytest.mark.asyncio
    async def test_start_docker_daemon_success(self, docker_config):
        """测试成功启动Docker daemon"""
        manager = DaemonManager(docker_config)
        
        mock_container = Mock()
        mock_container.attrs = {
            'NetworkSettings': {
                'IPAddress': '172.17.0.2'
            }
        }
        
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.containers.get.return_value = mock_container
            mock_docker.return_value = mock_client
            
            with patch.object(manager, '_wait_for_daemon', new_callable=AsyncMock) as mock_wait:
                await manager.start()
                
                assert manager.container_ip == '172.17.0.2'
                assert manager._is_running is True
                mock_wait.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_docker_daemon_container_not_found(self, docker_config):
        """测试Docker容器不存在"""
        manager = DaemonManager(docker_config)
        
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.containers.get.side_effect = Exception("Container not found")
            mock_docker.return_value = mock_client
            
            with pytest.raises(Exception, match="Container not found"):
                await manager.start()
    
    @pytest.mark.asyncio
    async def test_wait_for_daemon_success(self, daemon_manager):
        """测试等待daemon启动成功"""
        mock_response = Mock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            daemon_manager.session = mock_session
            
            await daemon_manager._wait_for_daemon()
            
            mock_session.get.assert_called()
    
    @pytest.mark.asyncio
    async def test_wait_for_daemon_timeout(self, daemon_manager):
        """测试等待daemon启动超时"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Connection refused")
            mock_session_class.return_value = mock_session
            
            daemon_manager.session = mock_session
            
            with pytest.raises(TimeoutError):
                await daemon_manager._wait_for_daemon()
    
    @pytest.mark.asyncio
    async def test_proxy_request_success(self, daemon_manager):
        """测试代理请求成功"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"response data")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            daemon_manager.session = mock_session
            daemon_manager._is_running = True
            
            response = await daemon_manager.proxy_request("8080", "api/data", "GET")
            
            assert response == mock_response
            mock_session.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_proxy_request_not_running(self, daemon_manager):
        """测试daemon未运行时代理请求"""
        with pytest.raises(Exception, match="Daemon is not running"):
            await daemon_manager.proxy_request("8080", "api/data", "GET")
    
    @pytest.mark.asyncio
    async def test_get_daemon_status_running(self, daemon_manager):
        """测试获取daemon状态 - 运行中"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"version": "1.0.0"})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            daemon_manager.session = mock_session
            
            status = await daemon_manager.get_daemon_status()
            
            assert status["status"] == "running"
            assert status["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_get_daemon_status_error(self, daemon_manager):
        """测试获取daemon状态 - 错误"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Connection error")
            mock_session_class.return_value = mock_session
            
            daemon_manager.session = mock_session
            
            status = await daemon_manager.get_daemon_status()
            
            assert status["status"] == "error"
            assert "Connection error" in status["error"]
    
    @pytest.mark.asyncio
    async def test_stop(self, daemon_manager):
        """测试停止daemon"""
        mock_process = Mock()
        mock_process.wait.return_value = 0
        
        daemon_manager.daemon_process = mock_process
        daemon_manager.session = AsyncMock()
        
        await daemon_manager.stop()
        
        assert daemon_manager._is_running is False
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
    
    def test_get_daemon_url_host_mode(self, daemon_manager):
        """测试获取daemon URL - 宿主机模式"""
        url = daemon_manager._get_daemon_url()
        assert url == "http://localhost:2280"
    
    def test_get_daemon_url_docker_mode(self, docker_config):
        """测试获取daemon URL - Docker模式"""
        manager = DaemonManager(docker_config)
        manager.container_ip = "172.17.0.2"
        
        url = manager._get_daemon_url()
        assert url == "http://172.17.0.2:2280"
    
    def test_is_running_property(self, daemon_manager):
        """测试is_running属性"""
        assert daemon_manager.is_running is False
        
        daemon_manager._is_running = True
        assert daemon_manager.is_running is True
    
    def test_daemon_url_property(self, daemon_manager):
        """测试daemon_url属性"""
        url = daemon_manager.daemon_url
        assert url == "http://localhost:2280"

