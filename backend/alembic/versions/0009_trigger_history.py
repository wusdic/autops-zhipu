"""add trigger_history table

Revision ID: 0009_trigger_history
Revises: 0008_exports_attach
Create Date: 2026-06-26

记录巡检规则 / 处置模板(Playbook) 的触发历史，供前端「历史」查看。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_trigger_history"
down_revision: str | None = "0008_exports_attach"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "trigger_history" in inspector.get_table_names():
        return
    op.create_table(
        "trigger_history",
        sa.Column("id", sa.String(36), primary_key=True),
        # inspection_rule / playbook
        sa.Column("ref_type", sa.String(32), nullable=False, index=True),
        sa.Column("ref_id", sa.String(36), nullable=False, index=True),
        sa.Column("ref_name", sa.String(256), nullable=True),
        sa.Column("action", sa.String(32), nullable=False, server_default="triggered"),
        sa.Column("status", sa.String(16), nullable=False, server_default="success"),
        sa.Column("detail", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("trigger_history")
