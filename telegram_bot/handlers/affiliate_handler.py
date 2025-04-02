import logging
from decimal import Decimal
from typing import Union, Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import API_URL, get_user_token
from utils.api_client import APIClient
from utils.decorators import authenticated
from utils.formatters import format_decimal
from utils.keyboard import build_main_menu_markup

# States for the conversation handler
VIEWING_AFFILIATE, WITHDRAWAL_AMOUNT, WITHDRAWAL_CONFIRMATION = range(3)

# Callback data constants
CB_VIEW_STATS = "affiliate_stats"
CB_VIEW_REFERRALS = "affiliate_referrals"
CB_VIEW_COMMISSIONS = "affiliate_commissions"
CB_WITHDRAW = "affiliate_withdraw"
CB_CONFIRM = "affiliate_withdraw_confirm"
CB_CANCEL = "affiliate_withdraw_cancel"
CB_BACK = "affiliate_back"
CB_MENU = "main_menu"


logger = logging.getLogger(__name__)


@authenticated
async def affiliate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show the affiliate menu to the user.
    """
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    client = APIClient(API_URL, token)
    
    # Get affiliate stats for the user
    try:
        stats = client.get("/affiliate/stats")
    except Exception as e:
        logger.error(f"Error fetching affiliate stats: {str(e)}")
        await update.effective_message.reply_text(
            "😕 Sorry, we couldn't fetch your affiliate information at the moment. Please try again later."
        )
        return ConversationHandler.END
    
    # Format the stats into a readable message
    message = "🔗 *Your Affiliate Dashboard* 🔗\n\n"
    
    if not stats.get("is_affiliate_enabled", False):
        message += "⚠️ Your affiliate account is not enabled. Please contact support for assistance.\n\n"
    else:
        message += f"🏷️ Your referral code: `{stats.get('affiliate_code', 'N/A')}`\n"
        message += f"🔗 Your referral link: {stats.get('affiliate_url', 'N/A')}\n\n"
        
        message += f"👥 Referred users: {stats.get('referred_users_count', 0)}\n"
        message += f"💰 Total earnings: ₽{format_decimal(stats.get('total_earnings', 0))}\n"
        message += f"⏳ Pending earnings: ₽{format_decimal(stats.get('pending_earnings', 0))}\n"
        message += f"✅ Paid earnings: ₽{format_decimal(stats.get('paid_earnings', 0))}\n"
        message += f"💼 Current balance: ₽{format_decimal(stats.get('current_balance', 0))}\n\n"
        
        if stats.get('can_withdraw', False):
            message += "✅ You can request a withdrawal of your current balance.\n"
        else:
            min_amount = stats.get('min_withdrawal_amount', 0)
            message += f"⚠️ Minimum withdrawal amount: ₽{format_decimal(min_amount)}\n"
    
    # Create the keyboard with affiliate options
    keyboard = [
        [
            InlineKeyboardButton("👥 My Referrals", callback_data=CB_VIEW_REFERRALS),
            InlineKeyboardButton("💰 My Commissions", callback_data=CB_VIEW_COMMISSIONS)
        ]
    ]
    
    # Only add withdrawal button if user can withdraw
    if stats.get('can_withdraw', False):
        keyboard.append([InlineKeyboardButton("💸 Withdraw Funds", callback_data=CB_WITHDRAW)])
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data=CB_MENU)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Save stats in context for later use
    context.user_data['affiliate_stats'] = stats
    
    await update.effective_message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return VIEWING_AFFILIATE


@authenticated
async def view_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show a list of users referred by the current user.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    client = APIClient(API_URL, token)
    
    try:
        referrals = client.get("/affiliate/referred-users")
    except Exception as e:
        logger.error(f"Error fetching referrals: {str(e)}")
        await query.edit_message_text(
            "😕 Sorry, we couldn't fetch your referrals at the moment. Please try again later.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)]])
        )
        return VIEWING_AFFILIATE
    
    message = "👥 *Your Referred Users* 👥\n\n"
    
    if not referrals:
        message += "You haven't referred any users yet. Share your referral link to start earning commissions!\n"
    else:
        for i, user in enumerate(referrals, 1):
            username = user.get('username') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or f"User {user.get('id')}"
            joined_date = user.get('created_at', '').split('T')[0] if user.get('created_at') else 'N/A'
            message += f"{i}. {username} - Joined: {joined_date}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data=CB_MENU)]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return VIEWING_AFFILIATE


@authenticated
async def view_commissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show a list of commissions earned by the user.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    client = APIClient(API_URL, token)
    
    try:
        commissions = client.get("/affiliate/commissions")
    except Exception as e:
        logger.error(f"Error fetching commissions: {str(e)}")
        await query.edit_message_text(
            "😕 Sorry, we couldn't fetch your commissions at the moment. Please try again later.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)]])
        )
        return VIEWING_AFFILIATE
    
    message = "💰 *Your Affiliate Commissions* 💰\n\n"
    
    if not commissions:
        message += "You haven't earned any commissions yet. Refer users to start earning!\n"
    else:
        # Group commissions by status
        pending = [c for c in commissions if c.get('status') == 'pending']
        approved = [c for c in commissions if c.get('status') == 'approved']
        paid = [c for c in commissions if c.get('status') == 'paid']
        
        # Show the latest 5 commissions
        latest = sorted(commissions, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        message += f"*Summary:*\n"
        message += f"⏳ Pending: {len(pending)} (₽{format_decimal(sum(Decimal(c.get('amount', 0)) for c in pending))})\n"
        message += f"✅ Approved: {len(approved)} (₽{format_decimal(sum(Decimal(c.get('amount', 0)) for c in approved))})\n"
        message += f"💸 Paid: {len(paid)} (₽{format_decimal(sum(Decimal(c.get('amount', 0)) for c in paid))})\n\n"
        
        message += f"*Latest Commissions:*\n"
        for i, comm in enumerate(latest, 1):
            amount = format_decimal(comm.get('amount', 0))
            date = comm.get('created_at', '').split('T')[0] if comm.get('created_at') else 'N/A'
            status = comm.get('status', 'unknown').upper()
            
            message += f"{i}. ₽{amount} - {date} - {status}"
            
            if comm.get('order_info'):
                message += f" - {comm.get('order_info')}"
                
            message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data=CB_MENU)]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return VIEWING_AFFILIATE


@authenticated
async def initiate_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the withdrawal process.
    """
    query = update.callback_query
    await query.answer()
    
    stats = context.user_data.get('affiliate_stats', {})
    current_balance = Decimal(stats.get('current_balance', 0))
    min_withdrawal = Decimal(stats.get('min_withdrawal_amount', 0))
    
    if current_balance < min_withdrawal:
        await query.edit_message_text(
            f"⚠️ Your current balance (₽{format_decimal(current_balance)}) is below the minimum withdrawal amount "
            f"(₽{format_decimal(min_withdrawal)}).\n\nRefer more users to increase your balance!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)]])
        )
        return VIEWING_AFFILIATE
    
    await query.edit_message_text(
        f"💸 *Withdraw Funds* 💸\n\n"
        f"Your current balance: ₽{format_decimal(current_balance)}\n"
        f"Minimum withdrawal: ₽{format_decimal(min_withdrawal)}\n\n"
        f"Please enter the amount you wish to withdraw (in rubles).\n"
        f"Example: 500",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data=CB_CANCEL)]]),
        parse_mode="Markdown"
    )
    
    return WITHDRAWAL_AMOUNT


@authenticated
async def process_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the withdrawal amount entered by the user.
    """
    text = update.message.text.strip()
    
    # Try to convert the input to a decimal
    try:
        amount = Decimal(text.replace(',', '.'))
    except Exception:
        await update.message.reply_text(
            "⚠️ Please enter a valid amount (e.g., 500).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data=CB_CANCEL)]])
        )
        return WITHDRAWAL_AMOUNT
    
    stats = context.user_data.get('affiliate_stats', {})
    current_balance = Decimal(stats.get('current_balance', 0))
    min_withdrawal = Decimal(stats.get('min_withdrawal_amount', 0))
    
    # Validate the amount
    if amount <= 0:
        await update.message.reply_text(
            "⚠️ The amount must be greater than zero.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data=CB_CANCEL)]])
        )
        return WITHDRAWAL_AMOUNT
    
    if amount > current_balance:
        await update.message.reply_text(
            f"⚠️ The amount (₽{format_decimal(amount)}) exceeds your current balance (₽{format_decimal(current_balance)}).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data=CB_CANCEL)]])
        )
        return WITHDRAWAL_AMOUNT
    
    if amount < min_withdrawal:
        await update.message.reply_text(
            f"⚠️ The minimum withdrawal amount is ₽{format_decimal(min_withdrawal)}.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data=CB_CANCEL)]])
        )
        return WITHDRAWAL_AMOUNT
    
    # Store the amount for confirmation
    context.user_data['withdrawal_amount'] = amount
    
    # Ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=CB_CONFIRM),
            InlineKeyboardButton("❌ Cancel", callback_data=CB_CANCEL)
        ]
    ]
    
    await update.message.reply_text(
        f"💸 *Withdrawal Confirmation* 💸\n\n"
        f"Amount: ₽{format_decimal(amount)}\n\n"
        f"Please confirm your withdrawal request. Once confirmed, our team will process your request within 24-48 hours.\n\n"
        f"Do you want to proceed?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return WITHDRAWAL_CONFIRMATION


@authenticated
async def confirm_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Confirm and process the withdrawal request.
    """
    query = update.callback_query
    await query.answer()
    
    amount = context.user_data.get('withdrawal_amount')
    
    if not amount:
        await query.edit_message_text(
            "⚠️ Error: Withdrawal amount not found. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Affiliate Menu", callback_data=CB_BACK)]])
        )
        return VIEWING_AFFILIATE
    
    user_id = update.effective_user.id
    token = get_user_token(user_id)
    client = APIClient(API_URL, token)
    
    # Submit the withdrawal request
    try:
        data = {
            "amount": str(amount),
            "note": f"Withdrawal requested via Telegram Bot"
        }
        response = client.post("/affiliate/withdrawals", data)
        
        if response:
            await query.edit_message_text(
                f"✅ *Withdrawal Request Submitted* ✅\n\n"
                f"Amount: ₽{format_decimal(amount)}\n"
                f"Status: {response.get('status', 'pending').upper()}\n\n"
                f"Your withdrawal request has been submitted successfully! Our team will process your request within 24-48 hours.\n"
                f"You will be notified once it's processed.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Affiliate Menu", callback_data=CB_BACK)],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data=CB_MENU)]
                ]),
                parse_mode="Markdown"
            )
        else:
            raise Exception("Empty response from server")
        
    except Exception as e:
        logger.error(f"Error processing withdrawal: {str(e)}")
        await query.edit_message_text(
            f"❌ *Withdrawal Failed* ❌\n\n"
            f"We couldn't process your withdrawal request at this time. Please try again later or contact support.\n\n"
            f"Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)]]),
            parse_mode="Markdown"
        )
    
    # Clean up context data
    if 'withdrawal_amount' in context.user_data:
        del context.user_data['withdrawal_amount']
    
    return VIEWING_AFFILIATE


@authenticated
async def cancel_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the withdrawal process.
    """
    query = update.callback_query
    await query.answer()
    
    # Clean up context data
    if 'withdrawal_amount' in context.user_data:
        del context.user_data['withdrawal_amount']
    
    await query.edit_message_text(
        "❌ Withdrawal cancelled. Returning to affiliate menu...",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=CB_BACK)]])
    )
    
    # Return to the affiliate menu
    return await back_to_affiliate(update, context)


@authenticated
async def back_to_affiliate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Go back to the main affiliate menu.
    """
    query = update.callback_query
    if query:
        await query.answer()
        return await affiliate_menu(update, context)
    else:
        return await affiliate_menu(update, context)


@authenticated
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Go back to the main menu.
    """
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Returning to main menu...",
        reply_markup=build_main_menu_markup()
    )
    
    return ConversationHandler.END


def get_affiliate_conversation_handler():
    """
    Create and return the conversation handler for the affiliate system.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("affiliate", affiliate_menu)],
        states={
            VIEWING_AFFILIATE: [
                CallbackQueryHandler(view_referrals, pattern=f"^{CB_VIEW_REFERRALS}$"),
                CallbackQueryHandler(view_commissions, pattern=f"^{CB_VIEW_COMMISSIONS}$"),
                CallbackQueryHandler(initiate_withdrawal, pattern=f"^{CB_WITHDRAW}$"),
                CallbackQueryHandler(back_to_affiliate, pattern=f"^{CB_BACK}$"),
                CallbackQueryHandler(back_to_main, pattern=f"^{CB_MENU}$"),
            ],
            WITHDRAWAL_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdrawal_amount),
                CallbackQueryHandler(cancel_withdrawal, pattern=f"^{CB_CANCEL}$"),
            ],
            WITHDRAWAL_CONFIRMATION: [
                CallbackQueryHandler(confirm_withdrawal, pattern=f"^{CB_CONFIRM}$"),
                CallbackQueryHandler(cancel_withdrawal, pattern=f"^{CB_CANCEL}$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
            CommandHandler("start", lambda u, c: ConversationHandler.END),
        ],
        name="affiliate_conversation",
        persistent=False,
    ) 