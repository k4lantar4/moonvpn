from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, DateTime, ForeignKey, BigInteger,
    Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .client_account import ClientAccount
#     from .panel import Panel

class ClientMigration(Base):
    """Model for tracking client migrations between panels using Mapped syntax."""
    
    __tablename__ = "client_migrations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    from_panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id"), nullable=False)
    to_panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id"), nullable=False)
    old_client_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    new_client_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    old_remark: Mapped[str] = mapped_column(String(255), nullable=False)
    new_remark: Mapped[str] = mapped_column(String(255), nullable=False)
    traffic_remaining: Mapped[int] = mapped_column(BigInteger, nullable=False) # Bytes?
    time_remaining_days: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    migrated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    # Renamed client_account to client to match back_populates in ClientAccount
    client: Mapped["ClientAccount"] = relationship(foreign_keys=[client_id], back_populates="migrations")
    from_panel: Mapped["Panel"] = relationship(foreign_keys=[from_panel_id])
    to_panel: Mapped["Panel"] = relationship(foreign_keys=[to_panel_id])

    def __repr__(self) -> str:
        return f"<ClientMigration(id={self.id}, client_id={self.client_id}, from={self.from_panel_id}, to={self.to_panel_id})>"