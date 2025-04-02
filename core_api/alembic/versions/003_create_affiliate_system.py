"""Create affiliate system tables and fields

Revision ID: 003
Revises: 002
Create Date: 2024-04-02 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add fields to User table for the affiliate system
    op.add_column('users', sa.Column('affiliate_code', sa.String(20), nullable=True, unique=True))
    op.add_column('users', sa.Column('affiliate_balance', sa.DECIMAL(10, 2), nullable=False, server_default='0.00'))
    op.add_column('users', sa.Column('is_affiliate_enabled', sa.Boolean, nullable=False, server_default='1'))
    
    # Create affiliate commissions table
    op.create_table(
        'affiliate_commissions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('referrer_id', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('percentage', sa.DECIMAL(5, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('commission_type', sa.String(20), nullable=False, server_default='order'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
    )
    
    # Create affiliate settings table
    op.create_table(
        'affiliate_settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('commission_percentage', sa.DECIMAL(5, 2), nullable=False, server_default='10.00'),
        sa.Column('min_withdrawal_amount', sa.DECIMAL(10, 2), nullable=False, server_default='100000.00'),
        sa.Column('code_length', sa.Integer, nullable=False, server_default='8'),
        sa.Column('is_enabled', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create affiliate withdrawals table
    op.create_table(
        'affiliate_withdrawals',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_id', sa.Integer, sa.ForeignKey('transactions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_by', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('note', sa.Text, nullable=True),
    )
    
    # Create indexes
    op.create_index(op.f('ix_users_affiliate_code'), 'users', ['affiliate_code'], unique=True)
    op.create_index(op.f('ix_affiliate_commissions_user_id'), 'affiliate_commissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_affiliate_commissions_referrer_id'), 'affiliate_commissions', ['referrer_id'], unique=False)
    op.create_index(op.f('ix_affiliate_commissions_order_id'), 'affiliate_commissions', ['order_id'], unique=False)
    op.create_index(op.f('ix_affiliate_withdrawals_user_id'), 'affiliate_withdrawals', ['user_id'], unique=False)
    
    # Insert default affiliate settings
    op.execute("""
    INSERT INTO affiliate_settings (commission_percentage, min_withdrawal_amount, code_length, is_enabled)
    VALUES (10.00, 100000.00, 8, 1)
    """)
    
    # Add trigger to generate affiliate code for new users
    op.execute("""
    CREATE TRIGGER after_user_insert
    AFTER INSERT ON users
    FOR EACH ROW
    BEGIN
        DECLARE code_length INT;
        DECLARE affiliate_code VARCHAR(20);
        
        -- Get code length from settings
        SELECT COALESCE(code_length, 8) INTO code_length FROM affiliate_settings LIMIT 1;
        
        -- Generate a random alphanumeric code
        SET affiliate_code = SUBSTRING(MD5(CONCAT(NEW.id, RAND())), 1, code_length);
        
        -- Update the user with the generated code
        UPDATE users SET affiliate_code = affiliate_code WHERE id = NEW.id;
    END;
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS after_user_insert")
    
    # Drop tables
    op.drop_table('affiliate_withdrawals')
    op.drop_table('affiliate_settings')
    op.drop_table('affiliate_commissions')
    
    # Drop columns from users table
    op.drop_column('users', 'affiliate_code')
    op.drop_column('users', 'affiliate_balance')
    op.drop_column('users', 'is_affiliate_enabled') 