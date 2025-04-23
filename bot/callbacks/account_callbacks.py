"""
هندلرهای Callback مربوط به مدیریت حساب‌ها
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.buttons.account_buttons import MY_ACCOUNTS_CB
from bot.commands.myaccounts import _display_my_accounts

async def handle_my_accounts_callback(callback: CallbackQuery, session: AsyncSession):
    """
    پردازش دکمه نمایش اشتراک‌های من
    """
    # Assuming AuthMiddleware injects the session
    await _display_my_accounts(callback, session)

def register_account_callbacks(router: Router, session_maker: async_sessionmaker[AsyncSession]):
    """
    ثبت هندلرهای callback مربوط به حساب‌ها
    """
    # دکمه اشتراک‌های من
    router.callback_query.register(
        handle_my_accounts_callback,
        F.data == MY_ACCOUNTS_CB
        # Assuming AuthMiddleware injects the session
    )
    # TODO: Register other account-related callbacks here later 