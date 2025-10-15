#!/bin/sh

# daemon-proxy启动脚本
# 用于Dockerfile.daemon版本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查daemon二进制文件
check_daemon_binary() {
    log_info "检查daemon二进制文件..."
    
    if [ ! -f "$DAEMON_BINARY_PATH" ]; then
        log_error "Daemon二进制文件不存在: $DAEMON_BINARY_PATH"
        exit 1
    fi
    
    if [ ! -x "$DAEMON_BINARY_PATH" ]; then
        log_warn "Daemon二进制文件没有执行权限，正在设置..."
        chmod +x "$DAEMON_BINARY_PATH"
    fi
    
    log_info "Daemon二进制文件检查通过: $DAEMON_BINARY_PATH"
    
    # 显示文件信息
    ls -la "$DAEMON_BINARY_PATH"
    # file命令在Alpine Linux中不可用，使用ls -la代替
}

# 检查Docker连接
check_docker_connection() {
    log_info "检查Docker连接..."
    
    if ! docker info >/dev/null 2>&1; then
        log_error "无法连接到Docker daemon"
        log_error "请确保Docker socket已正确挂载: /var/run/docker.sock"
        exit 1
    fi
    
    log_info "Docker连接检查通过"
}

# 检查配置文件
check_config_file() {
    log_info "检查daemon-proxy配置文件..."
    
    if [ -n "$DAEMON_CONFIG_FILE" ] && [ -f "$DAEMON_CONFIG_FILE" ]; then
        log_info "配置文件存在: $DAEMON_CONFIG_FILE"
    else
        log_warn "配置文件不存在或未设置: $DAEMON_CONFIG_FILE"
    fi
}

# 显示环境信息
show_environment() {
    log_info "=== daemon-proxy环境信息 ==="
    echo "DAEMON_BINARY_PATH: $DAEMON_BINARY_PATH"
    echo "DAEMON_INJECTION_METHOD: $DAEMON_INJECTION_METHOD"
    echo "DAEMON_INJECTION_MODE: $DAEMON_INJECTION_MODE"
    echo "DAEMON_PORT: $DAEMON_PORT"
    echo "DAEMON_STARTUP_TIMEOUT: $DAEMON_STARTUP_TIMEOUT"
    echo "DAEMON_CONFIG_FILE: $DAEMON_CONFIG_FILE"
    echo "SECURITY_ENABLED: $SECURITY_ENABLED"
    echo "LOG_LEVEL: $LOG_LEVEL"
    echo "PYTHONPATH: $PYTHONPATH"
    log_info "================================"
}

# 主函数
main() {
    log_info "启动daemon-proxy Backend服务..."
    
    # 显示环境信息
    show_environment
    
    # 检查依赖
    check_daemon_binary
    check_docker_connection
    check_config_file
    
    log_info "所有检查通过，启动Backend服务..."
    
    # 启动Gunicorn
    exec uv run gunicorn api:app \
        --workers ${WORKERS:-7} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --timeout 1800 \
        --graceful-timeout 600 \
        --keep-alive 1800 \
        --max-requests 0 \
        --max-requests-jitter 0 \
        --forwarded-allow-ips '*' \
        --worker-connections ${WORKER_CONNECTIONS:-2000} \
        --worker-tmp-dir /dev/shm \
        --preload \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        --capture-output \
        --enable-stdio-inheritance \
        --threads ${THREADS:-2}
}

# 执行主函数
main "$@"
