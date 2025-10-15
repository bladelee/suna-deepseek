#!/usr/bin/env python3
"""
简单使用示例

演示如何使用daemon-proxy服务
"""

import asyncio
import aiohttp
import time


async def example_usage():
    """使用示例"""
    base_url = "http://localhost:8080"
    
    print("Daemon Proxy 使用示例")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        # 1. 检查服务状态
        print("1. 检查服务状态...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 服务状态: {data['status']}")
                    print(f"   📊 运行时间: {data['uptime']:.1f}秒")
                else:
                    print(f"   ❌ 服务状态检查失败: {response.status}")
                    return
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            print("   请确保daemon-proxy服务正在运行")
            return
        
        # 2. 代理到8080端口
        print("\n2. 代理到8080端口...")
        try:
            async with session.get(f"{base_url}/proxy/8080/") as response:
                print(f"   状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   响应: {data}")
                else:
                    text = await response.text()
                    print(f"   错误: {text}")
        except Exception as e:
            print(f"   ❌ 代理请求失败: {e}")
        
        # 3. 代理到特定路径
        print("\n3. 代理到特定路径...")
        try:
            async with session.get(f"{base_url}/proxy/8080/api/status") as response:
                print(f"   状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   响应: {data}")
                else:
                    text = await response.text()
                    print(f"   错误: {text}")
        except Exception as e:
            print(f"   ❌ 代理请求失败: {e}")
        
        # 4. POST请求示例
        print("\n4. POST请求示例...")
        try:
            test_data = {"message": "Hello from daemon-proxy"}
            async with session.post(f"{base_url}/proxy/8080/api/data", 
                                  json=test_data) as response:
                print(f"   状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   响应: {data}")
                else:
                    text = await response.text()
                    print(f"   错误: {text}")
        except Exception as e:
            print(f"   ❌ POST请求失败: {e}")
        
        # 5. 获取指标
        print("\n5. 获取服务指标...")
        try:
            async with session.get(f"{base_url}/metrics") as response:
                if response.status == 200:
                    text = await response.text()
                    print("   📈 服务指标:")
                    for line in text.split('\n'):
                        if line and not line.startswith('#'):
                            print(f"      {line}")
                else:
                    print(f"   ❌ 获取指标失败: {response.status}")
        except Exception as e:
            print(f"   ❌ 获取指标失败: {e}")


async def test_with_authentication():
    """带认证的测试示例"""
    base_url = "http://localhost:8080"
    api_key = "your-secret-key"
    
    print("\n带认证的测试示例")
    print("=" * 40)
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with aiohttp.ClientSession() as session:
        # 测试带认证的请求
        try:
            async with session.get(f"{base_url}/proxy/8080/", headers=headers) as response:
                print(f"   认证请求状态码: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   响应: {data}")
                else:
                    text = await response.text()
                    print(f"   错误: {text}")
        except Exception as e:
            print(f"   ❌ 认证请求失败: {e}")


async def main():
    """主函数"""
    print("开始使用示例...")
    print("请确保daemon-proxy服务正在运行 (python main.py)")
    print("请确保目标服务在8080端口运行")
    print()
    
    # 等待用户确认
    input("按Enter键继续...")
    
    # 运行基本示例
    await example_usage()
    
    # 运行认证示例（可选）
    print("\n" + "=" * 50)
    auth_test = input("是否测试认证功能? (y/N): ").lower().strip()
    if auth_test == 'y':
        await test_with_authentication()
    
    print("\n示例完成!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"示例运行异常: {e}")

