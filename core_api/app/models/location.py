# Import necessary components from SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Import the Base class from the database configuration
from app.db.base import Base

# Define the Location model class, inheriting from Base
class Location(Base):
    """
    Location model for representing different server locations.
    This can be used for organizing servers by geographic location, network, etc.
    """
    # Define the table name explicitly
    __tablename__ = "locations"

    # Primary key column: 'id'
    id = Column(Integer, primary_key=True, index=True)

    # Location name column: 'name'
    # - Friendly name of the location (e.g., "Germany", "Frankfurt", "US West")
    # - Should be unique
    name = Column(String(100), unique=True, index=True, nullable=False)

    # Country code column: 'country_code'
    # - ISO 3166-1 alpha-2 country code (e.g., "DE", "FR", "US")
    # - Useful for standardization and potentially displaying flags
    # - Indexed for faster lookups
    country_code = Column(String(2), nullable=False)

    # City column: 'city'
    # - Optional city name associated with the location
    city = Column(String(100), nullable=True)

    # Description column: 'description'
    # - Optional text description of the location
    description = Column(Text, nullable=True)

    # Location status column: 'is_active'
    # - Indicates if this location is currently available for selection
    # - Defaults to True
    is_active = Column(Boolean, default=True)

    # Flag emoji column: 'flag_emoji'
    # - Optional emoji representation of the country's flag
    flag_emoji = Column(String(10), nullable=True)

    # Parent location ID column: 'parent_id'
    # - Foreign key to the parent location in a hierarchical structure
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    # Sort order column: 'sort_order'
    # - For controlling display order in UI
    sort_order = Column(Integer, default=100)

    # Created at column: 'created_at'
    # - Timestamp when the location record was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Updated at column: 'updated_at'
    # - Timestamp when the location record was last updated
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Self-referential relationship for hierarchy
    children = relationship("Location", backref="parent", remote_side=[id])

    # Relationship to Servers
    servers = relationship("Server", back_populates="location")

    # Representation method for easy debugging
    def __repr__(self) -> str:
        """
        Provides a string representation of the Location instance.
        """
        return f"<Location(id={self.id}, name='{self.name}', country='{self.country_code}')>"

    # Note: Relationship to Panel can be added later if needed
    # For example, a Many-to-Many relationship if one panel can host multiple locations
    # or one location can be served by multiple panels.
    # Or a ForeignKey if one location belongs to exactly one panel (less likely). 