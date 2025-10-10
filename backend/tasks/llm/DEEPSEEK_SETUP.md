# DeepSeek 集成配置指南

## 概述

本项目已成功集成了 DeepSeek 模型支持，可以完全替代 OpenAI 模型使用。DeepSeek 提供了强大的中文理解和代码生成能力。

## 支持的模型

### 主要模型
- `deepseek/deepseek-chat` - 通用对话模型
- `deepseek/deepseek-coder` - 代码生成专用模型
- `deepseek/deepseek-reasoner` - 推理专用模型

### 通过 OpenRouter 访问的模型
- `openrouter/deepseek/deepseek-chat`
- `openrouter/deepseek/deepseek-coder`
- `openrouter/deepseek/deepseek-reasoner`

## 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 可选：自定义 API 端点（如果需要）
# DEEPSEEK_API_BASE=https://api.deepseek.com
```

## 使用方法

### 1. 直接调用 DeepSeek 模型

```python
from services.llm import make_llm_api_call

# 使用 DeepSeek 聊天模型
response = await make_llm_api_call(
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    model_name="deepseek/deepseek-chat",
    temperature=0.7
)

# 使用 DeepSeek 代码模型
response = await make_llm_api_call(
    messages=[
        {"role": "user", "content": "请用 Python 写一个快速排序算法"}
    ],
    model_name="deepseek/deepseek-coder",
    temperature=0.3
)
```

### 2. 通过 OpenRouter 访问

```python
# 使用 OpenRouter 的 DeepSeek 模型
response = await make_llm_api_call(
    messages=[
        {"role": "user", "content": "请解释一下机器学习的基本概念"}
    ],
    model_name="openrouter/deepseek/deepseek-chat",
    api_key="your_openrouter_api_key"
)
```

## 模型特性

### DeepSeek 特有功能
- **中文优化**：对中文理解和生成进行了专门优化
- **代码生成**：强大的代码生成和调试能力
- **推理能力**：优秀的逻辑推理和问题解决能力
- **多轮对话**：支持复杂的多轮对话上下文

### 参数配置
- **temperature**: 默认 0.7，适合创造性任务
- **max_tokens**: 支持长文本生成
- **tools**: 支持函数调用和工具使用
- **streaming**: 支持流式响应

## 错误处理

系统会自动处理以下情况：
- API 密钥验证失败
- 网络连接问题
- 模型不可用时的自动回退
- 参数不兼容时的自动调整

## 成本优化

### 直接使用 DeepSeek
- 按 token 计费
- 支持批量调用
- 可设置使用限制

### 通过 OpenRouter
- 统一的计费接口
- 多模型对比选择
- 成本监控和分析

## 最佳实践

1. **模型选择**：
   - 通用对话：`deepseek/deepseek-chat`
   - 代码相关：`deepseek/deepseek-coder`
   - 逻辑推理：`deepseek/deepseek-reasoner`

2. **参数调优**：
   - 创造性任务：temperature = 0.7-0.9
   - 精确任务：temperature = 0.1-0.3
   - 代码生成：temperature = 0.1-0.5

3. **错误处理**：
   - 实现重试机制
   - 设置合理的超时时间
   - 监控 API 调用成功率

## 故障排除

### 常见问题

1. **API 密钥无效**
   - 检查 `DEEPSEEK_API_KEY` 是否正确设置
   - 确认 API 密钥是否有效且未过期

2. **模型不可用**
   - 检查网络连接
   - 确认模型名称是否正确
   - 尝试使用 OpenRouter 作为备选

3. **响应质量不佳**
   - 调整 temperature 参数
   - 优化 prompt 设计
   - 检查输入格式是否正确

### 调试模式

启用详细日志：
```python
import logging
logging.getLogger('services.llm').setLevel(logging.DEBUG)
```

## 更新日志

- **v1.0.0**: 初始 DeepSeek 集成
- 支持主要模型类型
- 自动参数配置
- 错误处理和回退机制
