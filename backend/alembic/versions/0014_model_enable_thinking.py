"""model_agents: per-model thinking-mode toggle

Revision ID: 0014_model_enable_thinking
Revises: 0013_business_system_link
Create Date: 2026-06-29

Qwen3 等推理模型在 vLLM/llama-server 上默认开启 thinking mode：每次请求会先产出
数百 token 的"思考"再给答案。GPU 上影响小，CPU 上可造成数十秒额外延迟，甚至
把 max_tokens 全消耗在思考、chat 接口返回空内容（AI 助手"无回答/默认回答"）。

是否关闭 thinking 取决于部署（CPU/GPU）和模型，不应硬编码。这里给每个注册模型
增加可选开关 enable_thinking：
- NULL  = 默认/自动：不向后端发送 chat_template_kwargs（对云端/非 Qwen 最安全）
- 1     = 显式开启 thinking（GPU、需要推理质量时）
- 0     = 显式关闭 thinking（CPU 部署、追求低延迟时）
仅当非 NULL 时，运行时才会在请求体加入 chat_template_kwargs.enable_thinking。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_model_enable_thinking"
down_revision: str | None = "0013_business_system_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "model_agents" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("model_agents")}
    if "enable_thinking" not in cols:
        # nullable：NULL=自动(不发送)，1=开启，0=关闭
        op.add_column(
            "model_agents",
            sa.Column("enable_thinking", sa.Integer, nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "model_agents" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("model_agents")}
    if "enable_thinking" in cols:
        op.drop_column("model_agents", "enable_thinking")
