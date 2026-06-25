"""add auto_onboard to discovery_tasks

Revision ID: 0004_auto_onboard
Revises: 1027918be8a1
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_auto_onboard"
down_revision: str | None = "1027918be8a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 新增 auto_onboard 列：是否自动纳管存活IP（默认 True）
    op.add_column(
        "discovery_tasks",
        sa.Column(
            "auto_onboard",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )


def downgrade() -> None:
    op.drop_column("discovery_tasks", "auto_onboard")
