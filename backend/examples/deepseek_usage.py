#!/usr/bin/env python3
"""
DeepSeek 使用示例

此文件展示了如何在项目中使用 DeepSeek 模型的各种功能。
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm import make_llm_api_call

async def example_basic_chat():
    """基本聊天示例"""
    print("=== 基本聊天示例 ===")
    
    response = await make_llm_api_call(
        messages=[
            {"role": "user", "content": "你好，请介绍一下 DeepSeek 模型的特点"}
        ],
        model_name="deepseek/deepseek-chat",
        temperature=0.7
    )
    
    print(f"用户: 你好，请介绍一下 DeepSeek 模型的特点")
    print(f"DeepSeek: {response.choices[0].message.content}")
    print()

async def example_code_generation():
    """代码生成示例"""
    print("=== 代码生成示例 ===")
    
    response = await make_llm_api_call(
        messages=[
            {"role": "user", "content": "请用 Python 写一个函数，计算斐波那契数列的第 n 项"}
        ],
        model_name="deepseek/deepseek-coder",
        temperature=0.3
    )
    
    print(f"用户: 请用 Python 写一个函数，计算斐波那契数列的第 n 项")
    print(f"DeepSeek: {response.choices[0].message.content}")
    print()

async def example_reasoning():
    """推理示例"""
    print("=== 推理示例 ===")
    
    response = await make_llm_api_call(
        messages=[
            {"role": "user", "content": "一个商店有 100 个苹果，第一天卖出 20%，第二天卖出剩下的 30%，第三天卖出剩下的 50%，问最后还剩多少个苹果？请详细计算。"}
        ],
        model_name="deepseek/deepseek-reasoner",
        temperature=0.1
    )
    
    print(f"用户: 一个商店有 100 个苹果，第一天卖出 20%，第二天卖出剩下的 30%，第三天卖出剩下的 50%，问最后还剩多少个苹果？请详细计算。")
    print(f"DeepSeek: {response.choices[0].message.content}")
    print()

async def example_streaming():
    """流式响应示例"""
    print("=== 流式响应示例 ===")
    
    print("用户: 请写一首关于秋天的诗")
    print("DeepSeek: ", end="", flush=True)
    
    response = await make_llm_api_call(
        messages=[
            {"role": "user", "content": "请写一首关于秋天的诗"}
        ],
        model_name="deepseek/deepseek-chat",
        temperature=0.8,
        stream=True
    )
    
    async for chunk in response:
        if hasattr(chunk, 'choices') and chunk.choices:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end='', flush=True)
    print("\n")

async def example_tool_calling():
    """工具调用示例"""
    print("=== 工具调用示例 ===")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "执行数学计算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '2 + 3 * 4'"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]
    
    response = await make_llm_api_call(
        messages=[
            {"role": "user", "content": "请计算 15 的平方根"}
        ],
        model_name="deepseek/deepseek-chat",
        temperature=0.1,
        tools=tools,
        tool_choice="auto"
    )
    
    print(f"用户: 请计算 15 的平方根")
    print(f"DeepSeek: {response.choices[0].message}")
    print()

async def example_multi_turn_conversation():
    """多轮对话示例"""
    print("=== 多轮对话示例 ===")
    
    messages = [
        {"role": "user", "content": "我想学习 Python 编程，应该从哪里开始？"}
    ]
    
    # 第一轮对话
    response = await make_llm_api_call(
        messages=messages,
        model_name="deepseek/deepseek-chat",
        temperature=0.7
    )
    
    print(f"用户: {messages[0]['content']}")
    print(f"DeepSeek: {response.choices[0].message.content}")
    print()
    
    # 添加回复到对话历史
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    messages.append({"role": "user", "content": "那你能推荐一些具体的 Python 教程资源吗？"})
    
    # 第二轮对话
    response = await make_llm_api_call(
        messages=messages,
        model_name="deepseek/deepseek-chat",
        temperature=0.7
    )
    
    print(f"用户: 那你能推荐一些具体的 Python 教程资源吗？")
    print(f"DeepSeek: {response.choices[0].message.content}")
    print()

async def example_openrouter_deepseek():
    """通过 OpenRouter 使用 DeepSeek 示例"""
    print("=== OpenRouter DeepSeek 示例 ===")
    
    response = await make_llm_api_call(
        messages=[
            {"role": "user", "content": "请解释一下什么是机器学习"}
        ],
        model_name="openrouter/deepseek/deepseek-chat",
        temperature=0.5
    )
    
    print(f"用户: 请解释一下什么是机器学习")
    print(f"DeepSeek (via OpenRouter): {response.choices[0].message.content}")
    print()

async def main():
    """主函数"""
    print("🚀 DeepSeek 使用示例")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请设置环境变量后重试:")
        print("export DEEPSEEK_API_KEY=your_api_key_here")
        return
    
    try:
        # 运行各种示例
        await example_basic_chat()
        await example_code_generation()
        await example_reasoning()
        await example_streaming()
        await example_tool_calling()
        await example_multi_turn_conversation()
        await example_openrouter_deepseek()
        
        print("✅ 所有示例运行完成!")
        
    except Exception as e:
        print(f"❌ 运行示例时出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
