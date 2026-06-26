"""add exports and ticket_attachments tables

Revision ID: 0008_exports_attach
Revises: 0007_inspection_rules
Create Date: 2026-06-26

为「导出中心」与「工单附件」提供真实后端表（此前 exports 表缺失、附件为 stub）。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_exports_attach"
down_revision: str | None = "0007_inspection_rules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "exports" not in tables:
        op.create_table(
            "exports",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("export_type", sa.String(64), nullable=False, index=True),
            sa.Column("format", sa.String(16), nullable=False, server_default="csv"),
            sa.Column("status", sa.String(16), nullable=False, server_default="pending", index=True),
            sa.Column("filters", sa.Text, nullable=True),
            sa.Column("file_path", sa.String(512), nullable=True),
            sa.Column("file_size", sa.BigInteger, nullable=False, server_default="0"),
            sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("error", sa.Text, nullable=True),
            sa.Column("created_by", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    if "ticket_attachments" not in tables:
        op.create_table(
            "ticket_attachments",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("ticket_id", sa.String(36), nullable=False, index=True),
            sa.Column("filename", sa.String(256), nullable=False),
            sa.Column("content_type", sa.String(128), nullable=True),
            sa.Column("size", sa.BigInteger, nullable=False, server_default="0"),
            sa.Column("storage_path", sa.String(512), nullable=False),
            sa.Column("uploaded_by", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "ticket_attachments" in tables:
        op.drop_table("ticket_attachments")
    if "exports" in tables:
        op.drop_table("exports")
