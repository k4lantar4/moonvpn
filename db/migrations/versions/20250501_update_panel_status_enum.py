"""update panel status enum values

Revision ID: 20250501_update_panel_status
Revises: 20250501_fix_panel_status
Create Date: 2025-05-01 04:00:00.000000+03:30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250501_update_panel_status'
down_revision = '20250501_fix_panel_status'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # First convert existing values to uppercase
    op.execute("UPDATE panels SET status = 'ACTIVE' WHERE status = 'active'")
    op.execute("UPDATE panels SET status = 'INACTIVE' WHERE status = 'inactive'")
    op.execute("UPDATE panels SET status = 'DELETED' WHERE status = 'deleted'")
    
    # Then modify the enum type
    op.execute("ALTER TABLE panels MODIFY COLUMN status ENUM('ACTIVE', 'INACTIVE', 'DELETED') NOT NULL DEFAULT 'ACTIVE'")

def downgrade() -> None:
    # Convert values back to lowercase
    op.execute("UPDATE panels SET status = 'active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE panels SET status = 'inactive' WHERE status = 'INACTIVE'")
    op.execute("UPDATE panels SET status = 'deleted' WHERE status = 'DELETED'")
    
    # Restore original enum type
    op.execute("ALTER TABLE panels MODIFY COLUMN status ENUM('active', 'inactive', 'disabled', 'error', 'deleted') NOT NULL DEFAULT 'active'") 