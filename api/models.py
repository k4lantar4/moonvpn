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
    panels_created = relationship("Panel", back_populates="created_by_user") # If tracking creator
    clients = relationship("Client", back_populates="user")
    orders = relationship("Order", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    payments_verified = relationship("Payment", foreign_keys="[Payment.admin_id]", back_populates="admin")

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
    
    # Additional fields for role types
    is_admin = Column(Boolean, default=False)
    is_seller = Column(Boolean, default=False)

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
    
    # New fields for inbound management
    default_inbound_id = Column(Integer, nullable=True)
    protocols_supported = Column(String(100), nullable=True)  # comma-separated list
    inbound_tag_pattern = Column(String(100), nullable=True)
    default_remark_prefix = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    panels = relationship("Panel", back_populates="location")
    client_id_sequences = relationship("ClientIdSequence", back_populates="location")
    clients = relationship("Client", back_populates="location")

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

    # Fields max_clients and current_clients removed as they're not needed

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
    clients = relationship("Client", back_populates="panel")
    health_checks = relationship("PanelHealthCheck", back_populates="panel")

    def __repr__(self):
        return f"<Panel(id={self.id}, name={self.name}, url={self.url})>"

class PlanCategory(Base):
    __tablename__ = "plan_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sorting_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with plans
    plans = relationship("Plan", back_populates="category")
    
    def __repr__(self):
        return f"<PlanCategory(id={self.id}, name={self.name})>"

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    traffic = Column(BigInteger, nullable=False)  # in GB
    days = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # JSON array of additional features
    
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    max_clients = Column(Integer, nullable=True)
    protocols = Column(String(255), nullable=True)  # comma-separated protocols (vmess, vless)
    
    category_id = Column(Integer, ForeignKey("plan_categories.id"), nullable=True)
    sorting_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("PlanCategory", back_populates="plans")
    clients = relationship("Client", back_populates="plan")
    orders = relationship("Order", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name}, traffic={self.traffic}GB, days={self.days})>"

class ClientIdSequence(Base):
    __tablename__ = "client_id_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    last_id = Column(Integer, default=0)
    prefix = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    location = relationship("Location", back_populates="client_id_sequences")
    
    def __repr__(self):
        return f"<ClientIdSequence(id={self.id}, location_id={self.location_id}, last_id={self.last_id})>"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    
    payment_method = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    discount_amount = Column(DECIMAL(10, 2), default=0)
    final_amount = Column(DECIMAL(10, 2), nullable=False)
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    plan = relationship("Plan", back_populates="orders")
    clients = relationship("Client", back_populates="order")
    payments = relationship("Payment", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"

class ClientStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    FROZEN = "frozen"

class Protocol(enum.Enum):
    VMESS = "vmess"
    VLESS = "vless"

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    client_uuid = Column(String(36), nullable=False)
    email = Column(String(255), nullable=False)
    remark = Column(String(255), nullable=False)  # Display name identifier
    
    expire_date = Column(DateTime, nullable=False)
    traffic = Column(BigInteger, nullable=False)  # in GB
    used_traffic = Column(BigInteger, default=0)  # in GB
    
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVE)
    protocol = Column(Enum(Protocol), nullable=False)
    
    config_json = Column(Text, nullable=True)  # JSON configuration for additional features
    subscription_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    freeze_start = Column(DateTime, nullable=True)
    freeze_end = Column(DateTime, nullable=True)
    is_trial = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=False)
    last_notified = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="clients")
    panel = relationship("Panel", back_populates="clients")
    location = relationship("Location", back_populates="clients")
    plan = relationship("Plan", back_populates="clients")
    order = relationship("Order", back_populates="clients")
    
    def __repr__(self):
        return f"<Client(id={self.id}, user_id={self.user_id}, email={self.email}, status={self.status})>"

class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    PURCHASE = "purchase"
    REFUND = "refund"
    COMMISSION = "commission"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    reference_id = Column(Integer, nullable=True)  # Can reference a payment_id or order_id
    description = Column(Text, nullable=True)
    balance_after = Column(DECIMAL(10, 2), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.type})>"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    
    payment_method = Column(String(50), nullable=False)
    payment_gateway_id = Column(String(100), nullable=True)
    card_number = Column(String(20), nullable=True)
    tracking_code = Column(String(100), nullable=True)
    receipt_image = Column(String(255), nullable=True)
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who verified
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="payments")
    admin = relationship("User", foreign_keys=[admin_id], back_populates="payments_verified")
    order = relationship("Order", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"

class BankCard(Base):
    __tablename__ = "bank_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(100), nullable=False)
    card_number = Column(String(20), nullable=False)
    account_number = Column(String(30), nullable=True)
    owner_name = Column(String(100), nullable=False)
    
    is_active = Column(Boolean, default=True)
    rotation_priority = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    daily_limit = Column(DECIMAL(15, 2), nullable=True)
    monthly_limit = Column(DECIMAL(15, 2), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BankCard(id={self.id}, bank_name={self.bank_name}, card_number={self.card_number})>"

class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # admin, payment, report, log, alert, backup
    channel_id = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    notification_types = Column(Text, nullable=True)  # JSON array of notification types
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationChannel(id={self.id}, name={self.name}, channel_id={self.channel_id})>"

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    group = Column(String(50), nullable=True)  # For grouping related settings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Settings(id={self.id}, key={self.key})>"

class PanelHealthCheck(Base):
    __tablename__ = "panel_health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    status = Column(String(50), nullable=False)  # 'healthy', 'error', etc.
    response_time_ms = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON string with detailed info
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    panel = relationship("Panel", back_populates="health_checks")
    
    def __repr__(self):
        return f"<PanelHealthCheck(id={self.id}, panel_id={self.panel_id}, status='{self.status}')>"

# Future models: DiscountCode, UserDevice, AuditLog, etc.
