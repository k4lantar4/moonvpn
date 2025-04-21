"""
/start command - Entry point for new users and registration.

This module handles the initial interaction with users and sets up their
basic profile and interface preferences.
"""

import logging
from typing import Optional

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.user_service import UserService
from core.services.wallet_service import WalletService
from bot.keyboards.start_keyboard import get_start_keyboard
from bot.keyboards.user_keyboard import get_main_keyboard
from db.models.user import User

logger = logging.getLogger(__name__)

router = Router(name="start_commands")

@router.message(CommandStart())
@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, user: Optional[User] = None) -> None:
    """Process /start command and set up user interface.
    
    Args:
        message: Telegram message object
        session: Database session
        user: Optional pre-loaded user from middleware
    """
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    logger.info(f"Start command received from user {user_id} ({username})")
    
    try:
        # Initialize services
        user_service = UserService(session)
        wallet_service = WalletService(session)
        
        # Get or create user if not provided by middleware
        if not user:
            user = await user_service.get_user_by_telegram_id(user_id)
            if not user:
                user = await user_service.create_user(
                    telegram_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                # Create wallet for new user
                await wallet_service.create_wallet(user.id)
        
        # Format name for display
        display_name = first_name
        if last_name:
            display_name += f" {last_name}"
        
        # Prepare welcome message in Persian
        welcome_text = (
            f"👋 {display_name} عزیز، خوش آمدید!\n\n"
            "🌙 به ربات MoonVPN خوش آمدید. من اینجا هستم تا به شما کمک کنم:\n\n"
            "• 🛒 خرید اشتراک VPN\n"
            "• 💳 مدیریت کیف پول\n"
            "• 📊 مشاهده پلن‌های موجود\n"
            "• 🔄 بررسی وضعیت اشتراک\n"
            "• 💬 پشتیبانی ۲۴/۷\n\n"
            "چه کاری می‌توانم برای شما انجام دهم؟"
        )
        
        # Send welcome message with appropriate keyboard
        await message.answer(
            text=welcome_text,
            reply_markup=get_start_keyboard(user.role)
        )
        
        # Set main menu keyboard with Persian labels
        await message.answer(
            "از منوی زیر برای دسترسی به امکانات استفاده کنید:",
            reply_markup=get_main_keyboard(user.role)
        )
        
        logger.info(f"Successfully welcomed user {user_id}")
        
    except Exception as e:
        logger.exception(f"Error in start command for user {user_id}: {e}")
        await message.answer(
            "⚠️ متأسفانه مشکلی در سیستم رخ داده است. لطفاً چند دقیقه دیگر دوباره تلاش کنید."
        )
