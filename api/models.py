import enum
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey,
                        DECIMAL, BigInteger, Text, Enum)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class RoleName(enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True) # Made nullable initially
    phone = Column(String(20), unique=True, nullable=True) # Phone verification later
    email = Column(String(255), unique=True, nullable=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_banned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True) # Added for soft delete/activation

    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    lang = Column(String(10), default='fa')
    last_login = Column(DateTime, nullable=True)
    login_ip = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    # Add relationships for clients, orders, transactions etc. later
    panels_created = relationship("Panel", back_populates="created_by_user") # If tracking creator

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role.name if self.role else None})>"

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(RoleName), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Permissions - Add more granular permissions as needed
    can_manage_panels = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_manage_plans = Column(Boolean, default=False)
    can_approve_payments = Column(Boolean, default=False)
    can_broadcast = Column(Boolean, default=False)

    discount_percent = Column(Integer, default=0) # For sellers
    commission_percent = Column(Integer, default=0) # For sellers

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    flag = Column(String(10), nullable=True) # Emoji flag e.g. 🇩🇪
    country_code = Column(String(2), nullable=True) # ISO 3166-1 alpha-2
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    panels = relationship("Panel", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name})>"

class Panel(Base):
    __tablename__ = "panels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(255), unique=True, nullable=False) # Panel API base URL
    login_path = Column(String(50), default="/login") # Default login path for 3x-ui
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False) # Store securely (e.g., encrypted)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    panel_type = Column(String(50), default='3x-ui') # Could support other types later
    # inbound_id = Column(Integer, nullable=True) # Might manage inbounds separately

    max_clients = Column(Integer, default=0) # 0 means unlimited/unknown
    current_clients = Column(Integer, default=0) # Tracked by system/health checks

    is_active = Column(Boolean, default=True) # Admin can disable
    is_healthy = Column(Boolean, default=False) # Updated by health checks
    last_check = Column(DateTime, nullable=True)
    status_message = Column(String(255), nullable=True) # Store last health check result/error
    priority = Column(Integer, default=0) # For load balancing/selection

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional: track who added it
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    location = relationship("Location", back_populates="panels")
    created_by_user = relationship("User", back_populates="panels_created")
    # Add relationship to Clients later

    def __repr__(self):
        return f"<Panel(id={self.id}, name={self.name}, url={self.url})>"

# Add other models later: Plan, Client, Order, Transaction, Payment, Settings, DiscountCode, etc.
