"""User model for authentication and user management."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"

class User(Base):
    """User model for authentication and user management."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # User information
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    
    # Authentication
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Account status
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False
    )
    
    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )
    
    vpn_accounts: Mapped[List["VPNAccount"]] = relationship(
        "VPNAccount",
        back_populates="user",
        lazy="selectin"
    )
    
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        lazy="selectin"
    )
    
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        lazy="selectin"
    )
    
    points_transactions: Mapped[List["PointsTransaction"]] = relationship(
        "PointsTransaction",
        back_populates="user",
        lazy="selectin"
    )
    
    points_redemptions: Mapped[List["PointsRedemption"]] = relationship(
        "PointsRedemption",
        back_populates="user",
        lazy="selectin"
    )
    
    chat_sessions: Mapped[List["LiveChatSession"]] = relationship(
        "LiveChatSession",
        back_populates="user",
        lazy="selectin"
    )
    
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        lazy="selectin"
    )
    
    webhooks: Mapped[List["Webhook"]] = relationship(
        "Webhook",
        back_populates="user",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.username}>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return any(
            permission.name == permission_name
            for role in self.roles
            for permission in role.permissions
        )
    
    def get_active_subscription(self) -> Optional["Subscription"]:
        """Get user's active subscription."""
        return next(
            (sub for sub in self.subscriptions if sub.is_active),
            None
        )
    
    def get_active_vpn_account(self) -> Optional["VPNAccount"]:
        """Get user's active VPN account."""
        return next(
            (acc for acc in self.vpn_accounts if acc.is_active),
            None
        )
    
    def get_points_balance(self) -> int:
        """Get user's current points balance."""
        return sum(
            transaction.points
            for transaction in self.points_transactions
        )
    
    def get_active_chat_session(self) -> Optional["LiveChatSession"]:
        """Get user's active chat session."""
        return next(
            (session for session in self.chat_sessions if session.status == ChatSessionStatus.ACTIVE),
            None
        ) 