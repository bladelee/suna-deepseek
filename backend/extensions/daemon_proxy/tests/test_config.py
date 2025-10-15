"""
配置模块测试
"""

import pytest
import tempfile
import os
from daemon_proxy.config import Config


class TestConfig:
    """配置类测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 8080
        assert config.daemon_mode == "host"
        assert config.daemon_port == 2280
        assert config.daemon_path == "/usr/local/bin/daytona"
        assert config.security_enabled is False
        assert config.log_level == "INFO"
    
    def test_config_file_loading(self):
        """测试配置文件加载"""
        config_content = """
server:
  host: "127.0.0.1"
  port: 9000

daemon:
  mode: "docker"
  port: 3000
  container_name: "test-container"

security:
  enabled: true
  api_key: "test-key"

logging:
  level: "DEBUG"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                config = Config(f.name)
                
                assert config.server_host == "127.0.0.1"
                assert config.server_port == 9000
                assert config.daemon_mode == "docker"
                assert config.daemon_port == 3000
                assert config.daemon_container_name == "test-container"
                assert config.security_enabled is True
                assert config.security_api_key == "test-key"
                assert config.log_level == "DEBUG"
                
            finally:
                os.unlink(f.name)
    
    def test_environment_variables(self):
        """测试环境变量覆盖"""
        import os
        
        # 设置环境变量
        os.environ['DAEMON_PROXY_HOST'] = '192.168.1.1'
        os.environ['DAEMON_PROXY_PORT'] = '9999'
        os.environ['DAEMON_MODE'] = 'docker'
        os.environ['SECURITY_ENABLED'] = 'true'
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        try:
            config = Config()
            
            assert config.server_host == '192.168.1.1'
            assert config.server_port == 9999
            assert config.daemon_mode == 'docker'
            assert config.security_enabled is True
            assert config.log_level == 'ERROR'
            
        finally:
            # 清理环境变量
            for key in ['DAEMON_PROXY_HOST', 'DAEMON_PROXY_PORT', 'DAEMON_MODE', 
                       'SECURITY_ENABLED', 'LOG_LEVEL']:
                os.environ.pop(key, None)
    
    def test_get_set_methods(self):
        """测试get和set方法"""
        config = Config()
        
        # 测试get方法
        assert config.get("server.host") == "0.0.0.0"
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("nonexistent.key") is None
        
        # 测试set方法
        config.set("server.host", "localhost")
        assert config.get("server.host") == "localhost"
        
        config.set("new.section.key", "value")
        assert config.get("new.section.key") == "value"
    
    def test_property_access(self):
        """测试属性访问"""
        config = Config()
        
        # 测试所有属性
        assert isinstance(config.server_host, str)
        assert isinstance(config.server_port, int)
        assert isinstance(config.daemon_mode, str)
        assert isinstance(config.daemon_port, int)
        assert isinstance(config.daemon_path, str)
        assert isinstance(config.daemon_container_name, str)
        assert isinstance(config.daemon_startup_timeout, int)
        assert isinstance(config.security_enabled, bool)
        assert isinstance(config.security_api_key, str)
        assert isinstance(config.log_level, str)
        assert isinstance(config.log_file, str)
        assert isinstance(config.proxy_timeout, int)
        assert isinstance(config.proxy_max_retries, int)
        assert isinstance(config.proxy_retry_delay, int)
        assert isinstance(config.monitoring_enabled, bool)
        assert isinstance(config.monitoring_metrics_port, int)
        assert isinstance(config.monitoring_health_check_interval, int)
    
    def test_config_save(self):
        """测试配置保存"""
        config = Config()
        config.set("server.host", "test-host")
        config.set("server.port", 1234)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            try:
                config.save(f.name)
                
                # 重新加载配置验证
                loaded_config = Config(f.name)
                assert loaded_config.server_host == "test-host"
                assert loaded_config.server_port == 1234
                
            finally:
                os.unlink(f.name)

