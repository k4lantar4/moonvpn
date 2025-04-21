"""
/profile command - Show user profile and account information
"""

import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from core.services.client_service import ClientService
from bot.keyboards.profile_keyboard import get_profile_keyboard

logger = logging.getLogger(__name__)

def register_profile_command(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """Register the /profile command handler"""
    
    @router.message(Command("profile"))
    async def cmd_profile(message: Message, session: AsyncSession) -> None:
        """Show user profile and account information"""
        user_id = message.from_user.id
        
        try:
            # Get user info
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer("⚠️ Please use /start to register first.")
                return
            
            # Get user's VPN accounts
            client_service = ClientService(session)
            active_accounts = await client_service.get_user_active_accounts(user.id)
            
            # Format profile text
            profile_text = (
                f"👤 <b>Your Profile</b>\n\n"
                f"🆔 User ID: <code>{user.telegram_id}</code>\n"
                f"👥 Role: {user.role}\n"
                f"📅 Joined: {user.created_at.strftime('%Y-%m-%d')}\n"
                f"📊 Status: {user.status}\n\n"
                f"📱 Active VPN Accounts: {len(active_accounts)}\n"
            )
            
            # Add account details if any
            if active_accounts:
                profile_text += "\n<b>Your Active Accounts:</b>\n"
                for account in active_accounts:
                    profile_text += (
                        f"\n🔹 {account.client_name}\n"
                        f"📍 Location: {account.panel.location_name}\n"
                        f"⏳ Expires: {account.expires_at.strftime('%Y-%m-%d')}\n"
                        f"📊 Traffic: {account.traffic_used}/{account.traffic_limit} GB\n"
                    )
            
            await message.answer(
                profile_text,
                reply_markup=get_profile_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in profile command for user {user_id}: {e}", exc_info=True)
            await message.answer(
                "⚠️ Sorry, couldn't load your profile. Please try again later."
            )
