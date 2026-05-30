# AIops 与知识中心 (AIops & Knowledge Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/aiops/` + `backend/app/domains/knowledge/`

---

## 1. 职责

- **AIops：** 基于多源证据进行 AI 根因分析，推荐处置方案
- **知识中心：** 结构化知识管理，支持 RAG 检索，支持知识沉淀

**关键约束：AI 是受控诊断层，推荐动作必须经过策略中心校验。**

## 2. AI 分析流程

```text
触发（告警/手动/工单）
  ↓
Context Builder（收集上下文）
  ↓
Prompt 模板选择
  ↓
LLM 调用（配置化模型）
  ↓
输出解析（结构化 JSON）
  ↓
展示分析结果
  ↓
推荐动作 → 策略校验 → 审批（如需）→ 执行
```

## 3. AI 上下文构建

### 3.1 输入来源

| 来源 | 数据 | 优先级 |
|---|---|---|
| 告警详情 | 标题、描述、严重度、时间 | 最高 |
| 关联资产 | 名称、类型、IP、配置 | 高 |
| 当前状态 | 健康、可达、指标 | 高 |
| 指标趋势 | 最近 24h 趋势数据 | 中 |
| 相关事件 | 同资产近期事件 | 中 |
| 相关日志 | 最近错误日志 | 中 |
| 配置变更 | 近期配置变更 | 低 |
| 执行记录 | 近期自动化执行 | 低 |
| 相似案例 | 知识库相似条目 | 高 |
| 可用策略 | 可匹配的处置策略 | 高 |

### 3.2 上下文窗口管理

- 总 token 控制在模型限制内
- 优先保留高优先级数据
- 低优先级数据截断或摘要

## 4. AI 输出格式

```json
{
  "summary": "web-server-01 磁盘 / 分区使用率达 92%",
  "impact": "影响日志写入，可能导致服务异常",
  "probable_causes": [
    {
      "cause": "日志文件过大",
      "confidence": 0.85,
      "evidence": ["nginx access.log 大小 15GB", "日志轮转未配置"]
    },
    {
      "cause": "临时文件未清理",
      "confidence": 0.6,
      "evidence": ["/tmp 目录使用 5GB"]
    }
  ],
  "recommended_actions": [
    {
      "action": "压缩并清理旧日志",
      "risk": "low",
      "requires_approval": false,
      "related_playbook": "playbook-disk-cleanup",
      "estimated_impact": "释放约 10GB 空间"
    }
  ],
  "verification_plan": [
    "检查磁盘使用率是否低于 80%",
    "确认 nginx 服务正常写入日志"
  ],
  "uncertainties": [
    "无法确认磁盘增长速度"
  ]
}
```

## 5. 知识库

### 5.1 知识类型

| 类型 | 说明 | 来源 |
|---|---|---|
| standard_solution | 标准处置方案 | 内置/导入 |
| case_study | 案例复盘 | 工单关闭后沉淀 |
| best_practice | 最佳实践 | 人工编写 |
| draft | 草稿 | AI 生成/工单转化 |

### 5.2 知识结构

```json
{
  "id": "kb-linux-disk-high",
  "title": "Linux 磁盘空间异常处置",
  "article_type": "standard_solution",
  "applicable_asset_types": ["linux_server"],
  "trigger_events": ["disk_usage_high"],
  "diagnosis_steps": [
    "检查磁盘使用率 df -h",
    "查找大文件 find / -type f -size +100M",
    "检查日志增长 du -sh /var/log/*"
  ],
  "action_steps": [
    "压缩旧日志 gzip /var/log/*.old",
    "清理临时文件 rm -rf /tmp/old_*",
    "清理包管理器缓存 apt clean"
  ],
  "verification_steps": [
    "检查磁盘使用率低于阈值 df -h"
  ],
  "risk_level": "low",
  "requires_approval": false,
  "related_policy": "policy-001",
  "related_playbook": "playbook-disk-cleanup"
}
```

### 5.3 标准知识库导入

第一批 8 个标准处置方案（见目标架构第 10 节），通过 data_seed 脚本导入。

### 5.4 知识 RAG

```text
知识条目 → 文本提取 → Embedding → 向量存储(Qdrant/Chroma)
  ↓
查询：提取关键词 → 向量化 → Top-K 检索 → 相关度过滤
```

## 6. 知识沉淀循环

```text
告警/故障 → AI 分析 → 策略匹配 → 自动化执行 → 验证结果
  ↓
工单复盘 → 生成知识草稿 → 审核 → 发布为知识文章
  ↓
知识文章关联策略和 Playbook → 优化后续分析
```

## 7. 模型降级

```text
主模型可用 → 使用主模型分析
主模型超时 → 使用备选模型
全部不可用 → 降级响应：
  {
    "status": "unavailable",
    "summary": "AI 分析服务暂时不可用，请人工分析",
    "recommendation": "稍后重试或查看知识库中的相似案例"
  }
```

模型不可用不影响：告警、采集、策略、自动化、工单。

## 8. 数据模型

见 `DATA_ARCHITECTURE.md` 3.12-3.13 节：
- ai_analysis_records
- knowledge_articles
- knowledge_feedback

## 9. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/v1/aiops/analyze | 触发 AI 分析 |
| GET | /api/v1/aiops/analysis/{id} | 分析结果 |
| GET | /api/v1/aiops/analysis | 分析记录列表 |
| POST | /api/v1/aiops/analysis/{id}/feedback | 分析反馈 |
| GET | /api/v1/knowledge | 知识列表 |
| POST | /api/v1/knowledge | 创建知识 |
| GET | /api/v1/knowledge/{id} | 知识详情 |
| PUT | /api/v1/knowledge/{id} | 更新知识 |
| POST | /api/v1/knowledge/{id}/publish | 发布知识 |
| POST | /api/v1/knowledge/search | 知识搜索（含向量检索） |
| POST | /api/v1/knowledge/import | 批量导入 |

## 10. 领域事件

| 事件 | 说明 |
|---|---|
| AIAnalysisStarted | AI 分析开始 |
| AIAnalysisCompleted | AI 分析完成 |
| AIAnalysisFailed | AI 分析失败 |
| AIModelUnavailable | AI 模型不可用 |
| KnowledgeCreated | 知识创建 |
| KnowledgePublished | 知识发布 |
| KnowledgeFeedbackGiven | 知识反馈 |

## 11. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| alert | 告警触发 AI 分析 | 事件订阅 |
| asset | AI 读取资产信息 | service 调用 |
| state | AI 读取状态 | service 调用 |
| event | AI 读取事件 | service 调用 |
| log | AI 读取日志 | service 调用 |
| policy | AI 推荐动作进入策略校验 | service 调用 |
| automation | 策略通过后调用自动化 | service 调用 |
| ticket | 工单触发 AI 分析、关闭沉淀知识 | 事件订阅 |
