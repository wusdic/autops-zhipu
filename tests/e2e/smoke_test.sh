#!/bin/bash
# AUTOPS E2E Smoke Test — 验证所有核心API端点
set -e

BASE="http://localhost:8001/api/v1"
PASS=0
FAIL=0

check() {
    local name="$1"
    local method="${2:-GET}"
    local url="$3"
    local expected="${4:-200}"
    local status
    if [ "$method" = "POST" ]; then
        status=$(curl -sf -o /dev/null -w '%{http_code}' -X POST "$url" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 2>/dev/null || echo "000")
    else
        status=$(curl -sf -o /dev/null -w '%{http_code}' "$url" -H "Authorization: Bearer $TOKEN" 2>/dev/null || echo "000")
    fi
    if [ "$status" = "$expected" ]; then
        echo "  ✅ $name ($status)"
        PASS=$((PASS+1))
    else
        echo "  ❌ $name (got $status, expected $expected)"
        FAIL=$((FAIL+1))
    fi
}

echo "=== AUTOPS E2E Smoke Test ==="
echo ""

# 1. Infrastructure
echo "--- Infrastructure ---"
curl -sf http://localhost:8001/health > /dev/null && { echo "  ✅ Health"; PASS=$((PASS+1)); } || { echo "  ❌ Health"; FAIL=$((FAIL+1)); }
curl -sf http://localhost:8001/ready > /dev/null && { echo "  ✅ Ready (DB+Redis)"; PASS=$((PASS+1)); } || { echo "  ❌ Ready"; FAIL=$((FAIL+1)); }

# 2. Auth
echo ""
echo "--- Auth ---"
TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null)
if [ -n "$TOKEN" ]; then
    echo "  ✅ Login"
    PASS=$((PASS+1))
else
    echo "  ❌ Login failed"
    FAIL=$((FAIL+1))
    exit 1
fi

# 3. Asset Center
echo ""
echo "--- Asset Center ---"
check "Assets" GET "$BASE/assets"
check "Asset Groups" GET "$BASE/asset-groups"
check "Discovery Tasks" GET "$BASE/discovery/tasks"

# 4. Config & Credentials
echo ""
echo "--- Config & Credentials ---"
check "Config Definitions" GET "$BASE/configs/definitions"
check "Credentials" GET "$BASE/credentials"

# 5. Collector & State
echo ""
echo "--- Collector & State ---"
check "Collectors" GET "$BASE/collectors"
check "Collection Jobs" GET "$BASE/collection-jobs"
check "State Changes" GET "$BASE/states/changes"
check "State Snapshots (POST)" POST "$BASE/states/snapshots"

# 6. Event & Alert
echo ""
echo "--- Event & Alert ---"
check "Events" GET "$BASE/events"
check "Alerts" GET "$BASE/alerts"
check "Alert Stats" GET "$BASE/alerts/stats/overview"
check "Alert Rules" GET "$BASE/alert-rules"

# 7. Policy & Automation
echo ""
echo "--- Policy & Automation ---"
check "Policies" GET "$BASE/policies"
check "Executions" GET "$BASE/executions"
check "Scripts" GET "$BASE/scripts"
check "Playbooks" GET "$BASE/playbooks"

# 8. AIops & Knowledge
echo ""
echo "--- AIops & Knowledge ---"
check "AIops Health" GET "$BASE/aiops/health"
check "Knowledge" GET "$BASE/knowledge"
check "Knowledge Stats" GET "$BASE/knowledge/stats"

# 9. Ticket
echo ""
echo "--- Ticket Center ---"
check "Tickets" GET "$BASE/tickets"

# 10. Governance
echo ""
echo "--- Governance ---"
check "Users" GET "$BASE/users"
check "Roles" GET "$BASE/roles"
check "API Keys" GET "$BASE/api-keys"
check "Audit Logs" GET "$BASE/audit-logs"

# 11. Notifications
echo ""
echo "--- Notifications ---"
check "Notifications" GET "$BASE/notifications"

# 12. Platform
echo ""
echo "--- Platform ---"
check "Platform Status" GET "$BASE/platform/status"
check "Backup Settings" GET "$BASE/backups/settings"

# Summary
TOTAL=$((PASS+FAIL))
echo ""
echo "=== Results: $PASS/$TOTAL passed ==="
[ "$FAIL" -eq 0 ] && echo "🎉 All checks passed!" || echo "⚠️  $FAIL checks failed"
exit $FAIL
