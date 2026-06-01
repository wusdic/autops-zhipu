"""initial schema - all domain tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all domain tables.

    NOTE: This migration uses create_all equivalent - it creates all tables
    registered in Base.metadata. For production, each schema change should
    have its own migration file.
    """
    from app.infra.database import Base
    # Import all models to ensure they're registered
    import app.domains.asset.models  # noqa
    import app.domains.asset.discovery_models  # noqa
    import app.domains.config.models  # noqa
    import app.domains.collector.models  # noqa
    import app.domains.event.models  # noqa
    import app.domains.alert.models  # noqa
    import app.domains.policy.models  # noqa
    import app.domains.automation.models  # noqa
    import app.domains.log.models  # noqa
    import app.domains.knowledge.models  # noqa
    import app.domains.ticket.models  # noqa
    import app.domains.governance.models  # noqa
    import app.domains.state.models  # noqa
    import app.domains.notification.models  # noqa

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop all tables."""
    from app.infra.database import Base
    import app.domains.asset.models  # noqa
    import app.domains.asset.discovery_models  # noqa
    import app.domains.config.models  # noqa
    import app.domains.collector.models  # noqa
    import app.domains.event.models  # noqa
    import app.domains.alert.models  # noqa
    import app.domains.policy.models  # noqa
    import app.domains.automation.models  # noqa
    import app.domains.log.models  # noqa
    import app.domains.knowledge.models  # noqa
    import app.domains.ticket.models  # noqa
    import app.domains.governance.models  # noqa
    import app.domains.state.models  # noqa
    import app.domains.notification.models  # noqa

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
