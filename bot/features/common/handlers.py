import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

# از User مدل دیتابیس استفاده می‌کنیم که از میدلور تزریق میشه
from db.models.user import User 
# کیبوردهای جدید رو وارد می‌کنیم
from .keyboards import get_start_inline_keyboard, get_main_reply_keyboard 
# دیگر نیازی به وارد کردن UserService و WalletService نیست

logger = logging.getLogger(__name__)

# روتر این ماژول که در main.py ثبت شده
router = Router(name="common")

# ثبت هندلر برای دستور /start
@router.message(CommandStart())
@router.message(Command("start"))
async def handle_start(message: Message, user: User, session: AsyncSession):
    """
    Handles the /start command.
    Sends a welcome message and the main keyboards.
    """
    logger.info(f"Start command received from user {user.id} ({user.username})")
    
    try:
        # Try to use full_name, fallback to username
        display_name = user.full_name or user.username
        
        welcome_text = (
            f"👋 {display_name} عزیز، خوش آمدید!\n\n"
            "🌙 به ربات MoonVPN خوش آمدید. من اینجا هستم تا به شما کمک کنم:\n\n"
            "• 🛒 خرید اشتراک VPN\n"
            "• 💰 مدیریت کیف پول\n"
            "• 📱 مدیریت اکانت‌ها\n"
            "• 👤 مشاهده پروفایل\n"
            "• ❓ راهنما و پشتیبانی\n\n"
            "از دکمه‌های زیر استفاده کنید 👇"
        )
        
        await message.answer(
            text=welcome_text,
            reply_markup=get_start_inline_keyboard(user.role)
        )
        
        await message.answer(
            "منوی اصلی:",
            reply_markup=get_main_reply_keyboard(user.role)
        )
        
        logger.info(f"Successfully welcomed user {user.id}")
        
    except Exception as e:
        logger.exception(f"Error in start command for user {user.id}: {e}")
        await message.answer(
            "앗! مشکلی پیش آمده. 😥 لطفا دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )

# TODO: پیاده‌سازی هندلرهای دیگر common (مثل help, support, و callback های دکمه‌ها) 