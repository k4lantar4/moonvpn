"""
منطق کلی هندلرهای ادمین
"""

from aiogram import Router
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .main_callbacks import register_admin_main_callbacks
from .panel_callbacks import register_admin_panel_callbacks
from .receipt_callbacks import register_admin_receipt_callbacks
from .bank_card_callbacks import register_admin_bank_card_callbacks
from .user_callbacks import register_admin_user_callbacks
from .plan_callbacks import register_admin_plan_callbacks
from .order_callbacks import register_admin_order_callbacks

def register_all_admin_callbacks(router: Router) -> None:
    """ثبت تمامی کالبک‌های ادمین در روتر اصلی"""
    register_admin_main_callbacks(router)
    register_admin_panel_callbacks(router)
    register_admin_receipt_callbacks(router)
    register_admin_bank_card_callbacks(router)
    register_admin_user_callbacks(router)
    register_admin_plan_callbacks(router)
    register_admin_order_callbacks(router) 