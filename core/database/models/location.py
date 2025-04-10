from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .panel import Panel
#     from .client import Client # Assuming Client model exists

class Location(Base):
    """Model for server locations."""
    
    __tablename__ = "locations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    flag: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # default_inbound_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # FK to panel_inbounds? Needs clarification
    protocols_supported: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    inbound_tag_pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_remark_prefix: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    remark_pattern: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    migration_remark_pattern: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None, nullable=True
    )
    
    # Relationships
    panels: Mapped[List["Panel"]] = relationship("Panel", back_populates="location")
    # clients: Mapped[List["Client"]] = relationship("Client", back_populates="location") # Uncomment when Client model is defined
    client_accounts: Mapped[List["ClientAccount"]] = relationship("ClientAccount", back_populates="location")

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name='{self.name}')>" 