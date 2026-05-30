#!/bin/bash
# AUTOPS 回滚脚本
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/opt/autops/backups"
LOG_FILE="/var/log/autops-rollback.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[AUTOPS-ROLLBACK]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2; exit 1; }

list_backups() {
    echo "可用备份:"
    echo "--- 数据库备份 ---"
    ls -lh "${BACKUP_DIR}"/autops_pre_upgrade_*.sql.gz 2>/dev/null || echo "  (无)"
    echo "--- 代码备份 ---"
    ls -lh "${BACKUP_DIR}"/autops_code_*.tar.gz 2>/dev/null || echo "  (无)"
}

select_backup() {
    local db_backups=($(ls -t "${BACKUP_DIR}"/autops_pre_upgrade_*.sql.gz 2>/dev/null || true))
    if [ ${#db_backups[@]} -eq 0 ]; then
        error "未找到数据库备份文件"
    fi
    DB_BACKUP="${db_backups[0]}"
    log "使用数据库备份: $DB_BACKUP"
    
    local code_ts=$(basename "$DB_BACKUP" | sed 's/autops_pre_upgrade_\(.*\)\.sql\.gz/\1/')
    CODE_BACKUP="${BACKUP_DIR}/autops_code_${code_ts}.tar.gz"
    if [ ! -f "$CODE_BACKUP" ]; then
        warn "未找到对应代码备份: $CODE_BACKUP"
        CODE_BACKUP=""
    fi
}

restore_database() {
    log "恢复数据库..."
    gunzip -c "$DB_BACKUP" | mysql -u autops -pautops_2026 autops
    log "数据库恢复完成"
}

restore_code() {
    if [ -n "$CODE_BACKUP" ] && [ -f "$CODE_BACKUP" ]; then
        log "恢复代码..."
        cd "$PROJECT_DIR"
        tar xzf "$CODE_BACKUP"
        log "代码恢复完成"
    else
        warn "跳过代码恢复"
    fi
}

main() {
    log "========================================"
    log "AUTOPS 回滚开始"
    log "========================================"
    
    if [ "${1:-}" = "--list" ]; then
        list_backups
        exit 0
    fi
    
    # 停止服务
    systemctl stop autops-backend 2>/dev/null || true
    
    select_backup
    restore_database
    restore_code
    
    # 重启
    systemctl start autops-backend 2>/dev/null || true
    
    sleep 3
    local health=$(curl -s http://localhost:8001/health 2>/dev/null || echo "failed")
    if echo "$health" | grep -q '"status"'; then
        log "回滚成功 ✅ 健康检查通过"
    else
        error "回滚后健康检查失败！"
    fi
    
    log "========================================"
    log "回滚完成"
    log "========================================"
}

main "$@"
