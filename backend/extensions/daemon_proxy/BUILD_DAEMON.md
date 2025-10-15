# 编译真实 Daemon 用于 E2E 测试

本文档说明如何编译真实的 daytona daemon 并用于 E2E 测试。

## 概述

为了进行完整的端到端测试，我们需要编译真实的 daytona daemon 二进制文件，而不是使用 mock 服务。这样可以测试：

- 真实的 daemon 进程管理
- 真实的网络通信
- 真实的端口转发
- 真实的配置加载

## 环境要求

### 必需依赖

1. **Go 1.23.0+**
   ```bash
   go version
   # 应该显示 go1.23.x 或更高版本
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Make**
   ```bash
   make --version
   ```

### 可选依赖

- **Docker** (用于第三组测试)
- **Python 3.8+** (用于运行测试)

## 编译步骤

### 方法 1: 使用 Makefile 命令（推荐）

```bash
# 编译 daemon
make e2e-build-daemon

# 检查编译结果
make e2e-check-daemon
```

### 方法 2: 手动编译

```bash
# 进入项目目录
cd /home/sa/agenthome/extentions/daemon-proxy

# 运行编译脚本
./tests/e2e/scripts/build_daemon.sh
```

### 方法 3: 直接使用 Go 编译

```bash
# 设置 Go 环境变量（使用国内镜像）
export GOPROXY=https://goproxy.cn,direct
export GOSUMDB=sum.golang.google.cn
export GO111MODULE=on

# 进入 daemon 源码目录
cd /home/sa/agenthome/daytona/apps/daemon

# 下载依赖
go mod download

# 编译
go build -ldflags="-s -w" -o /home/sa/agenthome/extentions/daemon-proxy/tests/e2e/bin/daytona-daemon ./cmd/daemon
```

## 编译输出

编译成功后，daemon 二进制文件将位于：
```
/home/sa/agenthome/extentions/daemon-proxy/tests/e2e/bin/daytona-daemon
```

## 验证编译结果

### 检查二进制文件

```bash
# 检查文件是否存在
ls -la tests/e2e/bin/daytona-daemon

# 检查文件权限
file tests/e2e/bin/daytona-daemon

# 检查版本信息
./tests/e2e/bin/daytona-daemon --version
```

### 测试运行

```bash
# 测试 daemon 启动
./tests/e2e/bin/daytona-daemon --help

# 检查环境
make e2e-check-daemon
```

## 运行 E2E 测试

### 第二组测试（真实 Daemon）

```bash
# 编译并运行真实 daemon 测试
make test-e2e-real-with-daemon

# 或者分步执行
make e2e-build-daemon
make test-e2e-real
```

### 第三组测试（Docker 环境）

```bash
# 编译并运行 Docker 环境测试
make test-e2e-docker-with-daemon

# 或者分步执行
make e2e-build-daemon
make test-e2e-docker
```

## 故障排查

### 编译失败

1. **Go 版本过低**
   ```bash
   # 检查 Go 版本
   go version
   # 需要 1.23.0 或更高版本
   ```

2. **网络问题**
   ```bash
   # 设置国内 Go proxy
   export GOPROXY=https://goproxy.cn,direct
   export GOSUMDB=sum.golang.google.cn
   ```

3. **权限问题**
   ```bash
   # 确保有写入权限
   chmod +x tests/e2e/scripts/build_daemon.sh
   mkdir -p tests/e2e/bin
   ```

### 测试失败

1. **Daemon 未编译**
   ```bash
   # 检查二进制文件
   ls -la tests/e2e/bin/daytona-daemon
   
   # 如果不存在，重新编译
   make e2e-build-daemon
   ```

2. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tuln | grep 2280
   
   # 清理端口
   make e2e-cleanup-daemon
   ```

3. **进程未清理**
   ```bash
   # 清理 daemon 进程
   make e2e-cleanup-daemon
   
   # 或者手动清理
   pkill -f daytona-daemon
   ```

## 高级用法

### 自定义编译参数

编辑 `tests/e2e/scripts/build_daemon.sh`：

```bash
# 修改编译标志
BUILD_FLAGS="-ldflags='-s -w -X main.version=test'"

# 修改输出路径
DAEMON_OUTPUT_DIR="/custom/path/bin"
```

### 调试模式编译

```bash
# 编译调试版本
cd /home/sa/agenthome/daytona/apps/daemon
go build -gcflags="all=-N -l" -o /path/to/daytona-daemon-debug ./cmd/daemon
```

### 交叉编译

```bash
# 编译 Linux 版本（在 macOS 上）
GOOS=linux GOARCH=amd64 go build -o daytona-daemon-linux ./cmd/daemon

# 编译 Windows 版本
GOOS=windows GOARCH=amd64 go build -o daytona-daemon.exe ./cmd/daemon
```

## 性能优化

### 编译优化

```bash
# 使用更激进的优化
go build -ldflags="-s -w" -trimpath -o daytona-daemon ./cmd/daemon
```

### 运行时优化

```bash
# 设置 Go 运行时参数
export GOMAXPROCS=4
export GOGC=100
```

## 持续集成

### GitHub Actions 示例

```yaml
name: E2E Tests with Real Daemon
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v3
        with:
          go-version: '1.23'
      - name: Build Daemon
        run: make e2e-build-daemon
      - name: Run E2E Tests
        run: make test-e2e-real-with-daemon
```

## 总结

通过编译真实的 daytona daemon，我们可以进行更完整和真实的端到端测试，确保 daemon-proxy 在实际生产环境中的稳定性和可靠性。

关键命令：
- `make e2e-build-daemon` - 编译 daemon
- `make e2e-check-daemon` - 检查环境
- `make test-e2e-real-with-daemon` - 运行真实 daemon 测试
- `make e2e-cleanup-daemon` - 清理环境
