# Daemon Proxy Service Makefile

.PHONY: help install install-dev test test-unit test-integration test-cov lint format clean run run-docker build

help: ## 显示帮助信息
	@echo "Daemon Proxy Service"
	@echo "==================="
	@echo ""
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	pip install -r requirements.txt

install-dev: ## 安装开发依赖
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-mock pytest-cov black flake8 mypy

test: ## 运行所有测试
	pytest

test-unit: ## 运行单元测试
	pytest tests/test_config.py tests/test_daemon.py tests/test_proxy.py

test-integration: ## 运行集成测试
	pytest tests/test_integration.py

test-e2e-mock: ## 运行 E2E Mock 环境测试
	pytest tests/e2e/test_e2e_mock.py -m e2e_mock -v

test-e2e-real: ## 运行 E2E 真实 daemon 测试
	pytest tests/e2e/test_e2e_real.py -m e2e_real -v

test-e2e-docker: ## 运行 E2E Docker 环境测试
	pytest tests/e2e/test_e2e_docker.py -m e2e_docker -v

test-e2e-all: ## 运行所有 E2E 测试
	pytest tests/e2e/ -v

# 真实 daemon 相关命令
e2e-build-daemon: ## 编译真实 daemon 用于测试
	@echo "编译 daytona daemon..."
	./tests/e2e/scripts/build_daemon.sh

e2e-check-daemon: ## 检查 daemon 环境
	@echo "检查 daemon 环境..."
	./tests/e2e/scripts/check_daemon.sh

e2e-cleanup-daemon: ## 清理 daemon 测试环境
	@echo "清理 daemon 测试环境..."
	./tests/e2e/scripts/cleanup_daemon.sh

test-e2e-real-with-daemon: e2e-build-daemon test-e2e-real ## 编译 daemon 并运行真实环境测试

test-e2e-docker-with-daemon: e2e-build-daemon test-e2e-docker ## 编译 daemon 并运行 Docker 环境测试

test-cov: ## 运行测试并生成覆盖率报告
	pytest --cov=daemon_proxy --cov-report=html --cov-report=term

lint: ## 代码检查
	flake8 daemon_proxy tests main.py
	mypy daemon_proxy main.py

format: ## 代码格式化
	black daemon_proxy tests main.py

clean: ## 清理临时文件
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

run: ## 运行服务
	python main.py

run-config: ## 使用配置文件运行服务
	python main.py --config config.yaml

run-docker: ## 在Docker中运行服务
	docker build -t daemon-proxy .
	docker run -p 8080:8080 daemon-proxy

build: ## 构建包
	python setup.py sdist bdist_wheel

install-package: ## 安装包
	pip install -e .

# 开发环境设置
dev-setup: install-dev ## 设置开发环境
	@echo "开发环境设置完成"
	@echo "运行 'make test' 来测试"
	@echo "运行 'make run' 来启动服务"

# 快速测试
quick-test: ## 快速测试（跳过集成测试）
	pytest -m "not integration"

# 性能测试
perf-test: ## 性能测试
	pytest tests/test_integration.py::TestIntegration::test_concurrent_requests -v

# E2E 测试相关
e2e-setup: ## 设置 E2E 测试环境
	@echo "Setting up E2E test environment..."

# 静态网站 E2E 测试
e2e-static: ## 运行静态网站 E2E 测试
	pytest tests/e2e/test_e2e_static.py -v -m e2e_static

e2e-static-docker: ## 运行静态网站 Docker E2E 测试
	docker-compose -f docker-compose-static-e2e.yml up -d
	sleep 30
	pytest tests/e2e/test_e2e_static.py -v -m e2e_static
	docker-compose -f docker-compose-static-e2e.yml down

e2e-static-clean: ## 清理静态网站 E2E 测试环境
	docker-compose -f docker-compose-static-e2e.yml down -v
	docker system prune -f
	@echo "Installing additional dependencies..."
	pip install docker docker-compose
	@echo "E2E test environment ready"

e2e-docker-build: ## 构建 E2E 测试 Docker 镜像
	docker build -f Dockerfile.test -t daemon-proxy-e2e-test .

e2e-docker-run: ## 在 Docker 中运行 E2E 测试
	docker-compose -f docker-compose-e2e.yml up --build --abort-on-container-exit

e2e-docker-clean: ## 清理 E2E Docker 环境
	docker-compose -f docker-compose-e2e.yml down -v
	docker system prune -f

# 安全检查
security-check: ## 安全检查
	pip install safety
	safety check

# 更新依赖
update-deps: ## 更新依赖
	pip install --upgrade -r requirements.txt

# 生成文档
docs: ## 生成文档
	@echo "文档已生成在 README.md 中"

# 发布准备
release-prep: clean test lint ## 发布准备
	@echo "发布准备完成"
	@echo "请检查版本号并运行 'make build'"

