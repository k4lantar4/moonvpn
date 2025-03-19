from telegram import Update
from telegram.ext import ContextTypes
from ..keyboards.main import get_main_keyboard
from ..utils.decorators import send_typing_action

@send_typing_action
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}! 👋\n"
        "به ربات مدیریت اکانت MoonVPN خوش آمدید.\n"
        "لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:",
        reply_markup=get_main_keyboard()
    ) 