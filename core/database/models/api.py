"""API models for managing API keys and requests."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class APIKeyStatus(str, enum.Enum):
    """API key status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"

class APIKey(Base):
    """API key model for managing API access."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Key information
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[APIKeyStatus] = mapped_column(
        Enum(APIKeyStatus),
        default=APIKeyStatus.ACTIVE,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Access control
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    requests: Mapped[List["APIRequest"]] = relationship(
        "APIRequest",
        back_populates="api_key",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the API key."""
        return f"<APIKey {self.name}>"
    
    def revoke(self) -> None:
        """Revoke the API key."""
        self.status = APIKeyStatus.REVOKED
        self.is_active = False
    
    def is_valid(self) -> bool:
        """Check if API key is valid."""
        if not self.is_active or self.status != APIKeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(self.expires_at.tzinfo) > self.expires_at:
            self.status = APIKeyStatus.EXPIRED
            self.is_active = False
            return False
        return True

class APIRequest(Base):
    """API request model for tracking API usage."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Request information
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # API key relationship
    api_key_id: Mapped[int] = mapped_column(ForeignKey("apikey.id"), nullable=False)
    
    # Request details
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    api_key: Mapped["APIKey"] = relationship("APIKey", back_populates="requests")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the API request."""
        return f"<APIRequest {self.method} {self.endpoint}>"

class APIRateLimit(Base):
    """API rate limit model for managing request limits."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Rate limit information
    api_key_id: Mapped[int] = mapped_column(ForeignKey("apikey.id"), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    api_key: Mapped["APIKey"] = relationship("APIKey", back_populates="rate_limits")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the rate limit."""
        return f"<APIRateLimit {self.api_key.name}>"
    
    def is_exceeded(self) -> bool:
        """Check if rate limit is exceeded."""
        return self.request_count >= self.api_key.rate_limit

class Webhook(Base):
    """Webhook model for managing webhook endpoints."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Webhook information
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Events
    events: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Security
    secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="webhooks")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the webhook."""
        return f"<Webhook {self.name}>"
    
    def trigger(self, event: str, data: dict) -> None:
        """Trigger the webhook with event data."""
        if event not in self.events:
            return
        self.last_triggered_at = datetime.now(self.created_at.tzinfo)
        # Webhook triggering logic would be implemented in the service layer 