#!/usr/bin/env python3
"""
测试模型选择修复的脚本
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config_consistency():
    """测试配置一致性"""
    print("=== 测试配置一致性 ===")
    
    try:
        from utils.config import config
        from utils.constants import MODEL_NAME_ALIASES
        
        # 检查默认模型
        print(f"后端默认模型: {config.DEFAULT_MODEL}")
        
        # 检查是否还有 gpt-5-mini 别名
        gpt_aliases = {k: v for k, v in MODEL_NAME_ALIASES.items() if 'gpt-5-mini' in k or 'gpt-5-mini' in v}
        
        if gpt_aliases:
            print("⚠️  仍然存在 gpt-5-mini 别名:")
            for alias, full_name in gpt_aliases.items():
                print(f"    {alias} -> {full_name}")
        else:
            print("✅ 没有发现 gpt-5-mini 别名")
            
        # 检查环境变量
        env_model = os.getenv('DEFAULT_MODEL')
        if env_model:
            print(f"环境变量 DEFAULT_MODEL: {env_model}")
            if env_model == config.DEFAULT_MODEL:
                print("✅ 环境变量与配置一致")
            else:
                print("❌ 环境变量与配置不一致")
        else:
            print("环境变量 DEFAULT_MODEL: 未设置")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_model_resolution():
    """测试模型名称解析"""
    print("\n=== 测试模型名称解析 ===")
    
    try:
        from utils.constants import MODEL_NAME_ALIASES
        
        test_models = [
            'deepseek/deepseek-chat',
            'gpt-5-mini',
            'openai/gpt-5-mini',
            'anthropic/claude-sonnet-4'
        ]
        
        for model in test_models:
            resolved = MODEL_NAME_ALIASES.get(model, model)
            print(f"{model} -> {resolved}")
            
            if 'gpt-5-mini' in resolved:
                print(f"  ⚠️  警告: {model} 解析为包含 gpt-5-mini 的模型")
            elif 'deepseek' in resolved:
                print(f"  ✅ 正常: {model} 解析为 DeepSeek 模型")
            else:
                print(f"  ℹ️  其他: {model} 解析为 {resolved}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_api_endpoints():
    """测试 API 端点"""
    print("\n=== 测试 API 端点 ===")
    
    try:
        import requests
        
        # 测试配置端点
        config_url = "http://localhost:8000/config"
        print(f"测试配置端点: {config_url}")
        
        try:
            response = requests.get(config_url, timeout=5)
            if response.status_code == 200:
                config_data = response.json()
                print(f"✅ 配置端点正常")
                print(f"   默认模型: {config_data.get('default_model')}")
                print(f"   环境: {config_data.get('environment')}")
            else:
                print(f"❌ 配置端点返回错误状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接到配置端点: {e}")
            
    except ImportError:
        print("ℹ️  requests 模块未安装，跳过 API 测试")
    except Exception as e:
        print(f"❌ API 测试失败: {e}")

def main():
    """主函数"""
    print("🧪 模型选择修复验证工具")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    test_config_consistency()
    test_model_resolution()
    test_api_endpoints()
    
    print("\n=== 修复状态总结 ===")
    
    # 检查修复状态
    try:
        from utils.config import config
        
        if config.DEFAULT_MODEL == "deepseek/deepseek-chat":
            print("✅ 后端默认模型已修复为 deepseek/deepseek-chat")
        else:
            print(f"❌ 后端默认模型仍然是: {config.DEFAULT_MODEL}")
            
        if not os.getenv('OPENAI_API_KEY'):
            print("✅ OpenAI API Key 已清空（正确）")
        else:
            print("⚠️  OpenAI API Key 仍然设置")
            
        if os.getenv('DEEPSEEK_API_KEY'):
            print("✅ DeepSeek API Key 已设置")
        else:
            print("❌ DeepSeek API Key 未设置")
            
    except Exception as e:
        print(f"❌ 无法检查修复状态: {e}")

if __name__ == "__main__":
    main()
