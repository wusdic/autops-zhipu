# AUTOPS 升级与回滚

> 文档状态：current
> 建议路径：`docs/06-operations/UPGRADE_AND_ROLLBACK.md`

---

## 1. 升级

```bash
./deploy/scripts/upgrade.sh
```

### 流程

1. 版本兼容性检查
2. 升级前自动备份（数据库+配置）
3. 停止服务
4. 加载新版本镜像/代码
5. 执行数据库迁移（`alembic upgrade head`，会应用到最新 head，含 `0004_discovery_auto_onboard` 等）
6. 配置差异合并（保留自定义配置）
7. 启动服务
8. 自动自检
9. 输出升级结果

### 注意事项

- 升级前确认备份完成
- 升级到含 `0004_discovery_auto_onboard` 的版本时，会为 `discovery_tasks` 表新增 `auto_onboard` 列（默认 true）
- 大版本升级注意破坏性变更说明
- 升级期间服务不可用

## 2. 回滚

```bash
./deploy/scripts/rollback.sh
```

### 流程

1. 确认回滚版本
2. 停止当前服务
3. 恢复数据库备份
4. 恢复配置文件
5. 加载旧版本镜像/代码
6. 启动服务
7. 健康检查

### 注意事项

- 只能回滚到已备份的版本
- 若回滚跨越 `0004_discovery_auto_onboard` 迁移，需先手动 `alembic downgrade` 该迁移（删除 `auto_onboard` 列）再降级代码
- 回滚后数据可能丢失（升级后的变更）

