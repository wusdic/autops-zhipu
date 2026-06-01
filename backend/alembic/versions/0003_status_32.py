"""expand status fields to String(32)

Revision ID: 0003_status_32
Revises: 0002_outbox
Create Date: 2026-06-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_status_32"
down_revision = "0002_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL ALTER COLUMN to expand String(16) → String(32)
    op.alter_column(
        "executions", "status",
        existing_type=sa.String(16),
        type_=sa.String(32),
        existing_nullable=False,
        existing_server_default="pending",
    )
    op.alter_column(
        "execution_steps", "status",
        existing_type=sa.String(16),
        type_=sa.String(32),
        existing_server_default="pending",
    )


def downgrade() -> None:
    op.alter_column(
        "execution_steps", "status",
        existing_type=sa.String(32),
        type_=sa.String(16),
        existing_server_default="pending",
    )
    op.alter_column(
        "executions", "status",
        existing_type=sa.String(32),
        type_=sa.String(16),
        existing_server_default="pending",
    )
