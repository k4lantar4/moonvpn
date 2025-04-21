"""
دستورات مربوط به فرآیند خرید اشتراک
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.services import PlanService
from ..keyboards.buy_keyboards import get_plans_keyboard

router = Router()


@router.message(Command("buy"))
async def buy_command(message: Message):
    """
    شروع فرآیند خرید اشتراک
    """
    # دریافت لیست پلن‌های فعال
    plans = await PlanService.get_active_plans()
    
    if not plans:
        await message.answer(
            "⚠️ در حال حاضر هیچ پلن فعالی موجود نیست.\n"
            "لطفا بعدا مجددا تلاش کنید."
        )
        return
    
    # نمایش لیست پلن‌ها
    await message.answer(
        "🛍 به فروشگاه MoonVPN خوش آمدید!\n\n"
        "لطفا یکی از پلن‌های زیر را انتخاب کنید:",
        reply_markup=get_plans_keyboard(plans)
    ) 