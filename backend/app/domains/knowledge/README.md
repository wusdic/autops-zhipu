# 知识中心（knowledge）

## 职责
管理运维知识库文章的创建、更新、发布和版本管理。支持文章分类、批量导入导出、相关文章推荐和文章转 Runbook 能力，为运维人员提供知识沉淀与共享平台。

## 核心模型
| 模型 | 说明 |
|------|------|
| KnowledgeArticle | 知识文章，包含标题、内容、分类、标签、状态、版本和浏览计数 |

## API端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/knowledge | 知识文章列表（支持按类型/状态筛选） |
| POST | /api/v1/knowledge | 创建知识文章 |
| GET | /api/v1/knowledge/stats | 知识库统计概览 |
| GET | /api/v1/knowledge/export | 导出知识文章 |
| POST | /api/v1/knowledge/import/validate | 验证导入数据格式 |
| POST | /api/v1/knowledge/import/batch | 批量导入知识文章 |
| GET | /api/v1/knowledge/{article_id} | 获取文章详情 |
| PUT | /api/v1/knowledge/{article_id} | 更新文章 |
| POST | /api/v1/knowledge/{article_id}/publish | 发布文章 |
| GET | /api/v1/knowledge/{article_id}/related | 获取相关文章 |
| GET | /api/v1/knowledge/{article_id}/versions | 获取文章版本历史 |
| POST | /api/v1/knowledge/{article_id}/view | 记录文章浏览 |
| POST | /api/v1/knowledge/{article_id}/feedback | 提交文章反馈 |
| POST | /api/v1/knowledge/{article_id}/convert-runbook | 转换为自动化 Runbook |

## 事件
### 发布的事件
- `knowledge.article_created` — 知识文章创建
- `knowledge.article_updated` — 知识文章更新
- `knowledge.article_published` — 知识文章发布
- `knowledge.article_imported` — 知识文章导入
- `knowledge.draft_created` — 知识草稿创建

### 订阅的事件
- `ticket.converted_to_knowledge` — 工单转为知识文章
- `aiops.analysis_completed` — AI 分析结果自动生成知识建议

## 领域边界
- **不直接访问**其他领域的数据库表
- **通过事件总线**与其他领域通信
- **通过Service层**对外提供能力
