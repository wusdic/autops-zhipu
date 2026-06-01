"""event outbox table

Revision ID: 0002_outbox
Revises: 0001_initial
Create Date: 2026-06-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_outbox"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "event_outbox" in inspector.get_table_names():
        return

    op.create_table(
        "event_outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, index=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("domain", sa.String(64), nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="5"),
        sa.Column("next_retry_at", sa.DateTime, nullable=True),
        sa.Column("locked_by", sa.String(64), nullable=True),
        sa.Column("locked_until", sa.DateTime, nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("processed_at", sa.DateTime, nullable=True),
    )

    op.create_index(
        "idx_event_outbox_status_retry",
        "event_outbox",
        ["status", "next_retry_at", "priority", "created_at"],
    )
    op.create_index(
        "idx_event_outbox_locked",
        "event_outbox",
        ["locked_by", "locked_until"],
    )


def downgrade() -> None:
    op.drop_index("idx_event_outbox_locked", table_name="event_outbox")
    op.drop_index("idx_event_outbox_status_retry", table_name="event_outbox")
    op.drop_table("event_outbox")
