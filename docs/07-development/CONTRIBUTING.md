# AUTOPS 贡献指南

> 文档状态：current
> 建议路径：`docs/07-development/CONTRIBUTING.md`

---

## 1. 开发环境搭建

```bash
# 后端
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# 前端
cd frontend && npm install
```

## 2. 开发流程

```text
创建分支 (feat/xxx 或 fix/xxx)
  → 编码（遵循设计文档）
  → 编写测试
  → 运行测试
  → 运行 lint
  → 更新文档
  → 提交 PR
  → Code Review
  → 合并
```

## 3. 分支策略

| 分支 | 说明 |
|---|---|
| main | 稳定发布 |
| develop | 开发主线 |
| feat/* | 功能分支 |
| fix/* | 修复分支 |
| release/* | 发布分支 |

## 4. Commit 规范

```
feat(asset): add asset import API
fix(alert): fix alert dedup logic
docs(api): update API contract
test(policy): add policy matching tests
refactor(config): extract config loader
```

## 5. PR 要求

- 关联 Issue
- 测试通过
- Lint 通过
- 文档同步更新
- PR 描述清晰

## 6. PR 检查项

见 `PR_CHECKLIST.md`
