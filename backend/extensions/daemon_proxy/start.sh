#!/bin/bash

# Daemon Proxy Service 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python版本: $PYTHON_VERSION"
    else
        print_error "Python3未安装"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt文件不存在"
        exit 1
    fi
    
    # 检查是否已安装依赖
    if ! python3 -c "import aiohttp, docker" 2>/dev/null; then
        print_warning "依赖未安装，正在安装..."
        pip3 install -r requirements.txt
        print_success "依赖安装完成"
    else
        print_success "依赖已安装"
    fi
}

# 检查配置文件
check_config() {
    print_info "检查配置文件..."
    if [ ! -f "config.yaml" ]; then
        if [ -f "config.example.yaml" ]; then
            print_warning "配置文件不存在，复制示例配置..."
            cp config.example.yaml config.yaml
            print_success "配置文件已创建: config.yaml"
            print_warning "请根据需要修改配置文件"
        else
            print_error "配置文件不存在且无示例配置"
            exit 1
        fi
    else
        print_success "配置文件存在"
    fi
}

# 检查daemon二进制文件
check_daemon() {
    print_info "检查daemon二进制文件..."
    
    # 从配置文件读取daemon路径
    if [ -f "config.yaml" ]; then
        DAEMON_PATH=$(grep -A 10 "daemon:" config.yaml | grep "path:" | cut -d':' -f2 | tr -d ' ')
        if [ -n "$DAEMON_PATH" ]; then
            if [ -f "$DAEMON_PATH" ]; then
                print_success "Daemon二进制文件存在: $DAEMON_PATH"
            else
                print_warning "Daemon二进制文件不存在: $DAEMON_PATH"
                print_warning "请确保daemon二进制文件在正确位置"
            fi
        fi
    fi
}

# 创建日志目录
create_log_dir() {
    print_info "创建日志目录..."
    mkdir -p logs
    print_success "日志目录已创建"
}

# 启动服务
start_service() {
    print_info "启动daemon-proxy服务..."
    print_info "按 Ctrl+C 停止服务"
    echo
    
    # 启动服务
    python3 main.py "$@"
}

# 显示帮助
show_help() {
    echo "Daemon Proxy Service 启动脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  --config FILE  指定配置文件"
    echo "  --host HOST    指定服务器主机"
    echo "  --port PORT    指定服务器端口"
    echo "  --daemon-mode MODE  指定daemon模式 (host/docker)"
    echo "  --security    启用安全认证"
    echo "  --test        运行测试后启动"
    echo
    echo "示例:"
    echo "  $0                                    # 使用默认配置启动"
    echo "  $0 --config my-config.yaml           # 使用自定义配置"
    echo "  $0 --host 0.0.0.0 --port 9000       # 指定主机和端口"
    echo "  $0 --daemon-mode docker              # 使用Docker模式"
    echo "  $0 --security                        # 启用安全认证"
    echo "  $0 --test                            # 运行测试后启动"
}

# 运行测试
run_tests() {
    print_info "运行测试..."
    if python3 -m pytest tests/ -v; then
        print_success "测试通过"
    else
        print_error "测试失败"
        exit 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "    Daemon Proxy Service 启动脚本"
    echo "=========================================="
    echo
    
    # 解析参数
    TEST_MODE=false
    EXTRA_ARGS=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --test)
                TEST_MODE=true
                shift
                ;;
            *)
                EXTRA_ARGS+=("$1")
                shift
                ;;
        esac
    done
    
    # 运行测试
    if [ "$TEST_MODE" = true ]; then
        run_tests
        echo
    fi
    
    # 检查环境
    check_python
    check_dependencies
    check_config
    check_daemon
    create_log_dir
    
    echo
    print_success "环境检查完成，准备启动服务..."
    echo
    
    # 启动服务
    start_service "${EXTRA_ARGS[@]}"
}

# 捕获中断信号
trap 'echo; print_info "服务已停止"; exit 0' INT

# 运行主函数
main "$@"

