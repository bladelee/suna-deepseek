#!/bin/bash

# Daemon二进制文件管理脚本
# 用于设置和管理host上的daemon二进制文件

set -e

# 配置
DAEMON_DIR="/opt/suna/daemon-proxy"
DAEMON_FILE="$DAEMON_DIR/daytona-daemon-static"
SOURCE_FILE="./backend/sandbox/daemon-proxy/daytona-daemon-static"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# 安装daemon二进制文件
install_daemon() {
    local source_file="$1"
    
    if [ -z "$source_file" ]; then
        source_file="$SOURCE_FILE"
    fi
    
    if [ ! -f "$source_file" ]; then
        log_error "Source file not found: $source_file"
        exit 1
    fi
    
    log_info "Installing daemon binary from $source_file to $DAEMON_FILE"
    
    # 创建目录
    mkdir -p "$DAEMON_DIR"
    
    # 复制文件
    cp "$source_file" "$DAEMON_FILE"
    
    # 设置权限
    chmod +x "$DAEMON_FILE"
    chown root:root "$DAEMON_FILE"
    
    log_info "Daemon binary installed successfully"
    show_status
}

# 更新daemon二进制文件
update_daemon() {
    local source_file="$1"
    
    if [ -z "$source_file" ]; then
        source_file="$SOURCE_FILE"
    fi
    
    if [ ! -f "$source_file" ]; then
        log_error "Source file not found: $source_file"
        exit 1
    fi
    
    if [ ! -f "$DAEMON_FILE" ]; then
        log_warn "Daemon binary not found, installing..."
        install_daemon "$source_file"
        return
    fi
    
    log_info "Updating daemon binary from $source_file to $DAEMON_FILE"
    
    # 备份现有文件
    cp "$DAEMON_FILE" "$DAEMON_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 复制新文件
    cp "$source_file" "$DAEMON_FILE"
    
    # 设置权限
    chmod +x "$DAEMON_FILE"
    chown root:root "$DAEMON_FILE"
    
    log_info "Daemon binary updated successfully"
    show_status
}

# 显示状态
show_status() {
    log_info "Daemon binary status:"
    
    if [ -f "$DAEMON_FILE" ]; then
        echo "  File: $DAEMON_FILE"
        echo "  Size: $(du -h "$DAEMON_FILE" | cut -f1)"
        echo "  Permissions: $(ls -la "$DAEMON_FILE" | cut -d' ' -f1)"
        echo "  Owner: $(ls -la "$DAEMON_FILE" | cut -d' ' -f3-4)"
        echo "  Type: $(file "$DAEMON_FILE")"
        
        # 检查是否可执行
        if [ -x "$DAEMON_FILE" ]; then
            log_info "  Status: Executable ✓"
        else
            log_warn "  Status: Not executable ✗"
        fi
    else
        log_error "Daemon binary not found at $DAEMON_FILE"
    fi
}

# 验证挂载
verify_mount() {
    log_info "Verifying mount configuration..."
    
    # 检查Docker是否运行
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # 检查文件是否存在
    if [ ! -f "$DAEMON_FILE" ]; then
        log_error "Daemon binary not found at $DAEMON_FILE"
        exit 1
    fi
    
    # 检查权限
    if [ ! -x "$DAEMON_FILE" ]; then
        log_error "Daemon binary is not executable"
        exit 1
    fi
    
    log_info "Mount configuration is valid"
}

# 清理备份文件
cleanup_backups() {
    log_info "Cleaning up backup files..."
    
    if [ -d "$DAEMON_DIR" ]; then
        find "$DAEMON_DIR" -name "daytona-daemon-static.backup.*" -mtime +7 -delete
        log_info "Backup files older than 7 days have been removed"
    fi
}

# 显示帮助
show_help() {
    echo "Daemon Binary Management Script"
    echo ""
    echo "Usage: $0 {install|update|status|verify|cleanup} [source_file]"
    echo ""
    echo "Commands:"
    echo "  install [source_file]  - Install daemon binary from source file"
    echo "  update [source_file]   - Update daemon binary from source file"
    echo "  status                 - Show daemon binary status"
    echo "  verify                 - Verify mount configuration"
    echo "  cleanup                - Clean up old backup files"
    echo "  help                   - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 install                                    # Install from default source"
    echo "  $0 install /path/to/daytona-daemon-static    # Install from specific source"
    echo "  $0 update                                     # Update from default source"
    echo "  $0 status                                     # Show current status"
    echo "  $0 verify                                     # Verify configuration"
    echo ""
    echo "Default paths:"
    echo "  Source: $SOURCE_FILE"
    echo "  Target: $DAEMON_FILE"
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            check_root
            install_daemon "$2"
            ;;
        update)
            check_root
            update_daemon "$2"
            ;;
        status)
            show_status
            ;;
        verify)
            verify_mount
            ;;
        cleanup)
            check_root
            cleanup_backups
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
