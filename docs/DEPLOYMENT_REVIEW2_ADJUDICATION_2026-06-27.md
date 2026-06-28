# 第二轮部署评审（R1–R15 + 前端审计）逐条评估与处置（2026-06-27）

针对部署小组第二轮材料（IMPROVEMENTS 第二/三/四轮 R1–R15 + AUDIT_FRONTEND_ISSUES）
逐条核对（基线版本不同，部分已在本仓修过）。

## 已修复（本次）
| 项 | 结论 | 处置 |
|---|---|---|
| R1/B4 tags.forEach（tags 是 JSON 字符串） | 成立 | 后端 `_to_dict` 用 `_parse_tags` 统一返回 list（单点修复所有消费方）；前端 AssetList/AssetRangeSelector 加 `Array.isArray` 防御。 |
| R2/R3/F4 `page_size` le=100 → 422 | 成立 | 资产 API 三处上限改 `le=500`。 |
| B1 业务系统 0 资产显示“健康” | 成立 | 新建默认 `health/reachability=unknown`；列表按**成员资产实时聚合**健康度 + 返回 `asset_count`。 |
| R4/B2 state_snapshots 始终 0 | 成立 | `run_collection_for_asset` 每条采集结果同步写 `StateSnapshot`（normal/critical）。 |
| R7/U3 资产健康写死、不反映真实 | 成立 | 新增 `AssetService.refresh_status_from_snapshots/refresh_all_statuses`，采集后自动刷新；端点 `POST /assets/{id}/refresh-status`、`POST /assets/refresh-all-statuses`。 |
| R9/F3/B3 资产报告顶部统计/类型分布全 0 | 成立 | `/dashboard/stats` 增 `asset_stats`（total/online/offline/abnormal/today_new/type_distribution，按 reachability/health 聚合）。 |
| R13 trigger_collection 在 API 进程跑（无 CAP_NET_RAW） | 成立 | 改发 `FULL_SCAN_REQUESTED` 事件，Worker 进程消费执行（与 P1-07 一致）。 |
| R14 `_run_all_assets` 提前 break | 成立 | 删除 `if not self._running: break`，支持一次性手动触发跑完全部资产。 |

## 已在本仓修复（本次核对确认，无需再改）
| 项 | 说明 |
|---|---|
| R1(审计)/R6 `/dashboard/asset-discovery` 菜单 404 | 侧边栏已指向 `/resources/discovery`。 |
| F1 手动新建资产 | `POST /assets` 已具备（去重 + 触发 ASSET_CREATED 采集）；前端“新建资产”按钮调它。无需 `/assets/manual` 别名。 |
| 第一轮 A.1.1/A.1.2/A.1.4 等 | 上一轮已修（outbox id / GovernanceService / LLM 降级）。 |

## R5（缺失外键导致 worker 崩）
- **环境相关**：评审基于其本地 0001 `create_all` 漏建 FK。本仓 collector 模型如声明 FK 而库未建会不一致。**受理**：建议在可运行 DB 环境用 autogenerate 对齐 FK（不盲加迁移，避免与现有库冲突）。

## R12（systemd CAP_NET_RAW）
- **部署配置**，非代码。建议随包提供 worker.service：
  `AmbientCapabilities=CAP_NET_RAW CAP_NET_BIND_SERVICE` + `NoNewPrivileges=false`。

## 受理待办（合理但属较大重构/基建）
- D1/D2/F2/R10 业务系统拆独立表 + `business_system_assets` 多对多 + `business_system_id` FK + 关联管理 UI（架构重构，影响面大）。
- 前端路由/菜单去重（R2 审计）；空状态“去新建”引导（U1/U2）。
- B.2 outbox DLQ/优先级（消费者已有 retry+dead+priority 排序，DLQ 表可后补）。

## 验证
- 后端 `py_compile` + `ruff -F` 通过（仅 1 处既有 F841，非本次引入）。
- 迁移 head 仍 `0012`（本轮无新迁移；R4/R7 复用既有 state_snapshots 表）。
- 前端本环境无 node_modules，未跑 vue-tsc/build，须 CI 复核。
