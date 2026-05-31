.PHONY: help dev dev-back dev-front build test lint migrate seed clean

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## 启动前后端开发服务器
	@echo "Starting backend and frontend dev servers..."
	$(MAKE) dev-back & $(MAKE) dev-front & wait

dev-back: ## 启动后端
	cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --port 8001 --reload

dev-front: ## 启动前端
	cd frontend && npm run dev

build: ## 构建前端
	cd frontend && npm run build

test: ## 运行测试
	cd backend && source .venv/bin/activate && pytest app/ -v

lint: ## 代码检查
	cd backend && source .venv/bin/activate && ruff check app/

migrate: ## 运行数据库迁移
	cd backend && source .venv/bin/activate && alembic upgrade head

seed: ## 填充种子数据
	cd backend && source .venv/bin/activate && python scripts/data_seed/comprehensive_seed.py

clean: ## 清理
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; rm -rf frontend/dist
