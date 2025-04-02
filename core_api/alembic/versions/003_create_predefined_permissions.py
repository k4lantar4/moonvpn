"""Create predefined permissions

Revision ID: 003_create_predefined_permissions
Revises: 002_create_seller_role
Create Date: 2023-08-20 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql import table, column

from app.core.permissions import get_all_permissions

# revision identifiers, used by Alembic.
revision = '003_create_predefined_permissions'
down_revision = '002_create_seller_role'
branch_labels = None
depends_on = None


def upgrade():
    # Create tables for the migration
    permissions_table = table(
        'permissions',
        column('id', sa.Integer),
        column('name', sa.String),
        column('description', sa.String)
    )
    
    # Create connection for executing data operations
    connection = op.get_bind()
    session = Session(bind=connection)
    
    # Get all predefined permissions
    all_permissions = get_all_permissions()
    
    # Insert permissions if they don't exist
    for permission_name in all_permissions:
        # Check if permission already exists
        existing = session.execute(
            sa.select(permissions_table).where(permissions_table.c.name == permission_name)
        ).fetchone()
        
        if not existing:
            # Insert the permission
            description = f"Permission to {permission_name.replace(':', ' ')}"
            session.execute(
                permissions_table.insert().values(
                    name=permission_name,
                    description=description
                )
            )
    
    # Make sure to flush changes to the database
    session.commit()


def downgrade():
    # Connect to the database
    connection = op.get_bind()
    session = Session(bind=connection)
    
    # Reference to permissions table
    permissions_table = table(
        'permissions',
        column('id', sa.Integer),
        column('name', sa.String)
    )
    
    # Get all predefined permissions
    all_permissions = get_all_permissions()
    
    # Delete all predefined permissions
    for permission_name in all_permissions:
        session.execute(
            permissions_table.delete().where(permissions_table.c.name == permission_name)
        )
    
    # Commit changes
    session.commit() 