"""add_threshold_rules_notification_rules_discovery_templates

Revision ID: 1027918be8a1
Revises: 943f502eeb7f
Create Date: 2026-06-03 20:44:25.005249
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1027918be8a1'
down_revision: Union[str, None] = '943f502eeb7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    def _ensure_index(table: str, name: str, columns: list[str]) -> None:
        insp = sa.inspect(bind)
        existing_idxs = {ix['name'] for ix in insp.get_indexes(table)}
        if name in existing_idxs:
            return
        op.create_index(name, table, columns, unique=False)

    # NOTE: 0001_initial_schema uses Base.metadata.create_all(checkfirst=True),
    # which already created these tables via the ORM. Re-running create_table
    # would 1050 — guard with `not in existing`.

    if 'discovery_templates' not in existing:
        op.create_table('discovery_templates',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('protocol', sa.String(length=32), nullable=False),
            sa.Column('target_scope', sa.Text(), nullable=False),
            sa.Column('port_range', sa.String(length=128), nullable=True),
            sa.Column('credential_id', sa.String(length=36), nullable=True),
            sa.Column('scan_interval', sa.Integer(), nullable=False),
            sa.Column('timeout', sa.Integer(), nullable=False),
            sa.Column('asset_type_mapping', sa.Text(), nullable=True),
            sa.Column('enabled', sa.Boolean(), nullable=False),
            sa.Column('is_builtin', sa.Boolean(), nullable=False),
            sa.Column('created_by', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'notification_rules' not in existing:
        op.create_table('notification_rules',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('event_type', sa.String(length=64), nullable=False),
            sa.Column('target_type', sa.String(length=32), nullable=False),
            sa.Column('target_ids', sa.Text(), nullable=False),
            sa.Column('channels', sa.String(length=256), nullable=False),
            sa.Column('severity_filter', sa.String(length=128), nullable=True),
            sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
            sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
            sa.Column('enabled', sa.Boolean(), nullable=False),
            sa.Column('created_by', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
    _ensure_index('notification_rules', 'ix_notification_rules_event_type', ['event_type'])

    if 'threshold_rules' not in existing:
        op.create_table('threshold_rules',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('metric_name', sa.String(length=128), nullable=False),
            sa.Column('asset_type', sa.String(length=32), nullable=True),
            sa.Column('condition', sa.String(length=16), nullable=False),
            sa.Column('threshold_value', sa.Float(), nullable=False),
            sa.Column('duration_seconds', sa.Integer(), nullable=False),
            sa.Column('severity', sa.String(length=16), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False),
            sa.Column('notify_channels', sa.String(length=256), nullable=True),
            sa.Column('created_by', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
    _ensure_index('threshold_rules', 'ix_threshold_rules_metric_name', ['metric_name'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'threshold_rules' in existing:
        op.drop_index('ix_threshold_rules_metric_name', table_name='threshold_rules')
        op.drop_table('threshold_rules')
    if 'notification_rules' in existing:
        op.drop_index('ix_notification_rules_event_type', table_name='notification_rules')
        op.drop_table('notification_rules')
    if 'discovery_templates' in existing:
        op.drop_table('discovery_templates')
