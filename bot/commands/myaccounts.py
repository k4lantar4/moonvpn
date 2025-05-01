"""
فرمان /myaccounts - نمایش اشتراک‌های فعال کاربر
"""

import logging
from typing import Union, List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.account_service import AccountService
from core.services.client_service import ClientService
from core.services.panel_service import PanelService
from db.models.client_account import ClientAccount, AccountStatus

# تنظیم لاگر
logger = logging.getLogger(__name__)

_session_pool: async_sessionmaker[AsyncSession] = None

async def _display_my_accounts(target: Union[Message, CallbackQuery], session: AsyncSession):
    """منطق اصلی نمایش اشتراک‌های کاربر"""
    user_id = target.from_user.id
    message = target if isinstance(target, Message) else target.message
    logger.info(f"Displaying accounts for user {user_id}")

    try:
        # ایجاد سرویس‌های مورد نیاز
        panel_service = PanelService(session)
        client_service = ClientService(
            session=session,
            client_repo=None,  # اینها در داخل سرویس مقداردهی می‌شوند
            order_repo=None,
            panel_repo=None,
            inbound_repo=None,
            user_repo=None,
            plan_repo=None,
            renewal_log_repo=None,
            panel_service=panel_service
        )
        account_service = AccountService(session, client_service, panel_service)
        
        # دریافت اکانت‌های فعال کاربر
        accounts: List[ClientAccount] = await account_service.get_active_accounts_by_user(user_id)
        
        if not accounts:
            # کاربر هیچ اکانت فعالی ندارد
            accounts_text = (
                "📊 اشتراک‌های من:\\n\\n" 
                "شما هنوز هیچ اشتراکی فعال ندارید.\\n\\n"
                "برای خرید اشتراک از دکمه '🛒 خرید اشتراک' استفاده کنید."
            )
        else:
            # نمایش لیست اکانت‌های فعال
            accounts_text = "📊 اشتراک‌های من:\\n\\n"
            
            for i, account in enumerate(accounts, 1):
                # تبدیل وضعیت به متن فارسی
                status_text = "✅ فعال"
                if account.status == AccountStatus.EXPIRED:
                    status_text = "❌ منقضی شده"
                elif account.status == AccountStatus.DISABLED:
                    status_text = "⛔ غیرفعال"
                elif account.status == AccountStatus.SWITCHED:
                    status_text = "🔄 انتقال یافته"
                
                # محاسبه ترافیک باقی‌مانده
                remaining_gb = account.traffic_limit - account.traffic_used
                
                # افزودن اطلاعات اکانت به متن
                accounts_text += (
                    f"{i}. {account.client_name} - {status_text}\\n"
                    f"   📆 انقضاء: {account.expires_at.strftime('%Y-%m-%d')}\\n"
                    f"   📊 ترافیک: {account.traffic_used} از {account.traffic_limit} GB ({remaining_gb} GB باقی‌مانده)\\n"
                    f"   🔗 {account.panel.location_name or 'بدون لوکیشن'}\\n\\n"
                )
            
            accounts_text += "برای دریافت کانفیگ یا تمدید، بر روی اکانت مورد نظر کلیک کنید."
        
        if isinstance(target, CallbackQuery):
            # Try editing the message, catch potential errors if message is identical or deleted
            try:
                await message.edit_text(accounts_text)
            except Exception as edit_err:
                logger.warning(f"Could not edit message for my_accounts, maybe it was not modified? {edit_err}")
            await target.answer() # Answer callback even if edit fails
        else:
            await message.answer(accounts_text)

        logger.info(f"Sent my accounts list to user {user_id}")

    except Exception as e:
        logger.error(f"Error displaying accounts for user {user_id}: {e}", exc_info=True)
        error_message = "خطایی در دریافت لیست اشتراک‌ها رخ داد. لطفاً بعداً دوباره تلاش کنید."
        if isinstance(target, CallbackQuery):
             try:
                 await message.edit_text(error_message)
             except Exception as edit_err:
                 logger.warning(f"Could not edit message on display accounts error: {edit_err}")
                 await message.answer(error_message) # Fallback
             await target.answer("خطا")
        else:
             await message.answer(error_message)

async def cmd_myaccounts(message: Message):
    """هندلر دستور /myaccounts و دکمه متنی"""
    # Assuming _session_pool is set during registration
    if not _session_pool:
        logger.error("Session pool not initialized for myaccounts command.")
        await message.answer("خطای سیستمی رخ داده است. لطفاً به پشتیبانی اطلاع دهید.")
        return
    async with _session_pool() as session: # Use global session_pool
         await _display_my_accounts(message, session) # Call helper

def register_myaccounts_command(router: Router, session_pool: async_sessionmaker[AsyncSession]):
    """ثبت فرمان /myaccounts و هندلر متن مربوطه"""
    global _session_pool
    _session_pool = session_pool
    
    # ثبت هندلر برای دستور /myaccounts
    router.message.register(cmd_myaccounts, Command("myaccounts"))
    
    # ثبت هندلر برای متن دکمه "اشتراک‌های من"
    router.message.register(cmd_myaccounts, F.text == "📊 اشتراک‌های من")