# AUTOPS PR 检查单

> 建议路径：`docs/07-development/PR_CHECKLIST.md`

---

## 每个 PR 必须确认

```text
[ ] 是否修改领域模型？
    → 是否更新 docs/02-domains/ 对应文档？

[ ] 是否修改 API？
    → 是否更新 docs/03-api/API_CONTRACT.md 或 OpenAPI？

[ ] 是否修改数据库？
    → 是否有 Alembic migration？
    → 是否更新 docs/01-architecture/DATA_ARCHITECTURE.md？

[ ] 是否修改配置？
    → 是否更新 configs/*.yaml 示例？
    → 是否更新 .env.example？

[ ] 是否修改事件？
    → 是否更新事件定义文档？

[ ] 是否修改策略？
    → 是否更新策略中心文档？

[ ] 是否修改自动化动作？
    → 是否更新自动化引擎文档？

[ ] 是否修改 AI 工具调用？
    → 是否更新 AI Agent 架构文档？

[ ] 是否修改前端页面？
    → 是否更新 docs/04-frontend/ 对应文档？

[ ] 是否修改部署？
    → 是否更新 docs/06-operations/ 对应文档？

[ ] 是否修改安全边界？
    → 是否更新 SECURITY_ARCHITECTURE.md？

[ ] 是否同步更新文档？

[ ] 是否新增或修改测试？
```
