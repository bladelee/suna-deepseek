# daemon-proxy E2E 测试指南

## 概述

本文档描述了 daemon-proxy 的端到端（E2E）测试体系，重点测试**预览链接功能**。测试分为三个层次，从简单到复杂：

1. **Mock 环境测试** - 使用 mock daemon 和 mock 服务
2. **真实 Daemon 测试** - 使用真实编译的 daemon 进程
3. **Docker 环境测试** - 在容器化环境中测试，包括真实编译的 daemon

## 测试架构

### 测试分组

```
tests/e2e/
├── conftest.py              # 共享配置和 fixtures
├── test_e2e_mock.py         # 第一组：Mock 环境测试
├── test_e2e_real.py         # 第二组：真实 daemon 测试
├── test_e2e_docker.py       # 第三组：Docker 环境测试
├── fixtures/                # 测试辅助工具
│   ├── mock_daemon.py       # Mock daemon 服务器
│   ├── mock_services.py     # Mock HTTP 服务器
│   └── docker_helpers.py    # Docker 测试辅助
└── scenarios/               # 测试场景
    └── preview_scenarios.py # 预览链接测试场景
```

### 测试标记

- `e2e_mock` - Mock 环境测试
- `e2e_real` - 真实 daemon 测试
- `e2e_docker` - Docker 环境测试

## 快速开始

### 1. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装 E2E 测试依赖
make e2e-setup
```

### 2. 运行测试

```bash
# 运行第一组测试（Mock 环境）
make test-e2e-mock

# 运行第二组测试（真实 daemon）
make test-e2e-real

# 运行第三组测试（Docker 环境）
make test-e2e-docker

# 运行所有 E2E 测试
make test-e2e-all
```

## 详细说明

### 第一组：Mock 环境测试

**目标**: 快速验证预览链接功能逻辑，不依赖外部服务

**特点**:
- 使用 mock daemon 服务器
- 使用 mock VNC/Web 服务
- 测试速度快，适合开发阶段
- 不依赖真实的 daytona daemon

**运行方式**:
```bash
pytest tests/e2e/test_e2e_mock.py -m e2e_mock -v
```

**测试场景**:
- 预览链接创建和访问
- 预览链接生命周期管理
- 多个预览链接并发处理
- 预览链接错误处理
- 预览链接统计功能

### 第二组：真实 Daemon 测试

**目标**: 验证与真实 daemon 的集成，测试实际网络通信

**前置条件**:
- daytona daemon 二进制文件存在且可执行
- 端口 2280 可用
- 如果条件不满足，测试会自动跳过

**特点**:
- 使用真实的 daytona daemon 进程
- 使用 mock 目标服务
- 测试真实的网络通信
- 验证 daemon 集成功能

**运行方式**:
```bash
pytest tests/e2e/test_e2e_real.py -m e2e_real -v
```

**测试场景**:
- 真实 daemon 连接和状态检查
- 通过真实 daemon 的代理功能
- 预览链接与真实 daemon 的集成
- 数据传输完整性验证
- 并发请求处理
- 长时间运行稳定性

### 第三组：Docker 环境测试

**目标**: 模拟生产环境，测试容器化部署

**前置条件**:
- Docker 和 docker-compose 可用
- 足够的系统资源

**特点**:
- 完整的容器化环境
- 模拟生产部署场景
- 测试容器间通信
- 验证网络隔离

**运行方式**:
```bash
# 使用 docker-compose
make e2e-docker-run

# 或直接运行测试
pytest tests/e2e/test_e2e_docker.py -m e2e_docker -v
```

**测试场景**:
- 容器化环境部署
- 容器间服务通信
- 网络隔离验证
- 资源限制下的表现
- 容器重启恢复

## 测试场景详解

### 预览链接核心功能

```python
# 创建预览链接
async with DaemonProxyClient(proxy_url) as client:
    vnc_link = await client.get_preview_link(6080)
    web_link = await client.get_preview_link(8080)
    
    # 访问预览链接
    async with aiohttp.ClientSession() as session:
        async with session.get(vnc_link.url) as response:
            assert response.status == 200
```

### 预览链接生命周期

```python
# 完整生命周期测试
scenarios = PreviewLinkTestScenarios(proxy_url)
result = await scenarios.test_preview_link_lifecycle(8080)

assert result["created"] is True
assert result["accessed"] is True
assert result["revoked"] is True
assert result["access_after_revoke"] is True
```

### 多个预览链接管理

```python
# 并发创建多个预览链接
result = await scenarios.test_multiple_preview_links([6080, 8080, 3000])

assert len(result["created_links"]) >= 2
assert result["stats"]["total_links"] >= 2
assert result["concurrent_access"]["successful"] >= 2
```

## 环境配置

### Mock 环境配置

```python
config = Config()
config.set("server.host", "127.0.0.1")
config.set("server.port", 0)  # 随机端口
config.set("daemon.mode", "mock")
config.set("security.enabled", False)
```

### 真实 Daemon 配置

```python
config = Config()
config.set("daemon.mode", "host")
config.set("daemon.port", 2280)
config.set("daemon.path", "/usr/local/bin/daytona")
config.set("daemon.startup_timeout", 30)
```

### Docker 环境配置

```yaml
# docker-compose-e2e.yml
services:
  daemon-proxy:
    build: .
    environment:
      - DAEMON_MODE=docker
      - DAEMON_CONTAINER_NAME=test-daemon
    networks:
      - e2e-network
```

## 故障排查

### 常见问题

1. **Mock 测试失败**
   - 检查端口是否被占用
   - 确认 Python 依赖已安装
   - 查看测试日志

2. **真实 Daemon 测试跳过**
   - 确认 daytona daemon 存在且可执行
   - 检查端口 2280 是否可用
   - 验证 daemon 启动权限

3. **Docker 测试失败**
   - 确认 Docker 和 docker-compose 可用
   - 检查系统资源是否充足
   - 清理旧的 Docker 容器和镜像

### 调试技巧

```bash
# 查看详细测试输出
pytest tests/e2e/ -v -s

# 运行特定测试
pytest tests/e2e/test_e2e_mock.py::TestE2EMock::test_preview_link_creation_vnc -v

# 查看测试覆盖率
pytest tests/e2e/ --cov=daemon_proxy --cov-report=html
```

### 日志分析

```bash
# 查看 daemon-proxy 日志
tail -f logs/daemon-proxy.log

# 查看 Docker 容器日志
docker-compose -f docker-compose-e2e.yml logs daemon-proxy

# 过滤错误日志
grep ERROR logs/daemon-proxy.log
```

## 性能基准

### 预期性能指标

| 测试组 | 创建链接时间 | 访问响应时间 | 并发处理能力 |
|--------|-------------|-------------|-------------|
| Mock   | < 0.1s      | < 0.1s      | 100+ 请求/s  |
| Real   | < 1.0s      | < 0.5s      | 50+ 请求/s   |
| Docker | < 2.0s      | < 1.0s      | 20+ 请求/s   |

### 性能测试

```bash
# 运行性能测试
make perf-test

# 运行并发测试
pytest tests/e2e/ -k "concurrent" -v
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-mock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: make e2e-setup
      - name: Run Mock E2E tests
        run: make test-e2e-mock

  e2e-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Docker
        run: |
          sudo systemctl start docker
          sudo usermod -aG docker $USER
      - name: Run Docker E2E tests
        run: make e2e-docker-run
```

## 最佳实践

### 开发阶段

1. **主要使用 Mock 测试** - 快速反馈，不依赖外部服务
2. **定期运行真实 Daemon 测试** - 验证集成功能
3. **发布前运行 Docker 测试** - 确保生产环境兼容性

### 测试编写

1. **使用场景封装** - 复用测试逻辑
2. **适当的断言** - 验证关键功能点
3. **错误处理** - 测试异常情况
4. **资源清理** - 避免测试间相互影响

### 维护建议

1. **定期更新依赖** - 保持测试环境稳定
2. **监控测试性能** - 及时发现性能回归
3. **文档同步更新** - 保持文档与代码一致

## 扩展测试

### 添加新的测试场景

1. 在 `scenarios/preview_scenarios.py` 中添加新场景
2. 在相应的测试文件中调用新场景
3. 更新文档说明

### 添加新的测试环境

1. 创建新的测试文件（如 `test_e2e_kubernetes.py`）
2. 添加相应的 fixtures 和配置
3. 更新 Makefile 和文档

## 总结

E2E 测试体系提供了完整的预览链接功能验证：

- ✅ **Mock 环境** - 快速验证逻辑正确性
- ✅ **真实环境** - 验证实际集成功能  
- ✅ **容器环境** - 验证生产部署兼容性

通过三层测试，确保 daemon-proxy 的预览链接功能在各种环境下都能稳定工作。


## 真实 Daemon 编译和测试

### 编译真实 Daemon

为了进行完整的端到端测试，我们需要编译真实的 daytona daemon：

```bash
# 编译 daemon
make e2e-build-daemon

# 检查编译结果
make e2e-check-daemon
```

### 环境要求

- Go 1.23.0+ 环境
- Git
- Make

### 运行真实 Daemon 测试

```bash
# 编译并运行真实 daemon 测试
make test-e2e-real-with-daemon

# 或者分步执行
make e2e-build-daemon
make test-e2e-real
```

### 清理环境

```bash
# 清理 daemon 进程和测试环境
make e2e-cleanup-daemon
```

### 故障排查

如果遇到编译问题：

1. 检查 Go 版本：`go version`
2. 设置 Go proxy：`export GOPROXY=https://goproxy.cn,direct`
3. 检查权限：确保有写入 `tests/e2e/bin/` 的权限

详细说明请参考 [BUILD_DAEMON.md](BUILD_DAEMON.md)。

## 完整测试流程

### 推荐测试顺序

1. **Mock 环境测试**（最快）
   ```bash
   make test-e2e-mock
   ```

2. **真实 Daemon 测试**（中等复杂度）
   ```bash
   make test-e2e-real-with-daemon
   ```

3. **Docker 环境测试**（最复杂）
   ```bash
   make test-e2e-docker-with-daemon
   ```

### 运行所有测试

```bash
# 运行所有 E2E 测试
make test-e2e-all
```

## 测试结果验证

### 成功指标

- 所有测试通过
- 预览链接功能正常
- 健康检查通过
- 无内存泄漏
- 无端口冲突

### 性能指标

- Mock 环境：< 0.1s 每个测试
- 真实环境：< 1.0s 每个测试  
- Docker 环境：< 2.0s 每个测试

