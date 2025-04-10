"""Handler for the /help command."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help-command")

@router.message(Command("help"))
async def handle_help(message: Message):
    """Displays the help message with available commands."""
    # TODO: Dynamically generate help text based on user role
    user = message.from_user
    full_name = user.full_name

    # Placeholder help text (adjust based on implemented features)
    help_text = (
        f"🙋‍♂️ سلام **{full_name}**! راهنمای ربات MoonVPN:\n\n"
        f"**دستورات عمومی:**\n"
        f"/start - شروع کار با ربات و نمایش منوی اصلی\n"
        f"/help - نمایش همین راهنما\n"
        f"/profile - نمایش اطلاعات کاربری شما\n"
        f"/wallet - نمایش موجودی کیف پول\n"
        f"/myaccounts - مشاهده و مدیریت اکانت‌های VPN فعال شما\n\n"
        f"**خرید و تمدید:**\n"
        f"🛒 **خرید سرویس:** از دکمه‌های منوی اصلی استفاده کنید.\n"
        f"🔄 **تمدید سرویس:** از بخش /myaccounts اقدام کنید.\n"
        f"--------------------\n"
        f"💡 نکته: همیشه می‌توانید با ارسال /start به منوی اصلی بازگردید.\n"
        f"📞 در صورت نیاز به پشتیبانی، با ادمین در تماس باشید."
    )

    await message.answer(help_text) 