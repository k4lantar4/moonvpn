import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode

from core.utils.helpers import authenticated_user
from core.utils.helpers import get_user
from backend.accounts.services import AccountService

logger = logging.getLogger(__name__)

# Define conversation states
SELECTING_SERVER = 0

@authenticated_user
async def change_server_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allow users to change their VPN server location"""
    user = get_user(update.effective_user.id)
    
    try:
        # Get server list
        success, servers, error = AccountService.get_all_servers()
        
        if not success or not servers:
            message = f"⚠️ <b>خطا در دریافت لیست سرورها:</b>\n{error or 'سروری یافت نشد.'}"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.HTML
                )
            return ConversationHandler.END
        
        # Check if user has an active account
        account_success, account_status, account_error = AccountService.get_account_status(user)
        
        if not account_success or not account_status:
            message = (
                "⚠️ <b>شما هیچ اشتراک فعالی ندارید</b>\n\n"
                "برای استفاده از این قابلیت، ابتدا باید یک اشتراک خریداری کنید.\n"
                "برای خرید اشتراک از دستور /buy استفاده کنید."
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.HTML
                )
            return ConversationHandler.END
        
        # User has an account, show server options
        message = (
            "🌐 <b>تغییر سرور</b>\n\n"
            "سرور فعلی شما: <b>" + account_status.get('server_name', 'نامشخص') + "</b>\n\n"
            "لطفا سرور جدید خود را انتخاب کنید:"
        )
        
        # Create buttons for each server
        buttons = []
        for server in servers:
            if not server.get('is_active', False):
                continue
                
            server_id = server.get('id')
            server_name = server.get('name', 'نامشخص')
            server_load = server.get('user_count', 0)
            
            # Add an emoji based on server load
            if server_load < 50:
                load_emoji = "🟢"  # Low load
            elif server_load < 80:
                load_emoji = "🟡"  # Medium load
            else:
                load_emoji = "🔴"  # High load
                
            button_text = f"{load_emoji} {server_name} ({server_load} کاربر)"
            buttons.append([InlineKeyboardButton(button_text, callback_data=f"server_{server_id}")])
        
        # Add cancel button
        buttons.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel_change")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        
        return SELECTING_SERVER
        
    except Exception as e:
        logger.exception(f"Error in change_server: {str(e)}")
        message = "⚠️ خطایی در دریافت لیست سرورها رخ داد. لطفا بعدا مجددا تلاش کنید."
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.HTML
            )
        return ConversationHandler.END

async def server_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle server selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_change":
        await query.edit_message_text(
            "❌ عملیات تغییر سرور لغو شد.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    server_id = int(query.data.split("_")[1])
    user = get_user(query.from_user.id)
    
    try:
        # Change server for user's account
        success, result, error = AccountService.change_server(user, server_id)
        
        if not success:
            await query.edit_message_text(
                f"⚠️ <b>خطا در تغییر سرور:</b>\n{error}",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Success, show new subscription link
        new_server_name = result.get('server_name', 'نامشخص')
        subscription_link = result.get('subscription_link', '')
        
        await query.edit_message_text(
            f"✅ <b>سرور شما با موفقیت تغییر کرد!</b>\n\n"
            f"سرور جدید: <b>{new_server_name}</b>\n\n"
            f"🔗 <b>لینک اتصال جدید شما:</b>\n"
            f"<code>{subscription_link}</code>\n\n"
            f"⚠️ لطفا برنامه VPN خود را بسته و با لینک جدید دوباره متصل شوید.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.exception(f"Error in server_selected: {str(e)}")
        await query.edit_message_text(
            "⚠️ خطایی در تغییر سرور رخ داد. لطفا بعدا مجددا تلاش کنید.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.id} canceled the change server conversation")
    await update.message.reply_text(
        "❌ عملیات تغییر سرور لغو شد."
    )
    return ConversationHandler.END

# Create the change server conversation handler
change_server_handler = ConversationHandler(
    entry_points=[
        CommandHandler("change_server", change_server_command),
        CallbackQueryHandler(change_server_command, pattern="^change_server$")
    ],
    states={
        SELECTING_SERVER: [
            CallbackQueryHandler(server_selected, pattern=r"^server_\d+$|^cancel_change$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
) 