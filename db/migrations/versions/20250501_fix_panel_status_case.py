"""fix panel status case

Revision ID: 20250501_fix_panel_status
Revises: 9919982bb3d2
Create Date: 2025-05-01 04:00:00.000000+03:30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250501_fix_panel_status'
down_revision = '9919982bb3d2'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Update lowercase status values to uppercase
    op.execute("UPDATE panels SET status = 'ACTIVE' WHERE status = 'active'")
    op.execute("UPDATE panels SET status = 'INACTIVE' WHERE status = 'inactive'")
    op.execute("UPDATE panels SET status = 'DELETED' WHERE status = 'deleted'")

def downgrade() -> None:
    # Convert back to lowercase if needed
    op.execute("UPDATE panels SET status = 'active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE panels SET status = 'inactive' WHERE status = 'INACTIVE'")
    op.execute("UPDATE panels SET status = 'deleted' WHERE status = 'DELETED'") 