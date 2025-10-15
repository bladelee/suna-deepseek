#!/usr/bin/env python3
"""
服务测试脚本

用于快速测试daemon-proxy服务是否正常工作
"""

import asyncio
import aiohttp
import time
import sys
import argparse
from typing import Optional


async def test_service(base_url: str, timeout: int = 30):
    """测试服务功能"""
    print(f"测试服务: {base_url}")
    print("=" * 50)
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        # 测试1: 健康检查
        print("1. 测试健康检查...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 健康检查通过: {data['status']}")
                    print(f"   📊 运行时间: {data.get('uptime', 0):.1f}秒")
                    print(f"   📈 请求数: {data.get('request_count', 0)}")
                else:
                    print(f"   ❌ 健康检查失败: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 健康检查异常: {e}")
            return False
        
        # 测试2: Daemon状态
        print("\n2. 测试Daemon状态...")
        try:
            async with session.get(f"{base_url}/daemon/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Daemon状态: {data['status']}")
                    if 'version' in data:
                        print(f"   📦 版本: {data['version']}")
                else:
                    print(f"   ❌ Daemon状态检查失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Daemon状态检查异常: {e}")
        
        # 测试3: 代理功能
        print("\n3. 测试代理功能...")
        test_ports = [8080, 3000, 5000]
        
        for port in test_ports:
            try:
                async with session.get(f"{base_url}/proxy/{port}/") as response:
                    if response.status == 200:
                        print(f"   ✅ 端口 {port} 代理成功")
                    elif response.status == 502:
                        print(f"   ⚠️  端口 {port} 代理失败 (目标服务不可用)")
                    else:
                        print(f"   ❌ 端口 {port} 代理失败: HTTP {response.status}")
            except Exception as e:
                print(f"   ❌ 端口 {port} 代理异常: {e}")
        
        # 测试4: 指标端点
        print("\n4. 测试指标端点...")
        try:
            async with session.get(f"{base_url}/metrics") as response:
                if response.status == 200:
                    text = await response.text()
                    if "daemon_proxy_requests_total" in text:
                        print("   ✅ 指标端点正常")
                    else:
                        print("   ⚠️  指标端点响应格式异常")
                else:
                    print(f"   ❌ 指标端点失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 指标端点异常: {e}")
        
        # 测试5: 根路径
        print("\n5. 测试根路径...")
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 服务信息: {data.get('service', 'Unknown')}")
                    print(f"   📋 版本: {data.get('version', 'Unknown')}")
                else:
                    print(f"   ❌ 根路径失败: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ 根路径异常: {e}")
        
        print("\n" + "=" * 50)
        print("测试完成!")
        return True


async def wait_for_service(base_url: str, max_wait: int = 60):
    """等待服务启动"""
    print(f"等待服务启动: {base_url}")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        print("✅ 服务已启动!")
                        return True
        except Exception:
            pass
        
        print(".", end="", flush=True)
        await asyncio.sleep(2)
    
    print(f"\n❌ 服务在 {max_wait} 秒内未启动")
    return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试daemon-proxy服务")
    parser.add_argument("--url", default="http://localhost:8080", help="服务URL")
    parser.add_argument("--wait", type=int, default=0, help="等待服务启动的时间（秒）")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间（秒）")
    
    args = parser.parse_args()
    
    # 等待服务启动
    if args.wait > 0:
        if not await wait_for_service(args.url, args.wait):
            sys.exit(1)
    
    # 测试服务
    success = await test_service(args.url, args.timeout)
    
    if success:
        print("🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("💥 测试失败!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试异常: {e}")
        sys.exit(1)

