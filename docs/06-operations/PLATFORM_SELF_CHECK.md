# AUTOPS 平台自检

> 文档状态：current
> 建议路径：`docs/06-operations/PLATFORM_SELF_CHECK.md`

---

## 1. 自检 API

```
GET /health                       # 存活检查，返回 {"status":"alive"}
GET /ready                        # 就绪检查（DB + Redis），返回 status: ready|degraded
GET /api/v1/platform/status       # 全组件状态（需登录）
POST /api/v1/platform/self-check  # 完整自检（需管理员）
```

> 注意：`/health` 返回的 status 值是 `alive`（不是 healthy/ok）。自检脚本中对健康值的判定需匹配。

## 2. 自检脚本

```bash
# 默认输出人类可读格式
./deploy/scripts/self_check.sh

# 输出 JSON 格式
./deploy/scripts/self_check.sh --json

# 静默模式（仅失败时输出）
./deploy/scripts/self_check.sh --quiet
```

脚本依赖环境变量（可用 `AUTOPS_URL`、`AUTOPS_HOME`、`AUTOPS_DB_*` 等覆盖默认值）。

### 检查项（与脚本实际一致）

| # | 检查项 | 检查方式 |
|---|---|---|
| 1 | 系统资源 | CPU/内存/磁盘使用率 |
| 2 | MySQL | 连接 + 简单查询 |
| 3 | Redis | PING |
| 4 | 后端健康 | `/health`、`/ready` |
| 5 | 前端静态文件 | HTTP GET 首页 |
| 6 | 服务端口 | 后端 8001 可达 |
| 7 | 数据完整性 | 告警规则/策略/脚本计数 |
| 8 | 安全 | `.env` 文件权限 + 凭证加密配置 |

## 3. 输出格式（JSON）

```json
{
  "checks": [
    {"name": "system_resources", "status": "pass", "detail": "..."},
    {"name": "mysql", "status": "pass", "detail": "..."},
    {"name": "redis", "status": "warn", "detail": "..."}
  ],
  "pass": 6,
  "warn": 1,
  "fail": 0,
  "exit_code": 0
}
```

`exit_code`：0 = 全部通过，1 = 有 warn，2 = 有 fail。
