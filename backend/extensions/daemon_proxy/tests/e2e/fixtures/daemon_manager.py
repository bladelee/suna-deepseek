"""
Daemon 进程管理器

用于管理真实 daemon 进程的启动、停止和监控
"""

import asyncio
import subprocess
import os
import signal
import time
import logging
import tempfile
import aiohttp
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Optional, Dict, Any


class DaemonManager:
    """Daemon 进程管理器"""
    
    def __init__(self, daemon_binary: str, port: int = 2280, host: str = "127.0.0.1"):
        """
        初始化 Daemon 管理器
        
        Args:
            daemon_binary: daemon 二进制文件路径
            port: daemon 监听端口
            host: daemon 监听地址
        """
        self.daemon_binary = daemon_binary
        self.port = port
        self.host = host
        self.process: Optional[subprocess.Popen] = None
        self.log_file: Optional[tempfile.NamedTemporaryFile] = None
        self.pid_file: Optional[tempfile.NamedTemporaryFile] = None
        self._is_running = False
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    async def start(self, timeout: int = 30) -> str:
        """
        启动 daemon 进程
        
        Args:
            timeout: 启动超时时间（秒）
            
        Returns:
            daemon URL
            
        Raises:
            RuntimeError: 启动失败
        """
        if self._is_running:
            raise RuntimeError("Daemon is already running")
        
        # 检查二进制文件
        if not os.path.exists(self.daemon_binary):
            raise FileNotFoundError(f"Daemon binary not found: {self.daemon_binary}")
        
        if not os.access(self.daemon_binary, os.X_OK):
            raise PermissionError(f"Daemon binary is not executable: {self.daemon_binary}")
        
        # 创建日志文件
        self.log_file = tempfile.NamedTemporaryFile(
            mode='w+', 
            suffix='.log', 
            prefix='daemon-',
            delete=False
        )
        
        # 创建 PID 文件
        self.pid_file = tempfile.NamedTemporaryFile(
            mode='w+', 
            suffix='.pid', 
            prefix='daemon-',
            delete=False
        )
        
        # 构建启动命令
        cmd = [
            self.daemon_binary,
            "daemon",
            "--port", str(self.port)
        ]
        
        self.logger.info(f"Starting daemon: {' '.join(cmd)}")
        self.logger.info(f"Log file: {self.log_file.name}")
        self.logger.info(f"PID file: {self.pid_file.name}")
        
        try:
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,  # 创建新的进程组
                cwd=os.path.dirname(self.daemon_binary)
            )
            
            # 写入 PID
            self.pid_file.write(str(self.process.pid))
            self.pid_file.flush()
            
            self.logger.info(f"Daemon started with PID: {self.process.pid}")
            
            # 等待 daemon 就绪
            daemon_url = f"http://{self.host}:{self.port}"
            await self._wait_for_daemon(daemon_url, timeout)
            
            self._is_running = True
            return daemon_url
            
        except Exception as e:
            self.logger.error(f"Failed to start daemon: {e}")
            await self.stop()
            raise RuntimeError(f"Failed to start daemon: {e}")
    
    async def stop(self, timeout: int = 10):
        """
        停止 daemon 进程
        
        Args:
            timeout: 停止超时时间（秒）
        """
        if not self._is_running and not self.process:
            return
        
        self.logger.info("Stopping daemon...")
        
        if self.process:
            try:
                # 优雅终止
                self.process.terminate()
                
                # 等待进程终止
                try:
                    self.process.wait(timeout=timeout)
                    self.logger.info("Daemon stopped gracefully")
                except subprocess.TimeoutExpired:
                    # 强制终止
                    self.logger.warning("Daemon did not stop gracefully, forcing termination")
                    self.process.kill()
                    self.process.wait(timeout=5)
                    self.logger.info("Daemon force stopped")
                
            except Exception as e:
                self.logger.error(f"Error stopping daemon: {e}")
            finally:
                self.process = None
        
        # 清理文件
        if self.log_file:
            try:
                self.log_file.close()
                # 保留日志文件用于调试
                self.logger.info(f"Daemon log saved to: {self.log_file.name}")
            except Exception as e:
                self.logger.error(f"Error closing log file: {e}")
        
        if self.pid_file:
            try:
                self.pid_file.close()
                os.unlink(self.pid_file.name)
            except Exception as e:
                self.logger.error(f"Error cleaning PID file: {e}")
        
        self._is_running = False
        self.logger.info("Daemon cleanup completed")
    
    async def _wait_for_daemon(self, daemon_url: str, timeout: int):
        """
        等待 daemon 就绪
        
        Args:
            daemon_url: daemon URL
            timeout: 超时时间（秒）
        """
        self.logger.info(f"Waiting for daemon to be ready at {daemon_url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 检查进程是否还在运行
                if self.process and self.process.poll() is not None:
                    raise RuntimeError(f"Daemon process exited with code: {self.process.returncode}")
                
                # 尝试连接 daemon
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{daemon_url}/version", timeout=2) as response:
                        if response.status == 200:
                            self.logger.info("Daemon is ready!")
                            return
                
            except aiohttp.ClientError:
                # 连接失败，继续等待
                pass
            except Exception as e:
                self.logger.warning(f"Error checking daemon status: {e}")
            
            await asyncio.sleep(1)
        
        # 超时
        raise RuntimeError(f"Daemon did not become ready within {timeout} seconds")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        检查 daemon 健康状态
        
        Returns:
            健康状态信息
        """
        if not self._is_running:
            return {"status": "stopped", "running": False}
        
        try:
            daemon_url = f"http://{self.host}:{self.port}"
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{daemon_url}/version", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "running": True,
                            "version": data.get("version", "unknown"),
                            "url": daemon_url
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "running": True,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "running": True,
                "error": str(e)
            }
    
    def get_log_content(self) -> str:
        """
        获取 daemon 日志内容
        
        Returns:
            日志内容
        """
        if not self.log_file:
            return ""
        
        try:
            with open(self.log_file.name, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading log file: {e}")
            return ""
    
    @property
    def is_running(self) -> bool:
        """检查 daemon 是否正在运行"""
        return self._is_running and self.process and self.process.poll() is None
    
    @property
    def daemon_url(self) -> str:
        """获取 daemon URL"""
        return f"http://{self.host}:{self.port}"


@pytest_asyncio.fixture
async def daemon_manager():
    """
    Daemon 管理器 fixture
    
    自动管理 daemon 的启动和停止
    """
    # 检查编译的 daemon
    daemon_binary = "/home/sa/agenthome/extentions/daemon-proxy/tests/e2e/bin/daytona-daemon"
    
    if not os.path.exists(daemon_binary):
        pytest.skip(f"Compiled daemon not found: {daemon_binary}. Run build_daemon.sh first.")
    
    manager = DaemonManager(daemon_binary)
    
    try:
        # 启动 daemon
        daemon_url = await manager.start()
        yield manager
    finally:
        # 停止 daemon
        await manager.stop()


@pytest_asyncio.fixture
async def real_daemon_url(daemon_manager):
    """
    真实 daemon URL fixture
    
    返回正在运行的 daemon URL
    """
    return daemon_manager.daemon_url
