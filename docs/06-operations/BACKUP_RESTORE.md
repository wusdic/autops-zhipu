# AUTOPS 备份与恢复

> 文档状态：current
> 建议路径：`docs/06-operations/BACKUP_RESTORE.md`

---

## 1. 备份方式

目前备份为**手动**方式（通过 API 或脚本）。系统尚未内置自动定时备份调度，如需每日自动备份请自行配置 cron 调用 `backup_restore.sh`。

备份内容：

| 数据 | 方式 |
|---|---|
| MySQL 数据库 | mysqldump（gzip 压缩） |
| Redis | RDB 快照（docker volume） |
| 配置文件 | 文件复制（`configs/`、`.env`） |

## 2. 手动备份

```bash
# 通过 API（需管理员 Token）
POST /api/v1/backups

# 或通过脚本（在项目根目录执行）
./deploy/scripts/backup_restore.sh backup
# 默认备份目录：/opt/autops/backups
# 可通过环境变量 AUTOPS_BACKUP_DIR 覆盖
```

备份文件命名格式：`autops_db_YYYYMMDD_HHMMSS.sql.gz`。

## 3. 恢复

```bash
# 列出可用备份
ls -la /opt/autops/backups/

# 恢复指定备份（传备份文件路径）
./deploy/scripts/backup_restore.sh restore /opt/autops/backups/autops_db_20260101_000000.sql.gz
```

### 恢复流程

1. 停止服务
2. 恢复 MySQL 数据（gunzip + mysql 导入）
3. 恢复 Redis 数据（如需）
4. 恢复配置文件
5. 启动服务
6. 健康检查（`GET /ready`）

> 注意：`backup_restore.sh` 通过 `MYSQL_PWD` 环境变量或 `--defaults-extra-file` 传递数据库密码，不要在命令行以 `-p<password>` 形式暴露密码。
