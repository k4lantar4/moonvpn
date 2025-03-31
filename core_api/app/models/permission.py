# Import necessary components from SQLAlchemy
from sqlalchemy import Column, Integer, String, Text
# Import relationship for defining model relations
from sqlalchemy.orm import relationship

# Import the Base class from the database configuration
from app.db.base_class import Base
# Import the association table
from .associations import role_permissions_table

# Define the Permission model class, inheriting from Base
class Permission(Base):
    """
    Represents a permission within the system.
    Permissions define specific actions or access rights that can be granted to roles.
    """
    # Define the table name explicitly (optional, SQLAlchemy can infer it)
    __tablename__ = "permissions"

    # Define the primary key column: 'id'
    # - Integer type
    # - Primary key constraint
    # - Indexed for faster lookups
    # - Autoincrementing
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Define the permission name column: 'name'
    # - String type with a maximum length of 255 characters
    # - Must be unique across all permissions
    # - Indexed for faster lookups
    # - Cannot be null
    name = Column(String(255), unique=True, index=True, nullable=False)

    # Define the permission description column: 'description'
    # - Text type for potentially longer descriptions
    # - Can be null (optional description)
    description = Column(Text, nullable=True)

    # Define the many-to-many relationship with Role
    # - 'roles' attribute will hold a list of Role objects associated with this Permission
    # - 'secondary' specifies the association table used for this relationship
    # - 'back_populates' creates a bidirectional relationship, linking back to the 'permissions' attribute in the Role model
    roles = relationship(
        "Role",
        secondary=role_permissions_table,
        back_populates="permissions"
    )

    # Representation method for easy debugging and logging
    def __repr__(self) -> str:
        """
        Provides a string representation of the Permission instance.
        """
        return f"<Permission(id={self.id}, name='{self.name}')>" 