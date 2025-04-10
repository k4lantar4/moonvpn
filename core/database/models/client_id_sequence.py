from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer, String, DateTime, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .location import Location

class ClientIdSequence(Base):
    """Model for managing unique client ID sequences per location using Mapped syntax."""
    
    __tablename__ = "client_id_sequences"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Changed unique=True to index=True to match SQL more closely (it has a unique index, not constraint)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False, index=True, unique=True) 
    last_id: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    prefix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    
    # Relationships
    # Add relationship back to Location if Location model defines `id_sequence`
    # location: Mapped["Location"] = relationship(back_populates="id_sequence")

    def __repr__(self) -> str:
        return f"<ClientIdSequence(id={self.id}, location_id={self.location_id}, last_id={self.last_id})>" 