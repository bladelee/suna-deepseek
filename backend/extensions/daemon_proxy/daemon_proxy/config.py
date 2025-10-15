"""
配置管理模块
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 默认配置
        default_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080
            },
            "daemon": {
                "mode": "host",
                "host": "localhost",
                "port": 2280,
                "path": "/usr/local/bin/daytona",
                "container_name": "my-sandbox",
                "startup_timeout": 30,
                "binary_source_path": "/usr/local/bin/daytona",
                "injection_mode": "volume",
                "injection_method": "copy"  # 新增：注入方式，可选 "copy" 或 "mount"
            },
            "security": {
                "enabled": False,
                "api_key": "your-secret-key"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/daemon-proxy.log",
                "max_size": 10485760,
                "backup_count": 5
            },
            "proxy": {
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 1
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 9090,
                "health_check_interval": 30
            }
        }
        
        # 从文件加载配置
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    default_config.update(file_config)
            except Exception as e:
                logging.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # 从环境变量覆盖配置
        self._config = self._load_from_env(default_config)
    
    def _load_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """从环境变量加载配置"""
        env_mappings = {
            "DAEMON_PROXY_HOST": ("server", "host"),
            "DAEMON_PROXY_PORT": ("server", "port"),
            "DAEMON_MODE": ("daemon", "mode"),
            "DAEMON_HOST": ("daemon", "host"),
            "DAEMON_PORT": ("daemon", "port"),
            "DAEMON_PATH": ("daemon", "path"),
            "DAEMON_CONTAINER_NAME": ("daemon", "container_name"),
            "DAEMON_BINARY_SOURCE_PATH": ("daemon", "binary_source_path"),
            "DAEMON_INJECTION_MODE": ("daemon", "injection_mode"),
            "SECURITY_ENABLED": ("security", "enabled"),
            "SECURITY_API_KEY": ("security", "api_key"),
            "LOG_LEVEL": ("logging", "level"),
            "LOG_FILE": ("logging", "file"),
            "PROXY_TIMEOUT": ("proxy", "timeout"),
            "MONITORING_ENABLED": ("monitoring", "enabled"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 类型转换
                if key in ["port", "startup_timeout", "timeout", "max_retries", 
                          "retry_delay", "metrics_port", "health_check_interval",
                          "max_size", "backup_count"]:
                    value = int(value)
                elif key in ["enabled"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                
                config[section][key] = value
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        save_path = file_path or self.config_file
        if not save_path:
            raise ValueError("No file path specified for saving config")
        
        # 确保目录存在
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)
    
    @property
    def server_host(self) -> str:
        return self.get("server.host", "0.0.0.0")
    
    @property
    def server_port(self) -> int:
        return self.get("server.port", 8080)
    
    @property
    def daemon_mode(self) -> str:
        return self.get("daemon.mode", "host")
    
    @property
    def daemon_host(self) -> str:
        return self.get("daemon.host", "localhost")
    
    @property
    def daemon_port(self) -> int:
        return self.get("daemon.port", 2280)
    
    @property
    def daemon_path(self) -> str:
        return self.get("daemon.path", "/usr/local/bin/daytona")
    
    @property
    def daemon_container_name(self) -> str:
        return self.get("daemon.container_name", "my-sandbox")
    
    @property
    def daemon_startup_timeout(self) -> int:
        return self.get("daemon.startup_timeout", 30)
    
    @property
    def daemon_binary_source_path(self) -> str:
        return self.get("daemon.binary_source_path", "/usr/local/bin/daytona")
    
    @property
    def daemon_injection_mode(self) -> str:
        return self.get("daemon.injection_mode", "volume")
    
    @property
    def daemon_injection_method(self) -> str:
        return self.get("daemon.injection_method", "copy")
    
    @property
    def security_enabled(self) -> bool:
        return self.get("security.enabled", False)
    
    @property
    def security_api_key(self) -> str:
        return self.get("security.api_key", "your-secret-key")
    
    @property
    def log_level(self) -> str:
        return self.get("logging.level", "INFO")
    
    @property
    def log_file(self) -> str:
        return self.get("logging.file", "logs/daemon-proxy.log")
    
    @property
    def proxy_timeout(self) -> int:
        return self.get("proxy.timeout", 30)
    
    @property
    def proxy_max_retries(self) -> int:
        return self.get("proxy.max_retries", 3)
    
    @property
    def proxy_retry_delay(self) -> int:
        return self.get("proxy.retry_delay", 1)
    
    @property
    def monitoring_enabled(self) -> bool:
        return self.get("monitoring.enabled", True)
    
    @property
    def monitoring_metrics_port(self) -> int:
        return self.get("monitoring.metrics_port", 9090)
    
    @property
    def monitoring_health_check_interval(self) -> int:
        return self.get("monitoring.health_check_interval", 30)
    
    @property
    def daemon_binary_source_path(self) -> str:
        return self.get("daemon.binary_source_path", "/usr/local/bin/daytona")
    
    @property
    def daemon_injection_mode(self) -> str:
        return self.get("daemon.injection_mode", "volume")

