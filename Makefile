# Backup Tool Makefile

.PHONY: help install dev test docker clean release

# 默认目标
help:
	@echo "可用命令:"
	@echo "  make install    - 安装依赖"
	@echo "  make dev        - 启动开发服务器"
	@echo "  make test       - 运行测试"
	@echo "  make docker     - Docker启动"
	@echo "  make docker-stop - Docker停止"
	@echo "  make clean      - 清理临时文件"
	@echo "  make release    - 创建发布版本"

# 安装依赖
install:
	cd backend && pip install -r requirements.txt

# 启动开发服务器
dev:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
test:
	cd backend && python -c "from models import *; from auth import *; from backup import *; print('All imports OK')"

# Docker启动
docker:
	docker-compose up -d

# Docker停止
docker-stop:
	docker-compose down

# Docker构建
docker-build:
	docker-compose build

# 清理临时文件
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf data/*.db backups/* logs/*

# 创建发布版本
release:
	@echo "使用 release.bat (Windows) 或 release.sh (Linux/Mac)"

# 开发环境初始化
init: install
	@echo "开发环境初始化完成"

# 代码格式化
format:
	cd backend && python -m black .

# 代码检查
lint:
	cd backend && python -m flake8 .

# 查看日志
logs:
	docker-compose logs -f

# 数据库备份
db-backup:
	cp backend/data/backup.db backend/data/backup.db.bak.$$(date +%Y%m%d)
