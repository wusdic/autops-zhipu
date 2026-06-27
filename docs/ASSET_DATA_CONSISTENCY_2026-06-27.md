# 「资源/资产」数据一致性审计与整改（2026-06-27）

针对"资源已存在但部分页面不显示/显示不一致"，对资产实体做端到端核对：
确认**单一数据源**，统一字段语义，修复前后端契约漂移。

## 1. 单一数据源（后端，已确认一致）
- 所有资产读写都走同一张 `assets` 表；列表/计数/搜索/业务系统/拓扑/仪表盘
  全部带 `is_deleted = False` 过滤（`repository.search`、`dashboard.py`、
  `business_systems.py`、`search.py` 一致）。后端不是不一致来源。
- 列表权威出参 `GET /assets` → `_to_dict()`。

## 2. 字段契约（canonical，前端必须按此读取）
| 字段 | 含义 | 取值 |
|---|---|---|
| `id` `name` `hostname` | 标识 | - |
| `asset_type` | 类型（非 `type`） | linux_server/windows_server/database/... |
| `ip` | 地址（**非 `ip_address`**） | - |
| `os_type` `os_version` | 系统（**非 `os_info`**） | - |
| `status` | **生命周期** | active / inactive / maintenance / decommissioned |
| `reachability` | **在线性** | reachable / unreachable / unknown |
| `health_status` | 健康度 | healthy / warning / critical / unknown |
| `business_system` `environment` `location` `tags` | 归属 | - |

## 3. 本轮修复的不一致点
1. **响应包裹错位（恒空的根因）**：Pinia `asset/ticket/alert/knowledge/inspection/execution`
   store 与 `useTableData` 把 `res.data`（信封 `{code,message,data}`）当负载读，
   `res.data.items` 永远 undefined。改为 `res.data.data.items`。
2. **`status` 语义被污染（筛选/展示不一致的根因）**：巡检 ping 与发现纳管把
   `online/offline` 写进了 `status`，而 `status` 应是生命周期、在线性应在
   `reachability`。导致自动纳管的资产 `status="online"`，被资产列表"活跃(active)"
   筛选排除、状态标签显示空白。
   - 修复：ping 调度器改写 `reachability`（不再覆盖 `status`）；发现纳管/导入设
     `status="active"` + `reachability`；新增迁移 `0011` 归一存量数据。
3. **字段名漂移**：
   - 发现纳管向导 POST `ip_address`/`os_info` → 后端 `AssetCreate` 只认 `ip`/`os_type`，
     导致纳管出的资产**无 IP/系统**。已改对齐。
   - 拓扑页读 `node.ip_address` → 资产无此字段，IP 显示空白。已改 `node.ip`。
4. **搜索参数契约**：`AssetSelector`/`PolicySimulate`/`TicketCreate` 发 `keyword`，
   后端只认 `search`。已让后端兼容 `keyword`（回落 `search`）。
5. 资产列表 `statusLabel/statusType` 容错生命周期+历史在线性取值；可达性列标签完善。

## 4. 建议（后续，未做）
- 前端已有统一标签库 `src/shared/utils/labels.ts`（含 status/health/online 映射），
  但**各页面仍各自定义** `statusLabel/statusType`。建议逐步收敛到 labels.ts，
  彻底消除"每页一套映射"的展示不一致。
- 同样的"单一数据源 + 字段契约 + 取值容错"审计，建议对 告警/工单/执行 等实体复用本范式。

## 5. 验证
- 后端 `py_compile` + `ruff -F` 通过；迁移链 head → `0011_normalize_asset_status`
  （部署需 `alembic upgrade head`）。
- 前端本环境无 `node_modules`，未跑 vue-tsc/build，须在 CI 复核。
