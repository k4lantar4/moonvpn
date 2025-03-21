"""create admin groups

Revision ID: 20240320_create_admin_groups
Revises: 20240319_create_users
Create Date: 2024-03-20 08:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20240320_create_admin_groups'
down_revision: Union[str, None] = '20240319_create_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE admin_group_type AS ENUM (
            'manage',
            'reports',
            'logs',
            'transactions',
            'outages',
            'sellers',
            'backups'
        )
    """)
    
    op.execute("""
        CREATE TYPE notification_level AS ENUM (
            'critical',
            'error',
            'warning',
            'info',
            'debug'
        )
    """)
    
    # Create admin_groups table
    op.create_table(
        'admin_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', postgresql.ENUM('manage', 'reports', 'logs', 'transactions', 'outages', 'sellers', 'backups', name='admin_group_type'), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=True),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('notification_level', postgresql.ENUM('critical', 'error', 'warning', 'info', 'debug', name='notification_level'), nullable=False),
        sa.Column('notification_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id')
    )
    
    # Create index on admin_groups type
    op.create_index('ix_admin_groups_type', 'admin_groups', ['type'])
    
    # Create admin_group_members table
    op.create_table(
        'admin_group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('added_by', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['admin_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index on admin_group_members
    op.create_index(
        'idx_group_user',
        'admin_group_members',
        ['group_id', 'user_id'],
        unique=True
    )
    
    # Create index on admin_group_members user_id
    op.create_index('ix_admin_group_members_user_id', 'admin_group_members', ['user_id'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_admin_group_members_user_id')
    op.drop_index('idx_group_user')
    op.drop_index('ix_admin_groups_type')
    
    # Drop tables
    op.drop_table('admin_group_members')
    op.drop_table('admin_groups')
    
    # Drop enum types
    op.execute('DROP TYPE notification_level')
    op.execute('DROP TYPE admin_group_type') 