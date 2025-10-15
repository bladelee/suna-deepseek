#!/bin/bash

# 编译 daytona daemon 用于 E2E 测试
# 使用国内 Go proxy 加速模块下载

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
DAEMON_SOURCE_DIR="/home/sa/agenthome/daytona/apps/daemon"
DAEMON_OUTPUT_DIR="/home/sa/agenthome/extentions/daemon-proxy/tests/e2e/bin"
DAEMON_BINARY="daytona-daemon"
REQUIRED_GO_VERSION="1.23"

echo -e "${GREEN}=== 编译 daytona daemon 用于 E2E 测试 ===${NC}"

# 检查 Go 环境
echo -e "${YELLOW}检查 Go 环境...${NC}"
if ! command -v go &> /dev/null; then
    echo -e "${RED}错误: Go 未安装或不在 PATH 中${NC}"
    exit 1
fi

GO_VERSION=$(go version | grep -oP 'go\d+\.\d+' | sed 's/go//')
echo "当前 Go 版本: $GO_VERSION"

# 检查 Go 版本
if ! go version | grep -q "go$REQUIRED_GO_VERSION"; then
    echo -e "${YELLOW}警告: 推荐使用 Go $REQUIRED_GO_VERSION，当前版本: $GO_VERSION${NC}"
fi

# 检查源码目录
echo -e "${YELLOW}检查源码目录...${NC}"
if [ ! -d "$DAEMON_SOURCE_DIR" ]; then
    echo -e "${RED}错误: daemon 源码目录不存在: $DAEMON_SOURCE_DIR${NC}"
    exit 1
fi

if [ ! -f "$DAEMON_SOURCE_DIR/go.mod" ]; then
    echo -e "${RED}错误: 未找到 go.mod 文件: $DAEMON_SOURCE_DIR/go.mod${NC}"
    exit 1
fi

# 创建输出目录
mkdir -p "$DAEMON_OUTPUT_DIR"

# 设置 Go proxy（使用国内镜像）
echo -e "${YELLOW}设置 Go proxy...${NC}"
export GOPROXY=https://goproxy.cn,direct
export GOSUMDB=sum.golang.google.cn
export GO111MODULE=on

echo "GOPROXY: $GOPROXY"
echo "GOSUMDB: $GOSUMDB"

# 进入源码目录
cd "$DAEMON_SOURCE_DIR"

# 清理之前的构建
echo -e "${YELLOW}清理之前的构建...${NC}"
go clean -cache
go mod download

# 编译 daemon
echo -e "${YELLOW}编译 daemon...${NC}"
echo "源码目录: $(pwd)"
echo "输出文件: $DAEMON_OUTPUT_DIR/$DAEMON_BINARY"

# 执行编译
if go build -ldflags="-s -w" -o "$DAEMON_OUTPUT_DIR/$DAEMON_BINARY" ./cmd/daemon; then
    echo -e "${GREEN}✅ daemon 编译成功！${NC}"
else
    echo -e "${RED}❌ daemon 编译失败${NC}"
    exit 1
fi

# 验证编译结果
echo -e "${YELLOW}验证编译结果...${NC}"
if [ -f "$DAEMON_OUTPUT_DIR/$DAEMON_BINARY" ]; then
    BINARY_SIZE=$(du -h "$DAEMON_OUTPUT_DIR/$DAEMON_BINARY" | cut -f1)
    echo -e "${GREEN}✅ 二进制文件已生成: $DAEMON_OUTPUT_DIR/$DAEMON_BINARY (大小: $BINARY_SIZE)${NC}"
    
    # 检查文件权限
    chmod +x "$DAEMON_OUTPUT_DIR/$DAEMON_BINARY"
    echo -e "${GREEN}✅ 已设置执行权限${NC}"
    
    # 测试运行
    echo -e "${YELLOW}测试 daemon 运行...${NC}"
    if "$DAEMON_OUTPUT_DIR/$DAEMON_BINARY" --help &> /dev/null; then
        echo -e "${GREEN}✅ daemon 可以正常启动${NC}"
    else
        echo -e "${YELLOW}⚠️  daemon 启动测试失败，但二进制文件已生成${NC}"
    fi
    
    # 显示版本信息
    echo -e "${YELLOW}daemon 版本信息:${NC}"
    "$DAEMON_OUTPUT_DIR/$DAEMON_BINARY" --version 2>/dev/null || echo "无法获取版本信息"
    
else
    echo -e "${RED}❌ 二进制文件未生成${NC}"
    exit 1
fi

echo -e "${GREEN}=== 编译完成 ===${NC}"
echo -e "${GREEN}daemon 二进制文件: $DAEMON_OUTPUT_DIR/$DAEMON_BINARY${NC}"
echo -e "${GREEN}现在可以运行 E2E 测试了！${NC}"
