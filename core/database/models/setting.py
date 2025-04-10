from typing import Optional
from sqlalchemy import (
    String, Text, Boolean, Integer
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database.session import Base

class Setting(Base):
    """Model for storing system settings using Mapped syntax."""
    
    __tablename__ = "settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Setting(id={self.id}, key='{self.key}', group='{self.group}')>" 