"""
SystemConfig model for managing system configurations and settings.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class ConfigType(str, enum.Enum):
    """Configuration type enumeration."""
    SYSTEM = "system"
    VPN = "vpn"
    PAYMENT = "payment"
    BOT = "bot"
    API = "api"
    SECURITY = "security"
    CUSTOM = "custom"

class ConfigScope(str, enum.Enum):
    """Configuration scope enumeration."""
    GLOBAL = "global"
    SERVER = "server"
    USER = "user"
    GROUP = "group"
    CUSTOM = "custom"

class SystemConfig(BaseModel):
    """
    SystemConfig model for managing system configurations.
    
    Attributes:
        type: Configuration type
        scope: Configuration scope
        key: Configuration key
        value: Configuration value
        description: Configuration description
        is_active: Whether the configuration is active
        server_id: Reference to server if applicable
        user_id: Reference to user if applicable
        group_id: Reference to group if applicable
        metadata: Additional configuration data
    """
    
    # Configuration identification
    type: Mapped[ConfigType] = mapped_column(Enum(ConfigType), nullable=False)
    scope: Mapped[ConfigScope] = mapped_column(Enum(ConfigScope), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Configuration details
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # References
    server_id: Mapped[Optional[int]] = mapped_column(ForeignKey("server.id"), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("group.id"), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    server: Mapped[Optional["Server"]] = relationship()
    user: Mapped[Optional["User"]] = relationship()
    group: Mapped[Optional["Group"]] = relationship()
    
    def __repr__(self) -> str:
        """String representation of the system configuration."""
        return f"<SystemConfig(type={self.type}, key={self.key})>" 