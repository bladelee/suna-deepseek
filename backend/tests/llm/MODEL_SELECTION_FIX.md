# 模型选择问题修复指南

## 问题描述

系统调用了 `gpt-5-mini` 而不是默认的 `deepseek/deepseek-chat` 模型，导致以下错误：

1. **模型选择错误**：前端硬编码了 `gpt-5-mini` 作为默认模型
2. **API 密钥缺失**：`gpt-5-mini` 需要 OpenAI API 密钥，但配置中为空

## 问题根源

### 1. 前端硬编码问题
```typescript
// suna/frontend/src/components/thread/chat-input/_use-model-selection.ts
export const DEFAULT_FREE_MODEL_ID = 'gpt-5-mini';  // 硬编码错误
```

### 2. 后端模型解析
```python
# suna/backend/utils/constants.py
"openai/gpt-5-mini": {
    "aliases": ["gpt-5-mini"],  # 别名解析
    # ...
}
```

### 3. 环境变量配置
```bash
# suna/backend/.env
DEFAULT_MODEL=deepseek/deepseek-chat  # 后端配置正确
OPENAI_API_KEY=                        # OpenAI 密钥为空
DEEPSEEK_API_KEY=sk-0904c18b73274394aacbe3c29b470d96  # DeepSeek 密钥已设置
```

## 解决方案

### 方案1：修复前端默认模型（已实施）

将前端的默认模型改为与后端一致：

```typescript
export const DEFAULT_FREE_MODEL_ID = 'deepseek/deepseek-chat';
```

### 方案2：添加后端配置 API（已实施）

在后端添加配置端点，让前端可以动态获取配置：

```python
@app.get("/config")
async def get_config():
    return {
        "default_model": config.DEFAULT_MODEL,
        "environment": config.ENV_MODE.value,
        "instance_id": instance_id
    }
```

### 方案3：前端动态获取配置（已实施）

前端尝试从后端 API 获取配置，失败时使用 fallback 值：

```typescript
export async function getDefaultModel(): Promise<string> {
  try {
    const response = await fetch('/api/config');
    if (response.ok) {
      const config = await response.json();
      return config.default_model || DEFAULT_FREE_MODEL_ID;
    }
  } catch (error) {
    console.warn('Failed to fetch default model from backend, using fallback:', error);
  }
  return DEFAULT_FREE_MODEL_ID;
}
```

### 方案4：自动清除旧的模型选择（已实施）

前端在初始化时自动清除 localStorage 中的旧模型选择：

```typescript
import { clearModelPreference } from '@/lib/utils/clear-model-preference';

// 在模型选择初始化时调用
useEffect(() => {
  if (typeof window === 'undefined' || hasInitialized) return;
  
  // 清除旧的模型选择（如果存在）
  clearModelPreference();
  
  // ... 其他初始化逻辑
}, []);
```

### 方案5：更新前端模型定义（已实施）

更新前端的 `MODELS` 对象，移除旧的 `gpt-5-mini` 定义：

```typescript
// 之前
'gpt-5-mini': { 
  tier: 'free', 
  priority: 100,
  recommended: true,
  lowQuality: false
},

// 现在
'deepseek/deepseek-chat': { 
  tier: 'free', 
  priority: 100,
  recommended: true,
  lowQuality: false
},
```

## 配置优先级

1. **后端环境变量**：`DEFAULT_MODEL` 在 `.env` 文件中设置
2. **前端 API 获取**：从 `/api/config` 端点获取
3. **前端 fallback**：如果 API 失败，使用硬编码的 fallback 值

## 验证修复

### 1. 检查后端配置
```bash
curl http://localhost:8000/config
```

预期输出：
```json
{
  "default_model": "deepseek/deepseek-chat",
  "environment": "local",
  "instance_id": "single"
}
```

### 2. 检查前端默认值
前端应该使用 `deepseek/deepseek-chat` 作为默认模型，而不是 `gpt-5-mini`。

### 3. 检查日志
日志应该显示：
```
Using model: deepseek/deepseek-chat
```

而不是：
```
Using model: openai/gpt-5-mini
```

## 如果需要使用 GPT-5-mini

如果你确实需要使用 `gpt-5-mini` 模型：

### 1. 设置 OpenAI API 密钥
```bash
# 在 suna/backend/.env 文件中添加
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 修改默认模型
```bash
# 在 suna/backend/.env 文件中修改
DEFAULT_MODEL=openai/gpt-5-mini
```

### 3. 重启服务
```bash
docker-compose restart
```

## 最佳实践

1. **统一配置**：前后端使用相同的默认模型配置
2. **环境变量**：通过环境变量管理模型配置，避免硬编码
3. **动态获取**：前端从后端 API 获取配置，确保一致性
4. **fallback 机制**：API 失败时有合理的 fallback 值
5. **日志监控**：监控模型选择日志，及时发现问题

## 相关文件

- `suna/backend/.env` - 后端环境变量配置
- `suna/backend/utils/config.py` - 后端配置管理
- `suna/backend/utils/constants.py` - 模型别名定义
- `suna/frontend/src/components/thread/chat-input/_use-model-selection.ts` - 前端模型选择
- `suna/backend/api.py` - 后端 API 端点
