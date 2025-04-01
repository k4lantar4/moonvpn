"""create bank cards table

Revision ID: f8a43b7e2a0c
Revises: prev_revision_id
Create Date: 2023-04-01 20:10:15.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'f8a43b7e2a0c'
down_revision = None  # Change this to the previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create bank_cards table
    op.create_table(
        'bank_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_name', sa.String(length=100), nullable=False),
        sa.Column('card_number', sa.String(length=20), nullable=False),
        sa.Column('card_holder_name', sa.String(length=100), nullable=False),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('sheba_number', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_bank_cards_id'), 'bank_cards', ['id'], unique=False)
    op.create_index(op.f('ix_bank_cards_bank_name'), 'bank_cards', ['bank_name'], unique=False)
    op.create_index(op.f('ix_bank_cards_card_number'), 'bank_cards', ['card_number'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index(op.f('ix_bank_cards_card_number'), table_name='bank_cards')
    op.drop_index(op.f('ix_bank_cards_bank_name'), table_name='bank_cards')
    op.drop_index(op.f('ix_bank_cards_id'), table_name='bank_cards')
    
    # Drop the bank_cards table
    op.drop_table('bank_cards') 