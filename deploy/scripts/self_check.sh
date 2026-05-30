#!/bin/bash
# AUTOPS 平台自检脚本
# 检查所有组件健康状态
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "pass" ]; then
        echo -e "  ${GREEN}✅${NC} $name"
        PASS=$((PASS + 1))
    elif [ "$result" = "warn" ]; then
        echo -e "  ${YELLOW}⚠️${NC} $name"
        WARN=$((WARN + 1))
    else
        echo -e "  ${RED}❌${NC} $name"
        FAIL=$((FAIL + 1))
    fi
}

API_BASE="${AUTOPS_URL:-http://localhost:8001}"

echo "========================================"
echo "  AUTOPS 平台自检"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. 系统检查
echo "【系统资源】"
CPU_USAGE=$(grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {printf "%.0f", usage}')
MEM_USAGE=$(free | grep -i -E 'mem|内存' | awk '{printf "%.0f", $3/$2*100}')
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')

check "CPU 使用率 ${CPU_USAGE}%" "$([ "$CPU_USAGE" -lt 90 ] && echo pass || echo warn)"
check "内存使用率 ${MEM_USAGE}%" "$([ "$MEM_USAGE" -lt 90 ] && echo pass || echo warn)"
check "磁盘使用率 ${DISK_USAGE}%" "$([ "$DISK_USAGE" -lt 85 ] && echo pass || echo warn)"
echo ""

# 2. 服务检查
echo "【服务状态】"
SYSTEMD_ACTIVE=$(systemctl is-active autops-backend 2>/dev/null || echo "unknown")
check "autops-backend 服务" "$([ "$SYSTEMD_ACTIVE" = "active" ] && echo pass || echo fail)"

MYSQL_ACTIVE=$(systemctl is-active mysql 2>/dev/null || systemctl is-active mysqld 2>/dev/null || echo "unknown")
check "MySQL 服务" "$([ "$MYSQL_ACTIVE" = "active" ] && echo pass || echo fail)"

REDIS_ACTIVE=$(systemctl is-active redis 2>/dev/null || systemctl is-active redis-server 2>/dev/null || echo "unknown")
check "Redis 服务" "$([ "$REDIS_ACTIVE" = "active" ] && echo pass || echo warn)"
echo ""

# 3. API 健康检查
echo "【API 检查】"
HEALTH=$(curl -sf "${API_BASE}/health" 2>/dev/null || echo "")
check "/health 端点" "$([ -n "$HEALTH" ] && echo pass || echo fail)"

READY=$(curl -sf "${API_BASE}/ready" 2>/dev/null || echo "")
check "/ready 端点" "$([ -n "$READY" ] && echo pass || echo fail)"
echo ""

# 4. 数据库连接
echo "【数据库连接】"
DB_CHECK=$(mysql -u autops -pautops_2026 -h 127.0.0.1 -e "SELECT 1" autops 2>/dev/null && echo "ok" || echo "fail")
check "MySQL 连接" "$([ "$DB_CHECK" = "ok" ] && echo pass || echo fail)"

TABLE_COUNT=$(mysql -u autops -pautops_2026 -h 127.0.0.1 -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='autops'" -sN autops 2>/dev/null || echo "0")
check "数据表数量 (${TABLE_COUNT})" "$([ "$TABLE_COUNT" -ge 30 ] && echo pass || echo warn)"
echo ""

# 5. 数据完整性
echo "【数据完整性】"
ALERT_RULES=$(curl -sf "${API_BASE}/api/v1/alert-rules" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null || echo "0")
check "告警规则 (${ALERT_RULES} 条)" "$([ "$ALERT_RULES" -ge 8 ] && echo pass || echo warn)"

POLICIES=$(curl -sf "${API_BASE}/api/v1/policies" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('items',[])))" 2>/dev/null || echo "0")
check "策略 (${POLICIES} 条)" "$([ "$POLICIES" -ge 4 ] && echo pass || echo warn)"

SCRIPTS=$(curl -sf "${API_BASE}/api/v1/scripts" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('items',[])))" 2>/dev/null || echo "0")
check "脚本 (${SCRIPTS} 个)" "$([ "$SCRIPTS" -ge 4 ] && echo pass || echo warn)"
echo ""

# 6. 安全检查
echo "【安全检查】"
CHECK_ENV=$(grep -r "password\|secret\|key" "${AUTOPS_HOME:-/home/zcxx/autops}/backend/.env" 2>/dev/null | grep -v "^#" | wc -l || echo "0")
check ".env 文件权限" "$(stat -c %a "${AUTOPS_HOME:-/home/zcxx/autops}/backend/.env" 2>/dev/null | grep -q '^600' && echo pass || echo warn)"

# 检查是否有未加密的凭证
PLAINTEXT_CREDS=$(mysql -u autops -pautops_2026 -h 127.0.0.1 -e "SELECT COUNT(*) FROM credential WHERE encrypted_data IS NULL OR encrypted_data=''" -sN autops 2>/dev/null || echo "0")
check "凭证加密检查" "$([ "$PLAINTEXT_CREDS" = "0" ] && echo pass || echo fail)"
echo ""

# 汇总
echo "========================================"
echo -e "  检查结果: ${GREEN}${PASS} 通过${NC}  ${YELLOW}${WARN} 警告${NC}  ${RED}${FAIL} 失败${NC}"
echo "========================================"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
