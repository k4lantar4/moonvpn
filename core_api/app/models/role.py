from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base
from .associations import role_permissions_table

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship (One-to-Many: Role to Users)
    users = relationship("User", back_populates="role")

    # Relationship (Many-to-Many: Role to Permissions)
    permissions = relationship(
        "Permission",
        secondary=role_permissions_table,
        back_populates="roles"
    )

    # Note: Permission model and role_permissions table will be defined later
