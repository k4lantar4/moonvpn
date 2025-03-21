"""Add backup system indexes

Revision ID: add_backup_system_indexes
Revises: # will be set by Alembic
Create Date: 2024-02-08 10:00:00.000000

This migration adds necessary indexes to the backup system tables for query optimization.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'add_backup_system_indexes'
down_revision = None  # will be set by Alembic
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes to system_backups table
    op.create_index('ix_system_backups_status', 'system_backups', ['status'])
    op.create_index('ix_system_backups_backup_type', 'system_backups', ['backup_type'])
    op.create_index('ix_system_backups_storage_provider', 'system_backups', ['storage_provider'])
    op.create_index('ix_system_backups_created_at', 'system_backups', ['created_at'])
    op.create_index('ix_system_backups_completed_at', 'system_backups', ['completed_at'])
    op.create_index('ix_system_backups_expires_at', 'system_backups', ['expires_at'])
    op.create_index('ix_system_backups_schedule_id', 'system_backups', ['schedule_id'])
    op.create_index('ix_system_backups_created_by', 'system_backups', ['created_by'])
    
    # Add composite indexes for common query patterns
    op.create_index(
        'ix_system_backups_status_created_at',
        'system_backups',
        ['status', 'created_at']
    )
    op.create_index(
        'ix_system_backups_type_status',
        'system_backups',
        ['backup_type', 'status']
    )
    
    # Add indexes to backup_schedules table
    op.create_index('ix_backup_schedules_is_active', 'backup_schedules', ['is_active'])
    op.create_index('ix_backup_schedules_backup_type', 'backup_schedules', ['backup_type'])
    op.create_index('ix_backup_schedules_next_run_at', 'backup_schedules', ['next_run_at'])
    op.create_index('ix_backup_schedules_created_at', 'backup_schedules', ['created_at'])
    op.create_index('ix_backup_schedules_created_by', 'backup_schedules', ['created_by'])
    
    # Add composite indexes for schedule queries
    op.create_index(
        'ix_backup_schedules_active_next_run',
        'backup_schedules',
        ['is_active', 'next_run_at']
    )


def downgrade():
    # Remove indexes from system_backups table
    op.drop_index('ix_system_backups_status', table_name='system_backups')
    op.drop_index('ix_system_backups_backup_type', table_name='system_backups')
    op.drop_index('ix_system_backups_storage_provider', table_name='system_backups')
    op.drop_index('ix_system_backups_created_at', table_name='system_backups')
    op.drop_index('ix_system_backups_completed_at', table_name='system_backups')
    op.drop_index('ix_system_backups_expires_at', table_name='system_backups')
    op.drop_index('ix_system_backups_schedule_id', table_name='system_backups')
    op.drop_index('ix_system_backups_created_by', table_name='system_backups')
    op.drop_index('ix_system_backups_status_created_at', table_name='system_backups')
    op.drop_index('ix_system_backups_type_status', table_name='system_backups')
    
    # Remove indexes from backup_schedules table
    op.drop_index('ix_backup_schedules_is_active', table_name='backup_schedules')
    op.drop_index('ix_backup_schedules_backup_type', table_name='backup_schedules')
    op.drop_index('ix_backup_schedules_next_run_at', table_name='backup_schedules')
    op.drop_index('ix_backup_schedules_created_at', table_name='backup_schedules')
    op.drop_index('ix_backup_schedules_created_by', table_name='backup_schedules')
    op.drop_index('ix_backup_schedules_active_next_run', table_name='backup_schedules') 