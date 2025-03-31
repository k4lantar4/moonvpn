# Define association tables for many-to-many relationships

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.base_class import Base

# Association table for the many-to-many relationship between Role and Permission
role_permissions_table = Table(
    "role_permissions",  # Name of the association table in the database
    Base.metadata,       # Associate with the metadata of the Base class
    # Column for the foreign key referencing the 'roles' table
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    # Column for the foreign key referencing the 'permissions' table
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True)
)

# Add more association tables here if needed in the future 