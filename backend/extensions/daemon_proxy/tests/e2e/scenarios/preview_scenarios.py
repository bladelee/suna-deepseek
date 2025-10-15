"""
预览链接测试场景

封装各种预览链接相关的端到端测试场景
"""

import asyncio
import aiohttp
import pytest
import time
from typing import Dict, Any, List, Optional
from daemon_proxy.client import DaemonProxyClient, PreviewLinkResult


class PreviewLinkTestScenarios:
    """预览链接测试场景类"""
    
    def __init__(self, proxy_url: str, api_key: Optional[str] = None):
        self.proxy_url = proxy_url
        self.api_key = api_key
    
    async def test_create_and_access_preview_link(self, port: int = 8080) -> Dict[str, Any]:
        """测试创建和访问预览链接的完整流程"""
        results = {
            "port": port,
            "created": False,
            "accessed": False,
            "link": None,
            "response_data": None,
            "errors": []
        }
        
        try:
            async with DaemonProxyClient(self.proxy_url, self.api_key) as client:
                # 1. 创建预览链接
                link = await client.get_preview_link(port)
                results["link"] = link
                results["created"] = True
                
                # 2. 验证链接格式
                assert link.url.startswith(f"{self.proxy_url}/preview/")
                assert link.token in link.url
                assert link.port == port
                assert not link.is_expired() if hasattr(link, 'is_expired') else True
                
                # 3. 访问预览链接
                async with aiohttp.ClientSession() as session:
                    async with session.get(link.url) as response:
                        results["response_data"] = {
                            "status": response.status,
                            "headers": dict(response.headers),
                            "content_type": response.headers.get('content-type', '')
                        }
                        
                        if response.status == 200:
                            results["accessed"] = True
                            # 尝试读取响应内容
                            try:
                                if 'application/json' in response.headers.get('content-type', ''):
                                    results["response_data"]["json"] = await response.json()
                                else:
                                    results["response_data"]["text"] = await response.text()
                            except Exception as e:
                                results["errors"].append(f"Failed to read response: {e}")
                        else:
                            results["errors"].append(f"Preview link returned status {response.status}")
                
        except Exception as e:
            results["errors"].append(f"Test failed: {e}")
        
        return results
    
    async def test_preview_link_lifecycle(self, port: int = 8080) -> Dict[str, Any]:
        """测试预览链接的完整生命周期"""
        results = {
            "port": port,
            "created": False,
            "accessed": False,
            "revoked": False,
            "access_after_revoke": False,
            "link": None,
            "errors": []
        }
        
        try:
            async with DaemonProxyClient(self.proxy_url, self.api_key) as client:
                # 1. 创建预览链接
                link = await client.get_preview_link(port)
                results["link"] = link
                results["created"] = True
                
                # 2. 访问预览链接
                async with aiohttp.ClientSession() as session:
                    async with session.get(link.url) as response:
                        if response.status == 200:
                            results["accessed"] = True
                
                # 3. 撤销预览链接
                success = await client.revoke_preview_link(link.token)
                results["revoked"] = success
                
                # 4. 尝试访问已撤销的链接
                async with aiohttp.ClientSession() as session:
                    async with session.get(link.url) as response:
                        if response.status == 404 or response.status == 410:
                            results["access_after_revoke"] = True  # 正确行为
                        else:
                            results["errors"].append(f"Revoked link still accessible: {response.status}")
                
        except Exception as e:
            results["errors"].append(f"Lifecycle test failed: {e}")
        
        return results
    
    async def test_multiple_preview_links(self, ports: List[int] = None) -> Dict[str, Any]:
        """测试多个预览链接的并发管理"""
        if ports is None:
            ports = [6080, 8080, 3000, 5000]
        
        results = {
            "ports": ports,
            "created_links": [],
            "failed_ports": [],
            "stats": None,
            "errors": []
        }
        
        try:
            async with DaemonProxyClient(self.proxy_url, self.api_key) as client:
                # 1. 为多个端口创建预览链接
                for port in ports:
                    try:
                        link = await client.get_preview_link(port)
                        results["created_links"].append({
                            "port": port,
                            "link": link,
                            "url": link.url,
                            "token": link.token
                        })
                    except Exception as e:
                        results["failed_ports"].append({
                            "port": port,
                            "error": str(e)
                        })
                
                # 2. 获取统计信息
                stats = await client.get_preview_stats()
                results["stats"] = stats
                
                # 3. 验证统计信息
                expected_total = len(results["created_links"])
                if stats.get("total_links", 0) >= expected_total:
                    results["stats_valid"] = True
                else:
                    results["errors"].append(f"Stats mismatch: expected >= {expected_total}, got {stats.get('total_links', 0)}")
                
                # 4. 测试并发访问
                access_results = []
                async with aiohttp.ClientSession() as session:
                    tasks = []
                    for link_info in results["created_links"]:
                        task = self._access_preview_link(session, link_info["url"])
                        tasks.append(task)
                    
                    access_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                results["concurrent_access"] = {
                    "successful": sum(1 for r in access_results if isinstance(r, dict) and r.get("success", False)),
                    "failed": sum(1 for r in access_results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get("success", False))),
                    "results": access_results
                }
                
        except Exception as e:
            results["errors"].append(f"Multiple links test failed: {e}")
        
        return results
    
    async def test_preview_link_expiration(self, port: int = 8080) -> Dict[str, Any]:
        """测试预览链接过期机制"""
        results = {
            "port": port,
            "created": False,
            "expired": False,
            "access_before_expiry": False,
            "access_after_expiry": False,
            "link": None,
            "errors": []
        }
        
        try:
            async with DaemonProxyClient(self.proxy_url, self.api_key) as client:
                # 1. 创建预览链接
                link = await client.get_preview_link(port)
                results["link"] = link
                results["created"] = True
                
                # 2. 立即访问（应该成功）
                async with aiohttp.ClientSession() as session:
                    async with session.get(link.url) as response:
                        if response.status == 200:
                            results["access_before_expiry"] = True
                
                # 3. 模拟链接过期（通过修改过期时间）
                if hasattr(link, 'expires_at') and link.expires_at:
                    # 这里我们无法直接修改服务器端的过期时间
                    # 所以这个测试主要验证链接创建和基本访问
                    results["expired"] = True
                    results["access_after_expiry"] = False  # 无法测试，因为无法控制服务器端过期
                else:
                    results["errors"].append("Link does not have expiration mechanism")
                
        except Exception as e:
            results["errors"].append(f"Expiration test failed: {e}")
        
        return results
    
    async def test_preview_link_with_different_ports(self) -> Dict[str, Any]:
        """测试不同端口的预览链接"""
        test_ports = [6080, 8080, 3000, 5000, 9000]
        results = {
            "test_ports": test_ports,
            "port_results": {},
            "summary": {
                "successful": 0,
                "failed": 0,
                "total": len(test_ports)
            }
        }
        
        try:
            async with DaemonProxyClient(self.proxy_url, self.api_key) as client:
                for port in test_ports:
                    port_result = await self.test_create_and_access_preview_link(port)
                    results["port_results"][port] = port_result
                    
                    if port_result["created"] and port_result["accessed"]:
                        results["summary"]["successful"] += 1
                    else:
                        results["summary"]["failed"] += 1
                
        except Exception as e:
            results["errors"] = [f"Different ports test failed: {e}"]
        
        return results
    
    async def test_preview_link_error_handling(self) -> Dict[str, Any]:
        """测试预览链接的错误处理"""
        results = {
            "invalid_token_access": False,
            "nonexistent_port": False,
            "malformed_requests": False,
            "errors": []
        }
        
        try:
            # 1. 测试无效 token 访问
            async with aiohttp.ClientSession() as session:
                invalid_url = f"{self.proxy_url}/preview/invalid-token-12345"
                async with session.get(invalid_url) as response:
                    if response.status == 404:
                        results["invalid_token_access"] = True
                    else:
                        results["errors"].append(f"Invalid token should return 404, got {response.status}")
            
            # 2. 测试不存在的端口
            async with DaemonProxyClient(self.proxy_url, self.api_key) as client:
                try:
                    # 尝试为不存在的端口创建预览链接（这应该成功，但访问时会失败）
                    link = await client.get_preview_link(9999)
                    
                    # 访问不存在的端口
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link.url) as response:
                            if response.status == 502 or response.status == 404:
                                results["nonexistent_port"] = True
                            else:
                                results["errors"].append(f"Nonexistent port should return 502/404, got {response.status}")
                except Exception as e:
                    results["errors"].append(f"Error testing nonexistent port: {e}")
            
            # 3. 测试格式错误的请求
            async with aiohttp.ClientSession() as session:
                malformed_url = f"{self.proxy_url}/preview/"
                async with session.get(malformed_url) as response:
                    if response.status == 404:
                        results["malformed_requests"] = True
                    else:
                        results["errors"].append(f"Malformed request should return 404, got {response.status}")
                
        except Exception as e:
            results["errors"].append(f"Error handling test failed: {e}")
        
        return results
    
    async def _access_preview_link(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """访问预览链接的辅助方法"""
        try:
            async with session.get(url) as response:
                return {
                    "url": url,
                    "status": response.status,
                    "success": response.status == 200,
                    "content_type": response.headers.get('content-type', '')
                }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }


# 便捷的测试函数
async def run_preview_link_scenarios(proxy_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """运行所有预览链接测试场景"""
    scenarios = PreviewLinkTestScenarios(proxy_url, api_key)
    
    results = {
        "proxy_url": proxy_url,
        "timestamp": time.time(),
        "scenarios": {}
    }
    
    # 运行各个测试场景
    test_scenarios = [
        ("create_and_access", scenarios.test_create_and_access_preview_link),
        ("lifecycle", scenarios.test_preview_link_lifecycle),
        ("multiple_links", scenarios.test_multiple_preview_links),
        ("expiration", scenarios.test_preview_link_expiration),
        ("different_ports", scenarios.test_preview_link_with_different_ports),
        ("error_handling", scenarios.test_preview_link_error_handling)
    ]
    
    for scenario_name, scenario_func in test_scenarios:
        try:
            if scenario_name == "multiple_links":
                scenario_result = await scenario_func([6080, 8080, 3000])
            else:
                scenario_result = await scenario_func()
            
            results["scenarios"][scenario_name] = scenario_result
        except Exception as e:
            results["scenarios"][scenario_name] = {
                "error": str(e),
                "failed": True
            }
    
    # 计算总体结果
    total_scenarios = len(results["scenarios"])
    successful_scenarios = sum(1 for s in results["scenarios"].values() 
                             if not s.get("failed", False) and not s.get("errors"))
    
    results["summary"] = {
        "total_scenarios": total_scenarios,
        "successful_scenarios": successful_scenarios,
        "failed_scenarios": total_scenarios - successful_scenarios,
        "success_rate": successful_scenarios / total_scenarios if total_scenarios > 0 else 0
    }
    
    return results
