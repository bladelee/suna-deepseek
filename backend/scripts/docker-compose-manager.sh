#!/bin/bash

# Docker Compose 服务管理脚本
# 用途: 统一管理不同环境的Docker Compose服务
# 支持: 基础版本、生产daemon版本、开发daemon版本
# 作者: Suna Team
# 更新: 2024-10-15

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

# 显示帮助
show_help() {
    echo "Docker Compose 服务管理脚本"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|clean} [environment]"
    echo ""
    echo "Commands:"
    echo "  start [env]     - 启动服务"
    echo "  stop [env]      - 停止服务"
    echo "  restart [env]   - 重启服务"
    echo "  status [env]    - 查看服务状态"
    echo "  logs [env]      - 查看服务日志"
    echo "  clean [env]     - 清理服务（删除容器和镜像）"
    echo ""
    echo "Environments:"
    echo "  base            - 基础版本（默认）"
    echo "  daemon          - 生产daemon-proxy版本"
    echo "  dev-daemon      - 开发daemon-proxy版本"
    echo ""
    echo "Examples:"
    echo "  $0 start base           # 启动基础版本"
    echo "  $0 start daemon         # 启动生产daemon版本"
    echo "  $0 start dev-daemon     # 启动开发daemon版本"
    echo "  $0 logs daemon          # 查看生产daemon版本日志"
    echo "  $0 clean dev-daemon     # 清理开发daemon版本"
    echo ""
    echo "Note: 脚本会自动切换到suna根目录执行Docker Compose命令"
}

# 获取Docker Compose文件路径
get_compose_file() {
    local env=$1
    
    case $env in
        base)
            echo "docker-compose.yaml"
            ;;
        daemon)
            echo "docker-compose.daemon.yml"
            ;;
        dev-daemon)
            echo "docker-compose.dev.daemon.yml"
            ;;
        *)
            log_error "未知环境: $env"
            return 1
            ;;
    esac
}

# 检查Docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
}

# 切换到suna根目录
switch_to_suna_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local suna_root="$(dirname "$(dirname "$script_dir")")"
    
    if [ ! -f "$suna_root/docker-compose.yaml" ]; then
        log_error "未找到suna根目录，请确保在正确的项目结构中运行此脚本"
        exit 1
    fi
    
    cd "$suna_root"
    log_debug "切换到目录: $(pwd)"
}

# 启动服务
start_services() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    
    log_info "启动 $env 环境服务..."
    log_info "使用配置文件: $compose_file"
    
    docker-compose -f "$compose_file" up -d
    
    log_info "$env 环境服务启动完成"
    
    # 显示服务状态
    sleep 3
    docker-compose -f "$compose_file" ps
}

# 停止服务
stop_services() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    
    log_info "停止 $env 环境服务..."
    
    docker-compose -f "$compose_file" down
    
    log_info "$env 环境服务已停止"
}

# 重启服务
restart_services() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    
    log_info "重启 $env 环境服务..."
    
    docker-compose -f "$compose_file" restart
    
    log_info "$env 环境服务重启完成"
}

# 查看服务状态
show_status() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    
    log_info "$env 环境服务状态:"
    docker-compose -f "$compose_file" ps
}

# 查看服务日志
show_logs() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    
    log_info "显示 $env 环境服务日志:"
    docker-compose -f "$compose_file" logs -f
}

# 清理服务
clean_services() {
    local env=$1
    local compose_file=$(get_compose_file $env)
    
    log_warn "清理 $env 环境服务（将删除容器和镜像）..."
    read -p "确认继续？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f "$compose_file" down --rmi all --volumes --remove-orphans
        log_info "$env 环境服务清理完成"
    else
        log_info "取消清理操作"
    fi
}

# 主函数
main() {
    local command=${1:-help}
    local environment=${2:-base}
    
    # 检查Docker
    check_docker
    
    # 切换到suna根目录
    switch_to_suna_root
    
    case $command in
        start)
            start_services $environment
            ;;
        stop)
            stop_services $environment
            ;;
        restart)
            restart_services $environment
            ;;
        status)
            show_status $environment
            ;;
        logs)
            show_logs $environment
            ;;
        clean)
            clean_services $environment
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
