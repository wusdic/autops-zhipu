"""add execution_queue table

Revision ID: 0010_execution_queue
Revises: 0009_trigger_history
Create Date: 2026-06-27

durable execution queue: Worker leases jobs, heartbeats lease, retries on failure.
replaces the previous fire-and-forget asyncio.create_task in the outbox handler.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_execution_queue"
down_revision: str | None = "0009_trigger_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "execution_queue" in inspector.get_table_names():
        return
    op.create_table(
        "execution_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(36), nullable=False, index=True),
        # queued / leased / done / failed
        sa.Column("status", sa.String(16), nullable=False, server_default="queued", index=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        # 何时可被领取（重试退避时推后）
        sa.Column("available_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("lease_owner", sa.String(64), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime, nullable=True),
        sa.Column("heartbeat_at", sa.DateTime, nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("execution_queue")
