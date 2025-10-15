# Docker 部署指南

## 概述

本指南提供Backend服务的完整Docker部署方案，包括基础版本和daemon-proxy版本的详细说明。

## 版本说明

### 基础版本 (Dockerfile)
- **用途**：标准的Backend API服务，不包含daemon-proxy功能
- **特点**：使用git原始内容，轻量级，启动速度快
- **适用场景**：纯API服务，测试环境，微服务架构

### daemon-proxy版本 (Dockerfile.daemon)
- **用途**：支持daemon-proxy功能的Backend API服务
- **特点**：包含完整的daemon-proxy功能，支持容器注入和预览链接
- **适用场景**：需要daemon-proxy完整功能，一体化部署

## 文件结构

```
backend/
├── Dockerfile                    # 基础版本Dockerfile
├── Dockerfile.daemon            # daemon-proxy版本Dockerfile
├── dockers/                     # Docker相关配置文件目录
│   ├── README.md               # dockers目录说明
│   ├── config.daemon.yaml      # daemon-proxy配置文件
│   ├── start-daemon-proxy.sh   # daemon-proxy启动脚本
│   ├── docker-compose.yml      # 基础版本生产环境
│   ├── docker-compose.dev.yml  # 基础版本开发环境
│   ├── docker-compose.daemon.yml      # daemon-proxy版本生产环境
│   ├── docker-compose.dev.daemon.yml  # daemon-proxy版本开发环境
│   ├── docker-compose.volume-mount.yml      # 挂载方案生产环境
│   └── docker-compose.dev.volume-mount.yml  # 挂载方案开发环境
└── scripts/
    └── build.sh                # 构建脚本
```

## 快速开始

### 基础版本部署

#### 生产环境
```bash
# 构建镜像
docker build -t backend-api .

# 运行服务
docker-compose -f dockers/docker-compose.yml up -d
```

#### 开发环境
```bash
# 运行开发环境
docker-compose -f dockers/docker-compose.dev.yml up -d
```

### daemon-proxy版本部署

#### 生产环境
```bash
# 构建镜像
docker build -f Dockerfile.daemon -t backend-api-daemon .

# 运行服务
docker-compose -f dockers/docker-compose.daemon.yml up -d
```

#### 开发环境
```bash
# 运行开发环境
docker-compose -f dockers/docker-compose.dev.daemon.yml up -d
```

### 使用构建脚本
```bash
# 构建和运行基础版本
./scripts/build.sh build base
./scripts/build.sh run base

# 构建和运行daemon-proxy版本
./scripts/build.sh build daemon
./scripts/build.sh run daemon
```

## 详细配置

### 环境变量

#### 基础版本
```bash
PYTHONPATH=/app
WORKERS=7
THREADS=2
WORKER_CONNECTIONS=2000
```

#### daemon-proxy版本
```bash
# 基础配置
PYTHONPATH=/app
WORKERS=7
THREADS=2
WORKER_CONNECTIONS=2000

# daemon-proxy配置
DAEMON_BINARY_PATH=/app/daemon-proxy/daytona-daemon-static
DAEMON_INJECTION_METHOD=copy
DAEMON_INJECTION_MODE=volume
DAEMON_PORT=2080
DAEMON_STARTUP_TIMEOUT=30
DAEMON_CONFIG_FILE=/app/config.daemon.yaml
SECURITY_ENABLED=false
LOG_LEVEL=INFO
```

### Docker Compose配置

#### 基础版本生产环境
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=info
    restart: unless-stopped
    networks:
      - suna-network

networks:
  suna-network:
    driver: bridge
```

#### daemon-proxy版本生产环境
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: Dockerfile.daemon
    ports:
      - "8000:8000"
    volumes:
      # 挂载Docker socket以访问Docker daemon
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      # 基础环境变量
      - PYTHONPATH=/app
      - LOG_LEVEL=info
      - ENVIRONMENT=production
      
      # daemon-proxy配置
      - DAEMON_BINARY_PATH=/app/daemon-proxy/daytona-daemon-static
      - DAEMON_INJECTION_METHOD=copy
      - DAEMON_INJECTION_MODE=volume
      - DAEMON_PORT=2080
      - DAEMON_STARTUP_TIMEOUT=30
      - DAEMON_CONFIG_FILE=/app/config.daemon.yaml
      - SECURITY_ENABLED=false
      
      # 其他配置
      - WORKERS=7
      - THREADS=2
      - WORKER_CONNECTIONS=2000
    restart: unless-stopped
    networks:
      - suna-network
    # 健康检查
    healthcheck:
      test: ["CMD", "sh", "-c", "curl -f http://localhost:8000/health && curl -f http://localhost:8000/api/daemon-proxy/service/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

networks:
  suna-network:
    driver: bridge
```

## daemon-proxy功能

### 核心功能
- ✅ 包含daemon二进制文件
- ✅ 支持拷贝和挂载两种注入方式
- ✅ 支持预览链接功能
- ✅ 支持容器管理功能
- ✅ 完整的配置管理

### 启动脚本功能
- 检查daemon二进制文件存在性和权限
- 验证Docker连接
- 检查配置文件
- 显示环境信息
- 启动Gunicorn服务

### 健康检查
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health && \
        curl -f http://localhost:8000/api/daemon-proxy/service/status || exit 1
```

### 配置文件支持
```yaml
# config.daemon.yaml
server:
  host: "0.0.0.0"
  port: 8080

daemon:
  mode: "docker"
  injection_method: "copy"
  injection_mode: "volume"
  port: 2080
  binary_source_path: "/app/daemon-proxy/daytona-daemon-static"

security:
  enabled: false

logging:
  level: "INFO"
```

## 环境差异

### 生产环境特点
- 使用拷贝方式注入（`DAEMON_INJECTION_METHOD=copy`）
- 更高的资源限制（2G内存，1 CPU）
- 更多的worker进程（7个）
- 更长的健康检查间隔

### 开发环境特点
- 使用挂载方式注入（`DAEMON_INJECTION_METHOD=mount`）
- 更宽松的资源限制（1G内存，0.5 CPU）
- 更少的worker进程（1个）
- 支持热重载和源代码挂载

## 功能验证

### 1. 服务启动验证
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查daemon-proxy状态
curl http://localhost:8000/api/daemon-proxy/service/status
```

### 2. 容器注入验证
```bash
# 注入daemon到容器
curl -X POST http://localhost:8000/api/daemon-proxy/container/test-container/inject

# 检查容器状态
curl http://localhost:8000/api/daemon-proxy/container/test-container/status
```

### 3. 预览链接验证
```bash
# 创建预览链接
curl -X POST http://localhost:8000/api/daemon-proxy/container/test-container/preview/8080

# 访问预览链接
curl http://localhost:8000/api/daemon-proxy/preview/{token}
```

## 故障排除

### 1. 常见问题

#### daemon二进制文件问题
```
Error: Daemon binary not found at /app/daemon-proxy/daytona-daemon-static
```
**解决方案：**
- 检查文件是否存在
- 验证文件权限
- 确认文件类型正确

#### 构建时file命令错误
```
/bin/sh: file: not found
```
**解决方案：**
- 这是Alpine Linux镜像中没有`file`命令导致的
- 已修复：移除了`file`命令验证，只使用`ls -la`验证文件存在性和权限

#### Docker连接问题
```
Error: Cannot connect to Docker daemon
```
**解决方案：**
- 检查Docker socket挂载
- 验证Docker daemon状态
- 检查容器权限

#### 配置文件问题
```
Error: Configuration file not found
```
**解决方案：**
- 检查配置文件路径
- 验证文件格式
- 确认环境变量设置

### 2. 调试技巧

#### 查看启动日志
```bash
# 基础版本
docker-compose -f dockers/docker-compose.yml logs backend

# daemon-proxy版本
docker-compose -f dockers/docker-compose.daemon.yml logs backend
```

#### 进入容器调试
```bash
# 基础版本
docker-compose -f dockers/docker-compose.yml exec backend bash

# daemon-proxy版本
docker-compose -f dockers/docker-compose.daemon.yml exec backend bash
```

#### 检查环境变量
```bash
# 检查daemon-proxy环境变量
docker-compose -f dockers/docker-compose.daemon.yml exec backend env | grep DAEMON
```

## 最佳实践

### 1. 安全考虑
- 限制Docker socket访问权限
- 使用非root用户运行容器
- 定期更新基础镜像

### 2. 性能优化
- 使用多阶段构建减少镜像大小
- 合理配置资源限制
- 启用健康检查

### 3. 监控和日志
- 配置结构化日志
- 启用健康检查端点
- 监控容器资源使用

## 迁移指南

### 从基础版本迁移到daemon-proxy版本

1. **停止当前服务**
```bash
docker-compose -f dockers/docker-compose.yml down
```

2. **切换到daemon-proxy版本**
```bash
docker-compose -f dockers/docker-compose.daemon.yml up -d
```

3. **验证功能**
```bash
# 检查daemon-proxy功能
curl http://localhost:8000/api/daemon-proxy/service/status
```

### 从daemon-proxy版本迁移到基础版本

1. **停止当前服务**
```bash
docker-compose -f dockers/docker-compose.daemon.yml down
```

2. **切换到基础版本**
```bash
docker-compose -f dockers/docker-compose.yml up -d
```

3. **注意功能限制**
- daemon-proxy相关功能将不可用
- 容器注入功能将不可用
- 预览链接功能将不可用

## 总结

通过提供两个版本的Dockerfile，我们实现了：

1. **灵活选择**：根据需求选择合适的版本
2. **功能完整**：daemon-proxy版本包含所有功能
3. **易于维护**：清晰的版本分离便于维护和升级
4. **向后兼容**：基础版本保持原有功能不变
5. **生产就绪**：包含健康检查、资源限制、安全配置

这种设计既满足了保持原始内容不变的要求，又提供了daemon-proxy功能的扩展版本，同时保证了生产环境的稳定性和开发环境的便利性。
