"""add backing tables for platform/model/backup facade pages

Revision ID: 0006_platform_tables
Revises: 0005_check_type
Create Date: 2026-06-26

新增此前前端有页面但后端缺表的后台表：
dictionaries / tenants / licenses / upgrade_history / model_agents /
system_settings / backups。均为增量建表，幂等（已存在则跳过）。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_platform_tables"
down_revision: str | None = "0005_check_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "dictionaries",
    "tenants",
    "licenses",
    "upgrade_history",
    "model_agents",
    "system_settings",
    "backups",
)


def _exists(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _exists(inspector, "dictionaries"):
        op.create_table(
            "dictionaries",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("type", sa.String(64), nullable=False, index=True),
            sa.Column("code", sa.String(128), nullable=False),
            sa.Column("label", sa.String(256), nullable=False),
            sa.Column("value", sa.Text, nullable=True),
            sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    if not _exists(inspector, "tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("code", sa.String(64), nullable=False, unique=True),
            sa.Column("admin_user_id", sa.String(36), nullable=True),
            sa.Column("resource_quota", sa.Text, nullable=True),
            sa.Column("feature_scope", sa.Text, nullable=True),
            sa.Column("status", sa.String(16), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    if not _exists(inspector, "licenses"):
        op.create_table(
            "licenses",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("license_key", sa.Text, nullable=False),
            sa.Column("licensed_to", sa.String(256), nullable=True),
            sa.Column("edition", sa.String(64), nullable=False, server_default="community"),
            sa.Column("max_assets", sa.Integer, nullable=True),
            sa.Column("features", sa.Text, nullable=True),
            sa.Column("issued_at", sa.DateTime, nullable=True),
            sa.Column("expires_at", sa.DateTime, nullable=True),
            sa.Column("status", sa.String(16), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _exists(inspector, "upgrade_history"):
        op.create_table(
            "upgrade_history",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("version", sa.String(64), nullable=False),
            sa.Column("from_version", sa.String(64), nullable=True),
            sa.Column("status", sa.String(16), nullable=False, server_default="success"),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("operated_by", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _exists(inspector, "model_agents"):
        op.create_table(
            "model_agents",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("provider", sa.String(64), nullable=False, server_default="openai"),
            sa.Column("model_id", sa.String(128), nullable=False),
            sa.Column("endpoint", sa.String(512), nullable=False),
            sa.Column("api_key_enc", sa.Text, nullable=True),
            sa.Column("max_tokens", sa.Integer, nullable=False, server_default="4096"),
            sa.Column("temperature", sa.Float, nullable=False, server_default="0.3"),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.text("0")),
            sa.Column("status", sa.String(16), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    if not _exists(inspector, "system_settings"):
        op.create_table(
            "system_settings",
            sa.Column("skey", sa.String(128), primary_key=True),
            sa.Column("svalue", sa.Text, nullable=True),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    if not _exists(inspector, "backups"):
        op.create_table(
            "backups",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("backup_type", sa.String(32), nullable=False, server_default="full"),
            sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
            sa.Column("file_path", sa.String(512), nullable=True),
            sa.Column("file_size", sa.BigInteger, nullable=False, server_default="0"),
            sa.Column("checksum", sa.String(128), nullable=True),
            sa.Column("error", sa.Text, nullable=True),
            sa.Column("created_by", sa.String(64), nullable=True),
            sa.Column("started_at", sa.DateTime, nullable=True),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for name in reversed(_TABLES):
        if _exists(inspector, name):
            op.drop_table(name)
