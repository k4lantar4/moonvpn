"""add_error_status_to_panel_enum

Revision ID: 9919982bb3d2
Revises: 20250429_create_inbounds
Create Date: 2025-05-01 03:42:59.733043+03:30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9919982bb3d2'
down_revision = '20250429_create_inbounds'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter panel status enum to include 'error' and 'disabled' values
    op.execute("ALTER TABLE panels MODIFY COLUMN status ENUM('active', 'inactive', 'disabled', 'error', 'deleted') NOT NULL DEFAULT 'active'")


def downgrade() -> None:
    # Revert panel status enum back to original values
    op.execute("ALTER TABLE panels MODIFY COLUMN status ENUM('active', 'inactive', 'deleted') NOT NULL DEFAULT 'active'") 