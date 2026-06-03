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
    op.create_index('ix_notification_rules_event_type', 'notification_rules', ['event_type'])

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
    op.create_index('ix_threshold_rules_metric_name', 'threshold_rules', ['metric_name'])


def downgrade() -> None:
    op.drop_index('ix_threshold_rules_metric_name', table_name='threshold_rules')
    op.drop_table('threshold_rules')
    op.drop_index('ix_notification_rules_event_type', table_name='notification_rules')
    op.drop_table('notification_rules')
    op.drop_table('discovery_templates')
