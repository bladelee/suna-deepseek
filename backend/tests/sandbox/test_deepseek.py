#!/usr/bin/env python3
"""
DeepSeek 集成测试脚本

此脚本用于测试 DeepSeek 模型的集成是否正常工作。
运行前请确保已设置 DEEPSEEK_API_KEY 环境变量。
"""

import asyncio
import os
import sys
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm import make_llm_api_call
from utils.logger import logger

async def test_deepseek_basic():
    """测试 DeepSeek 基本功能"""
    print("🧪 测试 DeepSeek 基本功能...")
    
    try:
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "你好，请用中文简单介绍一下自己"}
            ],
            model_name="deepseek/deepseek-chat",
            temperature=0.7,
            max_tokens=200
        )
        
        print("✅ DeepSeek 基本调用成功!")
        print(f"响应: {response.choices[0].message.content if hasattr(response, 'choices') else response}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek 基本调用失败: {e}")
        return False

async def test_deepseek_coding():
    """测试 DeepSeek 代码生成功能"""
    print("\n🧪 测试 DeepSeek 代码生成功能...")
    
    try:
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "请用 Python 写一个简单的计算器函数，包含加减乘除四则运算"}
            ],
            model_name="deepseek/deepseek-coder",
            temperature=0.3,
            max_tokens=500
        )
        
        print("✅ DeepSeek 代码生成成功!")
        print(f"响应: {response.choices[0].message.content if hasattr(response, 'choices') else response}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek 代码生成失败: {e}")
        return False

async def test_deepseek_reasoning():
    """测试 DeepSeek 推理功能"""
    print("\n🧪 测试 DeepSeek 推理功能...")
    
    try:
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "如果一个人每天存 10 元，一年后他能存多少钱？请详细计算并解释。"}
            ],
            model_name="deepseek/deepseek-reasoner",
            temperature=0.1,
            max_tokens=300
        )
        
        print("✅ DeepSeek 推理功能成功!")
        print(f"响应: {response.choices[0].message.content if hasattr(response, 'choices') else response}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek 推理功能失败: {e}")
        return False

async def test_deepseek_streaming():
    """测试 DeepSeek 流式响应"""
    print("\n🧪 测试 DeepSeek 流式响应...")
    
    try:
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "请写一首关于春天的短诗"}
            ],
            model_name="deepseek/deepseek-chat",
            temperature=0.8,
            max_tokens=150,
            stream=True
        )
        
        print("✅ DeepSeek 流式响应成功!")
        print("流式内容:")
        
        async for chunk in response:
            if hasattr(chunk, 'choices') and chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end='', flush=True)
        print()  # 换行
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek 流式响应失败: {e}")
        return False

async def test_deepseek_tools():
    """测试 DeepSeek 工具调用功能"""
    print("\n🧪 测试 DeepSeek 工具调用功能...")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定城市的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]
    
    try:
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "请帮我查询北京的天气"}
            ],
            model_name="deepseek/deepseek-chat",
            temperature=0.1,
            tools=tools,
            tool_choice="auto"
        )
        
        print("✅ DeepSeek 工具调用成功!")
        print(f"响应: {response.choices[0].message if hasattr(response, 'choices') else response}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek 工具调用失败: {e}")
        return False

async def test_openrouter_deepseek():
    """测试通过 OpenRouter 访问 DeepSeek"""
    print("\n🧪 测试通过 OpenRouter 访问 DeepSeek...")
    
    try:
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "请解释一下什么是人工智能"}
            ],
            model_name="openrouter/deepseek/deepseek-chat",
            temperature=0.5,
            max_tokens=200
        )
        
        print("✅ OpenRouter DeepSeek 调用成功!")
        print(f"响应: {response.choices[0].message.content if hasattr(response, 'choices') else response}")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter DeepSeek 调用失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始 DeepSeek 集成测试...")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请设置环境变量后重试:")
        print("export DEEPSEEK_API_KEY=your_api_key_here")
        print()
    
    # 运行测试
    tests = [
        test_deepseek_basic,
        test_deepseek_coding,
        test_deepseek_reasoning,
        test_deepseek_streaming,
        test_deepseek_tools,
        test_openrouter_deepseek
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 出现异常: {e}")
            results.append(False)
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过! DeepSeek 集成成功!")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")
    
    return passed == total

if __name__ == "__main__":
    # 设置日志级别
    logger.setLevel("INFO")
    
    # 运行测试
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试运行出现异常: {e}")
        sys.exit(1)
