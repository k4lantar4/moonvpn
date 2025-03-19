"""Role model for user permissions and access control."""
from typing import List, Optional
from sqlalchemy import String, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

# Association tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    mapped_column("user_id", ForeignKey("user.id"), primary_key=True),
    mapped_column("role_id", ForeignKey("role.id"), primary_key=True)
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    mapped_column("role_id", ForeignKey("role.id"), primary_key=True),
    mapped_column("permission_id", ForeignKey("permission.id"), primary_key=True)
)

class Role(Base):
    """Role model for user permissions and access control."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Role information
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin"
    )
    
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the role."""
        return f"<Role {self.name}>"
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        return any(permission.name == permission_name for permission in self.permissions)

class Permission(Base):
    """Permission model for granular access control."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Permission information
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the permission."""
        return f"<Permission {self.name}>" 