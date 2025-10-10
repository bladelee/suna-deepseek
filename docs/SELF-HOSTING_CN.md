# Suna 本地部署指南

本指南提供了设置和托管您自己的Suna实例的详细说明，Suna是一个开源的通用AI工作者。

## 目录

- [概述](#概述)
- [前提条件](#前提条件)
- [安装步骤](#安装步骤)
- [手动配置](#手动配置)
- [安装后步骤](#安装后步骤)
- [故障排除](#故障排除)

## 概述

Suna由五个主要组件组成：

1. **后端API** - Python/FastAPI服务，提供REST端点、线程管理和LLM集成
2. **后端Worker** - Python/Dramatiq工作者服务，处理代理任务
3. **前端** - Next.js/React应用程序，提供用户界面
4. **代理Docker** - 每个代理的隔离执行环境
5. **Supabase数据库** - 处理数据持久化和身份验证

## 前提条件

在开始安装过程之前，您需要设置以下内容：

### 1. 本地Supabase

本项目支持本地Supabase部署，不需要创建Supabase云账号。项目已包含完整的本地Supabase配置。

### 2. API密钥

获取以下API密钥：

#### 必需

- **LLM提供商**（至少选择一个）：

  - [Anthropic](https://console.anthropic.com/) - 推荐用于最佳性能
  - [OpenAI](https://platform.openai.com/) 
  - [Groq](https://console.groq.com/) 
  - [OpenRouter](https://openrouter.ai/) 
  - [AWS Bedrock](https://aws.amazon.com/bedrock/) 
  - [DeepSeek](https://platform.deepseek.com/) - 提供更好的中文支持

- **AI驱动的代码编辑（可选但推荐）**：
  - [Morph](https://morphllm.com/api-keys) - 用于智能代码编辑功能

- **搜索和网页抓取**：
  - [Tavily](https://tavily.com/) - 用于增强搜索功能
  - [Firecrawl](https://firecrawl.dev/) - 用于网页抓取功能

#### 可选

- **RapidAPI** - 用于访问其他API服务（启用LinkedIn抓取和其他工具）
- **自定义MCP服务器** - 用于通过自定义工具扩展功能

### 3. 必需软件

确保您的系统上安装了以下工具：

- **[Docker](https://docs.docker.com/get-docker/)**
- **[Git](https://git-scm.com/downloads)**
- **[Python 3.11](https://www.python.org/downloads/)**

对于手动设置，您还需要：

- **[uv](https://docs.astral.sh/uv/)**
- **[Node.js & npm](https://nodejs.org/en/download/)**

## 安装步骤

### 1. 克隆仓库

```bash
# 克隆并进入项目目录
git clone https://github.com/kortix-ai/suna.git
cd suna
```

### 2. 运行设置向导

设置向导将指导您完成安装过程：

```bash
python setup.py
```

向导将：

- 检查是否安装了所有必需的工具
- 收集您的API密钥和配置信息
- 设置Supabase数据库（使用本地Docker部署）
- 配置环境文件
- 安装依赖项
- 使用您首选的方法启动Suna

设置向导包含14个步骤，并支持进度保存，因此您可以在中断后恢复。

### 3. 本地Supabase配置

在设置过程中，您需要：

1. 使用本地Docker启动Supabase服务
2. 配置环境变量以连接到本地Supabase
3. 推送数据库迁移
4. 手动在Supabase中暴露'basejump'架构：
   - 访问本地Supabase Studio (http://localhost:54323)
   - 导航到项目设置 → API
   - 将'basejump'添加到暴露架构部分

### 4. 本地Docker沙箱配置

与使用Daytona不同，本指南使用本地Docker作为沙箱环境：

1. 确保Docker已正确安装并运行
2. 在.env文件中设置`USE_LOCAL_DOCKER_SANDBOX=true`
3. 项目将自动使用本地Docker创建和管理沙箱容器

## 手动配置

如果您更喜欢手动配置安装，或者需要在安装后修改配置，以下是您需要了解的内容：

### 后端配置 (.env)

后端配置存储在`backend/.env`中。

本地部署示例配置：

```sh
# 环境模式
ENV_MODE=local

# 数据库 - 本地Supabase配置
SUPABASE_URL=http://localhost:8000
SUPABASE_ANON_KEY=your-local-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-local-service-role-key

# REDIS
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_SSL=false

# LLM提供商
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
OPENROUTER_API_KEY=your-openrouter-key
GEMINI_API_KEY=your-gemini-key
MORPH_API_KEY=
DEEPSEEK_API_KEY=your-deepseek-key

# 网络搜索
TAVILY_API_KEY=your-tavily-key

# 网页抓取
FIRECRAWL_API_KEY=your-firecrawl-key
FIRECRAWL_URL=https://api.firecrawl.dev

# 沙箱容器提供商 - 使用本地Docker
USE_LOCAL_DOCKER_SANDBOX=true
# Daytona配置可以保留为空
DAYTONA_API_KEY=
DAYTONA_SERVER_URL=
DAYTONA_TARGET=

# 后台任务处理（必需）
WEBHOOK_BASE_URL=http://localhost:8000

# MCP配置
MCP_CREDENTIAL_ENCRYPTION_KEY=your-generated-encryption-key

# 可选API
RAPID_API_KEY=your-rapidapi-key
# 数据库中的MCP服务器配置

NEXT_PUBLIC_URL=http://localhost:3000
```

### 前端配置 (.env.local)

前端配置存储在`frontend/.env.local`中，包括：

- Supabase连接详细信息
- 后端API URL

本地部署示例配置：

```sh
NEXT_PUBLIC_SUPABASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-local-anon-key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api
NEXT_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_ENV_MODE=LOCAL
```

## 安装后步骤

完成安装后，您需要：

1. **创建账户** - 使用Supabase身份验证创建您的第一个账户
2. **验证安装** - 检查所有组件是否正常运行

## 启动选项

Suna可以通过两种方式启动：

### 1. 使用Docker Compose（推荐）

此方法在Docker容器中启动所有必需的服务：

```bash
docker compose up -d # 稍后使用 `docker compose down` 停止
# 或者
python start.py # 稍后使用相同命令停止
```

此方法会自动启动本地Supabase服务、Redis、后端、工作者和前端。

### 2. 手动启动

此方法要求您分别启动每个组件：

1. 启动Redis（后端必需）：

```bash
docker compose up redis -d
# 或者
python start.py # 稍后使用相同命令停止
```

2. 启动本地Supabase服务：

```bash
docker compose up -d db auth rest realtime storage meta kong studio
```

3. 启动前端（在一个终端中）：

```bash
cd frontend
npm run dev
```

4. 启动后端（在另一个终端中）：

```bash
cd backend
uv run api.py
```

5. 启动工作者（在另一个终端中）：

```bash
cd backend
uv run dramatiq run_agent_background
```

## 故障排除

### 常见问题

1. **Docker服务无法启动**

   - 检查Docker日志：`docker compose logs`
   - 确保Docker正确运行
   - 验证端口可用性（前端3000，后端8000）

2. **数据库连接问题**

   - 验证Supabase配置
   - 检查'basejump'架构是否在Supabase中暴露
   - 检查本地Supabase服务是否正常运行：`docker ps | grep supabase`

3. **LLM API密钥问题**

   - 验证API密钥是否正确输入
   - 检查是否有API使用限制或限制

4. **本地Docker沙箱问题**

   - 确保Docker守护进程正在运行：`systemctl status docker`
   - 检查当前用户是否在docker组中：`groups $USER`
   - 查看Docker沙箱日志：`docker logs <sandbox-container-id>`

5. **设置向导问题**

   - 删除`.setup_progress`文件以重置设置向导
   - 检查是否安装了所有必需的工具

### 日志

要查看日志并诊断问题：

```bash
# Docker Compose日志
docker compose logs -f

# 前端日志（手动设置）
cd frontend
npm run dev

# 后端日志（手动设置）
cd backend
uv run api.py

# 工作者日志（手动设置）
cd backend
uv run dramatiq run_agent_background
```

### 恢复设置

如果设置向导被中断，您可以通过运行以下命令从中断处恢复：

```bash
python setup.py
```

向导将检测您的进度并从最后完成的步骤继续。

---

如需进一步帮助，请加入[Suna Discord社区](https://discord.gg/Py6pCBUUPw)或查看[GitHub存储库](https://github.com/kortix-ai/suna)获取更新和问题解决方案。