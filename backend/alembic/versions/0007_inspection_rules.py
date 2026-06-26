"""add inspection_rules table

Revision ID: 0007_inspection_rules
Revises: 0006_platform_tables
Create Date: 2026-06-26

为「巡检规则」页提供真实后端表（此前该页为纯前端 mock）。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_inspection_rules"
down_revision: str | None = "0006_platform_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "inspection_rules" in inspector.get_table_names():
        return
    op.create_table(
        "inspection_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, index=True),
        # page_check / config_check / log_check / baseline_check / api_check
        sa.Column("category", sa.String(32), nullable=False, index=True),
        sa.Column("check_target", sa.String(256), nullable=True),
        sa.Column("condition", sa.Text, nullable=True),
        sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("asset_types", sa.JSON, nullable=True),
        sa.Column("remediation", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("last_triggered_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("inspection_rules")
