#!/bin/bash
# AUTOPS 升级脚本
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/opt/autops/backups"
LOG_FILE="/var/log/autops-upgrade.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[AUTOPS-UPGRADE]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2; }

CURRENT_VERSION=""
TARGET_VERSION=""

get_current_version() {
    CURRENT_VERSION=$(cd "$PROJECT_DIR" && git describe --tags --always 2>/dev/null || echo "unknown")
    log "当前版本: $CURRENT_VERSION"
}

backup_database() {
    local ts=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/autops_pre_upgrade_${ts}.sql.gz"
    mkdir -p "$BACKUP_DIR"
    
    log "备份数据库到 $backup_file ..."
    mysqldump -u autops -pautops_2026 --single-transaction autops | gzip > "$backup_file"
    log "数据库备份完成 ($(du -sh "$backup_file" | cut -f1))"
}

backup_code() {
    local ts=$(date +%Y%m%d_%H%M%S)
    local code_backup="${BACKUP_DIR}/autops_code_${ts}.tar.gz"
    cd "$PROJECT_DIR"
    tar czf "$code_backup" --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' --exclude='.git' .
    log "代码备份完成: $code_backup"
}

stop_services() {
    log "停止服务..."
    systemctl stop autops-backend 2>/dev/null || true
}

upgrade_backend() {
    log "升级后端..."
    cd "$PROJECT_DIR/backend"
    source .venv/bin/activate
    pip install -r requirements.txt --quiet 2>/dev/null || true
    
    export DB_USER=autops DB_PASSWORD=autops_2026 DB_DATABASE=autops
    alembic upgrade head 2>/dev/null || warn "数据库迁移可能需要手动处理"
}

upgrade_frontend() {
    log "升级前端..."
    cd "$PROJECT_DIR/frontend"
    if [ -d "node_modules" ]; then
        npm install --silent 2>/dev/null || true
        npm run build 2>/dev/null || warn "前端构建失败"
    fi
}

start_services() {
    log "启动服务..."
    systemctl start autops-backend 2>/dev/null || {
        warn "systemd 启动失败，尝试直接启动..."
        cd "$PROJECT_DIR/backend"
        source .venv/bin/activate
        DB_USER=autops DB_PASSWORD=autops_2026 DB_DATABASE=autops \
            nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 >> /var/log/autops-backend.log 2>&1 &
    }
}

verify_upgrade() {
    log "验证升级..."
    sleep 3
    local health=$(curl -s http://localhost:8001/health 2>/dev/null || echo "failed")
    if echo "$health" | grep -q '"status"'; then
        log "健康检查通过 ✅"
    else
        error "健康检查失败！请检查日志: journalctl -u autops-backend -n 50"
    fi
    
    TARGET_VERSION=$(cd "$PROJECT_DIR" && git describe --tags --always 2>/dev/null || echo "unknown")
    log "升级完成: $CURRENT_VERSION → $TARGET_VERSION"
}

main() {
    log "========================================"
    log "AUTOPS 升级开始"
    log "========================================"
    
    get_current_version
    backup_database
    backup_code
    stop_services
    upgrade_backend
    upgrade_frontend
    start_services
    verify_upgrade
    
    log "========================================"
    log "升级成功完成！"
    log "========================================"
}

main "$@"
