"""
工具函数模块
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(config) -> None:
    """设置日志配置"""
    # 创建日志目录
    log_file = config.log_file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    log_format = config.get("logging.format", 
                           "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # 配置日志级别
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # 基本配置
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # 设置第三方库日志级别
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.WARNING)


def validate_config(config) -> bool:
    """验证配置"""
    errors = []
    
    # 验证服务器配置
    if not isinstance(config.server_port, int) or config.server_port <= 0:
        errors.append("server.port must be a positive integer")
    
    if not config.server_host:
        errors.append("server.host cannot be empty")
    
    # 验证daemon配置
    if config.daemon_mode not in ["host", "docker"]:
        errors.append("daemon.mode must be 'host' or 'docker'")
    
    if not isinstance(config.daemon_port, int) or config.daemon_port <= 0:
        errors.append("daemon.port must be a positive integer")
    
    if config.daemon_mode == "host":
        if not config.daemon_path:
            errors.append("daemon.path is required for host mode")
        elif config.daemon_path and not os.path.exists(config.daemon_path):
            # 在容器环境中，daemon 可能运行在另一个容器中，跳过路径检查
            if not os.path.exists("/.dockerenv"):
                errors.append(f"daemon.path does not exist: {config.daemon_path}")
        elif config.daemon_path and not os.access(config.daemon_path, os.X_OK):
            errors.append(f"daemon.path is not executable: {config.daemon_path}")
    
    if config.daemon_mode == "docker":
        if not config.daemon_container_name:
            errors.append("daemon.container_name is required for docker mode")
    
    # 验证安全配置
    if config.security_enabled and not config.security_api_key:
        errors.append("security.api_key is required when security is enabled")
    
    # 验证代理配置
    if not isinstance(config.proxy_timeout, int) or config.proxy_timeout <= 0:
        errors.append("proxy.timeout must be a positive integer")
    
    if not isinstance(config.proxy_max_retries, int) or config.proxy_max_retries < 0:
        errors.append("proxy.max_retries must be a non-negative integer")
    
    if errors:
        for error in errors:
            logging.error(f"Config validation error: {error}")
        return False
    
    return True


def get_daemon_binary_path() -> Optional[str]:
    """获取daemon二进制文件路径"""
    possible_paths = [
        "/usr/local/bin/daytona",
        "/usr/bin/daytona",
        "./daytona",
        "./daemon",
        os.path.expanduser("~/bin/daytona")
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None


def check_docker_available() -> bool:
    """检查Docker是否可用"""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def get_system_info() -> dict:
    """获取系统信息"""
    import platform
    import psutil
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "disk_usage": psutil.disk_usage('/').percent
    }


def format_bytes(bytes_value: int) -> str:
    """格式化字节数"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """格式化时间长度"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


class GracefulKiller:
    """优雅关闭处理器"""
    
    def __init__(self):
        self.kill_now = False
        import signal
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)
    
    def _exit_gracefully(self, signum, frame):
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.kill_now = True

