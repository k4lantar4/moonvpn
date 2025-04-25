"""
ماژول models - تعریف مدل‌های پایگاه داده با SQLAlchemy
"""

from typing import Any, Dict, List, Optional, Type, cast

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base, declared_attr

# تنظیم naming convention استاندارد برای محدودیت‌ها (constraints)
convention: Dict[str, Any] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

# کلاس پایه برای همه مدل‌ها
class CustomBase:
    pass # Models define __tablename__ explicitly

# --- DEFINE Base FIRST ---
Base = declarative_base(metadata=metadata, cls=CustomBase)

# --- THEN import models that depend on Base ---
from .user import User
from .panel import Panel
from .inbound import Inbound
from .account_transfer import AccountTransfer
from .bank_card import BankCard
from .client_account import ClientAccount
from .discount_code import DiscountCode
# from .account import Account
from .plan import Plan
from .setting import Setting
from .transaction import Transaction
from .order import Order
from .test_account_log import TestAccountLog
from .receipt_log import ReceiptLog
from .notification_log import NotificationLog
from .client_renewal_log import ClientRenewalLog
from .enums import (
    UserRole,
    PanelStatus,
    InboundStatus,
    OrderStatus,
    TransactionStatus,
    # PaymentMethod,
    AccountStatus,
    # UserStatus
)

# لیست مدل‌ها برای استفاده توسط Alembic و __init__
__all__ = [
    "Base",
    "User",
    "Panel",
    "Inbound",
    "AccountTransfer",
    "BankCard",
    "ClientAccount",
    "DiscountCode",
    # "Account",
    "Plan",
    "Setting",
    "Transaction",
    "Order",
    "TestAccountLog",
    "ReceiptLog",
    "NotificationLog",
    "ClientRenewalLog",
    # Enums are also often included if needed directly from db.models
    "UserRole",
    "PanelStatus",
    "InboundStatus",
    "OrderStatus",
    "TransactionStatus",
    "AccountStatus",
    # "UserStatus"
] 