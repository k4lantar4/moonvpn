"""Add wallet model

Revision ID: 20240630wallet
Depends on: 5f6b84a12d7e
Create Date: 2024-06-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240630wallet'
down_revision = '5f6b84a12d7e'
branch_labels = None
depends_on = None


def upgrade():
    # Check if wallets table exists
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if 'wallets' not in insp.get_table_names():
        # Create wallet table
        op.create_table('wallets',
            sa.Column('id', sa.BigInteger(), sa.Identity(always=False, start=1, increment=1), nullable=False),
            sa.Column('user_id', sa.BigInteger(), nullable=False, index=True),
            sa.Column('balance', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0'),
            sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create unique index on user_id
        op.create_index('ix_wallets_user_id', 'wallets', ['user_id'], unique=True)


def downgrade():
    # Drop wallet table
    try:
        op.drop_index('ix_wallets_user_id', table_name='wallets')
    except:
        pass
    op.drop_table('wallets') 