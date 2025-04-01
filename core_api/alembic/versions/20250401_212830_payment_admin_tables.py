"""Payment admin tables

Revision ID: 20250401_212830
Revises: create_bank_cards_table
Create Date: 2025-04-01 21:28:30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20250401_212830'
down_revision = 'create_bank_cards_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create payment_admin_assignments table
    op.create_table(
        'payment_admin_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bank_card_id', sa.Integer(), nullable=True),
        sa.Column('telegram_group_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_assignment_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bank_card_id'], ['bank_cards.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create payment_admin_metrics table for tracking performance
    op.create_table(
        'payment_admin_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('total_approved', sa.Integer(), nullable=False, default=0),
        sa.Column('total_rejected', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_response_time_seconds', sa.Float(), nullable=True),
        sa.Column('last_processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index for efficient queries
    op.create_index(
        op.f('ix_payment_admin_assignments_user_id'),
        'payment_admin_assignments',
        ['user_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_payment_admin_assignments_bank_card_id'),
        'payment_admin_assignments',
        ['bank_card_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_payment_admin_metrics_user_id'),
        'payment_admin_metrics',
        ['user_id'],
        unique=True
    )


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_payment_admin_metrics_user_id'), table_name='payment_admin_metrics')
    op.drop_index(op.f('ix_payment_admin_assignments_bank_card_id'), table_name='payment_admin_assignments')
    op.drop_index(op.f('ix_payment_admin_assignments_user_id'), table_name='payment_admin_assignments')
    
    # Drop tables
    op.drop_table('payment_admin_metrics')
    op.drop_table('payment_admin_assignments')
