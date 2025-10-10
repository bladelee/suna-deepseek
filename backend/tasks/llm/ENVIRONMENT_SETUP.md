# 环境配置指南

## 🚨 重要提示

**如果你遇到 "OpenAI API key must be set" 错误，请按照以下步骤配置环境变量！**

## 🔧 问题分析

错误日志显示系统仍在尝试调用 OpenAI 模型：
- **错误**: `The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable`
- **原因**: 代码中仍有硬编码的 `openai/gpt-5-mini` 模型调用

## ✅ 解决方案

### 1. 设置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 创建环境变量文件
cp .env.example .env
# 或者手动创建
touch .env
```

### 2. 配置默认模型

在 `.env` 文件中添加：

```bash
# =============================================================================
# 默认模型配置 (最重要!)
# =============================================================================
DEFAULT_MODEL=deepseek/deepseek-chat

# 可选的其他模型：
# DEFAULT_MODEL=anthropic/claude-sonnet-4
# DEFAULT_MODEL=openai/gpt-4o-mini
# DEFAULT_MODEL=openrouter/deepseek/deepseek-chat
```

### 3. 配置对应的 API 密钥

```bash
# DeepSeek API 配置 (推荐)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 或者使用其他模型对应的密钥
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 🔍 已修复的硬编码位置

以下文件中的硬编码模型已修复为使用 `config.DEFAULT_MODEL`：

- ✅ `agent/api.py` - `generate_and_update_project_name` 函数
- ✅ `agent/api.py` - `initiate_agent_with_files` 函数
- ✅ `agent/run.py` - `AgentConfig` 类和 `run_agent` 函数
- ✅ `run_agent_background.py` - 后台执行逻辑
- ✅ `triggers/api.py` - 工作流执行
- ✅ `triggers/execution_service.py` - 触发器执行服务
- ✅ `agent/suna_config.py` - Suna 默认配置

## 🚀 快速配置

### 使用 DeepSeek (推荐)

```bash
# .env 文件
DEFAULT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 使用 Anthropic Claude

```bash
# .env 文件
DEFAULT_MODEL=anthropic/claude-sonnet-4
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 使用 OpenRouter (成本优化)

```bash
# .env 文件
DEFAULT_MODEL=openrouter/deepseek/deepseek-chat
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## 🔄 重启服务

配置完成后，重启服务：

```bash
# Docker Compose
docker-compose down
docker-compose up -d

# 或者重启特定服务
docker-compose restart suna-worker
```

## 🧪 验证配置

运行测试脚本验证配置：

```bash
cd backend
python test_default_model.py
```

## 📋 环境变量完整列表

```bash
# 核心配置
DEFAULT_MODEL=deepseek/deepseek-chat
ENV_MODE=local

# LLM API 密钥
DEEPSEEK_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key
OPENROUTER_API_KEY=your_key
XAI_API_KEY=your_key
MORPH_API_KEY=your_key
GEMINI_API_KEY=your_key

# 数据库配置
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
SUPABASE_SERVICE_ROLE_KEY=your_key

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_SSL=false

# 沙箱配置
DAYTONA_API_KEY=your_key
DAYTONA_SERVER_URL=your_url
DAYTONA_TARGET=your_target

# 工具 API 密钥
TAVILY_API_KEY=your_key
RAPID_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
```

## 🚨 常见问题

### 1. 仍然报 OpenAI 错误

**原因**: 环境变量未正确加载
**解决**: 
- 检查 `.env` 文件是否在正确位置
- 确认 `DEFAULT_MODEL` 已设置
- 重启服务

### 2. 模型调用失败

**原因**: API 密钥无效或模型不可用
**解决**:
- 验证 API 密钥是否正确
- 检查模型名称是否正确
- 尝试使用 OpenRouter 作为备选

### 3. 配置不生效

**原因**: 代码缓存或服务未重启
**解决**:
- 重启所有相关服务
- 清除 Python 缓存
- 检查环境变量是否正确加载

## 📞 获取帮助

如果问题仍然存在：

1. 检查日志中的具体错误信息
2. 确认环境变量是否正确设置
3. 验证 API 密钥是否有效
4. 运行测试脚本诊断问题

## 🔄 更新日志

- **v1.0.0**: 修复所有硬编码的 OpenAI 模型引用
- 添加 `DEFAULT_MODEL` 环境变量支持
- 支持多种模型提供商
- 完全替代 OpenAI 依赖
