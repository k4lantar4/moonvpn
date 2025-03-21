"""Add monitoring tables

Revision ID: 20240320000000
Revises: 20240319000000
Create Date: 2024-03-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240320000000'
down_revision = '20240319000000'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("CREATE TYPE metric_type AS ENUM ('system', 'application', 'custom')")
    op.execute("CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE alert_status AS ENUM ('active', 'resolved', 'acknowledged')")
    op.execute("CREATE TYPE system_health AS ENUM ('healthy', 'warning', 'critical', 'unknown')")

    # Create monitoring_metrics table
    op.create_table(
        'monitoring_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('type', postgresql.ENUM('system', 'application', 'custom', name='metric_type'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_metrics_id'), 'monitoring_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_monitoring_metrics_name'), 'monitoring_metrics', ['name'], unique=False)
    op.create_index(op.f('ix_monitoring_metrics_timestamp'), 'monitoring_metrics', ['timestamp'], unique=False)

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'critical', name='alert_severity'), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'resolved', 'acknowledged', name='alert_status'), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('resolved_at', sa.Float(), nullable=True),
        sa.Column('acknowledged_at', sa.Float(), nullable=True),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_name'), 'alerts', ['name'], unique=False)
    op.create_index(op.f('ix_alerts_created_at'), 'alerts', ['created_at'], unique=False)

    # Create system_status table
    op.create_table(
        'system_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('health', postgresql.ENUM('healthy', 'warning', 'critical', 'unknown', name='system_health'), nullable=False),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('alerts', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('components', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_status_id'), 'system_status', ['id'], unique=False)
    op.create_index(op.f('ix_system_status_timestamp'), 'system_status', ['timestamp'], unique=False)

    # Create logs table
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_logs_id'), 'logs', ['id'], unique=False)
    op.create_index(op.f('ix_logs_level'), 'logs', ['level'], unique=False)
    op.create_index(op.f('ix_logs_timestamp'), 'logs', ['timestamp'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_timestamp'), 'notifications', ['timestamp'], unique=False)

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    op.create_index(op.f('ix_reports_type'), 'reports', ['type'], unique=False)
    op.create_index(op.f('ix_reports_timestamp'), 'reports', ['timestamp'], unique=False)

    # Create report_schedules table
    op.create_table(
        'report_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('recipients', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('next_run', sa.Float(), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('last_run', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_schedules_id'), 'report_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_report_schedules_report_type'), 'report_schedules', ['report_type'], unique=False)
    op.create_index(op.f('ix_report_schedules_next_run'), 'report_schedules', ['next_run'], unique=False)

def downgrade():
    # Drop tables
    op.drop_table('report_schedules')
    op.drop_table('reports')
    op.drop_table('notifications')
    op.drop_table('logs')
    op.drop_table('system_status')
    op.drop_table('alerts')
    op.drop_table('monitoring_metrics')

    # Drop enum types
    op.execute('DROP TYPE metric_type')
    op.execute('DROP TYPE alert_severity')
    op.execute('DROP TYPE alert_status')
    op.execute('DROP TYPE system_health') 