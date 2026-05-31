#!/bin/bash
# AUTOPS 升级脚本
# 用法: ./upgrade.sh [--skip-backup] [--offline]
# 支持: 版本比对、数据库迁移、前端更新、回滚准备
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${AUTOPS_BACKUP_DIR:-/opt/autops/backups}"
LOG_FILE="/var/log/autops-upgrade.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[AUTOPS-UPGRADE]${NC} $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2; exit 1; }

# 参数解析
SKIP_BACKUP=false
OFFLINE_MODE=false
TARGET_VERSION=""

for arg in "$@"; do
  case "$arg" in
    --skip-backup) SKIP_BACKUP=true ;;
    --offline)     OFFLINE_MODE=true ;;
    --version=*)   TARGET_VERSION="${arg#--version=}" ;;
    --help|-h)
      echo "用法: $0 [--skip-backup] [--offline] [--version=X.Y.Z]"
      echo ""
      echo "  --skip-backup  跳过备份步骤(不推荐)"
      echo "  --offline      离线升级模式"
      echo "  --version      指定目标版本号"
      exit 0
      ;;
    *) warn "未知参数: $arg" ;;
  esac
done

CURRENT_VERSION=""
ROLLBACK_MARKER="/tmp/autops_upgrade_rollback_info"

# ============================================================
# 版本管理
# ============================================================
get_current_version() {
    # 优先从 VERSION 文件读取
    if [ -f "$PROJECT_DIR/VERSION" ]; then
        CURRENT_VERSION=$(cat "$PROJECT_DIR/VERSION" | tr -d '[:space:]')
    elif [ -f "$PROJECT_DIR/backend/app/__init__.py" ]; then
        CURRENT_VERSION=$(grep -oP '__version__\s*=\s*["\x27]\K[^"\x27]+' "$PROJECT_DIR/backend/app/__init__.py" 2>/dev/null || echo "")
    fi

    # fallback: git tag
    if [ -z "$CURRENT_VERSION" ] || [ "$CURRENT_VERSION" = "unknown" ]; then
        CURRENT_VERSION=$(cd "$PROJECT_DIR" && git describe --tags --always 2>/dev/null || echo "unknown")
    fi

    # 如果未指定目标版本
    if [ -z "$TARGET_VERSION" ]; then
        if [ -f "$PROJECT_DIR/VERSION" ]; then
            TARGET_VERSION=$(cat "$PROJECT_DIR/VERSION" | tr -d '[:space:]')
        else
            TARGET_VERSION="unknown"
        fi
    fi

    log "当前版本: $CURRENT_VERSION"
    log "目标版本: $TARGET_VERSION"

    # 版本比对
    if [ "$CURRENT_VERSION" = "$TARGET_VERSION" ]; then
        warn "当前版本与目标版本相同 ($CURRENT_VERSION)，是否继续升级？[y/N]"
        read -r confirm
        [[ "$confirm" =~ ^[Yy]$ ]] || { log "升级已取消"; exit 0; }
    fi
}

# ============================================================
# 备份 (回滚准备)
# ============================================================
prepare_rollback() {
    local ts=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$BACKUP_DIR"

    # 保存回滚信息
    cat > "$ROLLBACK_MARKER" <<EOF
CURRENT_VERSION=$CURRENT_VERSION
TARGET_VERSION=$TARGET_VERSION
TIMESTAMP=$ts
BACKUP_DIR=$BACKUP_DIR
PROJECT_DIR=$PROJECT_DIR
EOF

    log "回滚信息已保存到 $ROLLBACK_MARKER"
}

backup_database() {
    local ts=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/autops_pre_upgrade_${ts}.sql.gz"
    mkdir -p "$BACKUP_DIR"

    log "备份数据库到 $backup_file ..."
    mysqldump -u autops -pautops_2026 --single-transaction --routines --triggers autops | gzip > "$backup_file"
    log "数据库备份完成 ($(du -sh "$backup_file" | cut -f1))"

    # 记录备份文件路径到回滚信息
    echo "DB_BACKUP=$backup_file" >> "$ROLLBACK_MARKER"
}

backup_code() {
    local ts=$(date +%Y%m%d_%H%M%S)
    local code_backup="${BACKUP_DIR}/autops_code_${ts}.tar.gz"
    cd "$PROJECT_DIR"
    tar czf "$code_backup" --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' --exclude='.git' .
    log "代码备份完成: $code_backup ($(du -sh "$code_backup" | cut -f1))"

    echo "CODE_BACKUP=$code_backup" >> "$ROLLBACK_MARKER"
}

# ============================================================
# 停止服务
# ============================================================
stop_services() {
    log "停止服务..."
    systemctl stop autops-backend 2>/dev/null || true
}

# ============================================================
# 后端升级
# ============================================================
upgrade_backend() {
    log "升级后端..."
    cd "$PROJECT_DIR/backend"

    # 激活虚拟环境
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        warn "虚拟环境不存在，创建新的虚拟环境..."
        python3 -m venv .venv
        source .venv/bin/activate
    fi

    # 安装依赖
    WHEELS_DIR="$PROJECT_DIR/backend/wheels"
    if [ "$OFFLINE_MODE" = true ] && [ -d "$WHEELS_DIR" ] && [ "$(ls -A "$WHEELS_DIR" 2>/dev/null)" ]; then
        log "离线模式: 从本地 wheels 安装依赖..."
        pip install --no-index --find-links="$WHEELS_DIR" -r requirements.txt 2>/dev/null || \
            warn "部分离线包安装失败"
    else
        pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet 2>/dev/null || true
    fi

    # 数据库迁移
    log "运行数据库迁移 (alembic)..."
    export DB_USER=autops DB_PASSWORD=*** DB_DATABASE=autops
    alembic upgrade head 2>/dev/null || warn "数据库迁移可能需要手动处理"

    log "后端升级完成"
}

# ============================================================
# 前端升级
# ============================================================
upgrade_frontend() {
    log "升级前端..."

    if [ -d "$PROJECT_DIR/frontend/dist" ]; then
        log "前端构建产物已存在，部署到 nginx..."
        # 重新加载 nginx 以获取最新静态文件
        if command -v nginx &>/dev/null; then
            nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || true
        fi
        log "前端部署完成"
    elif [ -d "$PROJECT_DIR/frontend" ]; then
        cd "$PROJECT_DIR/frontend"
        if [ -d "node_modules" ]; then
            if [ "$OFFLINE_MODE" = false ]; then
                npm install --silent 2>/dev/null || true
            fi
            npm run build 2>/dev/null || warn "前端构建失败"
        else
            warn "前端 node_modules 不存在，跳过前端构建"
        fi
    else
        warn "前端目录不存在，跳过"
    fi
}

# ============================================================
# 启动服务
# ============================================================
start_services() {
    log "启动服务..."
    systemctl start autops-backend 2>/dev/null || {
        warn "systemd 启动失败，尝试直接启动..."
        cd "$PROJECT_DIR/backend"
        source .venv/bin/activate
        DB_USER=autops DB_PASSWORD=*** DB_DATABASE=autops \
            nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 >> /var/log/autops-backend.log 2>&1 &
    }
}

# ============================================================
# 升级验证
# ============================================================
verify_upgrade() {
    log "验证升级..."
    sleep 3

    # 健康检查
    local health=$(curl -sf http://localhost:8001/health 2>/dev/null || echo "")
    if echo "$health" | grep -q '"status"'; then
        log "健康检查通过 ✅"
    else
        error "健康检查失败！请检查日志: journalctl -u autops-backend -n 50"
    fi

    # 运行自检
    local check_script="$SCRIPT_DIR/self_check.sh"
    if [ -x "$check_script" ]; then
        log "运行自检脚本..."
        bash "$check_script" 2>/dev/null || warn "自检发现部分问题"
    fi

    # 更新版本记录
    if [ -n "$TARGET_VERSION" ] && [ "$TARGET_VERSION" != "unknown" ]; then
        echo "$TARGET_VERSION" > "$PROJECT_DIR/VERSION"
    fi

    log "升级完成: $CURRENT_VERSION → $TARGET_VERSION"
}

# ============================================================
# 主流程
# ============================================================
main() {
    log "========================================"
    log "AUTOPS 升级开始"
    log "========================================"

    get_current_version

    # 备份
    if [ "$SKIP_BACKUP" = false ]; then
        prepare_rollback
        backup_database
        backup_code
    else
        warn "跳过备份步骤 (--skip-backup)"
    fi

    stop_services
    upgrade_backend
    upgrade_frontend
    start_services
    verify_upgrade

    log "========================================"
    log "升级成功完成！"
    log "如需回滚，请运行: $SCRIPT_DIR/rollback.sh"
    log "========================================"
}

main "$@"
