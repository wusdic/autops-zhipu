# AUTOPS 备份与恢复

> 文档状态：current
> 建议路径：`docs/06-operations/BACKUP_RESTORE.md`

---

## 1. 自动备份

系统每日自动备份，备份内容：

| 数据 | 方式 |
|---|---|
| MySQL 数据库 | mysqldump |
| Redis | RDB 快照 |
| 配置文件 | 文件复制 |
| 执行日志 | 文件复制 |

备份保留 30 天，可在系统配置中调整。

## 2. 手动备份

```bash
# 通过 API
POST /api/v1/platform/backup

# 或通过脚本
./scripts/maintenance/backup.sh
```

## 3. 恢复

```bash
# 列出可用备份
ls -la /data/backups/

# 恢复指定备份
./scripts/maintenance/restore.sh --backup /data/backups/20260101_000000
```

### 恢复流程

1. 停止服务
2. 恢复 MySQL 数据
3. 恢复 Redis 数据
4. 恢复配置文件
5. 启动服务
6. 健康检查
