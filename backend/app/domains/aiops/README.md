# AIops中心（aiops）

## 职责
提供基于 LLM 的智能运维分析能力，包括告警根因分析、异常检测和智能诊断。支持分析请求提交、结果查询、LLM 服务健康检查和用户反馈收集。

## 核心模型
| 模型 | 说明 |
|------|------|
| AIAnalysis | AI 分析记录，包含分析类型、输入上下文、LLM 分析结果、状态和反馈评分 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/aiops/analyses | 分析记录列表（支持按类型/状态筛选） |
| POST | /api/v1/aiops/analyses | 提交分析请求 |
| GET | /api/v1/aiops/analyses/{analysis_id} | 获取分析详情 |
| GET | /api/v1/aiops/health | 检查 LLM 服务可用性 |
| POST | /api/v1/aiops/diagnose | 快捷诊断接口 |
| POST | /api/v1/aiops/analyses/{analysis_id}/feedback | 提交分析反馈 |

## 事件
### 发布的事件
- `aiops.analysis_requested` — 分析请求提交
- `aiops.analysis_completed` — 分析完成
- `aiops.analysis_failed` — 分析失败
- `aiops.analysis_degraded` — 分析降级（LLM 不可用时的降级处理）
- `aiops.feedback_submitted` — 反馈提交

### 订阅的事件
- `alert.created` — 新告警触发自动根因分析
- `event.created` — 关键事件触发智能分析
- `state.critical_detected` — 紧急状态触发异常分析

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
