# 代码 ↔ 文档一致性核对（0.7.0，2026-06-26）

本文件记录 0.7.0 一系列改动后的文档同步与一致性核对结果。

## 1. 已同步更新的"活文档"
| 文档 | 更新内容 |
|---|---|
| `CHANGELOG.md` | 新增 `[0.7.0]` 全量条目（深度采集/巡检/报告、SSH 执行器、平台与 AI 补齐、契约修复、迁移 0005–0009） |
| `README.md` | 统计修正（表 36→47、端点 145+→300+、页面/路由→124/127）；技术栈补充 asyncssh/pysnmp/pywinrm、执行器开关、alembic 提示 |
| `docs/03-api/API_CONTRACT.md` | 附录 A：0.7.0 新增端点（AI/模型服务/巡检规则/触发历史/平台/导出/附件/补齐端点） |
| `docs/01-architecture/DATA_ARCHITECTURE.md` | 附录 A：0.7.0 新增 11 张表 + 1 列（迁移 0005–0009） |
| `docs/01-architecture/adr/ADR-0003-command-execution-security.md` | SSHExecutor 标记为已实现 |
| `.env.example` | 新增 `AUTOPS_EXECUTOR` 与 4 个产物目录环境变量、模型服务页提示 |

## 2. 代码事实（核对基准）
- 后端路由装饰器：**323**（`@*_router.(get|post|put|delete|patch)`）。
- 迁移链 head：**`0009_trigger_history`**（0001→0002→0003→943f→1027→0004→0005→0006→0007→0008→0009）。
- 新增依赖：`pyproject.toml` 已含 `asyncssh>=2.14`、`pysnmp>=6.1`、`pywinrm>=0.4.3`（均懒加载）。
- 执行器：`automation/service._get_executor()` 按 `AUTOPS_EXECUTOR` 选择 `SSHExecutor`/`LocalDevExecutor`。

## 3. 历史快照类文档（**有意不改写**，仅在此标注其为旧状态）
以下文档是带"反向同步时间/审计时间"的**历史快照**，描述的是当时状态；其中的 mock/缺失描述已被后续版本修复。保留作为演进记录，不逐字回改：
| 文档 | 旧表述 | 现状 |
|---|---|---|
| `docs/05-implementation/BACKEND_DEEP_AUDIT_REPORT.md` | discovery `create_task` 返回 mock、备份 mock 等 | 均已实现真实逻辑（发现扫描、备份落库、导出等） |
| `docs/05-implementation/EXECUTION_ENGINES_DESIGN.md` | discovery mock、SSHExecutor 待建 | 已实现 discovery 真实扫描与 SSHExecutor |
| `docs/05-implementation/GAP_ANALYSIS_REPORT.md` | "36 表 / 145 端点 / 38 页" | 现为 47 表 / 300+ 端点 / 124 页（见 README） |
| `docs/04-frontend/FRONTEND_AUDIT_REPORT.md` | 指标趋势等用 mock | 多数已接真实 API（详见 `FRONTEND_PAGE_COMPLETENESS.md`） |

> 这些是"报告/设计"类文档（dated snapshot），权威现状以 README/CHANGELOG/API_CONTRACT/DATA_ARCHITECTURE + 代码为准。

## 4. 本会话产出的现状类文档（与代码一致）
- `docs/DEVICE_INSPECTION_REPORTING.md` — 深度采集/巡检/报告使用说明
- `docs/FRONTEND_PAGE_FUNCTIONAL_AUDIT.md` — 124 页接线审计
- `docs/FRONTEND_PAGE_COMPLETENESS.md` — 逐页功能完整性（剩余缺口）
- `docs/CODE_REVIEW_FINDINGS.md` / `CODE_REVIEW_CONSOLIDATED_PLAN.md` — 审查与整改

## 5. 已知仍存在的"文档/实现"差距（需后续）
- **主机升级/回滚**：`UpgradeMaintenancePage` 仍为演示模式（升级历史可读，真实执行未做）——属运维基建，待定方案。
- **多租户**：有 `tenants` 表与管理页，但核心业务表无 `tenant_id`，**无行级隔离**（伪多租户）；如纳入目标需补租户维度。
- 历史快照文档（§3）若要求"全量一致"，建议统一加 `> 状态：snapshot/outdated` 头标，或归档到 `docs/_archive/`。

## 6. 部署须知（与迁移一致）
- 升级后必须 `alembic upgrade head`（本版本含 0005–0009）；docker-compose 的 `migrate` 服务会自动执行。
- 设备采集/SSH 执行依赖 asyncssh/pysnmp/pywinrm，离线包需一并打入。
