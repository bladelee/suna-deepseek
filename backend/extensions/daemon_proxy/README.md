# Daemon Proxy Service

一个独立的Python服务，用于代理Daytona daemon的HTTP请求，无需完整的runner组件。

## 功能特性

- 🚀 **轻量级代理**：直接与daemon通信，绕过复杂的runner组件
- 🔄 **端口转发**：支持将任意端口服务通过daemon代理暴露
- 🔗 **预览链接**：提供安全的预览链接功能，支持VNC和Web服务
- 🐳 **Docker支持**：支持容器内daemon和宿主机daemon两种模式
- 🔒 **安全控制**：可选的API密钥认证
- 📊 **监控日志**：完整的请求/响应日志记录
- 🧪 **测试覆盖**：包含完整的单元测试和集成测试

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制配置文件
cp config.example.yaml config.yaml

# 编辑配置文件
vim config.yaml
```

### 3. 启动服务

```bash
# 直接启动
python main.py

# 或使用配置文件
python main.py --config config.yaml
```

### 4. 测试服务

```bash
# 运行测试
pytest tests/

# 测试代理功能
curl http://localhost:8080/proxy/8080/
```

## 配置说明

### 基本配置

```yaml
# config.yaml
server:
  host: "0.0.0.0"
  port: 8080

daemon:
  mode: "host"  # "host" 或 "docker"
  port: 2280
  path: "/usr/local/bin/daytona"  # 仅host模式需要
  container_name: "my-sandbox"    # 仅docker模式需要
  startup_timeout: 30
  # 注入模式（docker 模式可用）：
  # volume：从宿主机复制二进制，注入容器后启动
  # direct：使用容器内已有的 daytona 二进制
  injection_mode: "volume"
  # 注入模式下，宿主机二进制源路径（仅支持 amd64）
  binary_source_path: "/usr/local/bin/daytona"

security:
  enabled: false
  api_key: "your-secret-key"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 环境变量

```bash
export DAEMON_PROXY_HOST=0.0.0.0
export DAEMON_PROXY_PORT=8080
export DAEMON_MODE=host
export DAEMON_PORT=2280
export DAEMON_PATH=/usr/local/bin/daytona
export DAEMON_INJECTION_MODE=volume
export DAEMON_BINARY_SOURCE_PATH=/usr/local/bin/daytona
export SECURITY_ENABLED=false
export LOG_LEVEL=INFO
```

## 注入机制（与 Daytona Runner 一致的启动流程）

当以 docker 模式运行且 `daemon.injection_mode=volume` 时，daemon-proxy 会按以下步骤在目标容器中动态注入并启动 daytona 二进制：

- 二进制准备：从宿主机 `daemon.binary_source_path` 复制到临时目录 `.tmp/binaries/daemon-amd64` 并赋予执行权限
- 注入容器：以归档形式复制到容器内 `/usr/local/bin/daytona` 并 `chmod +x`
- 启动进程：在容器内执行 `/usr/local/bin/daytona --work-dir <容器工作目录或默认 /workspace>`
- 健康检查：轮询容器 IP 的 `http://<ip>:2280/version` 直至就绪或超时

仅支持 amd64/x86_64 架构，其他架构会直接失败。

### 运行示例（docker 注入）

```bash
# 指定容器名称，并启用注入
python main.py \
  --daemon-mode docker \
  --container-name my-sandbox \
  --injection-mode volume \
  --binary-source-path /usr/local/bin/daytona
```

### 运行示例（docker 直接模式）

```bash
python main.py \
  --daemon-mode docker \
  --container-name my-sandbox \
  --injection-mode direct
```

## API使用

### 代理请求

```bash
# 代理到8080端口的服务
curl http://localhost:8080/proxy/8080/

# 代理到特定路径
curl http://localhost:8080/proxy/8080/api/data

# 带查询参数
curl http://localhost:8080/proxy/8080/search?q=test

# POST请求
curl -X POST http://localhost:8080/proxy/8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

### 预览链接

```bash
# 创建预览链接
curl -X POST http://localhost:8080/api/preview/create \
  -H "Content-Type: application/json" \
  -d '{"port": 6080}'

# 访问预览链接
curl http://localhost:8080/preview/{token}/

# 获取预览链接统计
curl http://localhost:8080/api/preview/stats

# 撤销预览链接
curl -X DELETE http://localhost:8080/api/preview/{token}
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/health

# 检查daemon状态
curl http://localhost:8080/daemon/status
```

## Python客户端使用

### 基本使用

```python
import asyncio
from daemon_proxy.client import get_preview_link, get_vnc_preview_link, get_website_preview_link

async def main():
    # 获取VNC预览链接（6080端口）
    vnc_link = await get_vnc_preview_link()
    print(f"VNC预览链接: {vnc_link.url}")
    print(f"Token: {vnc_link.token}")
    
    # 获取网站预览链接（8080端口）
    website_link = await get_website_preview_link()
    print(f"网站预览链接: {website_link.url}")

asyncio.run(main())
```

### 客户端类使用

```python
import asyncio
from daemon_proxy.client import DaemonProxyClient

async def main():
    async with DaemonProxyClient("http://localhost:8080") as client:
        # 健康检查
        health = await client.health_check()
        print(f"服务状态: {health['status']}")
        
        # 获取预览链接
        vnc_link = await client.get_preview_link(6080)
        print(f"VNC预览链接: {vnc_link.url}")
        
        # 获取统计信息
        stats = await client.get_preview_stats()
        print(f"预览链接统计: {stats}")
        
        # 撤销链接
        await client.revoke_preview_link(vnc_link.token)

asyncio.run(main())
```

### 模拟Daytona SDK使用方式

```python
import asyncio
from daemon_proxy.client import DaemonProxyClient

class Sandbox:
    """模拟沙盒类"""
    def __init__(self, client: DaemonProxyClient):
        self.client = client
    
    async def get_preview_link(self, port: int):
        """获取预览链接（模拟Daytona SDK方法）"""
        return await self.client.get_preview_link(port)

async def main():
    async with DaemonProxyClient("http://localhost:8080") as client:
        sandbox = Sandbox(client)
        
        # 模拟Daytona SDK的使用方式
        vnc_link = await sandbox.get_preview_link(6080)
        website_link = await sandbox.get_preview_link(8080)
        
        # 提取URL和Token（模拟tool_base.py的处理方式）
        vnc_url = vnc_link.url
        website_url = website_link.url
        token = vnc_link.token
        
        print(f"VNC URL: {vnc_url}")
        print(f"Website URL: {website_url}")
        print(f"Token: {token}")

asyncio.run(main())
```

## 部署方式

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "main.py"]
```

### Systemd服务

```ini
[Unit]
Description=Daemon Proxy Service
After=network.target

[Service]
Type=simple
User=daemon-proxy
WorkingDirectory=/opt/daemon-proxy
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 开发指南

### 项目结构

```
daemon-proxy/
├── main.py                 # 主程序入口
├── daemon_proxy/          # 核心模块
│   ├── __init__.py
│   ├── proxy.py           # 代理服务
│   ├── daemon.py          # daemon管理
│   ├── config.py          # 配置管理
│   └── utils.py           # 工具函数
├── tests/                 # 测试代码
│   ├── __init__.py
│   ├── test_proxy.py      # 代理测试
│   ├── test_daemon.py     # daemon测试
│   └── test_integration.py # 集成测试
├── config.example.yaml    # 配置示例
├── requirements.txt       # 依赖列表
└── README.md             # 说明文档
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_proxy.py

# 运行集成测试
pytest tests/test_integration.py

# 生成覆盖率报告
pytest --cov=daemon_proxy --cov-report=html
```

## 故障排除

### 常见问题

1. **daemon启动失败**
   - 检查daemon二进制文件路径
   - 确认daemon有执行权限
   - 查看daemon日志

2. **代理请求失败**
   - 检查目标端口是否在监听
   - 确认daemon代理功能正常
   - 查看代理服务日志

3. **Docker模式问题**
   - 确认容器名称正确
   - 检查容器网络配置
   - 验证容器IP获取

### 日志分析

```bash
# 查看详细日志
tail -f logs/daemon-proxy.log

# 过滤错误日志
grep ERROR logs/daemon-proxy.log

# 分析请求日志
grep "Request:" logs/daemon-proxy.log
```

## 许可证

MIT License
