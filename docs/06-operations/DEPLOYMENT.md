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
# 编辑 .env，必须设置：MYSQL_ROOT_PASSWORD、DB_PASS、JWT_SECRET、CREDENTIAL_ENCRYPT_KEY
# 可选设置：ADMIN_INITIAL_PASSWORD（不设则种子脚本随机生成并打印到日志）

# 3. 启动所有服务（在项目根目录执行，勿用 deploy/docker/ 下的废弃 compose）
docker compose up -d

# 4. 等待 migrate 容器完成数据库迁移（含 0004 auto_onboard 迁移）
docker compose logs -f autops-migrate

# 5. 初始化种子数据（创建内置角色 + admin 用户）
docker compose exec autops-backend python scripts/data_seed/init_data.py
#    若未设 ADMIN_INITIAL_PASSWORD，初始口令会打印在上方输出，仅显示一次

# 6. 访问
# 前端:       http://localhost
# 后端 API:   仅绑定 127.0.0.1:8001，由前端 nginx 反代 /api/ 对外
# OpenAPI:    开发环境 http://localhost:8001/docs（生产关闭）
```

> ⚠️ **生产注意事项**
> - `JWT_SECRET` 必须 ≥32 字符且不能是占位值，否则启动报错
> - `configs/app.yaml` 的 `cors_origins` 不能为 `["*"]`（生产校验会拒绝），需改为具体域名
> - MySQL/Redis 端口仅绑定 `127.0.0.1`，不对外暴露
> - 后端 `/docs`、`/redoc` 在生产环境（`AUTOPS_ENV=prod`）自动关闭

## 2. 物理机部署

### 系统要求

- CentOS 7+ / Ubuntu 20.04+
- 4核 CPU / 8GB RAM / 100GB 磁盘
- Python 3.10+ / MySQL 8.0+ / Redis 7.0+

### 步骤

```bash
# 1. 安装（会自动完成依赖安装、建库、迁移、种子数据）
sudo ./deploy/scripts/install.sh

# 2. 配置（install.sh 会引导，也可手动）
cp .env.example .env
sudo vim .env

# 3. 启动后端（install.sh 生成 systemd 单元 autops-backend）
sudo systemctl start autops-backend

# 注意：当前 install.sh 仅部署并启动后端 (autops-backend)；
# worker 进程（采集调度器）需另行配置，例如另起一个 systemd 单元运行：
#   python -m app.workers.runner
```

## 3. 开发环境

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8001

# 前端
cd frontend
npm install
npm run dev
```

也可用 Makefile 提供的快捷命令：`make migrate`、`make dev`、`make seed`。

## 4. 端口配置

| 服务 | 默认端口 | 可配置 | 暴露范围 |
|---|---|---|---|
| 前端 (Nginx) | 80 | `.env FRONTEND_PORT` | 对外 |
| 后端 API | 8001 | `.env BACKEND_PORT` | 仅 `127.0.0.1`（由 nginx 反代） |
| MySQL | 3306 | `.env DB_PORT` | 仅 `127.0.0.1` |
| Redis | 6379 | `.env REDIS_PORT` | 仅 `127.0.0.1` |

> 健康检查：`GET /health` 返回 `{"status":"alive"}`；`GET /ready` 返回 DB+Redis 检查结果。
> 注意 docker-compose 中 backend 容器的 healthcheck 依赖 `curl`，若镜像未安装需改用 python urllib 或在 Dockerfile 安装 curl。
