#!/bin/bash

# 清理 daemon 进程和测试环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
DAEMON_PORT=2280
DAEMON_PROCESS_NAME="daytona-daemon"

echo -e "${GREEN}=== 清理 daemon 测试环境 ===${NC}"

# 查找并终止 daemon 进程
echo -e "${YELLOW}查找 daemon 进程...${NC}"

# 查找所有相关的 daemon 进程
DAEMON_PIDS=$(pgrep -f "$DAEMON_PROCESS_NAME" 2>/dev/null || true)

if [ -n "$DAEMON_PIDS" ]; then
    echo -e "${YELLOW}找到 daemon 进程: $DAEMON_PIDS${NC}"
    
    # 优雅终止
    echo -e "${YELLOW}正在优雅终止 daemon 进程...${NC}"
    for pid in $DAEMON_PIDS; do
        if kill -TERM "$pid" 2>/dev/null; then
            echo -e "${GREEN}✅ 已发送 TERM 信号到进程 $pid${NC}"
        else
            echo -e "${YELLOW}⚠️  无法发送 TERM 信号到进程 $pid${NC}"
        fi
    done
    
    # 等待进程终止
    sleep 2
    
    # 检查是否还有进程存在
    REMAINING_PIDS=$(pgrep -f "$DAEMON_PROCESS_NAME" 2>/dev/null || true)
    if [ -n "$REMAINING_PIDS" ]; then
        echo -e "${YELLOW}强制终止剩余进程...${NC}"
        for pid in $REMAINING_PIDS; do
            if kill -KILL "$pid" 2>/dev/null; then
                echo -e "${GREEN}✅ 已强制终止进程 $pid${NC}"
            else
                echo -e "${YELLOW}⚠️  无法强制终止进程 $pid${NC}"
            fi
        done
    fi
    
    echo -e "${GREEN}✅ daemon 进程已清理${NC}"
else
    echo -e "${GREEN}✅ 未找到运行中的 daemon 进程${NC}"
fi

# 检查端口占用
echo -e "${YELLOW}检查端口占用...${NC}"
if command -v netstat &> /dev/null; then
    PORT_PIDS=$(netstat -tulnp 2>/dev/null | grep ":$DAEMON_PORT " | awk '{print $7}' | cut -d'/' -f1 | sort -u || true)
elif command -v ss &> /dev/null; then
    PORT_PIDS=$(ss -tulnp 2>/dev/null | grep ":$DAEMON_PORT " | grep -oP 'pid=\d+' | cut -d'=' -f2 | sort -u || true)
else
    PORT_PIDS=""
fi

if [ -n "$PORT_PIDS" ]; then
    echo -e "${YELLOW}端口 $DAEMON_PORT 仍被占用，进程: $PORT_PIDS${NC}"
    for pid in $PORT_PIDS; do
        if [ "$pid" != "-" ] && [ -n "$pid" ]; then
            echo -e "${YELLOW}终止占用端口的进程 $pid...${NC}"
            kill -TERM "$pid" 2>/dev/null || true
            sleep 1
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    echo -e "${GREEN}✅ 端口占用已清理${NC}"
else
    echo -e "${GREEN}✅ 端口 $DAEMON_PORT 已释放${NC}"
fi

# 清理临时文件
echo -e "${YELLOW}清理临时文件...${NC}"

# 清理可能的日志文件
LOG_FILES=(
    "/tmp/daemon-proxy-test.log"
    "/tmp/daytona-daemon.log"
    "/tmp/e2e-test.log"
)

for log_file in "${LOG_FILES[@]}"; do
    if [ -f "$log_file" ]; then
        rm -f "$log_file"
        echo -e "${GREEN}✅ 已删除日志文件: $log_file${NC}"
    fi
done

# 清理可能的 PID 文件
PID_FILES=(
    "/tmp/daemon-proxy.pid"
    "/tmp/daytona-daemon.pid"
    "/tmp/e2e-test.pid"
)

for pid_file in "${PID_FILES[@]}"; do
    if [ -f "$pid_file" ]; then
        rm -f "$pid_file"
        echo -e "${GREEN}✅ 已删除 PID 文件: $pid_file${NC}"
    fi
done

# 清理 Docker 容器（如果存在）
echo -e "${YELLOW}清理 Docker 测试容器...${NC}"
if command -v docker &> /dev/null; then
    # 停止并删除 E2E 测试相关的容器
    E2E_CONTAINERS=$(docker ps -a --filter "name=e2e" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$E2E_CONTAINERS" ]; then
        echo -e "${YELLOW}停止 E2E 测试容器...${NC}"
        echo "$E2E_CONTAINERS" | xargs docker stop 2>/dev/null || true
        echo -e "${YELLOW}删除 E2E 测试容器...${NC}"
        echo "$E2E_CONTAINERS" | xargs docker rm 2>/dev/null || true
        echo -e "${GREEN}✅ E2E 测试容器已清理${NC}"
    else
        echo -e "${GREEN}✅ 未找到 E2E 测试容器${NC}"
    fi
    
    # 清理未使用的镜像
    echo -e "${YELLOW}清理未使用的 Docker 镜像...${NC}"
    docker image prune -f 2>/dev/null || true
    echo -e "${GREEN}✅ Docker 镜像已清理${NC}"
else
    echo -e "${YELLOW}⚠️  Docker 不可用，跳过容器清理${NC}"
fi

# 清理网络命名空间（如果有）
echo -e "${YELLOW}检查网络命名空间...${NC}"
if command -v ip &> /dev/null; then
    # 查找可能的测试网络命名空间
    TEST_NS=$(ip netns list 2>/dev/null | grep -E "(e2e|test|daemon)" || true)
    if [ -n "$TEST_NS" ]; then
        echo -e "${YELLOW}找到测试网络命名空间: $TEST_NS${NC}"
        echo -e "${YELLOW}注意: 请手动清理网络命名空间${NC}"
    else
        echo -e "${GREEN}✅ 未找到测试网络命名空间${NC}"
    fi
fi

echo -e "${GREEN}=== 清理完成 ===${NC}"
echo -e "${GREEN}daemon 测试环境已清理完毕${NC}"
