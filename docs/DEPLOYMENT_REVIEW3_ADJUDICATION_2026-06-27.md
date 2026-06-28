# 第三轮部署评审（第六轮材料 R26–R32）评估与处置（2026-06-27）

材料（bf1c8778 / 3db2db55 两包，内容基本相同，后者多"第六轮"LLM 部署章节 + autops-llm-small.service）
聚焦本地 LLM 部署与并发，大部分为**运维/部署操作**，少量为**代码级生产改进**。逐条核对：

## 已在本仓修复（前几轮已处置，本次核对确认）
| 项 | 说明 |
|---|---|
| 3 个 P0（outbox id / GovernanceService / worker 进程） | 前几轮已修；worker systemd 已随 install.sh 提供 |
| 13 项健康检查 | 已实现 `GET /platform/diagnostics`（三级告警，含 worker 存活/磁盘/数据完整性） |
| logrotate / systemd | 已提供 deploy/systemd/*.service + autops.logrotate |
| B.1 资产发现重构（协议 UX/模板可应用/大小写） | 前几轮已处置 |

## 本次采纳并实现（代码级，合理）
| 项 | 结论 | 处置 |
|---|---|---|
| R27 AI 诊断 30s 硬超时 | 成立 | `aiops/service.py` 两处 `timeout=30` → 改为 `_llm_timeout(config)`（config.llm.timeout，默认 300s）；agent `llm_client._load_llm_timeout` 默认 30→180s；`max_tokens` 1024→512 |
| R31 大小模型智能路由 + fallback | 成立（优秀生产设计） | `aiops/service.py` 新增 `_llm_endpoints`（按 prompt 长度路由）+ `_chat_completion`（依序尝试、ConnectError 回退、全挂降级）。**端点由环境变量配置，不硬编码部署 URL**：`SMALL_LLM_URL` / `SMALL_LLM_MODEL` / `SMALL_LLM_PROMPT_THRESHOLD`(默认300) |
| R32 小模型 systemd 持久化 | 成立（部署） | 提供模板 `deploy/systemd/autops-llm-small.service`（路径/端口可调，8 slot 并行） |

## 评估为"部署/运维操作"，非代码（不入库）
- R26 Q5 27B 模型下载/切换、R29 GGUF 转换踩坑、R30 小模型启动参数、R28 并发压测：均为部署侧操作与结论，
  代码侧已通过"可配置端点 + 智能路由 + 可配置超时"提供支撑，无需写死。

## 设计说明（整体考虑）
- **不硬编码**评审里的具体本地 URL/模型名/路径，全部走 config 或环境变量，保证本仓在不同部署形态下通用。
- 智能路由对调用方透明：`_call_llm` 与自由问答 `diagnose` 共用 `_chat_completion`，短问答自动走小模型、长上下文走大模型、连接失败自动回退、全部不可达优雅降级。

## 验证
- 后端 `py_compile` + `ruff -F` 通过。
- LLM 路由/超时依赖运行态（需配 SMALL_LLM_* 环境变量与两个 llama-server 端点）才能端到端验证。
