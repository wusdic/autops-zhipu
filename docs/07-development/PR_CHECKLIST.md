# AUTOPS PR 检查单

> 建议路径：`docs/07-development/PR_CHECKLIST.md`

---

## 每个 PR 必须确认

```text
[ ] 是否修改领域模型？
    → 是否更新 docs/02-domains/ 对应文档？

[ ] 是否修改 API？
    → 是否更新 docs/03-api/API_CONTRACT.md 或 OpenAPI？
    → 是否更新 frontend/src/shared/api/routes.ts？

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
    → 新页面是否在 router/index.ts 注册？
    → 新页面是否在 MainLayout.vue 侧边栏添加菜单？
    → API 路径是否使用 routes.ts 常量（禁止硬编码）？

[ ] 是否修改部署？
    → 是否更新 docs/06-operations/ 对应文档？

[ ] 是否修改安全边界？
    → 是否更新 SECURITY_ARCHITECTURE.md？

[ ] 是否修改认证相关？
    → TOKEN_KEY 是否使用 APP_CONFIG 常量？

[ ] 是否同步更新文档？

[ ] 是否新增或修改测试？

[ ] 是否通过浏览器实际验证？
    → 页面可访问，无白屏
    → API 请求路径正确，无 404
    → 数据正常显示
```
