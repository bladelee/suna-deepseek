"""
注入机制测试模块
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import docker

from daemon_proxy.binary_manager import BinaryManager, UnsupportedArchitectureError
from daemon_proxy.daemon import DaemonManager
from daemon_proxy.config import Config


class TestBinaryManager:
    """二进制管理器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.binary_manager = BinaryManager(temp_dir=self.temp_dir)
        
        # 创建测试二进制文件
        self.test_binary_path = os.path.join(self.temp_dir, "test-daemon")
        with open(self.test_binary_path, 'wb') as f:
            f.write(b'\x7fELF\x02\x01\x01\x00')  # ELF 文件头
        os.chmod(self.test_binary_path, 0o755)
    
    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_prepare_binary_success(self):
        """测试成功准备二进制文件"""
        result_path = self.binary_manager.prepare_binary(self.test_binary_path)
        
        assert result_path is not None
        assert os.path.exists(result_path)
        assert os.access(result_path, os.X_OK)
        assert self.binary_manager.get_binary_path() == result_path
    
    def test_prepare_binary_file_not_found(self):
        """测试源文件不存在"""
        with pytest.raises(FileNotFoundError):
            self.binary_manager.prepare_binary("/nonexistent/path")
    
    def test_prepare_binary_not_a_file(self):
        """测试源路径不是文件"""
        with pytest.raises(ValueError):
            self.binary_manager.prepare_binary(self.temp_dir)
    
    def test_prepare_binary_permission_denied(self):
        """测试源文件权限不足"""
        # 创建无读权限的文件
        no_read_file = os.path.join(self.temp_dir, "no-read")
        with open(no_read_file, 'w') as f:
            f.write("test")
        os.chmod(no_read_file, 0o000)
        
        try:
            with pytest.raises(PermissionError):
                self.binary_manager.prepare_binary(no_read_file)
        finally:
            os.chmod(no_read_file, 0o644)
    
    @patch('platform.machine')
    def test_unsupported_architecture(self, mock_machine):
        """测试不支持的架构"""
        mock_machine.return_value = 'arm64'
        
        with pytest.raises(UnsupportedArchitectureError):
            self.binary_manager.prepare_binary(self.test_binary_path)
    
    def test_cleanup(self):
        """测试清理功能"""
        # 准备二进制文件
        result_path = self.binary_manager.prepare_binary(self.test_binary_path)
        assert os.path.exists(result_path)
        
        # 清理
        self.binary_manager.cleanup()
        assert not os.path.exists(result_path)
        assert self.binary_manager.get_binary_path() is None
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with BinaryManager(temp_dir=self.temp_dir) as bm:
            result_path = bm.prepare_binary(self.test_binary_path)
            assert os.path.exists(result_path)
        
        # 上下文退出后应该自动清理
        assert not os.path.exists(result_path)


class TestDaemonManagerInjection:
    """DaemonManager 注入机制测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = Config()
        self.config.set("daemon.mode", "docker")
        self.config.set("daemon.injection_mode", "volume")
        self.config.set("daemon.container_name", "test-container")
        self.config.set("daemon.binary_source_path", "/usr/local/bin/daytona")
        
        self.daemon_manager = DaemonManager(self.config)
    
    @patch('docker.from_env')
    @patch('daemon_proxy.daemon.BinaryManager')
    def test_start_docker_injected_daemon_success(self, mock_binary_manager_class, mock_docker_from_env):
        """测试成功启动注入的Docker daemon"""
        # Mock 二进制管理器
        mock_binary_manager = Mock()
        mock_binary_manager.prepare_binary.return_value = "/tmp/daemon-amd64"
        mock_binary_manager_class.return_value = mock_binary_manager
        
        # Mock Docker 客户端和容器
        mock_docker_client = Mock()
        mock_container = Mock()
        mock_container.status = 'running'
        mock_container.attrs = {
            'NetworkSettings': {'IPAddress': '172.17.0.2'},
            'Config': {'WorkingDir': '/workspace'}
        }
        mock_container.exec_run.return_value = Mock(exit_code=0)
        mock_docker_client.containers.get.return_value = mock_container
        mock_docker_from_env.return_value = mock_docker_client
        
        # 执行测试
        import asyncio
        asyncio.run(self.daemon_manager._start_docker_injected_daemon())
        
        # 验证调用
        mock_binary_manager.prepare_binary.assert_called_once_with("/usr/local/bin/daytona")
        mock_docker_client.containers.get.assert_called_once_with("test-container")
        assert self.daemon_manager.container_ip == '172.17.0.2'
        assert self.daemon_manager.binary_manager == mock_binary_manager
    
    @patch('docker.from_env')
    def test_start_docker_injected_daemon_container_not_found(self, mock_docker_from_env):
        """测试容器不存在的情况"""
        mock_docker_client = Mock()
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound("Container not found")
        mock_docker_from_env.return_value = mock_docker_client
        
        import asyncio
        with pytest.raises(Exception, match="Container test-container not found"):
            asyncio.run(self.daemon_manager._start_docker_injected_daemon())
    
    @patch('docker.from_env')
    def test_start_docker_injected_daemon_container_not_running(self, mock_docker_from_env):
        """测试容器未运行的情况"""
        mock_docker_client = Mock()
        mock_container = Mock()
        mock_container.status = 'stopped'
        mock_docker_client.containers.get.return_value = mock_container
        mock_docker_from_env.return_value = mock_docker_client
        
        import asyncio
        with pytest.raises(Exception, match="Container test-container is not running"):
            asyncio.run(self.daemon_manager._start_docker_injected_daemon())
    
    @patch('docker.from_env')
    def test_start_docker_injected_daemon_no_ip(self, mock_docker_from_env):
        """测试容器无IP地址的情况"""
        mock_docker_client = Mock()
        mock_container = Mock()
        mock_container.status = 'running'
        mock_container.attrs = {'NetworkSettings': {'IPAddress': ''}}
        mock_docker_client.containers.get.return_value = mock_container
        mock_docker_from_env.return_value = mock_docker_client
        
        import asyncio
        with pytest.raises(Exception, match="Container test-container has no IP address"):
            asyncio.run(self.daemon_manager._start_docker_injected_daemon())
    
    def test_inject_binary_to_container(self):
        """测试二进制文件注入到容器"""
        mock_container = Mock()
        mock_container.exec_run.return_value = Mock(exit_code=0)
        
        import asyncio
        asyncio.run(self.daemon_manager._inject_binary_to_container(mock_container, "/tmp/test-binary"))
        
        # 验证 put_archive 被调用
        mock_container.put_archive.assert_called_once()
        
        # 验证 chmod 被调用
        mock_container.exec_run.assert_called_with(['chmod', '+x', '/usr/local/bin/daytona'])
    
    def test_start_daemon_in_container(self):
        """测试在容器内启动daemon"""
        mock_container = Mock()
        mock_container.attrs = {'Config': {'WorkingDir': '/workspace'}}
        mock_container.exec_run.return_value = Mock(exit_code=0)
        
        import asyncio
        asyncio.run(self.daemon_manager._start_daemon_in_container(mock_container))
        
        # 验证 exec_run 被调用
        mock_container.exec_run.assert_called_once()
        call_args = mock_container.exec_run.call_args
        assert call_args[0][0] == ['sh', '-c', '/usr/local/bin/daytona --work-dir /workspace']
        assert call_args[1]['detach'] is True
    
    def test_start_daemon_in_container_default_workdir(self):
        """测试使用默认工作目录启动daemon"""
        mock_container = Mock()
        mock_container.attrs = {'Config': {'WorkingDir': '/'}}  # 根目录，应该使用默认值
        mock_container.exec_run.return_value = Mock(exit_code=0)
        
        import asyncio
        asyncio.run(self.daemon_manager._start_daemon_in_container(mock_container))
        
        # 验证使用默认工作目录
        call_args = mock_container.exec_run.call_args
        assert '/usr/local/bin/daytona --work-dir /workspace' in call_args[0][0][2]


class TestConfigInjection:
    """配置注入相关测试"""
    
    def test_daemon_binary_source_path_property(self):
        """测试二进制源路径配置属性"""
        config = Config()
        assert config.daemon_binary_source_path == "/usr/local/bin/daytona"
        
        config.set("daemon.binary_source_path", "/custom/path/daemon")
        assert config.daemon_binary_source_path == "/custom/path/daemon"
    
    def test_daemon_injection_mode_property(self):
        """测试注入模式配置属性"""
        config = Config()
        assert config.daemon_injection_mode == "volume"
        
        config.set("daemon.injection_mode", "direct")
        assert config.daemon_injection_mode == "direct"
    
    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {
            'DAEMON_BINARY_SOURCE_PATH': '/env/path/daemon',
            'DAEMON_INJECTION_MODE': 'direct'
        }):
            config = Config()
            assert config.daemon_binary_source_path == "/env/path/daemon"
            assert config.daemon_injection_mode == "direct"


if __name__ == "__main__":
    pytest.main([__file__])
