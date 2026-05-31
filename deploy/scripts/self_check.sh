#!/bin/bash
# AUTOPS 平台自检脚本
# 检查所有组件健康状态: MySQL、Redis、后端API、前端静态文件、磁盘空间
# 用法: ./self_check.sh [--json] [--quiet]
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 参数
JSON_OUTPUT=false
QUIET_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json)  JSON_OUTPUT=true ;;
    --quiet) QUIET_MODE=true ;;
  esac
done

PASS=0
FAIL=0
WARN=0
RESULTS=()

check() {
    local name="$1"
    local result="$2"
    local detail="${3:-}"

    if [ "$JSON_OUTPUT" = true ]; then
        RESULTS+=("{\"name\":\"$name\",\"status\":\"$result\",\"detail\":\"$detail\"}")
    fi

    if [ "$QUIET_MODE" = true ]; then
        case "$result" in
            pass) PASS=$((PASS + 1)) ;;
            warn) WARN=$((WARN + 1)) ;;
            fail) FAIL=$((FAIL + 1)) ;;
        esac
        return
    fi

    case "$result" in
        pass)
            echo -e "  ${GREEN}✅${NC} $name"
            [ -n "$detail" ] && echo -e "       $detail"
            PASS=$((PASS + 1))
            ;;
        warn)
            echo -e "  ${YELLOW}⚠️${NC} $name"
            [ -n "$detail" ] && echo -e "       $detail"
            WARN=$((WARN + 1))
            ;;
        *)
            echo -e "  ${RED}❌${NC} $name"
            [ -n "$detail" ] && echo -e "       $detail"
            FAIL=$((FAIL + 1))
            ;;
    esac
}

API_BASE="${AUTOPS_URL:-http://localhost:8001}"
PROJECT_DIR="${AUTOPS_HOME:-/home/zcxx/autops}"

if [ "$QUIET_MODE" = false ]; then
    echo "========================================"
    echo "  AUTOPS 平台自检"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""
fi

# ============================================================
# 1. 系统资源检查
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【系统资源】"

CPU_USAGE=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {printf "%.0f", usage}')
MEM_USAGE=$(free | grep -i -E 'mem|内存' | awk '{printf "%.0f", $3/$2*100}')
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')

check "CPU 使用率 ${CPU_USAGE}%" "$([ "$CPU_USAGE" -lt 90 ] && echo pass || echo warn)" "阈值: 90%"
check "内存使用率 ${MEM_USAGE}%" "$([ "$MEM_USAGE" -lt 90 ] && echo pass || echo warn)" "阈值: 90%"
check "根磁盘使用率 ${DISK_USAGE}% (可用 ${DISK_AVAIL})" "$([ "$DISK_USAGE" -lt 85 ] && echo pass || echo warn)" "阈值: 85%"

# 数据目录磁盘空间(如果存在)
if [ -d "$PROJECT_DIR/data" ]; then
    DATA_DISK=$(df -h "$PROJECT_DIR/data" | tail -1 | awk '{print $5}' | tr -d '%')
    DATA_AVAIL=$(df -h "$PROJECT_DIR/data" | tail -1 | awk '{print $4}')
    check "数据目录磁盘 ${DATA_DISK}% (可用 ${DATA_AVAIL})" "$([ "$DATA_DISK" -lt 85 ] && echo pass || echo warn)"
fi

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 2. MySQL 连通性检查
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【MySQL 数据库】"

# 服务状态
MYSQL_ACTIVE=$(systemctl is-active mysql 2>/dev/null || systemctl is-active mysqld 2>/dev/null || echo "unknown")
check "MySQL 服务状态" "$([ "$MYSQL_ACTIVE" = "active" ] && echo pass || echo fail)" "systemctl status: $MYSQL_ACTIVE"

# 连接测试
MYSQL_PWD="${AUTOPS_DB_PASSWORD:-autops_2026}"
MYSQL_USER="${AUTOPS_DB_USER:-autops}"
MYSQL_HOST="${AUTOPS_DB_HOST:-127.0.0.1}"
MYSQL_DB="${AUTOPS_DB_NAME:-autops}"

DB_CHECK=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PWD" -h "$MYSQL_HOST" -e "SELECT 1" "$MYSQL_DB" 2>/dev/null && echo "ok" || echo "fail")
check "MySQL 连接 ($MYSQL_USER@$MYSQL_HOST/$MYSQL_DB)" "$([ "$DB_CHECK" = "ok" ] && echo pass || echo fail)"

# 数据表检查
if [ "$DB_CHECK" = "ok" ]; then
    TABLE_COUNT=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PWD" -h "$MYSQL_HOST" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DB'" -sN "$MYSQL_DB" 2>/dev/null || echo "0")
    check "数据表数量 (${TABLE_COUNT})" "$([ "$TABLE_COUNT" -ge 10 ] && echo pass || echo warn)" "预期至少 10 张表"

    # 连接数
    CONNECTIONS=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PWD" -h "$MYSQL_HOST" -e "SHOW STATUS LIKE 'Threads_connected'" -sN "$MYSQL_DB" 2>/dev/null | awk '{print $2}' || echo "?")
    check "MySQL 活跃连接数 (${CONNECTIONS})" "pass"
fi

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 3. Redis 连通性检查
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【Redis 缓存】"

REDIS_ACTIVE=$(systemctl is-active redis 2>/dev/null || systemctl is-active redis-server 2>/dev/null || echo "unknown")
check "Redis 服务状态" "$([ "$REDIS_ACTIVE" = "active" ] && echo pass || echo warn)" "systemctl status: $REDIS_ACTIVE"

# Redis ping
REDIS_HOST="${AUTOPS_REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${AUTOPS_REDIS_PORT:-6379}"
REDIS_PING=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null || echo "FAIL")
check "Redis PING ($REDIS_HOST:$REDIS_PORT)" "$([ "$REDIS_PING" = "PONG" ] && echo pass || echo fail)"

# Redis 内存使用
if [ "$REDIS_PING" = "PONG" ]; then
    REDIS_MEM=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info memory 2>/dev/null | grep used_memory_human | awk -F: '{print $2}' | tr -d '\r' || echo "?")
    REDIS_KEYS=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" dbsize 2>/dev/null | awk '{print $2}' || echo "?")
    check "Redis 内存使用 (${REDIS_MEM})" "pass"
    check "Redis 键数量 (${REDIS_KEYS})" "pass"
fi

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 4. 后端 Health 端点检查
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【后端 API】"

HEALTH=$(curl -sf --max-time 5 "${API_BASE}/health" 2>/dev/null || echo "")
check "/health 端点" "$([ -n "$HEALTH" ] && echo pass || echo fail)"

if [ -n "$HEALTH" ]; then
    # 提取状态
    HEALTH_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
    check "Health 状态: ${HEALTH_STATUS:-N/A}" "$([ "$HEALTH_STATUS" = "ok" ] || [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "UP" ] && echo pass || echo warn)"
fi

READY=$(curl -sf --max-time 5 "${API_BASE}/ready" 2>/dev/null || echo "")
check "/ready 端点" "$([ -n "$READY" ] && echo pass || echo warn)"

# API 响应时间
API_START=$(date +%s%N)
curl -sf --max-time 5 "${API_BASE}/api/v1/health" -o /dev/null 2>/dev/null || true
API_END=$(date +%s%N)
API_MS=$(( (API_END - API_START) / 1000000 ))
check "API 响应时间 (${API_MS}ms)" "$([ "$API_MS" -lt 3000 ] && echo pass || echo warn)" "阈值: 3000ms"

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 5. 前端静态文件检查
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【前端静态文件】"

FRONTEND_DIR="$PROJECT_DIR/frontend/dist"
if [ -d "$FRONTEND_DIR" ]; then
    check "前端 dist 目录" "pass" "$FRONTEND_DIR"

    # 检查 index.html
    check "index.html 存在" "$([ -f "$FRONTEND_DIR/index.html" ] && echo pass || echo fail)"

    # 检查 assets 目录
    ASSET_COUNT=$(ls "$FRONTEND_DIR/assets/" 2>/dev/null | wc -l || echo "0")
    check "静态资源文件 (${ASSET_COUNT} 个)" "$([ "$ASSET_COUNT" -gt 0 ] && echo pass || echo warn)"

    # 检查 nginx 配置
    if [ -f "/etc/nginx/conf.d/autops.conf" ]; then
        check "nginx 配置文件" "pass" "/etc/nginx/conf.d/autops.conf"
        NGINX_OK=$(nginx -t 2>&1 | grep -c "successful" || echo "0")
        check "nginx 配置语法" "$([ "$NGINX_OK" -ge 1 ] && echo pass || echo fail)"
    else
        check "nginx 配置文件" "warn" "未找到 /etc/nginx/conf.d/autops.conf"
    fi

    # 通过 nginx 检查前端可达性
    if command -v nginx &>/dev/null; then
        FRONTEND_HTTP=$(curl -sf --max-time 3 http://localhost/ -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")
        check "前端 HTTP 访问 (状态码: $FRONTEND_HTTP)" "$([ "$FRONTEND_HTTP" = "200" ] && echo pass || echo warn)"
    fi
else
    check "前端 dist 目录" "warn" "$FRONTEND_DIR 不存在"
fi

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 6. 服务状态
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【服务状态】"

SYSTEMD_ACTIVE=$(systemctl is-active autops-backend 2>/dev/null || echo "unknown")
check "autops-backend 服务" "$([ "$SYSTEMD_ACTIVE" = "active" ] && echo pass || echo fail)"

# 检查进程
BACKEND_PID=$(pgrep -f "uvicorn app.main:app" 2>/dev/null || echo "")
check "后端进程 (PID: ${BACKEND_PID:-无})" "$([ -n "$BACKEND_PID" ] && echo pass || echo warn)"

# 检查端口监听
PORT_CHECK=$(ss -tlnp 2>/dev/null | grep ':8001' || echo "")
check "端口 8001 监听" "$([ -n "$PORT_CHECK" ] && echo pass || echo fail)"

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 7. 数据完整性检查 (可选，依赖API)
# ============================================================
if [ -n "$HEALTH" ]; then
    [ "$QUIET_MODE" = false ] && echo "【数据完整性】"

    ALERT_RULES=$(curl -sf "${API_BASE}/api/v1/alert-rules" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null || echo "0")
    check "告警规则 (${ALERT_RULES} 条)" "$([ "$ALERT_RULES" -ge 8 ] && echo pass || echo warn)"

    POLICIES=$(curl -sf "${API_BASE}/api/v1/policies" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('items',[])))" 2>/dev/null || echo "0")
    check "策略 (${POLICIES} 条)" "$([ "$POLICIES" -ge 4 ] && echo pass || echo warn)"

    SCRIPTS=$(curl -sf "${API_BASE}/api/v1/scripts" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('items',[])))" 2>/dev/null || echo "0")
    check "脚本 (${SCRIPTS} 个)" "$([ "$SCRIPTS" -ge 4 ] && echo pass || echo warn)"

    [ "$QUIET_MODE" = false ] && echo ""
fi

# ============================================================
# 8. 安全检查
# ============================================================
[ "$QUIET_MODE" = false ] && echo "【安全检查】"

# .env 文件权限
ENV_FILE="$PROJECT_DIR/backend/.env"
if [ -f "$ENV_FILE" ]; then
    ENV_PERM=$(stat -c %a "$ENV_FILE" 2>/dev/null || echo "???")
    check ".env 文件权限 ($ENV_PERM)" "$(echo "$ENV_PERM" | grep -qE '^600|^400' && echo pass || echo warn)" "建议: chmod 600"
else
    check ".env 文件" "warn" "未找到 $ENV_FILE"
fi

# 凭证加密检查
if [ "$DB_CHECK" = "ok" ]; then
    PLAINTEXT_CREDS=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PWD" -h "$MYSQL_HOST" -e "SELECT COUNT(*) FROM credential WHERE encrypted_data IS NULL OR encrypted_data=''" -sN "$MYSQL_DB" 2>/dev/null || echo "0")
    check "凭证加密检查" "$([ "$PLAINTEXT_CREDS" = "0" ] && echo pass || echo fail)"
fi

[ "$QUIET_MODE" = false ] && echo ""

# ============================================================
# 汇总
# ============================================================
if [ "$JSON_OUTPUT" = true ]; then
    echo "{\"checks\":[$(IFS=,; echo "${RESULTS[*]}")],\"pass\":$PASS,\"warn\":$WARN,\"fail\":$FAIL,\"exit_code\":$([ "$FAIL" -eq 0 ] && echo 0 || echo 1)}"
    exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
fi

echo "========================================"
echo -e "  检查结果: ${GREEN}${PASS} 通过${NC}  ${YELLOW}${WARN} 警告${NC}  ${RED}${FAIL} 失败${NC}"
echo "========================================"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "  ⚠️  发现 ${FAIL} 个失败项，请检查上方详情"
    echo "  查看后端日志: journalctl -u autops-backend -n 100"
    echo ""
fi

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
