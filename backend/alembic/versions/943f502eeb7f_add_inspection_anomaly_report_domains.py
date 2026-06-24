"""add inspection anomaly report domains

Revision ID: 943f502eeb7f
Revises: 0003_status_32
Create Date: 2026-06-02 23:58:36.171076
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '943f502eeb7f'
down_revision: Union[str, None] = '0003_status_32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def _ensure_index(table: str, name: str, columns: list[str]) -> None:
        """Create index only if it doesn't exist yet (idempotent for re-run)."""
        insp = sa.inspect(bind)
        existing_idxs = {ix['name'] for ix in insp.get_indexes(table)}
        if name in existing_idxs:
            return
        op.create_index(name, table, columns, unique=False)

    # --- Recreate tables that were accidentally dropped (idempotent) ---
    if 'audit_logs' not in existing_tables:
        op.create_table('audit_logs',
            sa.Column('id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=False),
            sa.Column('trace_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=False),
            sa.Column('user_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=True),
            sa.Column('username', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=64), nullable=True),
            sa.Column('action', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=64), nullable=False),
            sa.Column('resource_type', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=64), nullable=False),
            sa.Column('resource_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=True),
            sa.Column('detail', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('ip_address', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=45), nullable=True),
            sa.Column('user_agent', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=256), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('(now())'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_trace_id'), 'audit_logs', ['trace_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)

    # event_outbox: 0002 already created it (id varchar(36)). Skip recreate to avoid conflict.
    # (The schema here would be id BIGINT AUTO_INCREMENT; existing 0002 table uses id VARCHAR(36)
    #  which is the historical schema and is what the outbox consumer code reads.)
    if 'event_outbox' not in existing_tables:
        op.create_table('event_outbox',
            sa.Column('id', mysql.BIGINT(), autoincrement=True, nullable=False),
            sa.Column('event_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=False),
            sa.Column('event_type', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=False),
            sa.Column('domain', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=64), nullable=False),
            sa.Column('payload', mysql.JSON(), nullable=True),
            sa.Column('priority', mysql.TINYINT(), server_default=sa.text("'1'"), autoincrement=False, nullable=True),
            sa.Column('source', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), server_default=sa.text("''"), nullable=True),
            sa.Column('status', mysql.ENUM('pending', 'processing', 'done', 'dead'), server_default=sa.text("'pending'"), nullable=False),
            sa.Column('error', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=512), nullable=True),
            sa.Column('retry_count', mysql.TINYINT(), server_default=sa.text("'0'"), autoincrement=False, nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('processed_at', mysql.DATETIME(), nullable=True),
            sa.Column('locked_by', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True),
            sa.Column('locked_until', mysql.DATETIME(), nullable=True),
            sa.Column('next_retry_at', mysql.DATETIME(), nullable=True),
            sa.Column('max_retries', mysql.INTEGER(), server_default=sa.text("'5'"), autoincrement=False, nullable=True),
            sa.Column('last_error', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('correlation_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True),
            sa.Column('idempotency_key', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=128), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )
    op.create_index(op.f('idx_outbox_status'), 'event_outbox', ['status', 'created_at'], unique=False)
    op.create_index(op.f('idx_outbox_event_type'), 'event_outbox', ['event_type'], unique=False)
    op.create_index(op.f('event_id'), 'event_outbox', ['event_id'], unique=True)

    if 'ai_analyses' not in existing_tables:
        op.create_table('ai_analyses',
            sa.Column('id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=False),
            sa.Column('analysis_type', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=32), nullable=False),
            sa.Column('alert_id', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=36), nullable=True),
            sa.Column('asset_ids', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('input_context', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('model_name', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=64), nullable=False),
            sa.Column('summary', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('root_causes', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('recommended_actions', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('raw_output', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('status', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=16), nullable=False),
            sa.Column('error_message', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('duration_ms', sa.INTEGER(), autoincrement=False, nullable=True),
            sa.Column('feedback_rating', sa.INTEGER(), autoincrement=False, nullable=True),
            sa.Column('feedback_comment', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('(now())'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )
    op.create_index(op.f('ix_ai_analyses_alert_id'), 'ai_analyses', ['alert_id'], unique=False)

    # --- Create inspection domain tables ---
    if 'inspection_templates' not in existing_tables:
        op.create_table('inspection_templates',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('name', mysql.VARCHAR(length=255), nullable=False),
            sa.Column('description', mysql.TEXT(), nullable=True),
            sa.Column('check_items', mysql.JSON(), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    if 'inspection_plans' not in existing_tables:
        op.create_table('inspection_plans',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('name', mysql.VARCHAR(length=255), nullable=False),
            sa.Column('template_id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('cron_expression', mysql.VARCHAR(length=128), nullable=True),
            sa.Column('target_assets', mysql.JSON(), nullable=True),
            sa.Column('enabled', mysql.BOOLEAN(), server_default=sa.text('1'), nullable=False),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['template_id'], ['inspection_templates.id'], ondelete='CASCADE'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    if 'inspection_tasks' not in existing_tables:
        op.create_table('inspection_tasks',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('plan_id', mysql.VARCHAR(length=36), nullable=True),
            sa.Column('template_id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('status', mysql.ENUM('pending', 'running', 'completed', 'failed'), server_default='pending', nullable=False),
            sa.Column('started_at', mysql.DATETIME(), nullable=True),
            sa.Column('completed_at', mysql.DATETIME(), nullable=True),
            sa.Column('summary', mysql.JSON(), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['template_id'], ['inspection_templates.id']),
            sa.ForeignKeyConstraint(['plan_id'], ['inspection_plans.id'], ondelete='SET NULL'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    if 'inspection_results' not in existing_tables:
        op.create_table('inspection_results',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('task_id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('asset_id', mysql.VARCHAR(length=36), nullable=True),
            sa.Column('check_item', mysql.VARCHAR(length=255), nullable=False),
            sa.Column('status', mysql.ENUM('pass', 'fail', 'warning'), nullable=False),
            sa.Column('detail', mysql.JSON(), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['task_id'], ['inspection_tasks.id'], ondelete='CASCADE'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    if 'inspection_reports' not in existing_tables:
        op.create_table('inspection_reports',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('task_id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('report_data', mysql.JSON(), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['task_id'], ['inspection_tasks.id'], ondelete='CASCADE'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    # --- Create anomaly domain table ---
    if 'anomalies' not in existing_tables:
        op.create_table('anomalies',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('title', mysql.VARCHAR(length=255), nullable=False),
            sa.Column('description', mysql.TEXT(), nullable=True),
            sa.Column('source', mysql.VARCHAR(length=128), nullable=True),
            sa.Column('severity', mysql.ENUM('low', 'medium', 'high', 'critical'), server_default='medium', nullable=False),
            sa.Column('status', mysql.ENUM('open', 'acknowledged', 'resolved', 'closed'), server_default='open', nullable=False),
            sa.Column('asset_id', mysql.VARCHAR(length=36), nullable=True),
            sa.Column('assigned_to', mysql.VARCHAR(length=36), nullable=True),
            sa.Column('detected_at', mysql.DATETIME(), nullable=False),
            sa.Column('resolved_at', mysql.DATETIME(), nullable=True),
            sa.Column('meta', mysql.JSON(), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )
    # 索引也加幂等检查，避免重复执行时报 Duplicate key name
    _ensure_index('anomalies', 'ix_anomalies_severity', ['severity'])
    _ensure_index('anomalies', 'ix_anomalies_status', ['status'])
    _ensure_index('anomalies', 'ix_anomalies_asset_id', ['asset_id'])
    _ensure_index('anomalies', 'ix_anomalies_detected_at', ['detected_at'])

    # --- Create report domain tables ---
    if 'report_templates' not in existing_tables:
        op.create_table('report_templates',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('name', mysql.VARCHAR(length=255), nullable=False),
            sa.Column('description', mysql.TEXT(), nullable=True),
            sa.Column('type', mysql.ENUM('daily', 'weekly', 'monthly', 'custom'), server_default='custom', nullable=False),
            sa.Column('config', mysql.JSON(), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    if 'report_tasks' not in existing_tables:
        op.create_table('report_tasks',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('template_id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('status', mysql.ENUM('pending', 'running', 'completed', 'failed'), server_default='pending', nullable=False),
            sa.Column('triggered_by', mysql.VARCHAR(length=128), nullable=True),
            sa.Column('started_at', mysql.DATETIME(), nullable=True),
            sa.Column('completed_at', mysql.DATETIME(), nullable=True),
            sa.Column('result_path', mysql.VARCHAR(length=512), nullable=True),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['template_id'], ['report_templates.id']),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )

    if 'report_archives' not in existing_tables:
        op.create_table('report_archives',
            sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('task_id', mysql.VARCHAR(length=36), nullable=False),
            sa.Column('filename', mysql.VARCHAR(length=255), nullable=False),
            sa.Column('file_size', mysql.BIGINT(), nullable=True),
            sa.Column('storage_path', mysql.VARCHAR(length=512), nullable=False),
            sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['task_id'], ['report_tasks.id'], ondelete='CASCADE'),
            mysql_collate='utf8mb4_unicode_ci',
            mysql_default_charset='utf8mb4',
            mysql_engine='InnoDB'
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if 'report_archives' in existing_tables:
        op.drop_table('report_archives')
    if 'report_tasks' in existing_tables:
        op.drop_table('report_tasks')
    if 'report_templates' in existing_tables:
        op.drop_table('report_templates')
    if 'anomalies' in existing_tables:
        op.drop_index('ix_anomalies_detected_at', table_name='anomalies')
        op.drop_index('ix_anomalies_asset_id', table_name='anomalies')
        op.drop_index('ix_anomalies_status', table_name='anomalies')
        op.drop_index('ix_anomalies_severity', table_name='anomalies')
        op.drop_table('anomalies')
    if 'inspection_reports' in existing_tables:
        op.drop_table('inspection_reports')
    if 'inspection_results' in existing_tables:
        op.drop_table('inspection_results')
    if 'inspection_tasks' in existing_tables:
        op.drop_table('inspection_tasks')
    if 'inspection_plans' in existing_tables:
        op.drop_table('inspection_plans')
    if 'inspection_templates' in existing_tables:
        op.drop_table('inspection_templates')
    # audit_logs and event_outbox are owned by 0001 / 0002, leave them alone.
