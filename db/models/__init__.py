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


# کلاس پایه برای همه مدل‌ها - سازگار با نسخه‌های قدیمی SQLAlchemy
class CustomBase:
    """کلاس پایه برای تمام مدل‌های SQLAlchemy"""
    
    # اضافه کردن پیشوند به نام جداول به صورت خودکار
    @declared_attr
    def __tablename__(cls) -> str:
        """تبدیل نام کلاس به نام جدول"""
        return cls.__name__.lower()


# ایجاد کلاس پایه با declarative_base
Base = declarative_base(metadata=metadata, cls=CustomBase)


# ایمپورت مدل‌های مورد نیاز
from .user import User
from .panel import Panel
from .inbound import Inbound
from .account_transfer import AccountTransfer
from .bank_card import BankCard
from .client_account import ClientAccount
from .discount_code import DiscountCode
# from .account import Account  # Temporarily commented out
from .plan import Plan
from .setting import Setting
from .transaction import Transaction
from .order import Order
from .test_account_log import TestAccountLog
from .receipt_log import ReceiptLog
from .notification_log import NotificationLog
from .enums import (
    UserRole,
    PanelStatus,
    InboundStatus,
    OrderStatus,
    TransactionStatus,
    PaymentMethod,
    AccountStatus
)

# لیست مدل‌ها برای استفاده توسط Alembic
__all__ = [
    "Base",
    "User",
    "Panel",
    "Inbound",
    "AccountTransfer",
    "BankCard",
    "ClientAccount",
    "DiscountCode",
    # "Account",  # Temporarily commented out
    "Plan",
    "Setting",
    "Transaction",
    "Order",
    "TestAccountLog",
    "ReceiptLog",
    "NotificationLog",
    "UserRole",
    "PanelStatus",
    "InboundStatus",
    "OrderStatus",
    "TransactionStatus",
    "PaymentMethod",
    "AccountStatus",
] 