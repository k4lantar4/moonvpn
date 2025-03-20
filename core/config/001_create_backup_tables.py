"""create backup tables

Revision ID: 001
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create system_backups table
    op.create_table(
        'system_backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('restore_status', sa.String(), nullable=True),
        sa.Column('restore_start_time', sa.DateTime(), nullable=True),
        sa.Column('restore_end_time', sa.DateTime(), nullable=True),
        sa.Column('restore_error_message', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for system_backups
    op.create_index('ix_system_backups_type', 'system_backups', ['type'])
    op.create_index('ix_system_backups_status', 'system_backups', ['status'])
    op.create_index('ix_system_backups_start_time', 'system_backups', ['start_time'])
    
    # Create backup_schedules table
    op.create_table(
        'backup_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backup_type', sa.String(), nullable=False),
        sa.Column('schedule_type', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('retention_days', sa.Integer(), default=30),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('backup_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['backup_id'], ['system_backups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for backup_schedules
    op.create_index('ix_backup_schedules_backup_type', 'backup_schedules', ['backup_type'])
    op.create_index('ix_backup_schedules_schedule_type', 'backup_schedules', ['schedule_type'])
    op.create_index('ix_backup_schedules_is_active', 'backup_schedules', ['is_active'])
    op.create_index('ix_backup_schedules_next_run', 'backup_schedules', ['next_run'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_backup_schedules_next_run')
    op.drop_index('ix_backup_schedules_is_active')
    op.drop_index('ix_backup_schedules_schedule_type')
    op.drop_index('ix_backup_schedules_backup_type')
    op.drop_index('ix_system_backups_start_time')
    op.drop_index('ix_system_backups_status')
    op.drop_index('ix_system_backups_type')
    
    # Drop tables
    op.drop_table('backup_schedules')
    op.drop_table('system_backups') 