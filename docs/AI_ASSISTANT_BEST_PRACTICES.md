# AI 助手 / 大模型调用最佳实践

> 适用范围：`/api/v1/ai/chat`（AI 助手）、`/api/v1/aiops/agent/run`（AI 诊断 Agent）、
> 模型服务（`/api/v1/aiops/agents`）。本文沉淀踩坑结论与正确做法。

## 1. 结论先行：为什么 AI 助手会出现"乱码 / 默认回答 / 复读工具描述"

实测根因（非配置问题，而是协议与模型能力不匹配）：

1. AI 助手早期实现把**每条消息都套进 ReAct 文本协议**（要求模型严格输出
   `Thought: / Action: / Action Input: / Final Answer:`）。
2. 小模型（如 Qwen3.5‑0.8B，尤其 CPU 部署）**指令跟随能力不足**：
   - 漏掉 `Final Answer:`，或幻觉编造 `Action Output:`；
   - 在 `max_tokens` 内复读，甚至**原样复读系统提示里的工具描述**
     （于是用户看到"我有多少资产/有哪些Linux服务器/在线资产数量"——那正是
     `query_assets` 工具的 description 文本）。
3. ReAct 解析器匹配不到关键标签 → 把整段原始输出当答案返回 → 表现为乱码；
   或输出为空 → 返回"（模型未返回内容）"。

**正确做法：用 OpenAI 原生 function calling（tools/tool_calls），不要用 ReAct 文本解析。**

## 2. 现行架构（已落地）

`/api/v1/ai/chat` 流程（`backend/app/api/ai_assistant.py`）：

1. `build_llm_client(db)` 取「模型服务」默认模型（base_url/model/api_key/max_tokens/
   思考模式），回退 env(`LLM_*`)/`llm.yaml`。
2. 组装 `messages = [system, ...最近10轮历史, user]`。
3. 把**只读工具**（`risk_level == read_only`）转成 OpenAI `tools` schema 传给模型。
4. 循环（≤4 轮）：
   - 模型返回 `tool_calls` → 执行对应只读工具，把结果以 `role: tool` 回灌，再问；
   - 模型返回普通 `content` → 即为答案，结束。
5. 普通问题（如 `1+1`）模型不会调用工具，直接回答。
6. **降级**：端点不支持 `tools` 或模型不可用 → 退回纯聊天（仍是真实模型，
   绝不返回硬编码假答案）；再失败 → 明确的降级提示。

只读工具（`backend/app/domains/aiops/tools/readonly.py`）——决定 AI 能回答哪些数据：

| 工具 | 覆盖 | 典型问题 |
|------|------|----------|
| `get_platform_overview` | **全平台概览**：资产/告警/异常/自动化/巡检/工单/报告/发现/策略/脚本/采集器/知识 计数 | 平台现状？系统总体情况？各模块数据 |
| `query_assets` | 资产清单（类型/状态/关键词） | 有多少资产？哪些 Linux？在线数量 |
| `check_asset_status` | 单台资产状态（按 id） | 某资产健康如何 |
| `query_alerts` | 告警（级别/状态） | 有哪些告警 |
| `query_events` | 事件（资产/类型） | 最近事件 |
| `query_tickets` | 工单（状态） | 有多少工单/待处理工单 |
| `query_knowledge` | 知识库检索 | 有没有 X 的处理方案 |
| `query_execution_logs` | 单次执行详情（按 id） | 某次执行结果 |

**智能问数（NL2SQL，覆盖结构化工具够不到的任意数据问题）**
`backend/app/domains/aiops/tools/nl2sql.py`：

| 工具 | 作用 |
|------|------|
| `get_database_schema` | 返回可查询的表与字段（中文释义），已自动排除鉴权/密钥等敏感表 |
| `run_sql_query` | 执行**一条只读 SELECT** 并返回结果 |

模型据 schema 自行生成 SQL → 执行 → 据结果作答，因此**任意表/任意维度的数据问题**
（按业务系统/环境分组统计、关联查询、时间范围筛选等）都能回答，无需为每类问题写专用工具。

安全闸门（纵深防御，见模块 docstring）：仅 SELECT/WITH、单条语句、关键字黑名单
（insert/update/delete/drop/outfile/load_file…）、**表白名单=全库−敏感表黑名单**
（users/roles/api_keys/credentials/model_agents/system_settings/config_versions…）、
**敏感字段名黑名单**（password/api_key/secret/token/credential/…）、强制 LIMIT≤200。
> 已实测：分号串联、非 SELECT、敏感表/字段、OUTFILE 等全部被拒；CTE 别名亦从严拒绝（安全优先）。

> 工具靠 `tools/__init__.py` 显式 import 触发 `@register` 注册——
> 不导入则 `ToolRegistry` 为空、Agent 无工具可用（历史 bug，已修）。

## 3. 模型选择（关键！能力决定可用性）

| 场景 | 推荐 | 说明 |
|------|------|------|
| 工具调用 / Agent 诊断 | **GLM‑4.6(z.ai) 或 ≥7B 且支持 function calling 的模型** | 小模型无法稳定遵守工具协议 |
| 纯问答 | 任意可用模型（含本地小模型） | 不调用工具时小模型也能用 |
| ❌ 不推荐 | 0.8B/1.5B 级模型做工具调用 | 会复读/幻觉/格式错乱 |

智谱 GLM(z.ai) 端点：`https://api.z.ai/api/coding/paas/v4`（见 `.env.example`），
在「平台管理‑模型服务」注册并设为默认即可让 AI 助手与 Agent 同时生效。

## 4. 思考模式（enable_thinking）

Qwen3 系列默认开启 thinking，会先产出数百 token "思考"。

- **CPU 部署：务必关闭**（模型服务表单「思考模式」选「关闭」），否则
  回答缓慢、甚至 token 全耗在思考、chat 返回空内容。
- GPU / 追求质量：可「开启」。
- 云端 API（GLM/OpenAI 等）：选「默认」（不下发该字段，最安全）。

实现：每个模型可单独配置（迁移 `0014`，列 `model_agents.enable_thinking`，
NULL=自动/1=开/0=关）；运行时仅在非 NULL 时通过 `chat_template_kwargs` 下发。

## 5. 超时

- 后端 LLM 超时默认 180s（`llm.yaml`），覆盖带思考的慢推理。
- 前端 `/ai/chat` 请求超时 200s（大于后端），避免前端提前中断显示兜底文案。

## 6. 已知限制 / 后续

- `/aiops/agent/run`（AI 诊断）目前仍是 ReAct 文本协议，存在同样的小模型脆弱性；
  搭配 GLM/≥7B 可用。后续建议统一迁移到原生 function calling。
- 工具调用质量天花板取决于所选模型；本平台只保证"接对、降级安全、不编造"，
  不保证弱模型的推理质量。
