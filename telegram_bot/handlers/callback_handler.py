from telegram import Update
from telegram.ext import ContextTypes

from handlers.profile_handler import profile_menu
from handlers.subscription_handler import subscription_menu
from handlers.order_handler import order_menu
from handlers.plan_handler import plan_menu
from handlers.payment_handler import payment_menu
from handlers.help_handler import help_command
from handlers.seller_handler import seller_menu
from handlers.affiliate_handler import affiliate_menu


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from inline keyboards.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract the callback data
    callback_data = query.data
    
    # Route to the appropriate handler based on the callback data
    if callback_data == "profile":
        await profile_menu(update, context)
    elif callback_data == "subscriptions":
        await subscription_menu(update, context)
    elif callback_data == "order":
        await order_menu(update, context)
    elif callback_data == "plans":
        await plan_menu(update, context)
    elif callback_data == "payment":
        await payment_menu(update, context)
    elif callback_data == "help":
        await help_command(update, context)
    elif callback_data == "seller":
        await seller_menu(update, context)
    elif callback_data == "affiliate":
        await affiliate_menu(update, context)
    else:
        # Unknown callback data
        await query.edit_message_text(
            text=f"I don't know how to handle callback: {callback_data}"
        ) 