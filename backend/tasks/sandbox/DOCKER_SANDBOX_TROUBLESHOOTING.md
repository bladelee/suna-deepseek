# Docker沙盒故障排除指南

本文档帮助解决使用本地Docker沙盒时遇到的常见问题。

## 常见错误和解决方案

### 1. Docker连接错误

#### 错误信息
```
Failed to initialize Docker client: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

#### 原因
- Docker守护进程未运行
- Docker套接字不可访问
- 权限不足

#### 解决方案

**检查Docker状态**
```bash
# 检查Docker服务状态
sudo systemctl status docker

# 启动Docker服务
sudo systemctl start docker

# 启用Docker服务（开机自启）
sudo systemctl enable docker
```

**检查Docker套接字**
```bash
# 检查套接字是否存在
ls -la /var/run/docker.sock

# 检查套接字权限
stat /var/run/docker.sock
```

**解决权限问题**
```bash
# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 重新加载组权限（无需重新登录）
newgrp docker

# 或者临时使用sudo（不推荐生产环境）
sudo docker ps
```

**验证Docker访问**
```bash
# 测试Docker命令
docker ps

# 测试Docker信息
docker info
```

### 2. 容器内Docker访问问题

#### 问题描述
在Docker容器内无法访问Docker守护进程

#### 解决方案

**确保Docker套接字挂载**
```yaml
# docker-compose.docker-sandbox.yml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

**检查容器内权限**
```bash
# 进入容器
docker exec -it <container_name> /bin/bash

# 检查套接字
ls -la /var/run/docker.sock

# 测试Docker命令
docker ps
```

**使用特权模式（仅开发环境）**
```yaml
# docker-compose.docker-sandbox.yml
privileged: true
```

### 3. 沙盒创建失败

#### 错误信息
```
Error creating Docker sandbox: ...
```

#### 解决方案

**检查镜像可用性**
```bash
# 拉取所需镜像
docker pull kortix/suna:0.1.3.6

# 检查镜像列表
docker images | grep suna
```

**检查资源限制**
```bash
# 检查可用磁盘空间
df -h

# 检查可用内存
free -h

# 检查Docker资源使用
docker system df
```

**清理Docker资源**
```bash
# 清理未使用的容器
docker container prune

# 清理未使用的镜像
docker image prune

# 清理未使用的卷
docker volume prune

# 全面清理
docker system prune -a
```

### 4. 网络连接问题

#### 问题描述
沙盒容器无法访问网络或外部服务

#### 解决方案

**检查网络配置**
```bash
# 查看Docker网络
docker network ls

# 检查容器网络
docker inspect <container_name> | grep -A 20 "NetworkSettings"
```

**配置DNS**
```yaml
# docker-compose.docker-sandbox.yml
dns:
  - 8.8.8.8
  - 114.114.114.114
```

**使用主机网络（仅开发环境）**
```yaml
# docker-compose.docker-sandbox.yml
network_mode: host
```

### 5. 性能问题

#### 问题描述
沙盒运行缓慢或资源占用过高

#### 解决方案

**调整资源限制**
```python
# docker_sandbox.py
container_config = {
    'mem_limit': '2g',        # 减少内存限制
    'cpu_quota': 100000,      # 减少CPU限制
    'storage_opt': {'size': '2G'}  # 减少磁盘限制
}
```

**优化容器配置**
```yaml
# docker-compose.docker-sandbox.yml
environment:
  - PYTHONUNBUFFERED=1
  - PYTHONDONTWRITEBYTECODE=1
```

**使用轻量级镜像**
```dockerfile
# 使用Alpine基础镜像
FROM python:3.11-alpine
```

## 环境检查脚本

创建一个环境检查脚本：

```bash
#!/bin/bash
# check-docker-environment.sh

echo "🔍 检查Docker环境..."

# 检查Docker服务
echo "1. 检查Docker服务状态..."
if systemctl is-active --quiet docker; then
    echo "   ✅ Docker服务正在运行"
else
    echo "   ❌ Docker服务未运行"
    echo "   运行: sudo systemctl start docker"
fi

# 检查Docker套接字
echo "2. 检查Docker套接字..."
if [ -S /var/run/docker.sock ]; then
    echo "   ✅ Docker套接字存在"
    echo "   权限: $(stat -c %a /var/run/docker.sock)"
else
    echo "   ❌ Docker套接字不存在"
fi

# 检查用户权限
echo "3. 检查用户权限..."
if docker ps > /dev/null 2>&1; then
    echo "   ✅ 当前用户可以访问Docker"
else
    echo "   ❌ 当前用户无法访问Docker"
    echo "   运行: sudo usermod -aG docker $USER"
fi

# 检查Docker版本
echo "4. 检查Docker版本..."
docker --version

# 检查可用资源
echo "5. 检查系统资源..."
echo "   内存: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "   磁盘: $(df -h / | awk 'NR==2{printf "%.1f%%", $5}')"

# 检查Docker资源
echo "6. 检查Docker资源..."
docker system df

echo "✅ 环境检查完成"
```

## 日志分析

### 查看应用日志
```bash
# 查看API服务日志
docker-compose -f docker-compose.docker-sandbox.yml logs api

# 查看工作进程日志
docker-compose -f docker-compose.docker-sandbox.yml logs worker

# 实时查看日志
docker-compose -f docker-compose.docker-sandbox.yml logs -f
```

### 查看Docker日志
```bash
# 查看Docker守护进程日志
sudo journalctl -u docker.service -f

# 查看特定容器日志
docker logs <container_name>
```

### 日志级别调整
```bash
# 设置更详细的日志级别
export LOG_LEVEL=DEBUG

# 或者在.env文件中
LOG_LEVEL=DEBUG
```

## 回退到Daytona

如果Docker沙盒持续出现问题，可以临时回退到Daytona：

```bash
# 禁用Docker沙盒
export USE_LOCAL_DOCKER_SANDBOX=false

# 或者在.env文件中
USE_LOCAL_DOCKER_SANDBOX=false

# 重启服务
docker-compose -f docker-compose.docker-sandbox.yml restart
```

## 获取帮助

如果问题仍然存在：

1. 检查本文档的故障排除部分
2. 查看应用日志获取详细错误信息
3. 运行环境检查脚本
4. 在GitHub Issues中搜索类似问题
5. 创建新的Issue并提供详细信息

### 提供信息时请包含：

- 操作系统和版本
- Docker版本
- 错误日志
- 环境检查脚本输出
- 复现步骤
