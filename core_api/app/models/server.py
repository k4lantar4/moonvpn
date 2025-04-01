from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .location import Location
    from .panel import Panel

class Server(Base):
    """ Represents a server instance where panels can be hosted. """
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    ip_address = Column(String(50), unique=True, index=True, nullable=False)
    hostname = Column(String(255), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    # Foreign Key to Location model
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    location = relationship("Location", back_populates="servers")
    panels = relationship("Panel", back_populates="server")

    def __repr__(self) -> str:
        return f"<Server(id={self.id}, name='{self.name}', ip='{self.ip_address}')>" 