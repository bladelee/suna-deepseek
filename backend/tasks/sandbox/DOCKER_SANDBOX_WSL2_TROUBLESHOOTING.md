# WSL2 + Docker Desktop 沙盒故障排除指南

本文档专门解决在WSL2环境中使用Windows Docker Desktop时的常见问题。

## 🚨 关键配置要求

### Docker Desktop设置
在Windows上的Docker Desktop中必须启用以下设置：

1. **Settings → General**
   - ✅ 启用 "Use the WSL 2 based engine"
   - ✅ 启用 "Expose daemon on tcp://localhost:2375 without TLS"

2. **Settings → Resources → WSL Integration**
   - ✅ 启用 "Enable integration with my default WSL distro"
   - ✅ 启用你的WSL2发行版

## 🔍 常见问题和解决方案

### 1. Docker连接错误

#### 错误信息
```
Docker client initialization failed (DockerException): Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

#### 原因
- Docker Desktop未启动
- WSL2集成未启用
- TCP端口2375未暴露
- 防火墙阻止连接

#### 解决方案

**步骤1：检查Docker Desktop状态**
```bash
# 在WSL2中检查Docker状态
docker info

# 如果失败，检查TCP连接
docker --host tcp://localhost:2375 ps
```

**步骤2：启用Docker Desktop TCP暴露**
1. 打开Windows上的Docker Desktop
2. 点击设置图标（齿轮）
3. 进入 "General" 设置
4. 勾选 "Expose daemon on tcp://localhost:2375 without TLS"
5. 点击 "Apply & Restart"

**步骤3：启用WSL2集成**
1. 在Docker Desktop设置中
2. 进入 "Resources" → "WSL Integration"
3. 启用你的WSL2发行版
4. 点击 "Apply & Restart"

**步骤4：检查防火墙设置**
```bash
# 在Windows PowerShell中检查端口
netstat -an | findstr 2375

# 如果端口未开放，检查Windows防火墙
# 控制面板 → 系统和安全 → Windows Defender防火墙 → 允许应用通过防火墙
```

### 2. 权限问题

#### 问题描述
无法在WSL2中访问Docker

#### 解决方案

**方法1：使用TCP连接（推荐）**
```bash
# 设置环境变量
export DOCKER_HOST=tcp://localhost:2375
export DOCKER_TLS_VERIFY=false

# 测试连接
docker ps
```

**方法2：配置Docker组（如果Unix套接字可用）**
```bash
# 创建docker组
sudo groupadd docker

# 添加用户到docker组
sudo usermod -aG docker $USER

# 重新加载组权限
newgrp docker
```

### 3. 网络连接问题

#### 问题描述
WSL2无法连接到Windows Docker Desktop

#### 解决方案

**检查网络配置**
```bash
# 检查WSL2网络
ip addr show

# 检查到Windows的连接
ping $(grep nameserver /etc/resolv.conf | awk '{print $2}')

# 测试Docker Desktop连接
curl -v telnet://localhost:2375
```

**配置WSL2网络**
```bash
# 在Windows PowerShell中创建.wslconfig文件
# C:\Users\<username>\.wslconfig

[wsl2]
networkingMode=mirrored
memory=4GB
processors=4
localhostForwarding=true
```

### 4. 性能问题

#### 问题描述
WSL2中Docker操作缓慢

#### 解决方案

**优化WSL2配置**
```bash
# 在Windows PowerShell中创建.wslconfig
# C:\Users\<username>\.wslconfig

[wsl2]
memory=8GB
processors=8
swap=2GB
localhostForwarding=true
```

**使用WSL2专用启动脚本**
```bash
# 使用WSL2优化脚本
./scripts/start-docker-sandbox-wsl2.sh
```

## 🛠️ 诊断工具

### 1. WSL2环境检查
```bash
# 检查WSL2版本
wsl --version

# 检查WSL2状态
wsl --status

# 检查发行版信息
cat /proc/version
```

### 2. Docker连接测试
```bash
# 测试标准连接
docker info

# 测试TCP连接
docker --host tcp://localhost:2375 info

# 测试Unix套接字（如果可用）
docker --host unix:///var/run/docker.sock info
```

### 3. 网络诊断
```bash
# 检查端口开放
netstat -tuln | grep 2375

# 测试端口连接
telnet localhost 2375

# 检查防火墙状态
sudo ufw status
```

## 📋 配置检查清单

### Docker Desktop设置
- [ ] 使用WSL2引擎
- [ ] 启用TCP暴露（端口2375）
- [ ] 启用WSL2集成
- [ ] 重启Docker Desktop

### WSL2环境
- [ ] WSL2版本 >= 0.50.0
- [ ] 发行版使用WSL2后端
- [ ] 网络连接正常
- [ ] 用户权限正确

### 环境变量
- [ ] DOCKER_HOST=tcp://localhost:2375
- [ ] DOCKER_TLS_VERIFY=false
- [ ] USE_LOCAL_DOCKER_SANDBOX=true

## 🚀 快速修复流程

### 1. 重启Docker Desktop
```bash
# 在Windows上完全关闭Docker Desktop
# 等待几秒钟后重新启动
```

### 2. 重启WSL2
```bash
# 在Windows PowerShell中
wsl --shutdown
# 重新打开WSL2终端
```

### 3. 重新配置环境
```bash
# 使用WSL2专用脚本
./scripts/start-docker-sandbox-wsl2.sh
```

### 4. 验证修复
```bash
# 检查Docker连接
docker ps

# 测试沙盒功能
python scripts/test-docker-sandbox.py
```

## 🔄 回退方案

如果WSL2 + Docker Desktop持续出现问题：

### 方案1：使用Unix套接字
```bash
# 在.env文件中
DOCKER_HOST=unix:///var/run/docker.sock
```

### 方案2：禁用Docker沙盒
```bash
# 在.env文件中
USE_LOCAL_DOCKER_SANDBOX=false
```

### 方案3：使用Daytona沙盒
```bash
# 配置Daytona API密钥
DAYTONA_API_KEY=your_key
DAYTONA_SERVER_URL=your_url
DAYTONA_TARGET=your_target
```

## 📞 获取帮助

如果问题仍然存在：

1. 检查本文档的故障排除部分
2. 运行WSL2环境检查脚本
3. 查看Docker Desktop日志
4. 在GitHub Issues中搜索类似问题
5. 创建新的Issue并提供详细信息

### 提供信息时请包含：
- Windows版本
- WSL2版本
- Docker Desktop版本
- WSL2发行版信息
- 错误日志
- 环境检查输出
- 复现步骤

