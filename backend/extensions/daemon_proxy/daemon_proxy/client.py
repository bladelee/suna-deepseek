"""
Daemon Proxy 客户端

提供get_preview_link方法，用于获取沙盒中指定端口的预览链接
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PreviewLinkResult:
    """预览链接结果"""
    url: str
    token: str
    port: int
    expires_at: Optional[float] = None


class DaemonProxyClient:
    """Daemon Proxy客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    async def get_preview_link(self, port: int) -> PreviewLinkResult:
        """
        获取指定端口的预览链接
        
        Args:
            port: 目标端口号
            
        Returns:
            PreviewLinkResult对象，包含url和token
            
        Raises:
            Exception: 当请求失败时
        """
        if not self.session:
            raise Exception("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/api/preview/create"
        data = {"port": port}
        headers = self._get_headers()
        headers['Content-Type'] = 'application/json'
        
        try:
            response_cm = await self.session.post(url, json=data, headers=headers)
            async with response_cm as response:
                if response.status == 200:
                    result = await response.json()
                    return PreviewLinkResult(
                        url=result['url'],
                        token=result['token'],
                        port=result['port'],
                        expires_at=result.get('expires_at')
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to create preview link: HTTP {response.status} - {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")
    
    async def revoke_preview_link(self, token: str) -> bool:
        """
        撤销预览链接
        
        Args:
            token: 预览链接的token
            
        Returns:
            bool: 是否成功撤销
        """
        if not self.session:
            raise Exception("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/api/preview/{token}"
        headers = self._get_headers()
        
        try:
            response_cm = await self.session.delete(url, headers=headers)
            async with response_cm as response:
                return response.status == 200
        
        except aiohttp.ClientError:
            return False
    
    async def get_preview_stats(self) -> Dict[str, Any]:
        """
        获取预览链接统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.session:
            raise Exception("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/api/preview/stats"
        headers = self._get_headers()
        
        try:
            response_cm = await self.session.get(url, headers=headers)
            async with response_cm as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get stats: HTTP {response.status}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        if not self.session:
            raise Exception("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/health"
        headers = self._get_headers()
        
        try:
            response_cm = await self.session.get(url, headers=headers)
            async with response_cm as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Health check failed: HTTP {response.status}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")


# 便捷函数
async def get_preview_link(port: int, base_url: str = "http://localhost:8080", 
                          api_key: Optional[str] = None) -> PreviewLinkResult:
    """
    便捷函数：获取预览链接
    
    Args:
        port: 目标端口号
        base_url: 服务基础URL
        api_key: API密钥（可选）
        
    Returns:
        PreviewLinkResult对象
    """
    async with DaemonProxyClient(base_url, api_key) as client:
        return await client.get_preview_link(port)


async def get_vnc_preview_link(base_url: str = "http://localhost:8080", 
                              api_key: Optional[str] = None) -> PreviewLinkResult:
    """
    便捷函数：获取VNC预览链接（6080端口）
    
    Args:
        base_url: 服务基础URL
        api_key: API密钥（可选）
        
    Returns:
        PreviewLinkResult对象
    """
    return await get_preview_link(6080, base_url, api_key)


async def get_website_preview_link(base_url: str = "http://localhost:8080", 
                                  api_key: Optional[str] = None) -> PreviewLinkResult:
    """
    便捷函数：获取网站预览链接（8080端口）
    
    Args:
        base_url: 服务基础URL
        api_key: API密钥（可选）
        
    Returns:
        PreviewLinkResult对象
    """
    return await get_preview_link(8080, base_url, api_key)

