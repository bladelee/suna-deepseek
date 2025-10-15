#!/usr/bin/env python3
"""
预览链接使用示例

演示如何使用get_preview_link方法获取VNC和网站预览链接
"""

import asyncio
import aiohttp
from daemon_proxy.client import DaemonProxyClient, get_preview_link, get_vnc_preview_link, get_website_preview_link


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 方式1: 使用便捷函数
    try:
        # 获取VNC预览链接（6080端口）
        vnc_link = await get_vnc_preview_link()
        print(f"VNC预览链接: {vnc_link.url}")
        print(f"Token: {vnc_link.token}")
        print(f"端口: {vnc_link.port}")
        print(f"过期时间: {vnc_link.expires_at}")
        
        # 获取网站预览链接（8080端口）
        website_link = await get_website_preview_link()
        print(f"\n网站预览链接: {website_link.url}")
        print(f"Token: {website_link.token}")
        print(f"端口: {website_link.port}")
        
    except Exception as e:
        print(f"错误: {e}")


async def example_client_usage():
    """客户端使用示例"""
    print("\n=== 客户端使用示例 ===")
    
    # 方式2: 使用客户端类
    async with DaemonProxyClient("http://localhost:8080") as client:
        try:
            # 健康检查
            health = await client.health_check()
            print(f"服务状态: {health['status']}")
            
            # 获取VNC预览链接
            vnc_link = await client.get_preview_link(6080)
            print(f"VNC预览链接: {vnc_link.url}")
            
            # 获取网站预览链接
            website_link = await client.get_preview_link(8080)
            print(f"网站预览链接: {website_link.url}")
            
            # 获取统计信息
            stats = await client.get_preview_stats()
            print(f"预览链接统计: {stats}")
            
        except Exception as e:
            print(f"错误: {e}")


async def example_with_authentication():
    """带认证的使用示例"""
    print("\n=== 带认证的使用示例 ===")
    
    api_key = "your-secret-key"
    
    async with DaemonProxyClient("http://localhost:8080", api_key) as client:
        try:
            # 获取预览链接
            vnc_link = await client.get_preview_link(6080)
            print(f"VNC预览链接: {vnc_link.url}")
            
            # 撤销链接
            success = await client.revoke_preview_link(vnc_link.token)
            print(f"撤销链接: {'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"错误: {e}")


async def example_sandbox_style():
    """沙盒风格的使用示例（模拟Daytona SDK）"""
    print("\n=== 沙盒风格使用示例 ===")
    
    class Sandbox:
        """模拟沙盒类"""
        
        def __init__(self, client: DaemonProxyClient):
            self.client = client
        
        async def get_preview_link(self, port: int):
            """获取预览链接（模拟Daytona SDK方法）"""
            return await self.client.get_preview_link(port)
    
    async with DaemonProxyClient("http://localhost:8080") as client:
        sandbox = Sandbox(client)
        
        try:
            # 模拟Daytona SDK的使用方式
            vnc_link = await sandbox.get_preview_link(6080)
            website_link = await sandbox.get_preview_link(8080)
            
            # 提取URL和Token（模拟tool_base.py的处理方式）
            vnc_url = vnc_link.url if hasattr(vnc_link, 'url') else str(vnc_link).split("url='")[1].split("'")[0]
            website_url = website_link.url if hasattr(website_link, 'url') else str(website_link).split("url='")[1].split("'")[0]
            token = vnc_link.token if hasattr(vnc_link, 'token') else str(vnc_link).split("token='")[1].split("'")[0]
            
            print(f"VNC URL: {vnc_url}")
            print(f"Website URL: {website_url}")
            print(f"Token: {token}")
            
        except Exception as e:
            print(f"错误: {e}")


async def example_test_preview_links():
    """测试预览链接功能"""
    print("\n=== 测试预览链接功能 ===")
    
    async with DaemonProxyClient("http://localhost:8080") as client:
        try:
            # 创建预览链接
            vnc_link = await client.get_preview_link(6080)
            print(f"创建VNC预览链接: {vnc_link.url}")
            
            # 测试访问预览链接
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(vnc_link.url) as response:
                        print(f"预览链接访问状态: {response.status}")
                        if response.status == 200:
                            print("✅ 预览链接工作正常")
                        else:
                            print("⚠️ 预览链接可能有问题")
                except Exception as e:
                    print(f"预览链接访问失败: {e}")
            
            # 撤销链接
            success = await client.revoke_preview_link(vnc_link.token)
            print(f"撤销链接: {'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"错误: {e}")


async def example_multiple_ports():
    """多端口示例"""
    print("\n=== 多端口示例 ===")
    
    ports = [6080, 8080, 3000, 5000, 9000]
    
    async with DaemonProxyClient("http://localhost:8080") as client:
        links = []
        
        try:
            # 为多个端口创建预览链接
            for port in ports:
                try:
                    link = await client.get_preview_link(port)
                    links.append(link)
                    print(f"端口 {port}: {link.url}")
                except Exception as e:
                    print(f"端口 {port} 创建失败: {e}")
            
            # 显示统计信息
            stats = await client.get_preview_stats()
            print(f"\n统计信息: {stats}")
            
            # 清理所有链接
            for link in links:
                await client.revoke_preview_link(link.token)
            
            print("所有链接已清理")
            
        except Exception as e:
            print(f"错误: {e}")


async def main():
    """主函数"""
    print("Daemon Proxy 预览链接使用示例")
    print("=" * 50)
    print("请确保daemon-proxy服务正在运行")
    print("请确保目标服务在相应端口运行")
    print()
    
    # 等待用户确认
    input("按Enter键继续...")
    
    # 运行各种示例
    await example_basic_usage()
    await example_client_usage()
    await example_with_authentication()
    await example_sandbox_style()
    await example_test_preview_links()
    await example_multiple_ports()
    
    print("\n示例完成!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"示例运行异常: {e}")

