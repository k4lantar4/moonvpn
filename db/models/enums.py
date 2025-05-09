import enum

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    AGENT = "agent"
    SUPERADMIN = "superadmin"

class PanelStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

class PanelType(str, enum.Enum):
    XUI = "xui"

class InboundStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    INACTIVE = "inactive"
    DELETED = "deleted" # Synced but removed from panel

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing" # Account creation/update in progress
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, enum.Enum):
    WALLET = "wallet"
    GATEWAY = "gateway"
    MANUAL = "manual"
    PROMO = "promo"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    SWITCHED = "switched" 