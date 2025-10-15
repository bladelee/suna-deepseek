#!/bin/bash

# WSL2 + Docker Desktop 沙盒开发环境启动脚本
# 此脚本专门为WSL2环境优化

set -e

echo "🚀 启动WSL2 + Docker Desktop沙盒开发环境..."
echo "================================================"

# 检查是否在WSL2环境中
check_wsl2_environment() {
    if [ ! -f "/proc/version" ] || ! grep -q "Microsoft\|WSL" /proc/version; then
        echo "❌ 此脚本专为WSL2环境设计"
        echo "   请使用 start-docker-sandbox.sh 脚本"
        exit 1
    fi
    
    echo "✅ 检测到WSL2环境"
}

# 检查Docker Desktop状态
check_docker_desktop() {
    echo "🔍 检查Docker Desktop状态..."
    
    # 检查Docker Desktop是否运行
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker Desktop未运行或无法访问"
        echo ""
        echo "解决方案："
        echo "1. 在Windows上启动Docker Desktop"
        echo "2. 等待Docker Desktop完全启动"
        echo "3. 确保在Docker Desktop设置中启用了WSL2集成"
        echo ""
        echo "Docker Desktop设置："
        echo "- Settings → Resources → WSL Integration → 启用"
        echo "- Settings → General → 启用 'Use the WSL 2 based engine'"
        echo "- Settings → General → 启用 'Expose daemon on tcp://localhost:2375 without TLS'"
        exit 1
    fi
    
    echo "✅ Docker Desktop可访问"
}

# 检查Docker Desktop WSL2集成
check_wsl2_integration() {
    echo "🔍 检查WSL2集成..."
    
    # 检查是否可以通过TCP连接
    if ! docker --host tcp://localhost:2375 ps > /dev/null 2>&1; then
        echo "⚠️  无法通过TCP连接到Docker Desktop"
        echo "   请确保在Docker Desktop设置中启用了TCP暴露"
        echo "   Settings → General → 'Expose daemon on tcp://localhost:2375 without TLS'"
        echo ""
        echo "或者使用Unix套接字（如果可用）："
        if [ -S /var/run/docker.sock ]; then
            echo "✅ Unix套接字可用，将使用套接字连接"
        else
            echo "❌ Unix套接字不可用"
            exit 1
        fi
    else
        echo "✅ TCP连接正常"
    fi
}

# 配置环境
setup_environment() {
    echo "🔧 配置环境..."
    
    # 检查环境文件
    if [ ! -f ".env" ]; then
        echo "⚠️  .env文件不存在，从WSL2示例创建..."
        if [ -f "docker-sandbox-wsl2.env.example" ]; then
            cp docker-sandbox-wsl2.env.example .env
            echo "✅ 创建了.env文件"
            echo "📝 请编辑.env文件配置你的API密钥等信息"
            echo "   按Enter继续..."
            read
        else
            echo "❌ docker-sandbox-wsl2.env.example不存在"
            exit 1
        fi
    fi
    
    # 设置WSL2环境变量
    export DOCKER_HOST=tcp://localhost:2375
    export DOCKER_TLS_VERIFY=false
    export USE_LOCAL_DOCKER_SANDBOX=true
    
    echo "✅ 环境配置完成"
}

# 启动服务
start_services() {
    echo "🔧 启动服务..."
    
    # 启动Redis
    docker-compose -f docker-compose.docker-sandbox.yml up -d redis
    
    # 等待Redis就绪
    echo "⏳ 等待Redis就绪..."
    until docker-compose -f docker-compose.docker-sandbox.yml exec -T redis redis-cli ping > /dev/null 2>&1; do
        echo "   等待Redis..."
        sleep 2
    done
    echo "✅ Redis就绪"
    
    # 启动后端服务
    echo "🔧 启动后端服务..."
    docker-compose -f docker-compose.docker-sandbox.yml up -d api worker
    
    # 等待服务就绪
    echo "⏳ 等待服务就绪..."
    sleep 15
}

# 验证服务
verify_services() {
    echo "🔍 验证服务..."
    
    # 检查API健康状态
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ API服务健康"
    else
        echo "⚠️  API服务健康检查失败，可能仍在启动中"
    fi
    
    # 检查工作进程健康状态
    if docker-compose -f docker-compose.docker-sandbox.yml exec -T worker uv run worker_health.py > /dev/null 2>&1; then
        echo "✅ 工作进程健康"
    else
        echo "⚠️  工作进程健康检查失败，可能仍在启动中"
    fi
}

# 显示状态信息
show_status() {
    echo ""
    echo "🎉 WSL2 + Docker Desktop沙盒开发环境启动完成！"
    echo ""
    echo "📋 服务信息："
    echo "   API: http://localhost:8000"
    echo "   Redis: localhost:6379"
    echo ""
    echo "🔧 管理命令："
    echo "   查看日志: docker-compose -f docker-compose.docker-sandbox.yml logs -f"
    echo "   停止服务: docker-compose -f docker-compose.docker-sandbox.yml down"
    echo "   重启服务: docker-compose -f docker-compose.docker-sandbox.yml restart"
    echo ""
    echo "🐳 Docker沙盒特性："
    echo "   - 通过TCP连接到Windows Docker Desktop"
    echo "   - 在Windows上创建沙盒容器"
    echo "   - 完全隔离和资源管理"
    echo ""
    echo "📚 下一步："
    echo "   1. 配置.env文件中的API密钥"
    echo "   2. 测试API端点"
    echo "   3. 创建你的第一个沙盒"
    echo ""
    echo "Happy coding in WSL2! 🚀"
}

# 主函数
main() {
    check_wsl2_environment
    check_docker_desktop
    check_wsl2_integration
    setup_environment
    start_services
    verify_services
    show_status
}

# 运行主函数
main "$@"

