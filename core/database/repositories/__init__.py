# core/database/repositories/__init__.py
"""Repositories for accessing database models."""

from .base_repo import BaseRepository
from .user_repository import UserRepository
from .role_repository import RoleRepository
from .panel_repository import PanelRepository
from .location_repository import LocationRepository
from .plan_repository import PlanRepository
from .plan_category_repository import PlanCategoryRepository
from .client_repository import ClientRepository
from .transaction_repository import TransactionRepository
from .notification_channel_repository import NotificationChannelRepository
from .panel_inbound_repository import PanelInboundRepository
from .discount_code_repository import DiscountCodeRepository
from .order_repository import OrderRepository
from .wallet_repository import WalletRepository
from .bank_card_repository import BankCardRepository
from .payment_repository import PaymentRepository
from .setting_repository import SettingRepository

# Define alias for ClientRepository (for backward compatibility)
ClientAccountRepository = ClientRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "RoleRepository",
    "PanelRepository",
    "LocationRepository",
    "PlanRepository",
    "PlanCategoryRepository",
    "ClientRepository",
    "ClientAccountRepository",
    "TransactionRepository",
    "NotificationChannelRepository",
    "PanelInboundRepository",
    "DiscountCodeRepository",
    "OrderRepository",
    "WalletRepository",
    "BankCardRepository",
    "PaymentRepository",
    "SettingRepository",
]
