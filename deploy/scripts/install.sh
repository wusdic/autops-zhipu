#!/bin/bash
# AUTOPS 离线/在线安装脚本
# 用法: ./install.sh [--offline] [--skip-deps] [--skip-db]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/autops-install.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[AUTOPS]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2; exit 1; }

# 解析参数
OFFLINE_MODE=false
SKIP_DEPS=false
SKIP_DB=false

for arg in "$@"; do
  case "$arg" in
    --offline)  OFFLINE_MODE=true ;;
    --skip-deps) SKIP_DEPS=true ;;
    --skip-db)   SKIP_DB=true ;;
    --help|-h)
      echo "用法: $0 [--offline] [--skip-deps] [--skip-db]"
      echo ""
      echo "  --offline    离线安装模式(使用本地wheels)"
      echo "  --skip-deps  跳过系统依赖安装"
      echo "  --skip-db    跳过数据库初始化"
      exit 0
      ;;
    *) warn "未知参数: $arg" ;;
  esac
done

# 自动检测离线模式: 如果存在 wheels 目录且有文件，自动启用离线安装
WHEELS_DIR="$PROJECT_DIR/backend/wheels"
if [ -d "$WHEELS_DIR" ] && [ "$(ls -A "$WHEELS_DIR" 2>/dev/null)" ]; then
  if [ "$OFFLINE_MODE" = false ]; then
    log "检测到本地 wheels 目录，自动启用离线安装模式"
    OFFLINE_MODE=true
  fi
fi

check_root() {
    [ "$(id -u)" -eq 0 ] || error "请以 root 用户运行此脚本"
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_ID="${ID:-unknown}"
        OS_VERSION="${VERSION_ID:-unknown}"
    else
        error "无法检测操作系统版本"
    fi
    log "检测到操作系统: ${OS_ID} ${OS_VERSION}"
}

# ============================================================
# 系统依赖检查与安装
# ============================================================
check_system_deps() {
    local missing=()

    # Python 3.12 / 3.11 / 3.x
    if command -v python3.12 &>/dev/null; then
        PYTHON_BIN="python3.12"
    elif command -v python3.11 &>/dev/null; then
        PYTHON_BIN="python3.11"
    elif command -v python3 &>/dev/null; then
        PYTHON_BIN="python3"
    else
        missing+=("python3")
        PYTHON_BIN=""
    fi
    if [ -n "$PYTHON_BIN" ]; then
        local pyver=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
        log "Python 版本: $pyver ($PYTHON_BIN)"
    fi

    # MySQL / MariaDB
    if command -v mysql &>/dev/null; then
        log "MySQL: $(mysql --version 2>&1 | head -1)"
    else
        missing+=("mysql")
    fi

    # Redis
    if command -v redis-server &>/dev/null || command -v redis-cli &>/dev/null; then
        log "Redis: $(redis-server --version 2>&1 | head -1)"
    else
        missing+=("redis")
    fi

    # nginx (可选)
    if command -v nginx &>/dev/null; then
        log "Nginx: $(nginx -v 2>&1)"
    else
        warn "nginx 未安装(可选，用于前端部署)"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        if [ "$OFFLINE_MODE" = true ]; then
            error "离线模式下缺少系统依赖: ${missing[*]}，请手动安装后重试"
        else
            warn "缺少系统依赖: ${missing[*]}，将尝试安装..."
        fi
    fi
}

install_system_deps() {
    log "安装系统依赖..."
    case "$OS_ID" in
        centos|rhel|rocky|alma)
            yum install -y python3.12 python3.12-devel mysql-server redis nginx \
                gcc make cmake 2>/dev/null || \
            yum install -y python3 python3-devel mysql-server redis nginx gcc make cmake
            ;;
        ubuntu|debian)
            apt-get update
            apt-get install -y python3.12 python3.12-dev python3.12-venv \
                mysql-server redis-server nginx gcc make cmake 2>/dev/null || \
            apt-get install -y python3 python3-dev python3-venv \
                mysql-server redis-server nginx gcc make cmake
            ;;
        *)
            warn "未测试的操作系统: $OS_ID，尝试继续安装..."
            ;;
    esac
}

# ============================================================
# 数据库初始化
# ============================================================
setup_database() {
    log "配置 MySQL 数据库..."

    # 检查 MySQL 是否运行
    if ! systemctl is-active --quiet mysql 2>/dev/null && ! systemctl is-active --quiet mysqld 2>/dev/null; then
        systemctl start mysql 2>/dev/null || systemctl start mysqld 2>/dev/null || error "MySQL 启动失败"
    fi

    # 创建数据库和用户
    MYSQL_PWD_ROOT="${MYSQL_ROOT_PASSWORD:-}"
    if [ -n "$MYSQL_PWD_ROOT" ]; then
        MYSQL_CMD="mysql -u root -p${MYSQL_PWD_ROOT}"
    else
        MYSQL_CMD="mysql -u root"
    fi

    # 不再使用硬编码弱口令：优先取环境变量 DB_PASS，否则随机生成并打印一次。
    APP_DB_PASS="${DB_PASS:-}"
    if [ -z "$APP_DB_PASS" ]; then
        APP_DB_PASS="$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
        warn "未提供 DB_PASS，已随机生成 autops 数据库口令（请妥善保存，仅显示一次）："
        echo "    DB_PASS=${APP_DB_PASS}"
    fi

    $MYSQL_CMD <<EOF
CREATE DATABASE IF NOT EXISTS autops CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'autops'@'127.0.0.1' IDENTIFIED BY '${APP_DB_PASS}';
ALTER USER 'autops'@'127.0.0.1' IDENTIFIED BY '${APP_DB_PASS}';
GRANT ALL PRIVILEGES ON autops.* TO 'autops'@'127.0.0.1';
FLUSH PRIVILEGES;
EOF
    log "数据库配置完成（口令来自 DB_PASS 环境变量或随机生成）"
}

# ============================================================
# Redis 初始化
# ============================================================
setup_redis() {
    log "配置 Redis..."
    if ! systemctl is-active --quiet redis 2>/dev/null && ! systemctl is-active --quiet redis-server 2>/dev/null; then
        systemctl start redis 2>/dev/null || systemctl start redis-server 2>/dev/null || warn "Redis 启动失败"
    fi
    # 安全提示：生产环境 Redis 必须设置 requirepass 或内网隔离。
    if [ -n "${REDIS_PASS:-}" ]; then
        REDIS_CONF="$(redis-cli CONFIG GET dir >/dev/null 2>&1 && echo ok || echo '')"
        if redis-cli CONFIG SET requirepass "${REDIS_PASS}" >/dev/null 2>&1; then
            log "已为 Redis 设置 requirepass（来自 REDIS_PASS）"
        else
            warn "无法自动设置 Redis requirepass，请手动在 redis.conf 配置 requirepass=${REDIS_PASS}"
        fi
    else
        warn "未设置 REDIS_PASS：生产环境务必为 Redis 配置 requirepass 或仅绑定 127.0.0.1/内网"
    fi
}

# ============================================================
# 后端安装 (支持离线模式)
# ============================================================
setup_backend() {
    log "安装后端..."
    cd "$PROJECT_DIR/backend"

    # 确定Python解释器
    local py="${PYTHON_BIN:-python3}"

    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        $py -m venv .venv
    fi
    source .venv/bin/activate

    # 安装依赖
    if [ "$OFFLINE_MODE" = true ] && [ -d "$WHEELS_DIR" ] && [ "$(ls -A "$WHEELS_DIR" 2>/dev/null)" ]; then
        log "离线模式: 从本地 wheels 安装依赖..."
        pip install --upgrade pip --quiet --no-index --find-links="$WHEELS_DIR" 2>/dev/null || true
        pip install --no-index --find-links="$WHEELS_DIR" -r requirements.txt 2>/dev/null || \
        pip install --no-index --find-links="$WHEELS_DIR" \
            fastapi uvicorn sqlalchemy[asyncio] aiomysql alembic \
            pydantic pydantic-settings redis python-jose[cryptography] \
            passlib[bcrypt] python-multipart pyyaml httpx --quiet 2>/dev/null || \
            warn "部分离线包安装失败，请检查 wheels 目录"
    else
        log "在线模式: 从 PyPI 安装依赖..."
        pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet 2>/dev/null || \
            pip install fastapi uvicorn sqlalchemy[asyncio] aiomysql alembic \
                pydantic pydantic-settings redis python-jose[cryptography] \
                passlib[bcrypt] python-multipart pyyaml httpx --quiet
    fi

    # 数据库迁移
    if [ "$SKIP_DB" = false ]; then
        log "运行数据库迁移..."
        export DB_USER=autops DB_PASSWORD=*** DB_DATABASE=autops
        alembic upgrade head 2>/dev/null || python -c "
import asyncio
from app.infra.database import engine, Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
" 2>/dev/null || warn "数据库迁移失败，可能需要手动处理"
    fi

    log "后端安装完成"
}

# ============================================================
# 前端静态文件部署
# ============================================================
setup_frontend() {
    log "部署前端静态文件..."

    # 离线模式: 使用预构建的 dist
    if [ -d "$PROJECT_DIR/frontend/dist" ]; then
        log "检测到前端构建产物，部署到 nginx..."
        local nginx_conf="/etc/nginx/conf.d/autops.conf"
        if [ -d "/etc/nginx/conf.d" ]; then
            cat > "$nginx_conf" <<EOF
server {
    listen 80;
    server_name _;

    root $PROJECT_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8001;
    }
}
EOF
            nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || warn "nginx 配置测试失败，请手动配置"
            log "前端已部署到 nginx"
        else
            log "前端构建产物已就绪 ($PROJECT_DIR/frontend/dist)"
        fi
    else
        # 在线模式: 尝试构建
        if command -v node &>/dev/null && command -v npm &>/dev/null; then
            cd "$PROJECT_DIR/frontend"
            npm install --silent 2>/dev/null || true
            npm run build 2>/dev/null || warn "前端构建失败，请手动构建"
        else
            warn "前端构建产物不存在且 Node.js 未安装，跳过前端部署"
        fi
    fi

    log "前端安装完成"
}

# ============================================================
# 种子数据
# ============================================================
setup_seed_data() {
    log "初始化种子数据..."
    cd "$PROJECT_DIR"
    source backend/.venv/bin/activate
    export DB_USER=autops DB_PASSWORD=*** DB_DATABASE=autops

    python scripts/data_seed/init_data.py 2>/dev/null || warn "种子数据初始化失败（可能已初始化）"
    python scripts/data_seed/seed_knowledge.py 2>/dev/null || warn "知识库种子数据初始化失败"
    python scripts/data_seed/seed_m3_scenarios.py 2>/dev/null || warn "M3 场景数据初始化失败"

    log "种子数据初始化完成"
}

# ============================================================
# systemd 服务配置
# ============================================================
setup_systemd() {
    log "配置 systemd 服务..."

    cat > /etc/systemd/system/autops-backend.service <<EOF
[Unit]
Description=AUTOPS Backend Service
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}/backend
Environment=DB_USER=autops
Environment=DB_PASSWORD=${DB_PASSWORD:-autops}
Environment=DB_DATABASE=autops
ExecStart=${PROJECT_DIR}/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
EOF

    # Worker 进程：事件驱动核心（outbox 消费 + 采集/巡检调度 + 执行队列）。
    # 必须随 backend 一起启用，否则 outbox 永不消费、采集/执行全部停滞。
    cat > /etc/systemd/system/autops-worker.service <<EOF
[Unit]
Description=AUTOPS Worker (outbox consumer + scheduler + execution worker)
After=network.target mysql.service redis.service autops-backend.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}/backend
Environment=DB_USER=autops
Environment=DB_PASSWORD=${DB_PASSWORD:-autops}
Environment=DB_DATABASE=autops
ExecStart=${PROJECT_DIR}/backend/.venv/bin/python -m app.workers.runner
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5
# ping/SNMP 需要原始套接字与低端口能力
AmbientCapabilities=CAP_NET_RAW CAP_NET_BIND_SERVICE
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
EOF

    # logrotate：应用文件日志轮转（systemd 日志由 journald 管理）
    mkdir -p /var/log/autops
    if [ -f "${SCRIPT_DIR}/../systemd/autops.logrotate" ]; then
        cp "${SCRIPT_DIR}/../systemd/autops.logrotate" /etc/logrotate.d/autops
        log "logrotate 配置已安装到 /etc/logrotate.d/autops"
    fi

    systemctl daemon-reload
    systemctl enable autops-backend
    systemctl enable autops-worker
    log "systemd 服务配置完成（backend + worker）"
}

# ============================================================
# 安装后自检
# ============================================================
run_self_check() {
    log "运行安装自检..."
    local check_script="$SCRIPT_DIR/self_check.sh"
    if [ -x "$check_script" ]; then
        bash "$check_script" 2>/dev/null || warn "自检发现部分问题，请查看上方详情"
    else
        warn "自检脚本不存在或不可执行，跳过"
    fi
}

# ============================================================
# 打印安装摘要
# ============================================================
print_summary() {
    local mode="在线"
    [ "$OFFLINE_MODE" = true ] && mode="离线"
    echo ""
    echo "============================================"
    log "AUTOPS 安装完成！(${mode}模式)"
    echo "============================================"
    echo ""
    log "后端地址: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):8001"
    log "前端地址: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost')"
    log "健康检查: http://localhost:8001/health"
    log "默认账户: admin / admin123"
    echo ""
    log "启动服务: systemctl start autops-backend autops-worker"
    log "停止服务: systemctl stop autops-backend autops-worker"
    log "查看日志: journalctl -u autops-backend -u autops-worker -f"
    log "综合诊断: curl http://localhost:8001/api/v1/platform/diagnostics"
    log "运行自检: $SCRIPT_DIR/self_check.sh"
    echo ""
}

# ===== 主流程 =====
main() {
    log "AUTOPS 安装开始..."
    check_root
    check_os

    if [ "$OFFLINE_MODE" = true ]; then
        log "离线安装模式"
        check_system_deps
    elif [ "$SKIP_DEPS" = true ]; then
        log "跳过系统依赖安装"
        check_system_deps
    else
        install_system_deps
        check_system_deps
    fi

    if [ "$SKIP_DB" = false ]; then
        setup_database
    else
        log "跳过数据库初始化"
    fi

    setup_redis
    setup_backend
    setup_frontend
    setup_seed_data
    setup_systemd

    # 启动服务（backend + worker 必须同时运行）
    systemctl start autops-backend || warn "后端服务启动失败，请手动检查"
    systemctl start autops-worker || warn "Worker 服务启动失败，请手动检查（outbox/采集/执行依赖它）"

    # 运行自检
    run_self_check

    print_summary
}

main "$@"
