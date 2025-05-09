"""
/profile command - Show user profile and account information
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from core.services.client_service import ClientService
from core.services.panel_service import PanelService
from db.repositories.user_repo import UserRepository
from db.repositories.client_repo import ClientRepository
from db.repositories.order_repo import OrderRepository
from db.repositories.panel_repo import PanelRepository
from db.repositories.inbound_repo import InboundRepository
from db.repositories.plan_repo import PlanRepository
from db.repositories.client_renewal_log_repo import ClientRenewalLogRepository
from bot.keyboards.profile_keyboard import get_profile_keyboard

logger = logging.getLogger(__name__)

def register_profile_command(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """Register the /profile command handler"""
    
    @router.message(Command("profile"))
    @router.message(F.text == "👤 حساب کاربری")
    async def cmd_profile(message: Message, session: AsyncSession) -> None:
        """Show user profile and account information"""
        user_id = message.from_user.id
        
        try:
            # فقط استفاده از سرویس‌ها
            user_service = UserService(session)
            client_service = ClientService(session)

            # Get user info
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer("⚠️ لطفاً ابتدا با دستور /start ثبت نام کنید.")
                return
            
            # Get user's VPN accounts
            active_accounts = await client_service.get_user_active_accounts(user.id)
            
            # Format profile text
            profile_text = (
                f"👤 <b>پروفایل شما</b>\n\n"
                f"🆔 شناسه کاربری: <code>{user.telegram_id}</code>\n"
                f"👥 نقش: {user.role}\n"
                f"📅 تاریخ عضویت: {user.created_at.strftime('%Y-%m-%d')}\n"
                f"📊 وضعیت: {user.status}\n\n"
                f"📱 تعداد اشتراک‌های فعال: {len(active_accounts)}\n"
            )
            
            # Add account details if any
            if active_accounts:
                profile_text += "\n<b>اشتراک‌های فعال شما:</b>\n"
                for account in active_accounts:
                    profile_text += (
                        f"\n🔹 نام اشتراک: {account.client_name}\n"
                        f"📍 موقعیت: {account.panel.location_name}\n"
                        f"⏳ تاریخ انقضا: {account.expires_at.strftime('%Y-%m-%d')}\n"
                        f"📊 حجم مصرفی: {account.traffic_used_gb:.2f}/{account.traffic_limit_gb:.2f} گیگابایت\n"
                    )
            
            await message.answer(
                profile_text,
                reply_markup=get_profile_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in profile command for user {user_id}: {e}", exc_info=True)
            await message.answer(
                "⚠️ متاسفانه بارگذاری پروفایل شما با مشکل مواجه شد. لطفاً بعداً دوباره امتحان کنید."
            )
