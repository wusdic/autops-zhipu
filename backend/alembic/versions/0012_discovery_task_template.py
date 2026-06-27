"""add template_id to discovery_tasks

Revision ID: 0012_discovery_task_template
Revises: 0011_normalize_asset_status
Create Date: 2026-06-27

让发现任务可引用发现模板（B.1）：创建任务时从模板继承 protocols/ports/凭据/超时。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_discovery_task_template"
down_revision: str | None = "0011_normalize_asset_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "discovery_tasks" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("discovery_tasks")}
    if "template_id" not in cols:
        op.add_column(
            "discovery_tasks",
            sa.Column("template_id", sa.String(36), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("discovery_tasks", "template_id")
