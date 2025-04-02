"""Add max_users to plans table

Revision ID: 004
Revises: 003
Create Date: 2023-08-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003' # Adjust this to match your previous migration
branch_labels = None
depends_on = None


def upgrade():
    """Add max_users column to plans table."""
    op.add_column(
        'plans',
        sa.Column('max_users', sa.Integer(), nullable=True)
    )


def downgrade():
    """Remove max_users column from plans table."""
    op.drop_column('plans', 'max_users') 