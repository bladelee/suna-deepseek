#!/usr/bin/env python3
"""
默认模型配置测试脚本

此脚本用于测试默认模型配置是否正常工作。
"""

import os
import sys
import asyncio

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import config
from services.llm import make_llm_api_call
from utils.logger import logger

async def test_default_model_config():
    """测试默认模型配置"""
    print("🧪 测试默认模型配置...")
    
    # 显示当前配置
    print(f"当前默认模型: {config.DEFAULT_MODEL}")
    print(f"环境模式: {config.ENV_MODE.value}")
    
    # 检查环境变量
    env_model = os.getenv("DEFAULT_MODEL")
    if env_model:
        print(f"环境变量 DEFAULT_MODEL: {env_model}")
    else:
        print("环境变量 DEFAULT_MODEL: 未设置")
    
    return True

async def test_default_model_usage():
    """测试使用默认模型进行 LLM 调用"""
    print("\n🧪 测试使用默认模型进行 LLM 调用...")
    
    try:
        # 使用默认模型
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "请用一句话介绍自己"}
            ],
            model_name=config.DEFAULT_MODEL,
            max_tokens=100,
            temperature=0.7
        )
        
        print("✅ 默认模型调用成功!")
        print(f"使用的模型: {config.DEFAULT_MODEL}")
        print(f"响应: {response.choices[0].message.content if hasattr(response, 'choices') else response}")
        return True
        
    except Exception as e:
        print(f"❌ 默认模型调用失败: {e}")
        return False

async def test_model_switching():
    """测试模型切换功能"""
    print("\n🧪 测试模型切换功能...")
    
    # 测试不同的模型
    test_models = [
        "deepseek/deepseek-chat",
        "anthropic/claude-sonnet-4",
        "openai/gpt-4o-mini"
    ]
    
    results = []
    for model in test_models:
        try:
            print(f"测试模型: {model}")
            response = await make_llm_api_call(
                messages=[
                    {"role": "user", "content": "你好"}
                ],
                model_name=model,
                max_tokens=50,
                temperature=0.7
            )
            
            print(f"✅ {model} 调用成功")
            results.append(True)
            
        except Exception as e:
            print(f"❌ {model} 调用失败: {e}")
            results.append(False)
    
    return results

async def test_environment_override():
    """测试环境变量覆盖"""
    print("\n🧪 测试环境变量覆盖...")
    
    # 保存原始环境变量
    original_env = os.getenv("DEFAULT_MODEL")
    
    try:
        # 设置新的环境变量
        os.environ["DEFAULT_MODEL"] = "deepseek/deepseek-chat"
        
        # 重新加载配置
        from importlib import reload
        import utils.config
        reload(utils.config)
        
        # 获取新的配置
        new_config = utils.config.config
        print(f"环境变量覆盖后的默认模型: {new_config.DEFAULT_MODEL}")
        
        # 测试调用
        response = await make_llm_api_call(
            messages=[
                {"role": "user", "content": "测试环境变量覆盖"}
            ],
            model_name=new_config.DEFAULT_MODEL,
            max_tokens=50
        )
        
        print("✅ 环境变量覆盖测试成功!")
        return True
        
    except Exception as e:
        print(f"❌ 环境变量覆盖测试失败: {e}")
        return False
        
    finally:
        # 恢复原始环境变量
        if original_env:
            os.environ["DEFAULT_MODEL"] = original_env
        else:
            os.environ.pop("DEFAULT_MODEL", None)
        
        # 重新加载配置
        from importlib import reload
        import utils.config
        reload(utils.config)

async def test_project_naming_function():
    """测试项目命名函数是否使用默认模型"""
    print("\n🧪 测试项目命名函数...")
    
    try:
        # 模拟项目命名函数的逻辑
        from agent.api import generate_and_update_project_name
        
        # 检查函数是否使用了 config.DEFAULT_MODEL
        import inspect
        source = inspect.getsource(generate_and_update_project_name)
        
        if "config.DEFAULT_MODEL" in source:
            print("✅ 项目命名函数已使用 config.DEFAULT_MODEL")
            return True
        else:
            print("❌ 项目命名函数仍在使用硬编码模型")
            return False
            
    except Exception as e:
        print(f"❌ 测试项目命名函数失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始默认模型配置测试...")
    print("=" * 50)
    
    # 运行测试
    tests = [
        test_default_model_config,
        test_default_model_usage,
        test_model_switching,
        test_environment_override,
        test_project_naming_function
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            if isinstance(result, list):
                results.extend(result)
            else:
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
        print("🎉 所有测试通过! 默认模型配置工作正常!")
    else:
        print("⚠️  部分测试失败，请检查配置")
    
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
