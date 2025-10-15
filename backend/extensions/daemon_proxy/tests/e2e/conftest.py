"""
E2E 测试共享配置和 fixtures
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from daemon_proxy import Config


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest_asyncio.fixture
def base_config():
    """基础测试配置"""
    config = Config()
    config.set("server.host", "127.0.0.1")
    config.set("server.port", 0)  # 使用随机端口
    config.set("daemon.mode", "host")
    config.set("daemon.port", 2280)
    config.set("daemon.path", "/usr/local/bin/daytona")
    config.set("daemon.startup_timeout", 5)
    config.set("security.enabled", False)
    config.set("proxy.timeout", 10)
    config.set("logging.level", "WARNING")  # 减少测试日志
    return config


@pytest_asyncio.fixture
def mock_config():
    """Mock 环境配置"""
    config = Config()
    config.set("server.host", "127.0.0.1")
    config.set("server.port", 0)  # 使用随机端口
    config.set("daemon.mode", "mock")  # 使用 mock 模式
    config.set("daemon.port", 2280)
    config.set("daemon.path", "/usr/local/bin/daytona")
    config.set("daemon.startup_timeout", 5)
    config.set("security.enabled", False)
    config.set("proxy.timeout", 10)
    config.set("logging.level", "WARNING")  # 减少测试日志
    return config


@pytest_asyncio.fixture
def real_daemon_config():
    """真实 daemon 配置"""
    config = Config()
    config.set("server.host", "127.0.0.1")
    config.set("server.port", 0)  # 使用随机端口
    config.set("daemon.mode", "host")
    config.set("daemon.port", 2280)
    config.set("daemon.path", "/usr/local/bin/daytona")
    config.set("daemon.startup_timeout", 5)
    config.set("security.enabled", False)
    config.set("proxy.timeout", 10)
    config.set("logging.level", "WARNING")  # 减少测试日志
    return config


@pytest_asyncio.fixture
def docker_config():
    """Docker 环境配置"""
    config = Config()
    config.set("server.host", "127.0.0.1")
    config.set("server.port", 0)  # 使用随机端口
    config.set("daemon.mode", "docker")
    config.set("daemon.container_name", "test-daemon")
    config.set("daemon.port", 2280)
    config.set("daemon.path", "/usr/local/bin/daytona")
    config.set("daemon.startup_timeout", 5)
    config.set("security.enabled", False)
    config.set("proxy.timeout", 10)
    config.set("logging.level", "WARNING")  # 减少测试日志
    return config


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "e2e_mock: 标记为 E2E Mock 环境测试"
    )
    config.addinivalue_line(
        "markers", "e2e_real: 标记为 E2E 真实 daemon 测试"
    )
    config.addinivalue_line(
        "markers", "e2e_docker: 标记为 E2E Docker 环境测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 如果没有指定标记，默认运行所有测试
    if not any(mark in config.option.markexpr for mark in ["e2e_mock", "e2e_real", "e2e_docker"]):
        return
    
    # 根据标记过滤测试
    for item in items:
        if "e2e_mock" in item.keywords:
            item.add_marker(pytest.mark.e2e_mock)
        elif "e2e_real" in item.keywords:
            item.add_marker(pytest.mark.e2e_real)
        elif "e2e_docker" in item.keywords:
            item.add_marker(pytest.mark.e2e_docker)
