# Docker沙盒实现变更

本文档总结了为支持本地Docker容器作为沙盒替代Daytona所做的更改。

## 概述

Suna AI Worker项目已增强以支持两种沙盒模式：
1. **Daytona沙盒**（默认）：外部Daytona服务
2. **本地Docker沙盒**：本地Docker容器

## 修改的文件

### 1. 新创建的文件

#### `sandbox/docker_sandbox.py`
- **DockerSandbox**：实现沙盒接口的主要沙盒类
- **DockerSandboxFS**：文件系统操作（上传、下载、列表、删除）
- **DockerSandboxProcess**：进程和会话管理
- **DockerSandboxManager**：容器生命周期管理
- **支持类**：FileInfo、SessionExecuteRequest

#### `docker-sandbox.env.example`
- Docker沙盒模式的环境配置模板
- 包含所有必要的配置变量

#### `docker-compose.docker-sandbox.yml`
- 本地开发的Docker Compose配置
- 包含Redis、API和工作进程服务
- 挂载Docker套接字用于沙盒管理

#### `scripts/start-docker-sandbox.sh`
- Docker沙盒环境的自动化启动脚本
- 健康检查和服务验证

#### `DOCKER_SANDBOX_README.md`
- Docker沙盒使用的综合文档
- 配置、故障排除和最佳实践

#### `test_docker_sandbox.py`
- Docker沙盒功能的单元测试
- 所有组件的基于Mock的测试

#### `scripts/test-docker-sandbox.py`
- Docker沙盒的集成测试脚本
- 沙盒操作的端到端测试

### 2. 修改的文件

#### `utils/config.py`
- 添加了Docker沙盒配置选项
- 使Daytona配置变为可选
- 添加了新的环境变量：
  - `USE_LOCAL_DOCKER_SANDBOX`
  - `DOCKER_HOST`
  - `DOCKER_CERT_PATH`
  - `DOCKER_TLS_VERIFY`

#### `sandbox/sandbox.py`
- 修改以支持Daytona和Docker两种沙盒模式
- 更新函数签名以处理两种类型
- 添加沙盒提供者选择的条件逻辑
- 增强对缺失提供者的错误处理

#### `pyproject.toml`
- 添加了`docker>=6.0.0`依赖

## 主要更改

### 配置管理
- **基于环境的模式选择**：`USE_LOCAL_DOCKER_SANDBOX`标志
- **可选的Daytona配置**：不再需要Daytona密钥
- **Docker配置选项**：支持远程Docker主机和TLS

### 沙盒接口兼容性
- **统一接口**：Daytona和Docker沙盒都实现相同的接口
- **类型提示**：更新以支持两种沙盒类型
- **错误处理**：当提供者不可用时的优雅回退

### Docker集成
- **Docker套接字挂载**：从容器访问Docker守护进程
- **容器生命周期管理**：创建、启动、停止、删除操作
- **文件操作**：通过Docker exec API进行上传、下载、列表、删除
- **进程管理**：命令执行和会话处理

### 安全和隔离
- **容器隔离**：每个沙盒运行在独立的Docker容器中
- **资源限制**：可配置的CPU、内存和磁盘限制
- **网络隔离**：沙盒之间相互隔离
- **自动清理**：旧沙盒自动移除

## 架构变更

### 之前（仅Daytona）
```
API → Daytona SDK → Daytona Service → Remote Sandbox
```

### 之后（双模式）
```
API → Sandbox Manager → [Daytona SDK → Daytona Service] OR [Docker Client → Local Container]
```

### 沙盒提供者选择
```python
if config.USE_LOCAL_DOCKER_SANDBOX and docker_manager:
    # 使用Docker沙盒
    sandbox = await docker_manager.get_sandbox(sandbox_id)
else:
    # 使用Daytona沙盒
    sandbox = await daytona.get(sandbox_id)
```

## 配置示例

### 本地Docker模式
```bash
# 启用Docker沙盒
USE_LOCAL_DOCKER_SANDBOX=true

# Docker配置（可选）
DOCKER_HOST=unix:///var/run/docker.sock
SANDBOX_IMAGE_NAME=kortix/suna:0.1.3.6
```

### Daytona模式（默认）
```bash
# 禁用Docker沙盒
USE_LOCAL_DOCKER_SANDBOX=false

# Daytona配置
DAYTONA_API_KEY=your_key
DAYTONA_SERVER_URL=your_url
DAYTONA_TARGET=your_target
```

## 使用示例

### 启动Docker沙盒环境
```bash
# 使用启动脚本
./scripts/start-docker-sandbox.sh

# 或者手动
docker-compose -f docker-compose.docker-sandbox.yml up -d
```

### 测试Docker沙盒
```bash
# 运行单元测试
pytest test_docker_sandbox.py

# 运行集成测试
python scripts/test-docker-sandbox.py
```

### 在模式之间切换
```bash
# 切换到Docker模式
export USE_LOCAL_DOCKER_SANDBOX=true

# 切换到Daytona模式
export USE_LOCAL_DOCKER_SANDBOX=false
```

## 本地Docker沙盒的优势

### 开发
- **无外部依赖**：离线工作
- **更快迭代**：无网络延迟
- **更容易调试**：直接访问容器
- **自定义配置**：完全控制沙盒设置

### 部署
- **隔离网络环境**：无需互联网访问
- **自定义镜像**：使用修改或专门的镜像
- **资源控制**：精确控制容器资源
- **网络隔离**：自定义网络配置

### 成本和性能
- **无外部成本**：无Daytona服务费用
- **更低延迟**：本地执行
- **资源效率**：更好的资源利用
- **可扩展性**：易于水平扩展

## 迁移指南

### 从Daytona到Docker
1. 设置`USE_LOCAL_DOCKER_SANDBOX=true`
2. 确保Docker正在运行
3. 拉取所需的沙盒镜像
4. 使用提供的测试脚本进行测试

### 从Docker到Daytona
1. 设置`USE_LOCAL_DOCKER_SANDBOX=false`
2. 配置Daytona API密钥
3. 验证Daytona服务连接性
4. 测试沙盒功能

## 测试和验证

### 单元测试
- **组件测试**：单个类测试
- **基于Mock**：无实际Docker容器
- **快速执行**：开发期间的快速反馈

### 集成测试
- **端到端测试**：完整的沙盒生命周期
- **真实容器**：实际的Docker操作
- **全面验证**：测试所有功能

### 健康检查
- **服务监控**：API和工作进程健康状态
- **容器状态**：沙盒容器健康状态
- **资源监控**：内存和CPU使用情况

## 未来增强

### 计划功能
- **多架构支持**：ARM64等
- **自定义资源配置文件**：不同的容器配置
- **高级网络**：自定义网络配置
- **持久存储**：卷挂载和数据持久化

### 潜在改进
- **容器编排**：Kubernetes集成
- **高级监控**：Prometheus指标
- **安全加固**：SELinux、AppArmor支持
- **性能优化**：容器优化技术

## 故障排除

### 常见问题
- **Docker权限错误**：检查Docker套接字权限
- **容器启动失败**：验证镜像可用性
- **文件操作错误**：检查容器文件系统
- **资源耗尽**：监控系统资源

### 调试命令
```bash
# 检查容器状态
docker ps --filter "label=suna.sandbox=true"

# 查看容器日志
docker logs <container_id>

# 在容器中执行命令
docker exec -it <container_id> /bin/bash

# 检查Docker守护进程
docker info
```

## 结论

本地Docker沙盒的实现为本地开发和部署场景提供了Daytona的强大替代方案。双模式架构确保了向后兼容性，同时为离线开发和自定义配置添加了新功能。

主要优势包括：
- **灵活性**：根据需求在Daytona和Docker之间选择
- **可靠性**：无外部服务依赖
- **性能**：本地执行，延迟更低
- **安全性**：完全控制沙盒隔离和资源

该实现遵循Docker集成的最佳实践，并提供全面的测试和文档，便于采用和维护。
