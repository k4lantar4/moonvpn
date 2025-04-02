import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from app.keyboards.admin_keyboards import get_admin_main_keyboard

# TODO: Load ADMIN_IDS from environment variables or a config file for security
ADMIN_IDS = {int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "123456789").split(',') if admin_id.isdigit()}

# --- Helper Function to Check Admin --- #
def is_admin(user_id: int) -> bool:
    """Checks if the given user ID belongs to an admin."""
    # A simple check against a predefined set of admin IDs
    # In a real application, this might involve checking roles from a database via API
    return user_id in ADMIN_IDS

# --- Command Handler for /admin --- #
async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /admin command, showing the admin menu if authorized."""
    user = update.effective_user
    if not user:
        # Should not happen in a command handler, but good practice to check
        return

    if not is_admin(user.id):
        await update.message.reply_text("🚫 شما دسترسی لازم برای استفاده از این دستور را ندارید.")
        return

    # User is an admin, show the admin menu
    admin_keyboard = get_admin_main_keyboard()
    await update.message.reply_text(
        "🔑 به پنل مدیریت خوش آمدید. لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=admin_keyboard
    )

# --- Export Handler --- #
admin_command_handler = CommandHandler("admin", handle_admin_command) 