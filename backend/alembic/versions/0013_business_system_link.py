"""business system ↔ asset stable link

Revision ID: 0013_business_system_link
Revises: 0012_discovery_task_template
Create Date: 2026-06-28

业务系统与资源的归属此前仅靠 asset.business_system(名字字符串) 匹配，改名即断链、
无引用完整性。本迁移新增稳定的自引用外键 assets.business_system_id → assets.id
（业务系统本身也是一条 asset_type='business_system' 的资产行）：
- business_system_id 为成员关系的事实源（改名安全）；
- business_system(名) 保留为展示用反范式缓存，由 service 同步。
回填：按现有名字匹配把存量成员的 business_system_id 补上。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_business_system_link"
down_revision: str | None = "0012_discovery_task_template"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "assets" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("assets")}
    if "business_system_id" not in cols:
        op.add_column(
            "assets",
            sa.Column("business_system_id", sa.String(length=36), nullable=True),
        )
        op.create_index(
            "ix_assets_business_system_id", "assets", ["business_system_id"]
        )
    # 回填：成员资产.business_system(名) == 业务系统资产.name → 写入 business_system_id
    op.execute(
        """
        UPDATE assets a
        JOIN assets b
          ON a.business_system = b.name
         AND b.asset_type = 'business_system'
         AND b.is_deleted = 0
        SET a.business_system_id = b.id
        WHERE a.asset_type <> 'business_system'
          AND a.business_system IS NOT NULL
          AND a.business_system <> ''
          AND a.business_system_id IS NULL
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "assets" not in inspector.get_table_names():
        return
    idx = {i["name"] for i in inspector.get_indexes("assets")}
    if "ix_assets_business_system_id" in idx:
        op.drop_index("ix_assets_business_system_id", table_name="assets")
    cols = {c["name"] for c in inspector.get_columns("assets")}
    if "business_system_id" in cols:
        op.drop_column("assets", "business_system_id")
