#!/usr/bin/env python3
"""
E2E 测试运行脚本

用于快速运行和验证 E2E 测试
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 成功!")
            if result.stdout:
                print("输出:")
                print(result.stdout)
        else:
            print("❌ 失败!")
            if result.stderr:
                print("错误:")
                print(result.stderr)
            if result.stdout:
                print("输出:")
                print(result.stdout)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ 超时!")
        return False
    except Exception as e:
        print(f"💥 异常: {e}")
        return False


def main():
    """主函数"""
    print("daemon-proxy E2E 测试运行器")
    print("="*60)
    
    # 检查当前目录
    if not os.path.exists("main.py"):
        print("❌ 请在 daemon-proxy 项目根目录运行此脚本")
        sys.exit(1)
    
    # 检查 Python 环境
    print(f"Python 版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    # 测试列表
    tests = [
        {
            "cmd": "python -m pytest tests/e2e/test_e2e_mock.py::TestE2EMock::test_mock_environment_setup -v",
            "description": "Mock 环境基础测试"
        },
        {
            "cmd": "python -m pytest tests/e2e/test_e2e_mock.py::TestE2EMock::test_preview_link_creation_vnc -v",
            "description": "Mock 环境 VNC 预览链接测试"
        },
        {
            "cmd": "python -m pytest tests/e2e/test_e2e_mock.py::TestE2EMock::test_preview_link_creation_web -v",
            "description": "Mock 环境 Web 预览链接测试"
        },
        {
            "cmd": "python -m pytest tests/e2e/test_e2e_mock.py::TestE2EMock::test_preview_link_lifecycle -v",
            "description": "Mock 环境预览链接生命周期测试"
        }
    ]
    
    # 运行测试
    success_count = 0
    total_count = len(tests)
    
    for test in tests:
        if run_command(test["cmd"], test["description"]):
            success_count += 1
    
    # 显示总结
    print(f"\n{'='*60}")
    print("测试总结")
    print('='*60)
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n💥 {total_count - success_count} 个测试失败!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试运行异常: {e}")
        sys.exit(1)
