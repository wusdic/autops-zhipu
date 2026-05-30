#!/bin/bash
# AUTOPS 离线安装脚本
# 用法: ./install.sh [--offline]
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
    
    $MYSQL_CMD <<EOF
CREATE DATABASE IF NOT EXISTS autops CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'autops'@'127.0.0.1' IDENTIFIED BY 'autops_2026';
GRANT ALL PRIVILEGES ON autops.* TO 'autops'@'127.0.0.1';
FLUSH PRIVILEGES;
EOF
    log "数据库配置完成"
}

setup_redis() {
    log "配置 Redis..."
    if ! systemctl is-active --quiet redis 2>/dev/null && ! systemctl is-active --quiet redis-server 2>/dev/null; then
        systemctl start redis 2>/dev/null || systemctl start redis-server 2>/dev/null || warn "Redis 启动失败"
    fi
}

setup_backend() {
    log "安装后端..."
    cd "$PROJECT_DIR/backend"
    
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    
    # 安装依赖
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet 2>/dev/null || \
        pip install fastapi uvicorn sqlalchemy[asyncio] aiomysql alembic \
            pydantic pydantic-settings redis python-jose[cryptography] \
            passlib[bcrypt] python-multipart pyyaml httpx --quiet
    
    # 运行数据库迁移
    export DB_USER=autops DB_PASSWORD=autops_2026 DB_DATABASE=autops
    alembic upgrade head 2>/dev/null || python -c "
import asyncio
from app.infra.database import engine, Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
    
    log "后端安装完成"
}

setup_frontend() {
    log "安装前端..."
    cd "$PROJECT_DIR/frontend"
    
    if command -v node &>/dev/null && command -v npm &>/dev/null; then
        npm install --silent 2>/dev/null || true
        npm run build 2>/dev/null || warn "前端构建失败，请手动构建"
    else
        warn "Node.js 未安装，跳过前端构建"
    fi
    
    log "前端安装完成"
}

setup_seed_data() {
    log "初始化种子数据..."
    cd "$PROJECT_DIR"
    source backend/.venv/bin/activate
    export DB_USER=autops DB_PASSWORD=autops_2026 DB_DATABASE=autops
    
    python scripts/data_seed/init_data.py 2>/dev/null || warn "种子数据初始化失败（可能已初始化）"
    python scripts/data_seed/seed_knowledge.py 2>/dev/null || warn "知识库种子数据初始化失败"
    python scripts/data_seed/seed_m3_scenarios.py 2>/dev/null || warn "M3 场景数据初始化失败"
    
    log "种子数据初始化完成"
}

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
Environment=DB_PASSWORD=autops_2026
Environment=DB_DATABASE=autops
ExecStart=${PROJECT_DIR}/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable autops-backend
    log "systemd 服务配置完成"
}

print_summary() {
    echo ""
    echo "============================================"
    log "AUTOPS 安装完成！"
    echo "============================================"
    echo ""
    log "后端地址: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):8001"
    log "健康检查: http://localhost:8001/health"
    log "默认账户: admin / admin123"
    echo ""
    log "启动服务: systemctl start autops-backend"
    log "停止服务: systemctl stop autops-backend"
    log "查看日志: journalctl -u autops-backend -f"
    echo ""
}

# ===== 主流程 =====
main() {
    log "AUTOPS 安装开始..."
    check_root
    check_os
    
    if [ "${1:-}" = "--offline" ]; then
        log "离线安装模式"
    else
        install_system_deps
    fi
    
    setup_database
    setup_redis
    setup_backend
    setup_frontend
    setup_seed_data
    setup_systemd
    
    # 启动服务
    systemctl start autops-backend || warn "服务启动失败，请手动检查"
    
    print_summary
}

main "$@"
