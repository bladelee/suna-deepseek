#!/bin/bash

# 检查 daemon 环境和状态

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
DAEMON_BINARY="/home/sa/agenthome/extentions/daemon-proxy/tests/e2e/bin/daytona-daemon"
SYSTEM_DAEMON="/usr/local/bin/daytona"
DAEMON_PORT=2280

echo -e "${GREEN}=== 检查 daemon 环境 ===${NC}"

# 检查编译的 daemon
echo -e "${YELLOW}检查编译的 daemon...${NC}"
if [ -f "$DAEMON_BINARY" ]; then
    echo -e "${GREEN}✅ 找到编译的 daemon: $DAEMON_BINARY${NC}"
    
    # 检查权限
    if [ -x "$DAEMON_BINARY" ]; then
        echo -e "${GREEN}✅ daemon 具有执行权限${NC}"
    else
        echo -e "${YELLOW}⚠️  daemon 没有执行权限，正在设置...${NC}"
        chmod +x "$DAEMON_BINARY"
        echo -e "${GREEN}✅ 已设置执行权限${NC}"
    fi
    
    # 检查版本
    echo -e "${YELLOW}daemon 版本信息:${NC}"
    if "$DAEMON_BINARY" --version 2>/dev/null; then
        echo -e "${GREEN}✅ daemon 版本信息获取成功${NC}"
    else
        echo -e "${YELLOW}⚠️  无法获取 daemon 版本信息${NC}"
    fi
    
else
    echo -e "${RED}❌ 未找到编译的 daemon: $DAEMON_BINARY${NC}"
    echo -e "${YELLOW}请先运行: ./tests/e2e/scripts/build_daemon.sh${NC}"
fi

# 检查系统 daemon
echo -e "${YELLOW}检查系统 daemon...${NC}"
if [ -f "$SYSTEM_DAEMON" ]; then
    echo -e "${GREEN}✅ 找到系统 daemon: $SYSTEM_DAEMON${NC}"
    
    if [ -x "$SYSTEM_DAEMON" ]; then
        echo -e "${GREEN}✅ 系统 daemon 具有执行权限${NC}"
    else
        echo -e "${YELLOW}⚠️  系统 daemon 没有执行权限${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到系统 daemon: $SYSTEM_DAEMON${NC}"
fi

# 检查端口占用
echo -e "${YELLOW}检查端口占用...${NC}"
if command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":$DAEMON_PORT "; then
        echo -e "${YELLOW}⚠️  端口 $DAEMON_PORT 已被占用${NC}"
        echo "占用进程:"
        netstat -tulnp | grep ":$DAEMON_PORT "
    else
        echo -e "${GREEN}✅ 端口 $DAEMON_PORT 可用${NC}"
    fi
elif command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":$DAEMON_PORT "; then
        echo -e "${YELLOW}⚠️  端口 $DAEMON_PORT 已被占用${NC}"
        echo "占用进程:"
        ss -tulnp | grep ":$DAEMON_PORT "
    else
        echo -e "${GREEN}✅ 端口 $DAEMON_PORT 可用${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  无法检查端口占用（netstat 和 ss 都不可用）${NC}"
fi

# 检查 Go 环境
echo -e "${YELLOW}检查 Go 环境...${NC}"
if command -v go &> /dev/null; then
    GO_VERSION=$(go version | grep -oP 'go\d+\.\d+' | sed 's/go//')
    echo -e "${GREEN}✅ Go 已安装，版本: $GO_VERSION${NC}"
    
    # 检查 Go proxy 设置
    if [ -n "$GOPROXY" ]; then
        echo -e "${GREEN}✅ GOPROXY 已设置: $GOPROXY${NC}"
    else
        echo -e "${YELLOW}⚠️  GOPROXY 未设置，建议设置国内镜像${NC}"
        echo "建议运行: export GOPROXY=https://goproxy.cn,direct"
    fi
else
    echo -e "${RED}❌ Go 未安装或不在 PATH 中${NC}"
fi

# 检查 Docker 环境（用于第三组测试）
echo -e "${YELLOW}检查 Docker 环境...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    echo -e "${GREEN}✅ Docker 已安装，版本: $DOCKER_VERSION${NC}"
    
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker 服务正在运行${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker 服务未运行${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker 未安装（第三组测试需要）${NC}"
fi

# 检查 Python 环境
echo -e "${YELLOW}检查 Python 环境...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+\.\d+')
    echo -e "${GREEN}✅ Python3 已安装，版本: $PYTHON_VERSION${NC}"
    
    # 检查必要的 Python 包
    REQUIRED_PACKAGES=("aiohttp" "pytest" "pytest-asyncio" "pyyaml" "docker")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}✅ $package 已安装${NC}"
        else
            echo -e "${YELLOW}⚠️  $package 未安装${NC}"
        fi
    done
else
    echo -e "${RED}❌ Python3 未安装或不在 PATH 中${NC}"
fi

echo -e "${GREEN}=== 检查完成 ===${NC}"

# 总结
echo -e "${YELLOW}总结:${NC}"
if [ -f "$DAEMON_BINARY" ] && [ -x "$DAEMON_BINARY" ]; then
    echo -e "${GREEN}✅ 可以运行 E2E 测试${NC}"
    echo -e "${GREEN}运行命令: make test-e2e-real${NC}"
else
    echo -e "${RED}❌ 需要先编译 daemon${NC}"
    echo -e "${YELLOW}运行命令: ./tests/e2e/scripts/build_daemon.sh${NC}"
fi
