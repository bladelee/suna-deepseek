#!/bin/bash

# Backend Docker 构建脚本
# 用途: 简化 Docker 镜像的构建、运行、停止和清理操作
# 支持基础版本和 daemon-proxy 版本
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
    echo "Backend Docker 构建脚本"
    echo ""
    echo "Usage: $0 {build|run|stop|clean} [options]"
    echo ""
    echo "Commands:"
    echo "  build [version]     - 构建Docker镜像"
    echo "  run [version]       - 运行Docker容器"
    echo "  stop [version]      - 停止Docker容器"
    echo "  clean [version]     - 清理Docker镜像和容器"
    echo "  help                - 显示帮助信息"
    echo ""
    echo "Versions:"
    echo "  base                - 基础版本（默认）"
    echo "  daemon              - daemon-proxy版本"
    echo ""
    echo "Examples:"
    echo "  $0 build base       # 构建基础版本"
    echo "  $0 build daemon     # 构建daemon-proxy版本"
    echo "  $0 run base         # 运行基础版本"
    echo "  $0 run daemon       # 运行daemon-proxy版本"
    echo "  $0 stop daemon      # 停止daemon-proxy版本"
    echo "  $0 clean daemon     # 清理daemon-proxy版本"
    echo ""
    echo "Note: Docker Compose files are located in the 'dockers/' directory"
}

# 构建镜像
build_image() {
    local version=$1
    
    case $version in
        base)
            log_info "构建基础版本镜像..."
            docker build -t backend-api:latest .
            log_info "基础版本镜像构建完成"
            ;;
        daemon)
            log_info "构建daemon-proxy版本镜像..."
            docker build -f Dockerfile.daemon -t backend-api-daemon:latest .
            log_info "daemon-proxy版本镜像构建完成"
            ;;
        *)
            log_error "未知版本: $version"
            show_help
            exit 1
            ;;
    esac
}

# 运行容器
run_container() {
    local version=$1
    
    case $version in
        base)
            log_info "运行基础版本容器..."
            docker-compose -f dockers/docker-compose.yml up -d
            log_info "基础版本容器启动完成"
            ;;
        daemon)
            log_info "运行daemon-proxy版本容器..."
            docker-compose -f dockers/docker-compose.daemon.yml up -d
            log_info "daemon-proxy版本容器启动完成"
            ;;
        *)
            log_error "未知版本: $version"
            show_help
            exit 1
            ;;
    esac
}

# 停止容器
stop_container() {
    local version=$1
    
    case $version in
        base)
            log_info "停止基础版本容器..."
            docker-compose -f dockers/docker-compose.yml down
            log_info "基础版本容器已停止"
            ;;
        daemon)
            log_info "停止daemon-proxy版本容器..."
            docker-compose -f dockers/docker-compose.daemon.yml down
            log_info "daemon-proxy版本容器已停止"
            ;;
        *)
            log_error "未知版本: $version"
            show_help
            exit 1
            ;;
    esac
}

# 清理镜像和容器
clean_all() {
    local version=$1
    
    case $version in
        base)
            log_info "清理基础版本..."
            docker-compose -f dockers/docker-compose.yml down --rmi all --volumes --remove-orphans
            docker rmi backend-api:latest 2>/dev/null || true
            log_info "基础版本清理完成"
            ;;
        daemon)
            log_info "清理daemon-proxy版本..."
            docker-compose -f dockers/docker-compose.daemon.yml down --rmi all --volumes --remove-orphans
            docker rmi backend-api-daemon:latest 2>/dev/null || true
            log_info "daemon-proxy版本清理完成"
            ;;
        *)
            log_error "未知版本: $version"
            show_help
            exit 1
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

# 主函数
main() {
    local command=${1:-help}
    local version=${2:-base}
    
    # 检查Docker
    check_docker
    
    case $command in
        build)
            build_image $version
            ;;
        run)
            run_container $version
            ;;
        stop)
            stop_container $version
            ;;
        clean)
            clean_all $version
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
