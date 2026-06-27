# 部署实测评审逐条评估与处置（2026-06-27）

针对外部部署小组的实测材料（IMPROVEMENTS.md / E2E / 资产发现实测）逐条核对合理性并处置。

## A.1 致命（P0）
| 项 | 结论 | 处置 |
|---|---|---|
| A.1.1 `event_outbox.id` 无默认值 + INSERT 漏传 id | **成立（致命）** | **已修**：`events._persist_to_outbox` INSERT 显式传 `id=uuid`。否则 MySQL 严格模式 1364，所有事件发布失败、业务事务连带回滚。 |
| A.1.2 `GovernanceService` 缺失 | **成立** | **已修**：补 `GovernanceService.create_audit_log`（写 audit_logs，容错）。`governance/handlers` 以 subscribe_all 落审计，此前每事件 ImportError。 |
| A.1.3 Worker Runner 未启动 | **成立（部署遗漏）** | 代码侧 `app.workers.runner` 已具备（outbox/scheduler/inspection/execution-worker/heartbeat）。属部署编排，建议随包提供 systemd unit（材料已含）。 |
| A.1.4 Qwen3.6 MTP + llama.cpp chat 返回空 | **成立（环境相关）** | **已修**：`LLMClient` chat 返回空内容时降级 `/completions` + 手工 ChatML。 |

## A.2 业务（P1）
| 项 | 结论 | 处置 |
|---|---|---|
| A.2.1 super_admin `*:*` 裸串 → /auth/me 500 | 成立 | 此前已修（`RoleResponse._coerce_permissions` 容错）。 |
| A.2.2 `HTTPBearer(auto=False)` | 成立 | 此前已修（`auto_error=False`）。 |
| A.2.3 App.vue 未登录 401 风暴 | 成立 | 此前已修（未登录只渲染 router-view）。 |
| A.2.4 子菜单默认折叠 | 成立 | 此前已修（default-openeds）。 |
| A.2.5 alembic 迁移幂等 | 部分 | 0009–0012 均带 `inspector` 守卫；早期 0001 用 create_all(checkfirst) 幂等。其余如需可补，风险低收益小。 |

## A.3 UI（P2）
| 项 | 结论 | 处置 |
|---|---|---|
| A.3.1 发现页协议无说明 + 单选 | **成立** | **已修**：协议改多选 checkbox + `el-tooltip` 说明；**并修正大小写 bug**（前端发 `ICMP`，后端按 `icmp` 匹配 → ICMP 扫描被静默跳过）；默认 `['icmp','tcp']`。 |
| A.3.2 模板 duplicate class build 失败 / A.3.3 tsconfig | 需 CI 复核 | 本环境无 node_modules，未复现；建议 CI `vue-tsc`+`vite build` 验证。 |

## A.4 配置/安全
| 项 | 结论 | 处置 |
|---|---|---|
| A.4.1 CORS `*`+credentials | 成立 | 此前已修（`*` 时 allow_credentials=False）。 |
| A.4.2 凭证 key 明文 .env | 合理（增强） | 受理待办（keyring/Vault），属基建。 |
| A.4.3 AsyncSession IllegalStateChange | 已知 | get_db 无条件 commit（已注释 P3）。 |

## B 设计改进
| 项 | 结论 | 处置 |
|---|---|---|
| B.1 发现模块（模板/协议/端口策略） | **合理；大部分已实现** | `discovery-templates` 已有完整 CRUD+toggle 并注册；本次补 **任务引用模板**：`discovery_tasks.template_id`（迁移 0012）+ `create_task` 从模板继承 protocols/ports/凭据/超时；前端创建对话框加“发现模板”选择器。**未做（受理）**：每协议独立 timeout/retry/concurrency 的 `protocol_config`、port_strategy(top-100/all/custom)、BuiltinCollectorRegistry 按协议拆分——属较大重构，建议在可运行环境分阶段做。 |
| B.2 outbox 死信队列/优先级 | 合理 | 受理待办（DLQ 表 + 按 priority 拉取）。 |
| B.3 LLM 稳定性（vLLM/GPU/流式） | 合理 | 短期 fallback 已做；中长期 vLLM/GPU 属部署演进。 |
| B.4 DB 高可用 / B.5 可观测（Prometheus/Loki/Grafana） | 合理 | 受理待办，属生产化基建，按路线图推进。 |

## A.5 行为澄清（非 bug）
- 重复 IP 扫描标 `ignored`：by design；建议 UI 文案区分 `already_onboarded`（小改，待办）。
- API 字段是 `ip` 非 `ip_address`：本会话已统一前端字段（拓扑/纳管已改 `ip`）。

## 验证
- 后端 `py_compile` + `ruff -F` 通过；迁移链 head → `0012_discovery_task_template`（部署 `alembic upgrade head`）。
- 前端本环境无 node_modules，未跑 vue-tsc/build，须 CI 复核（尤其 A.3.2/A.3.3）。
