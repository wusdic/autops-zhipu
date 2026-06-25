"""add check_type to inspection_results

Revision ID: 0005_check_type
Revises: 0004_auto_onboard
Create Date: 2026-06-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_check_type"
down_revision: str | None = "0004_auto_onboard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("inspection_results")}
    if "check_type" not in cols:
        # 巡检结果分类：baseline / config / log / page / resource / service / security
        op.add_column(
            "inspection_results",
            sa.Column(
                "check_type",
                sa.String(32),
                nullable=False,
                server_default="baseline",
                index=True,
            ),
        )


def downgrade() -> None:
    op.drop_column("inspection_results", "check_type")
