# 本地Docker沙盒开发指南

本文档说明如何使用本地Docker容器作为沙盒，替代Daytona进行本地开发和部署。

## 概述

Suna AI Worker项目现在支持两种沙盒模式：

1. **Daytona沙盒**（默认）：使用外部Daytona服务进行沙盒管理
2. **本地Docker沙盒**：使用本地Docker容器进行沙盒管理

本地Docker沙盒特别适合：
- 无需外部依赖的本地开发
- 离线开发环境
- 自定义沙盒配置
- 更容易的调试和故障排除

## 前置要求

- 安装并运行Docker和Docker Compose
- 至少4GB可用内存
- 至少10GB可用磁盘空间

## 快速开始

### 1. 配置环境

复制示例环境文件并进行配置：

```bash
cp docker-sandbox.env.example .env
```

编辑`.env`文件并设置你的配置：

```bash
# 启用本地Docker沙盒
USE_LOCAL_DOCKER_SANDBOX=true

# 设置你的API密钥
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# 配置Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

### 2. 启动服务

使用提供的启动脚本：

```bash
chmod +x scripts/start-docker-sandbox.sh
./scripts/start-docker-sandbox.sh
```

或者手动使用Docker Compose：

```bash
docker-compose -f docker-compose.docker-sandbox.yml up -d
```

### 3. 验证安装

检查服务是否正在运行：

```bash
# 检查服务状态
docker-compose -f docker-compose.docker-sandbox.yml ps

# 检查API健康状态
curl http://localhost:8000/api/health

# 查看日志
docker-compose -f docker-compose.docker-sandbox.yml logs -f
```

## 配置选项

### 环境变量

| 变量 | 描述 | 默认值 |
|-------|------|--------|
| `USE_LOCAL_DOCKER_SANDBOX` | 启用本地Docker沙盒模式 | `false` |
| `DOCKER_HOST` | Docker守护进程套接字路径 | `unix:///var/run/docker.sock` |
| `DOCKER_CERT_PATH` | Docker TLS证书路径 | `None` |
| `DOCKER_TLS_VERIFY` | 启用Docker TLS验证 | `false` |
| `SANDBOX_IMAGE_NAME` | 沙盒的Docker镜像 | `kortix/suna:0.1.3.6` |
| `SANDBOX_ENTRYPOINT` | 沙盒中运行的命令 | `/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf` |

### Docker配置

系统自动检测Docker配置：

- **本地Docker**：使用默认Unix套接字
- **远程Docker**：设置`DOCKER_HOST`环境变量
- **Docker Desktop**：在macOS/Windows上开箱即用

## 架构

### 沙盒生命周期

1. **创建**：使用指定镜像和配置创建Docker容器
2. **初始化**：启动容器并运行supervisord和所需服务
3. **执行**：通过Docker exec API执行命令
4. **清理**：不再需要时移除容器

### 文件操作

- **上传**：使用`docker cp`将文件复制到容器
- **下载**：使用`docker cp`从容器提取文件
- **列表**：通过执行`ls`命令获取目录内容
- **删除**：通过执行`rm`命令删除文件

### 进程管理

- **会话**：命令执行的逻辑分组
- **命令**：通过Docker exec API执行
- **异步支持**：支持后台命令执行

## 安全特性

### 容器隔离

- 每个沙盒运行在独立的Docker容器中
- 沙盒之间的网络隔离
- 资源限制和约束
- 自动清理旧容器

### 访问控制

- 私有项目需要用户认证
- 项目级访问控制
- 沙盒ID验证
- 所有操作的审计日志

## 监控和调试

### 健康检查

```bash
# 检查容器状态
docker ps --filter "label=suna.sandbox=true"

# 查看容器日志
docker logs <container_id>

# 在容器中执行命令
docker exec -it <container_id> /bin/bash
```

### 日志

```bash
# 查看应用日志
docker-compose -f docker-compose.docker-sandbox.yml logs -f api

# 查看工作进程日志
docker-compose -f docker-compose.docker-sandbox.yml logs -f worker

# 查看Redis日志
docker-compose -f docker-compose.docker-sandbox.yml logs -f redis
```

### 故障排除

常见问题和解决方案：

#### 容器无法启动

```bash
# 检查Docker守护进程状态
docker info

# 检查可用磁盘空间
df -h

# 检查Docker日志
journalctl -u docker.service
```

#### 沙盒无响应

```bash
# 检查容器状态
docker ps -a

# 重启容器
docker restart <container_id>

# 查看容器日志
docker logs <container_id>
```

#### 文件操作失败

```bash
# 检查容器文件系统
docker exec -it <container_id> ls -la /workspace

# 检查权限
docker exec -it <container_id> id

# 验证工作目录
docker exec -it <container_id> pwd
```

## 性能优化

### 资源限制

默认容器限制：
- CPU：2核
- 内存：4GB
- 磁盘：5GB

在`docker_sandbox.py`中调整：

```python
container_config = {
    'mem_limit': '4g',
    'cpu_quota': 200000,  # 2核
    'storage_opt': {'size': '5G'}
}
```

### 清理策略

自动清理旧沙盒：
- 默认：24小时
- 可通过`cleanup_sandboxes(max_age_hours)`配置
- 支持手动清理

## 从Daytona迁移

### 切换模式

1. **切换到本地Docker**：设置`USE_LOCAL_DOCKER_SANDBOX=true`
2. **切换到Daytona**：设置`USE_LOCAL_DOCKER_SANDBOX=false`并配置Daytona密钥

### 数据迁移

- 沙盒数据不会自动迁移
- 切换前从Daytona沙盒导出数据
- 根据需要将数据导入新的Docker沙盒

## 开发工作流

### 本地开发

```bash
# 启动开发环境
./scripts/start-docker-sandbox.sh

# 进行代码修改
# 代码修改会自动重新加载

# 测试沙盒功能
curl http://localhost:8000/api/sandboxes/test/files?path=/

# 停止环境
docker-compose -f docker-compose.docker-sandbox.yml down
```

### 测试

```bash
# 运行测试
docker-compose -f docker-compose.docker-sandbox.yml exec api pytest

# 运行特定测试
docker-compose -f docker-compose.docker-sandbox.yml exec api pytest test_sandbox.py::test_docker_sandbox
```

## 生产环境考虑

### 何时使用本地Docker

- **开发**：本地开发和测试
- **预发布**：内部预发布环境
- **隔离网络**：无互联网访问的环境
- **自定义**：需要自定义配置的环境

### 何时使用Daytona

- **生产**：生产环境部署
- **扩展**：高规模部署
- **托管**：托管服务要求
- **合规**：特定合规要求

## 支持和故障排除

### 获取帮助

1. 检查日志中的错误消息
2. 验证Docker配置
3. 检查环境变量
4. 查看本文档

### 常见问题

- **权限被拒绝**：检查Docker套接字权限
- **内存不足**：增加Docker内存限制
- **端口冲突**：检查端口冲突
- **镜像未找到**：拉取所需的Docker镜像

### 贡献

要改进本地Docker沙盒支持：

1. Fork仓库
2. 创建功能分支
3. 进行修改
4. 添加测试
5. 提交拉取请求

## 许可证

此功能是Suna AI Worker项目的一部分，遵循相同的许可证条款。
