# Backend Scripts 目录

本目录包含 Suna Backend 项目的各种管理脚本，用于简化开发、部署和运维操作。

## 📁 文件列表

### 🔧 核心管理脚本

| 文件名 | 用途 | 适用环境 | 说明 |
|--------|------|----------|------|
| `build.sh` | Docker镜像构建管理 | 开发/生产 | 构建、运行、停止、清理Docker镜像和容器 |
| `docker-compose-manager.sh` | Docker Compose服务管理 | 开发/生产 | 统一管理不同环境的Docker Compose服务 |

### 🔍 诊断和检查脚本

| 文件名 | 用途 | 适用环境 | 说明 |
|--------|------|----------|------|
| `check-docker-environment.sh` | Docker环境诊断 | 开发 | 检查Docker服务、权限、资源等，用于故障排除 |

### 🚀 启动脚本

| 文件名 | 用途 | 适用环境 | 说明 |
|--------|------|----------|------|
| `start-dev-daemon-proxy.sh` | 开发环境启动 | 开发 | 启动开发环境的Backend服务，支持daemon-proxy功能 |

### ⚙️ 部署脚本

| 文件名 | 用途 | 适用环境 | 说明 |
|--------|------|----------|------|
| `setup-daemon-binary.sh` | Daemon二进制文件管理 | 生产 | 安装、更新、验证daemon-proxy二进制文件 |

## 🚀 快速开始

### 1. 开发环境

```bash
# 启动开发环境（daemon-proxy版本）
./scripts/docker-compose-manager.sh start dev-daemon

# 查看开发环境日志
./scripts/docker-compose-manager.sh logs dev-daemon

# 停止开发环境
./scripts/docker-compose-manager.sh stop dev-daemon
```

### 2. 生产环境

```bash
# 启动生产环境（daemon-proxy版本）
./scripts/docker-compose-manager.sh start daemon

# 查看生产环境状态
./scripts/docker-compose-manager.sh status daemon

# 停止生产环境
./scripts/docker-compose-manager.sh stop daemon
```

### 3. 基础环境

```bash
# 启动基础环境
./scripts/docker-compose-manager.sh start base

# 查看基础环境状态
./scripts/docker-compose-manager.sh status base
```

## 📋 详细使用说明

### build.sh - Docker构建管理

```bash
# 构建基础版本镜像
./scripts/build.sh build base

# 构建daemon-proxy版本镜像
./scripts/build.sh build daemon

# 运行daemon-proxy版本
./scripts/build.sh run daemon

# 停止daemon-proxy版本
./scripts/build.sh stop daemon

# 清理daemon-proxy版本
./scripts/build.sh clean daemon
```

### docker-compose-manager.sh - 服务管理

```bash
# 启动不同环境
./scripts/docker-compose-manager.sh start base           # 基础版本
./scripts/docker-compose-manager.sh start daemon         # 生产daemon版本
./scripts/docker-compose-manager.sh start dev-daemon     # 开发daemon版本

# 查看服务状态
./scripts/docker-compose-manager.sh status daemon

# 查看服务日志
./scripts/docker-compose-manager.sh logs dev-daemon

# 重启服务
./scripts/docker-compose-manager.sh restart daemon

# 清理服务（删除容器和镜像）
./scripts/docker-compose-manager.sh clean dev-daemon
```

### check-docker-environment.sh - 环境诊断

```bash
# 检查Docker环境
./scripts/check-docker-environment.sh
```

此脚本会检查：
- Docker服务状态
- Docker套接字权限
- 用户权限
- Docker版本
- 系统资源使用
- Docker资源使用
- 网络连接

### setup-daemon-binary.sh - Daemon二进制管理

```bash
# 安装daemon二进制文件
sudo ./scripts/setup-daemon-binary.sh install

# 更新daemon二进制文件
sudo ./scripts/setup-daemon-binary.sh update

# 查看daemon二进制文件状态
./scripts/setup-daemon-binary.sh status

# 验证挂载配置
./scripts/setup-daemon-binary.sh verify

# 清理备份文件
sudo ./scripts/setup-daemon-binary.sh cleanup
```

## 🔧 环境配置

### 开发环境特点

- **热重载**: 支持代码修改后自动重启
- **调试日志**: 详细的日志输出
- **单工作进程**: 便于调试
- **资源限制**: 适合开发的资源配置

### 生产环境特点

- **多工作进程**: 高性能处理
- **资源限制**: 严格的资源管理
- **安全配置**: 生产级别的安全设置
- **监控支持**: 完整的监控和日志

## 🐛 故障排除

### 常见问题

1. **Docker权限问题**
   ```bash
   # 检查Docker环境
   ./scripts/check-docker-environment.sh
   
   # 添加用户到docker组
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **服务启动失败**
   ```bash
   # 查看服务日志
   ./scripts/docker-compose-manager.sh logs dev-daemon
   
   # 检查服务状态
   ./scripts/docker-compose-manager.sh status dev-daemon
   ```

3. **镜像构建失败**
   ```bash
   # 清理并重新构建
   ./scripts/build.sh clean daemon
   ./scripts/build.sh build daemon
   ```

### 日志查看

```bash
# 查看实时日志
./scripts/docker-compose-manager.sh logs dev-daemon

# 查看特定服务日志
docker-compose -f docker-compose.dev.daemon.yml logs backend

# 查看容器日志
docker logs suna-backend-1
```

## 📚 相关文档

- [Docker部署指南](../dockers/DOCKER_GUIDE.md)
- [开发环境配置指南](../../DEVELOPMENT_ENVIRONMENT_GUIDE.md)
- [Daemon-Proxy集成文档](../designs/daemon-proxy/README.md)

## 🤝 贡献

如需添加新的脚本或修改现有脚本，请：

1. 遵循现有的脚本结构和命名规范
2. 添加详细的注释和文档
3. 包含错误处理和日志输出
4. 更新此README文档

## 📝 更新日志

- **2024-10-15**: 清理和重组脚本目录，添加统一的服务管理脚本
- **2024-10-15**: 删除过时的Docker沙盒启动脚本
- **2024-10-15**: 添加开发环境启动脚本
- **2024-10-15**: 完善脚本文档和注释
