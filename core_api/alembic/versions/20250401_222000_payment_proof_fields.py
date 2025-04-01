"""Payment proof fields

Revision ID: 20250401_222000
Revises: 20250401_212830
Create Date: 2025-04-01 22:20:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20250401_222000'
down_revision = '20250401_212830'
branch_labels = None
depends_on = None


def upgrade():
    # Enhance orders table with payment proof fields
    op.add_column('orders', sa.Column('payment_proof_img_url', sa.String(255), nullable=True))
    op.add_column('orders', sa.Column('payment_proof_submitted_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('payment_verified_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('payment_verification_admin_id', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('payment_rejection_reason', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('payment_proof_telegram_msg_id', sa.String(50), nullable=True))
    
    # Add foreign key for the verification admin
    op.create_foreign_key(
        'fk_orders_payment_verification_admin',
        'orders', 'users',
        ['payment_verification_admin_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for faster queries by payment status
    op.create_index(
        op.f('ix_orders_payment_verified_at'),
        'orders',
        ['payment_verified_at'],
        unique=False
    )


def downgrade():
    # Drop foreign key first
    op.drop_constraint('fk_orders_payment_verification_admin', 'orders', type_='foreignkey')
    
    # Drop index
    op.drop_index(op.f('ix_orders_payment_verified_at'), table_name='orders')
    
    # Drop columns
    op.drop_column('orders', 'payment_proof_telegram_msg_id')
    op.drop_column('orders', 'payment_rejection_reason')
    op.drop_column('orders', 'payment_verification_admin_id')
    op.drop_column('orders', 'payment_verified_at')
    op.drop_column('orders', 'payment_proof_submitted_at')
    op.drop_column('orders', 'payment_proof_img_url') 