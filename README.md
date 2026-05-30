# AUTOPS - 自治运维操作系统

> 面向私有化部署场景的自治运维操作系统

## 项目定位

AUTOPS 不是普通监控平台、工单系统、脚本平台或简单 AI 助手。它将资产、配置、状态、事件、告警、日志、策略、自动化执行、AI 分析、工单协同、知识沉淀和平台自身治理整合成一个可持续演进的闭环系统。

## 核心闭环

```
资源发现 → 资产纳管 → 配置治理 → 状态采集 → 事件识别 → 告警收敛
→ 影响分析 → AI 诊断 → 策略决策 → 自动化执行 → 实时日志
→ 结果验证 → 回滚/升级/关闭 → 知识沉淀 → 策略优化
```

## 文档入口

| 文档 | 路径 |
|---|---|
| 全局约束 | [docs/00-overview/GLOBAL_CONSTRAINTS.md](docs/00-overview/GLOBAL_CONSTRAINTS.md) |
| 目标架构 | [docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md](docs/01-architecture/AUTOPS_TARGET_ARCHITECTURE.md) |
| 开发计划 | [docs/05-implementation/AUTOPS_DEVELOPMENT_AND_GOVERNANCE_PLAN.md](docs/05-implementation/AUTOPS_DEVELOPMENT_AND_GOVERNANCE_PLAN.md) |

## 技术栈

- **后端：** Python 3.10+ / FastAPI / SQLAlchemy 2.0 / Pydantic V2 / Alembic
- **前端：** Vue 3 / TypeScript / Vite / Pinia / Element Plus
- **数据库：** MySQL/MariaDB（兼容 PostgreSQL / openGauss / 达梦 / 人大金仓）
- **中间件：** Redis / VictoriaMetrics / MinIO / Qdrant

## 开发原则

1. **先设计，后编码** — 未完成设计文档前不得开始编码
2. **平台整体优先** — 不围绕 MVP 写专项代码
3. **模型驱动** — 所有功能归入九类统一模型
4. **国产化兼容** — 通过抽象层保留迁移空间
5. **安全边界不可绕过** — 凭证加密、审批机制、审计日志

## 快速开始

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 许可证

待定
