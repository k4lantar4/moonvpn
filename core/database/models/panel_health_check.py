from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer, String, Text, DateTime, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .panel import Panel

class PanelHealthCheck(Base):
    """Model for storing panel health check results using Mapped syntax."""
    
    __tablename__ = "panel_health_checks"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'HEALTHY', 'UNHEALTHY', 'TIMEOUT'
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Store error messages or stats
    # Corrected checked_at definition (no default on client side)
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Relationships
    panel: Mapped["Panel"] = relationship(back_populates="health_checks")

    def __repr__(self) -> str:
        return f"<PanelHealthCheck(id={self.id}, panel_id={self.panel_id}, status='{self.status}')>" 