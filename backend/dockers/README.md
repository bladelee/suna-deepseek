# Docker 配置文件目录

本目录包含所有Docker相关的配置文件，用于构建和部署Backend服务。

## 📖 完整文档

**详细的使用指南请参考：[DOCKER_GUIDE.md](./DOCKER_GUIDE.md)**

## 文件结构

### Docker Compose 文件

#### 基础版本
- `docker-compose.yml` - 基础版本生产环境配置
- `docker-compose.dev.yml` - 基础版本开发环境配置

#### daemon-proxy版本
- `docker-compose.daemon.yml` - daemon-proxy版本生产环境配置
- `docker-compose.dev.daemon.yml` - daemon-proxy版本开发环境配置

#### 挂载方案版本
- `docker-compose.volume-mount.yml` - 挂载方案生产环境配置
- `docker-compose.dev.volume-mount.yml` - 挂载方案开发环境配置

### 配置文件
- `config.daemon.yaml` - daemon-proxy配置文件

### 启动脚本
- `start-daemon-proxy.sh` - daemon-proxy启动脚本

### 文档
- `DOCKER_GUIDE.md` - 完整的Docker部署指南

## 使用方法

### 基础版本
```bash
# 生产环境
docker-compose -f dockers/docker-compose.yml up -d

# 开发环境
docker-compose -f dockers/docker-compose.dev.yml up -d
```

### daemon-proxy版本
```bash
# 生产环境
docker-compose -f dockers/docker-compose.daemon.yml up -d

# 开发环境
docker-compose -f dockers/docker-compose.dev.daemon.yml up -d
```

### 挂载方案版本
```bash
# 生产环境
docker-compose -f dockers/docker-compose.volume-mount.yml up -d

# 开发环境
docker-compose -f dockers/docker-compose.dev.volume-mount.yml up -d
```

## 构建上下文

所有Docker Compose文件都使用`context: ..`，这意味着：
- 构建上下文是backend目录的父目录
- Dockerfile位于backend目录下
- 所有源代码和依赖都在正确的路径下

## 注意事项

1. **构建上下文**：所有Docker Compose文件都使用`context: ..`，确保构建上下文正确
2. **文件路径**：Dockerfile.daemon中的文件路径已更新为`dockers/`前缀
3. **权限**：启动脚本具有执行权限
4. **环境变量**：每个配置文件都有相应的环境变量设置

## 相关文档

- `DOCKER_GUIDE.md` - 完整的Docker部署指南（包含所有版本说明、配置、故障排除等）
- `../scripts/build.sh` - 构建脚本
