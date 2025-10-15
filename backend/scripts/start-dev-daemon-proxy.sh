#!/bin/sh

# 开发环境启动脚本
# 用途: 启动开发环境的Suna Backend服务，支持daemon-proxy功能
# 特性: 热重载、调试日志、单工作进程
# 作者: Suna Team
# 更新: 2024-10-15

set -e

echo "🚀 Starting Suna Backend in Development Mode with Daemon-Proxy..."

# 日志函数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1"
}

# 检查环境变量
log_info "Environment: ${ENVIRONMENT:-development}"
log_info "Log Level: ${LOG_LEVEL:-DEBUG}"
log_info "Workers: ${WORKERS:-1}"

# 检查 daemon 二进制文件
DAEMON_BINARY_PATH=${DAEMON_BINARY_PATH:-/app/daemon-proxy/daytona-daemon-static}
if [ -f "$DAEMON_BINARY_PATH" ]; then
    log_info "Daemon binary found: $DAEMON_BINARY_PATH"
    ls -la "$DAEMON_BINARY_PATH"
else
    log_warn "Daemon binary not found at $DAEMON_BINARY_PATH"
fi

# 检查 Docker 连接
if docker info >/dev/null 2>&1; then
    log_info "Docker connection: OK"
else
    log_error "Docker connection: FAILED"
    exit 1
fi

# 检查配置文件
CONFIG_FILE=${DAEMON_CONFIG_FILE:-/app/config.daemon.yaml}
if [ -f "$CONFIG_FILE" ]; then
    log_info "Daemon config file found: $CONFIG_FILE"
else
    log_warn "Daemon config file not found at $CONFIG_FILE"
fi

# 开发环境信息
log_info "Development mode features:"
log_info "  - Hot reload: ${RELOAD:-true}"
log_info "  - Debug logging: ${LOG_LEVEL:-DEBUG}"
log_info "  - Single worker: ${WORKERS:-1}"
log_info "  - Source code mounted: $(if [ -d /app/api.py ]; then echo "YES"; else echo "NO"; fi)"

# 启动 Gunicorn 服务器（开发模式）
log_info "Starting Gunicorn server in development mode..."

exec uv run gunicorn api:app \
  --workers "${WORKERS:-1}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 1800 \
  --graceful-timeout 600 \
  --keep-alive 1800 \
  --max-requests 0 \
  --max-requests-jitter 0 \
  --forwarded-allow-ips '*' \
  --worker-connections "${WORKER_CONNECTIONS:-1000}" \
  --worker-tmp-dir /dev/shm \
  --preload \
  --log-level "${LOG_LEVEL:-debug}" \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance \
  --threads "${THREADS:-1}" \
  --reload
