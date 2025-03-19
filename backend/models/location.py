"""
Location database model.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Location(Base):
    """
    Location model for VPN server locations.
    
    Represents a geographic location where VPN servers may be hosted.
    Each location can have multiple servers associated with it.
    """
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String(2), nullable=False, index=True)  # Country code (e.g., US, DE)
    flag = Column(String, nullable=True)  # Flag emoji or icon code
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    servers = relationship("Server", back_populates="location", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """String representation of the location."""
        return f"<Location(id={self.id}, name={self.name}, code={self.code})>" 