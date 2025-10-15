"""
Docker 测试辅助工具

用于 E2E Docker 环境测试的辅助函数
"""

import asyncio
import aiohttp
import docker
import logging
import time
from typing import Dict, List, Optional, Tuple
import tempfile
import os
from pathlib import Path
import pytest


class DockerTestEnvironment:
    """Docker 测试环境管理器"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.containers: List[docker.models.containers.Container] = []
        self.networks: List[docker.models.networks.Network] = []
        self.volumes: List[docker.models.volumes.Volume] = []
        
    async def start_environment(self, compose_file: str = None) -> Dict[str, str]:
        """启动 Docker 测试环境"""
        try:
            if compose_file and os.path.exists(compose_file):
                return await self._start_with_compose(compose_file)
            else:
                return await self._start_manual_environment()
        except Exception as e:
            logging.error(f"Failed to start Docker environment: {e}")
            await self.cleanup()
            raise
    
    async def _start_with_compose(self, compose_file: str) -> Dict[str, str]:
        """使用 docker-compose 启动环境"""
        import subprocess
        
        # 尝试使用 docker compose 命令（新版本）
        commands = [
            ['docker', 'compose', '-f', compose_file, 'up', '-d'],
            ['docker-compose', '-f', compose_file, 'up', '-d']
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    break
            except FileNotFoundError:
                continue
        else:
            raise Exception(f"Failed to start compose: {result.stderr}")
        
        # 等待服务启动
        await asyncio.sleep(10)
        
        # 获取服务信息
        services = {}
        containers = self.client.containers.list(filters={'status': 'running'})
        
        for container in containers:
            if 'daemon-proxy' in container.name:
                # 查找 8080 端口映射
                for port_info in container.ports.get('8080/tcp', []):
                    if port_info.get('HostPort'):
                        services['daemon-proxy'] = f"http://localhost:{port_info['HostPort']}"
                        break
            elif 'static-website-simple' in container.name:
                # 查找 80 端口映射
                for port_info in container.ports.get('80/tcp', []):
                    if port_info.get('HostPort'):
                        services['static-simple'] = f"http://localhost:{port_info['HostPort']}"
                        break
            elif 'static-website-complete' in container.name:
                # 查找 80 端口映射
                for port_info in container.ports.get('80/tcp', []):
                    if port_info.get('HostPort'):
                        services['static-complete'] = f"http://localhost:{port_info['HostPort']}"
                        break
            elif 'vnc-service' in container.name:
                # 查找 6080 端口映射
                for port_info in container.ports.get('6080/tcp', []):
                    if port_info.get('HostPort'):
                        services['vnc-service'] = f"http://localhost:{port_info['HostPort']}"
                        break
            elif 'web-service' in container.name:
                # 查找 8080 端口映射
                for port_info in container.ports.get('8080/tcp', []):
                    if port_info.get('HostPort'):
                        services['web-service'] = f"http://localhost:{port_info['HostPort']}"
                        break
        
        return services
    
    async def _start_manual_environment(self) -> Dict[str, str]:
        """手动启动环境"""
        services = {}
        
        # 创建网络
        network = self.client.networks.create(
            "e2e-test-network",
            driver="bridge"
        )
        self.networks.append(network)
        
        # 启动 mock VNC 服务
        vnc_container = self.client.containers.run(
            "python:3.9-slim",
            command="python -m http.server 6080",
            ports={'6080/tcp': 6080},
            network="e2e-test-network",
            name="e2e-mock-vnc",
            detach=True,
            remove=True
        )
        self.containers.append(vnc_container)
        services['mock-vnc'] = "http://localhost:6080"
        
        # 启动 mock Web 服务
        web_container = self.client.containers.run(
            "python:3.9-slim",
            command="python -m http.server 8080",
            ports={'8080/tcp': 8081},  # 避免端口冲突
            network="e2e-test-network",
            name="e2e-mock-web",
            detach=True,
            remove=True
        )
        self.containers.append(web_container)
        services['mock-web'] = "http://localhost:8081"
        
        # 等待服务启动
        await asyncio.sleep(5)
        
        return services
    
    async def wait_for_service(self, url: str, timeout: int = 60) -> bool:
        """等待服务就绪"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            return True
            except Exception:
                pass
            
            await asyncio.sleep(2)
        
        return False
    
    async def cleanup(self):
        """清理 Docker 环境"""
        # 停止容器
        for container in self.containers:
            try:
                container.stop(timeout=5)
            except Exception as e:
                logging.warning(f"Failed to stop container {container.name}: {e}")
        
        # 删除网络
        for network in self.networks:
            try:
                network.remove()
            except Exception as e:
                logging.warning(f"Failed to remove network {network.name}: {e}")
        
        # 删除卷
        for volume in self.volumes:
            try:
                volume.remove()
            except Exception as e:
                logging.warning(f"Failed to remove volume {volume.name}: {e}")
        
        # 清理 compose 环境
        try:
            import subprocess
            # 尝试使用 docker compose 命令（新版本）
            commands = [
                ['docker', 'compose', '-f', 'docker-compose-e2e.yml', 'down', '-v'],
                ['docker-compose', '-f', 'docker-compose-e2e.yml', 'down', '-v']
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(cmd, capture_output=True)
                    break
                except FileNotFoundError:
                    continue
        except Exception:
            pass
        
        self.containers.clear()
        self.networks.clear()
        self.volumes.clear()


def create_docker_compose_e2e():
    """创建 E2E 测试用的 docker-compose 文件"""
    compose_content = """
version: '3.8'

services:
  daemon-proxy:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DAEMON_PROXY_HOST=0.0.0.0
      - DAEMON_PROXY_PORT=8080
      - DAEMON_MODE=docker
      - DAEMON_PORT=2280
      - DAEMON_CONTAINER_NAME=test-daemon
      - SECURITY_ENABLED=false
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    networks:
      - e2e-network
    depends_on:
      - test-daemon
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  test-daemon:
    image: python:3.9-slim
    command: |
      bash -c "
        apt-get update && 
        apt-get install -y curl &&
        python -m http.server 2280 &
        tail -f /dev/null
      "
    ports:
      - "2280:2280"
    networks:
      - e2e-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:2280/"]
      interval: 10s
      timeout: 5s
      retries: 3

  mock-vnc:
    image: python:3.9-slim
    command: |
      bash -c "
        apt-get update && 
        apt-get install -y curl &&
        python -m http.server 6080 &
        tail -f /dev/null
      "
    ports:
      - "6080:6080"
    networks:
      - e2e-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6080/"]
      interval: 10s
      timeout: 5s
      retries: 3

  mock-web:
    image: python:3.9-slim
    command: |
      bash -c "
        apt-get update && 
        apt-get install -y curl &&
        python -m http.server 8080 &
        tail -f /dev/null
      "
    ports:
      - "8081:8080"  # 避免与 daemon-proxy 端口冲突
    networks:
      - e2e-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  e2e-network:
    driver: bridge

volumes:
  logs:
"""
    
    with open('docker-compose-e2e.yml', 'w') as f:
        f.write(compose_content)
    
    return 'docker-compose-e2e.yml'


# Pytest fixtures
@pytest.fixture
async def docker_environment():
    """Docker 测试环境 fixture"""
    env = DockerTestEnvironment()
    
    # 创建 compose 文件
    compose_file = create_docker_compose_e2e()
    
    try:
        services = await env.start_environment(compose_file)
        yield env, services
    finally:
        await env.cleanup()
        # 清理 compose 文件
        if os.path.exists(compose_file):
            os.remove(compose_file)


@pytest.fixture
async def docker_services(docker_environment):
    """Docker 服务 fixture"""
    env, services = docker_environment
    return services
