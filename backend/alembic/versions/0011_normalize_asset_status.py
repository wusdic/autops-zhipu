"""normalize asset status vs reachability

Revision ID: 0011_normalize_asset_status
Revises: 0010_execution_queue
Create Date: 2026-06-27

历史上 asset.status 被混用了生命周期(active/inactive/...)与在线性(online/offline)。
本迁移把存量数据的在线性迁回 reachability，status 归一为 active，确保各页面
按统一语义筛选/展示（status=生命周期，reachability=在线性）。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_normalize_asset_status"
down_revision: str | None = "0010_execution_queue"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "assets" not in inspector.get_table_names():
        return
    # 在线性迁回 reachability
    op.execute(
        "UPDATE assets SET reachability = 'reachable' WHERE status = 'online'"
    )
    op.execute(
        "UPDATE assets SET reachability = 'unreachable' WHERE status = 'offline'"
    )
    # status 归一为生命周期 active
    op.execute(
        "UPDATE assets SET status = 'active' WHERE status IN ('online', 'offline')"
    )


def downgrade() -> None:
    # 不可逆（无法区分原本就是 active 的资产），保持空实现
    pass
