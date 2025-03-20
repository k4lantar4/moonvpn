"""
Location model for managing VPN server locations.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import BaseModel

class Location(BaseModel):
    """
    Location model for managing VPN server locations.
    
    Attributes:
        name: Location name
        country: Country code (ISO 3166-1 alpha-2)
        city: City name
        region: Region/state name
        latitude: Location latitude
        longitude: Location longitude
        is_active: Whether the location is active
        priority: Location priority for server selection
        description: Location description
    """
    
    # Location identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Geographic coordinates
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Location status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    servers: Mapped[List["Server"]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the location."""
        return f"<Location(name={self.name}, country={self.country})>" 