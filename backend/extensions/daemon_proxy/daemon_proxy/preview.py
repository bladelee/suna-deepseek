"""
预览链接管理模块

提供get_preview_link方法，用于获取沙盒中指定端口的预览链接
"""

import asyncio
import aiohttp
import logging
import secrets
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from .config import Config


@dataclass
class PreviewLink:
    """预览链接数据类"""
    url: str
    token: str
    port: int
    expires_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查链接是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class PreviewLinkManager:
    """预览链接管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.links: Dict[str, PreviewLink] = {}
        self.token_to_link: Dict[str, str] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """启动链接管理器"""
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_links())
        logging.info("Preview link manager started")
    
    async def stop(self):
        """停止链接管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logging.info("Preview link manager stopped")
    
    async def get_preview_link(self, port: int, base_url: Optional[str] = None) -> PreviewLink:
        """
        获取指定端口的预览链接
        
        Args:
            port: 目标端口号
            base_url: 基础URL，如果为None则使用配置中的URL
            
        Returns:
            PreviewLink对象，包含url和token
        """
        if base_url is None:
            # 如果服务器绑定到 0.0.0.0，对外使用 localhost
            host = "localhost" if self.config.server_host == "0.0.0.0" else self.config.server_host
            base_url = f"http://{host}:{self.config.server_port}"
        
        # 生成唯一token
        token = self._generate_token()
        
        # 构建预览URL
        preview_url = f"{base_url}/preview/{token}"
        
        # 创建预览链接
        link = PreviewLink(
            url=preview_url,
            token=token,
            port=port,
            expires_at=time.time() + 3600  # 1小时过期
        )
        
        # 存储链接
        self.links[token] = link
        self.token_to_link[token] = token
        
        logging.info(f"Created preview link for port {port}: {preview_url}")
        
        return link
    
    def _generate_token(self) -> str:
        """生成安全的token"""
        return secrets.token_urlsafe(32)
    
    def get_link_by_token(self, token: str) -> Optional[PreviewLink]:
        """根据token获取链接"""
        return self.links.get(token)
    
    def revoke_link(self, token: str) -> bool:
        """撤销链接"""
        if token in self.links:
            del self.links[token]
            if token in self.token_to_link:
                del self.token_to_link[token]
            logging.info(f"Revoked preview link: {token}")
            return True
        return False
    
    async def _cleanup_expired_links(self):
        """清理过期的链接"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                
                expired_tokens = []
                for token, link in self.links.items():
                    if link.is_expired():
                        expired_tokens.append(token)
                
                for token in expired_tokens:
                    self.revoke_link(token)
                
                if expired_tokens:
                    logging.info(f"Cleaned up {len(expired_tokens)} expired preview links")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in cleanup task: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_links = len(self.links)
        expired_links = sum(1 for link in self.links.values() if link.is_expired())
        active_links = total_links - expired_links
        
        return {
            "total_links": total_links,
            "active_links": active_links,
            "expired_links": expired_links
        }


class PreviewHandler:
    """预览请求处理器"""
    
    def __init__(self, link_manager: PreviewLinkManager, daemon_manager):
        self.link_manager = link_manager
        self.daemon_manager = daemon_manager
    
    async def handle_preview_request(self, request) -> aiohttp.web.Response:
        """处理预览请求"""
        token = request.match_info['token']
        
        # 获取链接信息
        link = self.link_manager.get_link_by_token(token)
        if not link:
            return aiohttp.web.Response(
                text="Preview link not found or expired",
                status=404
            )
        
        if link.is_expired():
            self.link_manager.revoke_link(token)
            return aiohttp.web.Response(
                text="Preview link has expired",
                status=410
            )
        
        # 获取请求路径
        path = request.match_info.get('path', '')
        
        # 准备请求数据
        headers = dict(request.headers)
        body = None
        if request.can_read_body:
            body = await request.read()
        
        try:
            # 直接使用链接的端口，不需要端口映射
            target_port = str(link.port)
            
            # 代理请求到目标端口
            response = await self.daemon_manager.proxy_request(
                port=target_port,
                path=path,
                method=request.method,
                headers=headers,
                data=body,
                query_string=request.query_string
            )
            
            # 读取响应体
            response_body = await response.read()
            
            # 创建响应
            return aiohttp.web.Response(
                body=response_body,
                status=response.status,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            logging.error(f"Preview proxy error for {link.port}/{path}: {e}")
            return aiohttp.web.Response(
                text=f"Preview proxy error: {str(e)}",
                status=502
            )

