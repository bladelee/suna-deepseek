# Daemon Proxy Integration

## 概述

这个目录包含了 daemon-proxy 与 Suna backend 的集成代码，实现了全局 daemon-proxy 服务，可以同时管理多个容器中的 daemon 进程。

## 架构

daemon-proxy 是一个全局系统服务，与 backend API 一同启动，提供统一的预览链接功能。

### 核心概念

- **全局服务**: 一个 daemon-proxy 服务管理所有容器
- **多容器支持**: 可以同时管理多个容器的 daemon 进程
- **统一接口**: 提供统一的预览链接创建和管理功能

## 文件结构

```
sandbox/daemon-proxy/
├── README.md                           # 本文件
├── GLOBAL_DAEMON_PROXY_ARCHITECTURE.md # 全局服务架构文档
├── daytona-daemon-static              # daemon 二进制文件
├── examples/
│   └── global_daemon_proxy_example.py # 全局服务使用示例
└── tests/
    └── test_global_daemon_proxy_service.py # 全局服务测试
```

## API 端点

全局 daemon-proxy 服务提供以下 API 端点：

```
POST /api/daemon-proxy/container/{id}/inject      # 注入 daemon 到容器
POST /api/daemon-proxy/container/{id}/remove      # 从容器移除 daemon  
POST /api/daemon-proxy/container/{id}/preview/{port}  # 创建预览链接
GET  /api/daemon-proxy/container/{id}/status      # 获取容器 daemon 状态
GET  /api/daemon-proxy/service/status             # 获取全局服务状态
```

## 使用方式

### 1. 通过 Docker Sandbox

```python
from backend.sandbox.docker_sandbox import get_docker_manager

# 创建 sandbox
docker_manager = get_docker_manager()
sandbox = await docker_manager.create_sandbox(
    container_id="test-container",
    project_id="default",
    inject_daytona_daemon=True  # 自动注入 daemon
)

# 获取预览链接（自动使用全局 daemon-proxy 服务）
preview_link = await sandbox.get_preview_link(8080)
print(f"Preview URL: {preview_link.url}")
```

### 2. 使用便捷函数

```python
from backend.sandbox.sandbox import get_preview_link_for_docker_sandbox

# 直接调用 API
preview_link = await get_preview_link_for_docker_sandbox("container-123", 8080)
if preview_link:
    print(f"URL: {preview_link['url']}")
    print(f"Token: {preview_link['token']}")
```

### 3. 直接 API 调用

```python
import aiohttp

async with aiohttp.ClientSession() as session:
    # 注入 daemon
    async with session.post("http://localhost:8001/api/daemon-proxy/container/abc123/inject") as response:
        print(f"Inject status: {response.status}")
    
    # 创建预览链接
    async with session.post("http://localhost:8001/api/daemon-proxy/container/abc123/preview/8080") as response:
        data = await response.json()
        print(f"Preview URL: {data['url']}")
```

## 示例和测试

### 运行示例

```bash
cd backend/sandbox/daemon-proxy/examples
python global_daemon_proxy_example.py
```

### 运行测试

```bash
cd backend/sandbox/daemon-proxy/tests
python -m pytest test_global_daemon_proxy_service.py -v
```

## 配置

### 环境变量

```bash
# Backend API 配置
BACKEND_URL=http://localhost:8001/api  # 用于内部 API 调用
```

### 无需额外配置

- daemon-proxy 服务随 backend API 自动启动
- 自动绑定到 localhost 和动态端口
- 使用 backend 的统一配置和中间件

## 工作流程

1. **服务启动**: Backend API 启动时自动启动全局 daemon-proxy 服务
2. **容器管理**: 调用 `/inject` 将 daemon 注入到容器，容器被添加到管理列表
3. **预览链接**: 调用 `/preview/{port}` 为指定容器的端口创建预览链接
4. **请求代理**: 全局服务代理请求到对应容器的目标端口

## 优势

1. **全局服务**: 一个服务管理所有容器，统一资源管理
2. **多容器支持**: 同时管理多个容器的 daemon 进程
3. **资源效率**: 共享服务实例，统一的连接池和缓存
4. **统一接口**: 所有容器使用相同的 API 接口

## 相关文档

- [全局服务架构文档](GLOBAL_DAEMON_PROXY_ARCHITECTURE.md) - 详细的架构说明
- [使用示例](examples/global_daemon_proxy_example.py) - 完整的使用示例
- [测试代码](tests/test_global_daemon_proxy_service.py) - 单元测试

## 注意事项

1. daemon-proxy 服务与 backend API 一同启动，无需独立部署
2. 所有容器共享同一个 daemon-proxy 服务实例
3. 预览链接通过全局服务统一管理和代理
4. 支持多容器并发访问和预览链接创建

