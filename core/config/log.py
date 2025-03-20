"""
SystemLog model for managing system logs and audit trails.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class LogLevel(str, enum.Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(str, enum.Enum):
    """Log category enumeration."""
    SYSTEM = "system"
    SECURITY = "security"
    USER = "user"
    PAYMENT = "payment"
    VPN = "vpn"
    API = "api"
    BOT = "bot"
    CUSTOM = "custom"

class SystemLog(BaseModel):
    """
    SystemLog model for managing system logs.
    
    Attributes:
        level: Log level
        category: Log category
        message: Log message
        source: Log source
        user_id: Reference to user if applicable
        ip_address: IP address of the request
        user_agent: User agent string
        metadata: Additional log data
    """
    
    # Log identification
    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), nullable=False)
    category: Mapped[LogCategory] = mapped_column(Enum(LogCategory), nullable=False)
    
    # Log details
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship()
    
    def __repr__(self) -> str:
        """String representation of the system log."""
        return f"<SystemLog(level={self.level}, category={self.category})>" 