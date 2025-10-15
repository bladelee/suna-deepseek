#!/usr/bin/env python3
"""
Daemon Proxy Service 主程序

一个独立的Python服务，用于代理Daytona daemon的HTTP请求。
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from daemon_proxy import Config, DaemonProxy
from daemon_proxy.utils import setup_logging, validate_config, GracefulKiller


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Daemon Proxy Service")
    parser.add_argument("--config", "-c", help="配置文件路径")
    parser.add_argument("--host", help="服务器主机地址")
    parser.add_argument("--port", type=int, help="服务器端口")
    parser.add_argument("--daemon-mode", choices=["host", "docker"], help="Daemon模式")
    parser.add_argument("--daemon-port", type=int, help="Daemon端口")
    parser.add_argument("--daemon-path", help="Daemon二进制文件路径")
    parser.add_argument("--container-name", help="Docker容器名称")
    parser.add_argument("--binary-source-path", help="Daemon二进制源文件路径")
    parser.add_argument("--injection-mode", choices=["volume", "direct"], help="Daemon注入模式")
    parser.add_argument("--security-enabled", action="store_true", help="启用安全认证")
    parser.add_argument("--api-key", help="API密钥")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="日志级别")
    parser.add_argument("--version", action="version", version="Daemon Proxy 1.0.0")
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config(args.config)
    
    # 命令行参数覆盖配置
    if args.host:
        config.set("server.host", args.host)
    if args.port:
        config.set("server.port", args.port)
    if args.daemon_mode:
        config.set("daemon.mode", args.daemon_mode)
    if args.daemon_port:
        config.set("daemon.port", args.daemon_port)
    if args.daemon_path:
        config.set("daemon.path", args.daemon_path)
    if args.container_name:
        config.set("daemon.container_name", args.container_name)
    if args.binary_source_path:
        config.set("daemon.binary_source_path", args.binary_source_path)
    if args.injection_mode:
        config.set("daemon.injection_mode", args.injection_mode)
    if args.security_enabled:
        config.set("security.enabled", True)
    if args.api_key:
        config.set("security.api_key", args.api_key)
    if args.log_level:
        config.set("logging.level", args.log_level)
    
    # 设置日志
    setup_logging(config)
    
    # 验证配置
    if not validate_config(config):
        logging.error("Configuration validation failed")
        sys.exit(1)
    
    # 显示配置信息
    logging.info("Daemon Proxy Service starting...")
    logging.info(f"Server: {config.server_host}:{config.server_port}")
    logging.info(f"Daemon mode: {config.daemon_mode}")
    logging.info(f"Daemon port: {config.daemon_port}")
    if config.daemon_mode == "host":
        logging.info(f"Daemon path: {config.daemon_path}")
    else:
        logging.info(f"Container name: {config.daemon_container_name}")
        logging.info(f"Injection mode: {config.daemon_injection_mode}")
        if config.daemon_injection_mode == "volume":
            logging.info(f"Binary source path: {config.daemon_binary_source_path}")
    logging.info(f"Security enabled: {config.security_enabled}")
    logging.info(f"Log level: {config.log_level}")
    
    # 创建代理服务
    proxy = DaemonProxy(config)
    
    # 设置优雅关闭
    killer = GracefulKiller()
    
    try:
        # 启动服务
        await proxy.start()
        
        # 保持运行直到收到关闭信号
        while not killer.kill_now:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    except Exception as e:
        logging.error(f"Service error: {e}")
        sys.exit(1)
    finally:
        # 停止服务
        logging.info("Shutting down service...")
        await proxy.stop()
        logging.info("Service stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Service interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

