# AUTOPS 部署指南

> 文档状态：current
> 建议路径：`docs/06-operations/DEPLOYMENT.md`

---

## 1. Docker Compose 部署（推荐）

```bash
# 1. 克隆仓库
git clone <repo-url> /opt/autops
cd /opt/autops

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写实际配置

# 3. 启动所有服务
cd deploy/docker
docker compose up -d

# 4. 等待服务就绪
docker compose logs -f autops-backend

# 5. 初始化数据
docker compose exec autops-backend python scripts/data_seed/init_data.py

# 6. 访问
# 前端: http://localhost
# 后端 API: http://localhost:8000/docs
# 默认管理员: admin / admin123
```

## 2. 物理机部署

### 系统要求

- CentOS 7+ / Ubuntu 20.04+
- 4核 CPU / 8GB RAM / 100GB 磁盘
- Python 3.10+ / MySQL 8.0+ / Redis 7.0+

### 步骤

```bash
# 1. 安装依赖
./deploy/scripts/install.sh

# 2. 配置
cp .env.example .env
vim .env

# 3. 启动
systemctl start autops-backend
systemctl start autops-worker
systemctl start autops-frontend
```

## 3. 开发环境

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## 4. 端口配置

| 服务 | 默认端口 | 可配置 |
|---|---|---|
| 前端 (Nginx) | 80 | .env APP_PORT |
| 后端 API | 8000 | .env APP_PORT |
| MySQL | 3306 | .env DB_PORT |
| Redis | 6379 | .env REDIS_PORT |
