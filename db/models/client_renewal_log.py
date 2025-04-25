from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text, BigInteger, Column, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import Base


class OperationType(str, PyEnum):
    EXTEND_TIME = "extend_time"
    EXTEND_TRAFFIC = "extend_traffic"
    FULL_RENEW = "full_renew"


class ClientRenewalLog(Base):
    """Model for tracking client account renewals."""
    
    __tablename__ = "client_renewal_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("client_accounts.id"), nullable=False)
    time_added = Column(Integer, nullable=True)  # Days added
    data_added = Column(Float, nullable=True)  # GB added
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="renewal_logs")
    client = relationship("ClientAccount", back_populates="renewal_logs")

    # Indexes
    __table_args__ = (
        Index("ix_client_renewal_log_user_id", "user_id"),
        Index("ix_client_renewal_log_client_id", "client_id"),
        Index("ix_client_renewal_log_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ClientRenewalLog(id={self.id}, client_id={self.client_id}, time_added={self.time_added}, data_added={self.data_added})>" 