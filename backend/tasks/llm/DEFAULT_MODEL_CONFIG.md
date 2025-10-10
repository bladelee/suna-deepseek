# 默认模型配置指南

## 概述

本项目现在支持配置默认的 LLM 模型，避免在代码中硬编码特定的模型名称。这样可以灵活地切换不同的模型提供商，比如从 OpenAI 切换到 DeepSeek。

## 配置方法

### 1. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 默认模型配置
DEFAULT_MODEL=deepseek/deepseek-chat

# 或者使用其他模型
# DEFAULT_MODEL=anthropic/claude-sonnet-4
# DEFAULT_MODEL=openai/gpt-4o-mini
# DEFAULT_MODEL=openrouter/deepseek/deepseek-chat
```

### 2. 支持的模型格式

#### 直接提供商模型
- `deepseek/deepseek-chat` - DeepSeek 聊天模型
- `deepseek/deepseek-coder` - DeepSeek 代码模型
- `anthropic/claude-sonnet-4` - Anthropic Claude 模型
- `openai/gpt-4o-mini` - OpenAI GPT-4o Mini 模型

#### OpenRouter 模型
- `openrouter/deepseek/deepseek-chat` - 通过 OpenRouter 访问 DeepSeek
- `openrouter/anthropic/claude-sonnet-4` - 通过 OpenRouter 访问 Claude
- `openrouter/openai/gpt-4o-mini` - 通过 OpenRouter 访问 GPT-4o Mini

## 代码中的使用

### 1. 获取默认模型

```python
from utils.config import config

# 获取系统配置的默认模型
default_model = config.DEFAULT_MODEL
```

### 2. 在函数中使用

```python
async def some_function():
    # 使用系统默认模型
    response = await make_llm_api_call(
        messages=[{"role": "user", "content": "Hello"}],
        model_name=config.DEFAULT_MODEL
    )
```

### 3. 动态模型选择

```python
async def smart_model_selection(user_preference=None):
    if user_preference:
        model_name = user_preference
    else:
        model_name = config.DEFAULT_MODEL
    
    response = await make_llm_api_call(
        messages=[{"role": "user", "content": "Hello"}],
        model_name=model_name
    )
```

## 已修改的函数

### `generate_and_update_project_name`

这个函数之前硬编码使用了 `"openai/gpt-4o-mini"`，现在已经修改为使用系统配置的默认模型：

```python
# 之前（硬编码）
model_name = "openai/gpt-4o-mini"

# 现在（使用配置）
model_name = config.DEFAULT_MODEL
```

## 配置优先级

1. **环境变量** - 最高优先级
2. **代码默认值** - 如果环境变量未设置
3. **硬编码值** - 最低优先级（已移除）

## 环境特定配置

### 开发环境
```bash
# .env.local
DEFAULT_MODEL=deepseek/deepseek-chat
```

### 生产环境
```bash
# .env.production
DEFAULT_MODEL=anthropic/claude-sonnet-4
```

### 测试环境
```bash
# .env.test
DEFAULT_MODEL=openai/gpt-4o-mini
```

## 模型切换策略

### 1. 完全替换 OpenAI
```bash
# 设置环境变量
export DEFAULT_MODEL=deepseek/deepseek-chat

# 或者使用 OpenRouter 作为备选
export DEFAULT_MODEL=openrouter/deepseek/deepseek-chat
```

### 2. 混合使用
```bash
# 主要使用 DeepSeek
export DEFAULT_MODEL=deepseek/deepseek-chat

# 在特定场景下可以覆盖
# 例如：代码生成使用专门的代码模型
```

### 3. 成本优化
```bash
# 使用成本较低的模型作为默认
export DEFAULT_MODEL=openrouter/deepseek/deepseek-chat

# 或者使用本地模型（如果可用）
export DEFAULT_MODEL=local/llama-3.1-8b
```

## 故障排除

### 1. 模型不可用
- 检查 API 密钥是否正确设置
- 确认模型名称是否正确
- 尝试使用 OpenRouter 作为备选

### 2. 性能问题
- 调整模型参数（temperature, max_tokens 等）
- 考虑使用更快的模型
- 启用流式响应

### 3. 成本控制
- 监控 API 调用次数
- 设置使用限制
- 使用成本较低的模型

## 最佳实践

1. **环境隔离**：不同环境使用不同的默认模型
2. **成本控制**：生产环境使用稳定且成本合理的模型
3. **性能优化**：根据使用场景选择合适的模型
4. **备份方案**：配置多个备选模型
5. **监控告警**：设置模型调用失败时的告警机制

## 更新日志

- **v1.0.0**: 添加默认模型配置支持
- 移除硬编码的模型名称
- 支持环境变量配置
- 添加 DeepSeek 作为默认选项
