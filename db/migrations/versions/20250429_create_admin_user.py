"""create_admin_user

Revision ID: 20250429_create_admin_user
Revises: 20250429_seed_initial_data
Create Date: 2025-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = '20250429_create_admin_user'
down_revision = '20250429_seed_initial_data'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create tables references
    admin_permissions = table('admin_permissions',
        column('id', sa.BigInteger),
        column('user_id', sa.BigInteger),
        column('can_approve_receipt', sa.Boolean),
        column('can_support', sa.Boolean),
        column('can_view_users', sa.Boolean),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )

    # Insert admin permissions for existing admin user
    op.bulk_insert(admin_permissions, [
        {
            'id': 1,
            'user_id': 1,  # Admin user ID
            'can_approve_receipt': True,
            'can_support': True,
            'can_view_users': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ])

def downgrade() -> None:
    # Remove admin permissions
    op.execute("DELETE FROM admin_permissions WHERE user_id = 1") 