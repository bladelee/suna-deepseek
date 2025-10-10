#!/usr/bin/env python3
"""
检查 agent 配置脚本
用于诊断模型选择问题
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import config
from utils.logger import logger

def check_configuration():
    """检查系统配置"""
    print("=== 系统配置检查 ===")
    print(f"环境模式: {config.ENV_MODE.value}")
    print(f"默认模型: {config.DEFAULT_MODEL}")
    print(f"OpenAI API Key: {'已设置' if config.OPENAI_API_KEY else '未设置'}")
    print(f"DeepSeek API Key: {'已设置' if config.DEEPSEEK_API_KEY else '未设置'}")
    
    # 检查环境变量
    print("\n=== 环境变量检查 ===")
    env_vars = [
        'DEFAULT_MODEL',
        'OPENAI_API_KEY', 
        'DEEPSEEK_API_KEY',
        'ENV_MODE'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var and len(value) > 10:
                print(f"{var}: {value[:10]}...{value[-4:]}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: 未设置")

def check_model_aliases():
    """检查模型别名配置"""
    print("\n=== 模型别名检查 ===")
    try:
        from utils.constants import MODEL_NAME_ALIASES
        
        # 查找包含 gpt-5-mini 的别名
        gpt_aliases = {k: v for k, v in MODEL_NAME_ALIASES.items() if 'gpt-5-mini' in k or 'gpt-5-mini' in v}
        
        if gpt_aliases:
            print("发现 gpt-5-mini 相关别名:")
            for alias, full_name in gpt_aliases.items():
                print(f"  {alias} -> {full_name}")
        else:
            print("未发现 gpt-5-mini 相关别名")
            
    except ImportError as e:
        print(f"无法导入 MODEL_NAME_ALIASES: {e}")

def check_database_agents():
    """检查数据库中的 agent 配置"""
    print("\n=== 数据库 Agent 检查 ===")
    try:
        from services.supabase import DBConnection
        
        db = DBConnection()
        # 这里可以添加数据库查询逻辑
        print("数据库连接检查: 需要实际运行环境")
        
    except Exception as e:
        print(f"数据库检查失败: {e}")

def main():
    """主函数"""
    print("🔍 Agent 配置诊断工具")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    try:
        check_configuration()
        check_model_aliases()
        check_database_agents()
        
        print("\n=== 建议 ===")
        if config.DEFAULT_MODEL != "deepseek/deepseek-chat":
            print("⚠️  默认模型不是 deepseek/deepseek-chat")
            print("   建议检查 .env 文件中的 DEFAULT_MODEL 设置")
        
        if not config.DEEPSEEK_API_KEY:
            print("⚠️  DeepSeek API Key 未设置")
            print("   建议设置 DEEPSEEK_API_KEY 环境变量")
            
        if config.OPENAI_API_KEY:
            print("ℹ️  OpenAI API Key 已设置")
            print("   如果不需要使用 OpenAI 模型，可以清空此变量")
        else:
            print("ℹ️  OpenAI API Key 未设置")
            print("   这是正常的，因为我们使用 DeepSeek 作为默认模型")
            
    except Exception as e:
        print(f"❌ 检查过程中出现错误: {e}")
        logger.error(f"配置检查失败: {e}", exc_info=True)

if __name__ == "__main__":
    main()
