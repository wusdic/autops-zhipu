# AUTOPS 平台自检

> 文档状态：current
> 建议路径：`docs/06-operations/PLATFORM_SELF_CHECK.md`

---

## 1. 自检 API

```
GET /health          # 存活检查
GET /ready           # 就绪检查（DB + Redis + 组件）
GET /api/v1/platform/status  # 全组件状态
POST /api/v1/platform/self-check  # 完整自检
```

## 2. 自检脚本

```bash
./self_check.sh
```

### 检查项

| # | 检查项 | 检查方式 |
|---|---|---|
| 1 | 系统资源 | CPU/内存/磁盘使用率 |
| 2 | 端口监听 | 各服务端口可达性 |
| 3 | 数据库连接 | 连接 + 简单查询 |
| 4 | Redis 连接 | PING |
| 5 | 后端健康 | /health /ready |
| 6 | 前端可达 | HTTP GET |
| 7 | 数据库迁移 | 版本一致性 |
| 8 | 配置完整性 | 必要配置项存在 |
| 9 | 服务进程 | 进程存活 |
| 10 | 日志错误 | 最近 1h ERROR 数 |
| 11 | 证书有效期 | SSL 证书天数 |
| 12 | 安全基线 | 密码策略等 |

## 3. 输出格式

```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": [
    {"name": "mysql", "status": "healthy", "latency_ms": 5},
    {"name": "redis", "status": "healthy", "latency_ms": 1},
    {"name": "vllm", "status": "unhealthy", "error": "connection refused"}
  ],
  "timestamp": "2026-01-01T00:00:00Z"
}
```
