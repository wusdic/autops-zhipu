#!/bin/bash
# AUTOPS 备份恢复脚本
# 用法: 
#   ./backup_restore.sh backup   - 创建备份
#   ./backup_restore.sh restore  - 恢复最新备份
#   ./backup_restore.sh restore <file>  - 恢复指定备份
set -euo pipefail

BACKUP_DIR="${AUTOPS_BACKUP_DIR:-/opt/autops/backups}"
PROJECT_DIR="${AUTOPS_HOME:-/home/zcxx/autops}"
LOG_FILE="/var/log/autops-backup.log"

GREEN='\033[0;32m'
NC='\033[0m'
log() { echo -e "${GREEN}[AUTOPS-BACKUP]${NC} $1" | tee -a "$LOG_FILE"; }

do_backup() {
    local ts=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$BACKUP_DIR"
    
    # 数据库备份
    local db_file="${BACKUP_DIR}/autops_db_${ts}.sql.gz"
    log "备份数据库..."
    mysqldump -u autops -pautops_2026 --single-transaction --routines --triggers autops | gzip > "$db_file"
    log "数据库备份: $db_file ($(du -sh "$db_file" | cut -f1))"
    
    # 配置备份
    local cfg_file="${BACKUP_DIR}/autops_config_${ts}.tar.gz"
    tar czf "$cfg_file" -C "$PROJECT_DIR" configs/ .env 2>/dev/null || true
    log "配置备份: $cfg_file"
    
    # 清理 30 天前的备份
    find "$BACKUP_DIR" -name "autops_*" -mtime +30 -delete 2>/dev/null || true
    
    log "备份完成！"
}

do_restore() {
    local db_file="${1:-}"
    
    if [ -z "$db_file" ]; then
        # 找最新的备份
        db_file=$(ls -t "${BACKUP_DIR}"/autops_db_*.sql.gz 2>/dev/null | head -1)
        if [ -z "$db_file" ]; then
            echo "未找到备份文件"
            exit 1
        fi
    fi
    
    log "恢复数据库: $db_file"
    
    # 停止服务
    systemctl stop autops-backend 2>/dev/null || true
    
    # 恢复
    gunzip -c "$db_file" | mysql -u autops -pautops_2026 autops
    
    # 重启
    systemctl start autops-backend 2>/dev/null || true
    
    log "恢复完成！"
}

case "${1:-help}" in
    backup)  do_backup ;;
    restore) do_restore "${2:-}" ;;
    list)    ls -lh "${BACKUP_DIR}"/autops_* 2>/dev/null || echo "无备份" ;;
    *)
        echo "用法: $0 {backup|restore [file]|list}"
        exit 1
        ;;
esac
