#!/bin/bash

# Docker环境检查脚本
# 用于诊断Docker沙盒环境问题

set -e

echo "🔍 Docker环境检查脚本"
echo "========================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_docker_service() {
    echo -e "\n${BLUE}1. 检查Docker服务状态...${NC}"
    if systemctl is-active --quiet docker; then
        echo -e "   ${GREEN}✅ Docker服务正在运行${NC}"
        return 0
    else
        echo -e "   ${RED}❌ Docker服务未运行${NC}"
        echo "   运行: sudo systemctl start docker"
        return 1
    fi
}

check_docker_socket() {
    echo -e "\n${BLUE}2. 检查Docker套接字...${NC}"
    if [ -S /var/run/docker.sock ]; then
        echo -e "   ${GREEN}✅ Docker套接字存在${NC}"
        echo "   权限: $(stat -c %a /var/run/docker.sock)"
        echo "   所有者: $(stat -c %U:%G /var/run/docker.sock)"
        return 0
    else
        echo -e "   ${RED}❌ Docker套接字不存在${NC}"
        return 1
    fi
}

check_user_permissions() {
    echo -e "\n${BLUE}3. 检查用户权限...${NC}"
    if docker ps > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ 当前用户可以访问Docker${NC}"
        return 0
    else
        echo -e "   ${RED}❌ 当前用户无法访问Docker${NC}"
        echo "   解决方案:"
        echo "   1. 将用户添加到docker组: sudo usermod -aG docker $USER"
        echo "   2. 重新加载组权限: newgrp docker"
        echo "   3. 或者使用sudo (不推荐): sudo docker ps"
        return 1
    fi
}

check_docker_version() {
    echo -e "\n${BLUE}4. 检查Docker版本...${NC}"
    if command -v docker > /dev/null 2>&1; then
        echo "   Docker版本: $(docker --version)"
        echo "   Docker Compose版本: $(docker-compose --version)"
        return 0
    else
        echo -e "   ${RED}❌ Docker未安装${NC}"
        return 1
    fi
}

check_system_resources() {
    echo -e "\n${BLUE}5. 检查系统资源...${NC}"
    
    # 内存使用
    memory_usage=$(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')
    echo "   内存使用: $memory_usage"
    
    # 磁盘使用
    disk_usage=$(df -h / | awk 'NR==2{printf "%.1f%%", $5}')
    echo "   磁盘使用: $disk_usage"
    
    # 检查是否资源不足
    memory_percent=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $memory_percent -gt 90 ]; then
        echo -e "   ${YELLOW}⚠️  内存使用率较高: $memory_usage${NC}"
    fi
    
    disk_percent=$(df / | awk 'NR==2{printf "%.0f", $5}' | sed 's/%//')
    if [ $disk_percent -gt 90 ]; then
        echo -e "   ${YELLOW}⚠️  磁盘使用率较高: $disk_usage${NC}"
    fi
    
    return 0
}

check_docker_resources() {
    echo -e "\n${BLUE}6. 检查Docker资源...${NC}"
    if docker info > /dev/null 2>&1; then
        echo "   Docker信息:"
        docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}"
        return 0
    else
        echo -e "   ${RED}❌ 无法获取Docker信息${NC}"
        return 1
    fi
}

check_docker_compose() {
    echo -e "\n${BLUE}7. 检查Docker Compose配置...${NC}"
    
    # 检查配置文件
    if [ -f "docker-compose.docker-sandbox.yml" ]; then
        echo -e "   ${GREEN}✅ Docker Compose配置文件存在${NC}"
        
        # 检查环境变量文件
        if [ -f ".env" ]; then
            echo -e "   ${GREEN}✅ 环境变量文件存在${NC}"
            
            # 检查关键配置
            if grep -q "USE_LOCAL_DOCKER_SANDBOX=true" .env; then
                echo -e "   ${GREEN}✅ Docker沙盒已启用${NC}"
            else
                echo -e "   ${YELLOW}⚠️  Docker沙盒未启用${NC}"
                echo "   在.env文件中设置: USE_LOCAL_DOCKER_SANDBOX=true"
            fi
        else
            echo -e "   ${YELLOW}⚠️  环境变量文件不存在${NC}"
            echo "   创建.env文件或复制docker-sandbox.env.example"
        fi
    else
        echo -e "   ${RED}❌ Docker Compose配置文件不存在${NC}"
        return 1
    fi
    
    return 0
}

check_network_connectivity() {
    echo -e "\n${BLUE}8. 检查网络连接...${NC}"
    
    # 检查DNS解析
    if nslookup google.com > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ DNS解析正常${NC}"
    else
        echo -e "   ${YELLOW}⚠️  DNS解析可能有问题${NC}"
    fi
    
    # 检查外部连接
    if curl -s --connect-timeout 5 https://httpbin.org/ip > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ 外部网络连接正常${NC}"
    else
        echo -e "   ${YELLOW}⚠️  外部网络连接可能有问题${NC}"
    fi
    
    return 0
}

# 主检查流程
main() {
    local exit_code=0
    
    # 运行所有检查
    check_docker_service || exit_code=1
    check_docker_socket || exit_code=1
    check_user_permissions || exit_code=1
    check_docker_version || exit_code=1
    check_system_resources
    check_docker_resources || exit_code=1
    check_docker_compose || exit_code=1
    check_network_connectivity
    
    echo -e "\n${BLUE}========================"
    echo "检查完成"
    echo "========================"
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ 所有关键检查都通过了！${NC}"
        echo "Docker环境应该可以正常工作。"
    else
        echo -e "${RED}❌ 发现了一些问题${NC}"
        echo "请根据上面的建议修复问题，然后重新运行此脚本。"
        echo ""
        echo "常见解决方案:"
        echo "1. 启动Docker服务: sudo systemctl start docker"
        echo "2. 添加用户到docker组: sudo usermod -aG docker $USER"
        echo "3. 重新加载组权限: newgrp docker"
        echo "4. 检查配置文件和环境变量"
    fi
    
    return $exit_code
}

# 运行主函数
main "$@"
