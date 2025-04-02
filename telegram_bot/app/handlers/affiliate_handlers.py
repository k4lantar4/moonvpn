import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, CommandHandler, MessageHandler, filters

from app.keyboards.main_menu import main_menu_keyboard, BTN_REFERRAL
from api_client.affiliate import affiliate_client
from app.utils import api_client
from app.keyboards.payment import CANCEL_CALLBACK, get_cancel_keyboard

# Enable logging
logger = logging.getLogger(__name__)

# Define conversation states
(
    VIEWING_REFERRAL_INFO,
    VIEWING_REFERRAL_STATS,
    VIEWING_TRANSACTIONS,
    WITHDRAW_AMOUNT_SELECTION,
    WITHDRAW_CONFIRMATION,
) = range(5)

# Define callback data patterns
AFFILIATE_CALLBACK_PREFIX = "affiliate_"
VIEW_REFERRAL_STATS = f"{AFFILIATE_CALLBACK_PREFIX}stats"
VIEW_REFERRAL_TRANSACTIONS = f"{AFFILIATE_CALLBACK_PREFIX}transactions"
REGENERATE_LINK = f"{AFFILIATE_CALLBACK_PREFIX}regenerate_link"
WITHDRAW_COMMISSION = f"{AFFILIATE_CALLBACK_PREFIX}withdraw"
WITHDRAW_AMOUNT_PREFIX = f"{AFFILIATE_CALLBACK_PREFIX}amount_"
CONFIRM_WITHDRAW = f"{AFFILIATE_CALLBACK_PREFIX}confirm_withdraw"

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Referral' button press from main menu."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if not chat_id or not user:
        logger.warning("handle_referral called without chat_id or user")
        return ConversationHandler.END
    
    logger.info(f"User {user.id} accessed the referral section")
    
    try:
        # Get user referral information
        referral_info = await affiliate_client.get_user_referral_info(user.id)
        
        # Extract key information
        referral_code = referral_info.get("referral_code", "")
        referral_link = referral_info.get("referral_link", "")
        total_referrals = referral_info.get("total_referrals", 0)
        total_earnings = referral_info.get("total_earnings", 0)
        available_commission = referral_info.get("available_commission", 0)
        withdrawn_commission = referral_info.get("withdrawn_commission", 0)
        
        # Format monetary values
        formatted_earnings = f"{int(total_earnings):,}" if total_earnings else "0"
        formatted_available = f"{int(available_commission):,}" if available_commission else "0"
        formatted_withdrawn = f"{int(withdrawn_commission):,}" if withdrawn_commission else "0"
        
        # Prepare response message
        message = f"🔗 *معرفی دوستان (Affiliate)*\n\n"
        message += "با معرفی دوستان خود به MoonVPN، از هر خریدی که آنها انجام می‌دهند، کمیسیون دریافت کنید!\n\n"
        
        message += f"📊 *آمار شما:*\n"
        message += f"👥 تعداد افراد معرفی شده: {total_referrals}\n"
        message += f"💰 کل درآمد: {formatted_earnings} تومان\n"
        message += f"💵 موجودی قابل برداشت: {formatted_available} تومان\n"
        message += f"🏦 برداشت شده: {formatted_withdrawn} تومان\n\n"
        
        if referral_code and referral_link:
            message += f"*لینک معرفی شما:*\n"
            message += f"`{referral_link}`\n\n"
            message += f"*کد معرفی شما:*\n"
            message += f"`{referral_code}`\n\n"
            message += "این لینک یا کد را با دوستان خود به اشتراک بگذارید."
        else:
            message += "*شما هنوز لینک معرفی ندارید.*\n"
            message += "برای دریافت لینک روی دکمه «دریافت لینک معرفی» کلیک کنید."
        
        # Create keyboard
        keyboard = []
        
        if referral_code and referral_link:
            keyboard.append([InlineKeyboardButton("🔄 بازسازی لینک", callback_data=REGENERATE_LINK)])
        else:
            keyboard.append([InlineKeyboardButton("🔗 دریافت لینک معرفی", callback_data=REGENERATE_LINK)])
        
        keyboard.append([InlineKeyboardButton("📊 آمار تفصیلی", callback_data=VIEW_REFERRAL_STATS)])
        keyboard.append([InlineKeyboardButton("📜 تاریخچه تراکنش‌ها", callback_data=VIEW_REFERRAL_TRANSACTIONS)])
        
        if available_commission > 0:
            keyboard.append([InlineKeyboardButton("💸 برداشت کمیسیون", callback_data=WITHDRAW_COMMISSION)])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")])
        
        await update.effective_message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return VIEWING_REFERRAL_INFO
        
    except Exception as e:
        logger.error(f"Error in handle_referral: {e}")
        await update.effective_message.reply_text(
            "❌ خطا در دریافت اطلاعات معرفی دوستان. لطفاً بعداً تلاش کنید.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

async def handle_affiliate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles callback queries from the affiliate section."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not user or not chat_id:
        return ConversationHandler.END
    
    # Handle main menu return
    if query.data == "back_to_main_menu":
        await query.message.reply_text(
            "بازگشت به منوی اصلی...",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Handle regenerate link
    elif query.data == REGENERATE_LINK:
        try:
            result = await affiliate_client.generate_referral_link(user.id)
            
            referral_code = result.get("referral_code", "")
            referral_link = result.get("referral_link", "")
            
            if referral_code and referral_link:
                message = f"🔗 *لینک معرفی شما با موفقیت ساخته شد!*\n\n"
                message += f"*لینک معرفی:*\n"
                message += f"`{referral_link}`\n\n"
                message += f"*کد معرفی:*\n"
                message += f"`{referral_code}`\n\n"
                message += "این لینک یا کد را با دوستان خود به اشتراک بگذارید."
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                    ]),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "❌ خطا در ساخت لینک معرفی. لطفاً بعداً تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                    ])
                )
            
            return VIEWING_REFERRAL_INFO
            
        except Exception as e:
            logger.error(f"Error in handle_affiliate_callback (REGENERATE_LINK): {e}")
            await query.edit_message_text(
                "❌ خطا در ساخت لینک معرفی. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ])
            )
            return VIEWING_REFERRAL_INFO
    
    # Handle refresh referral info (return to main referral page)
    elif query.data == "refresh_referral_info":
        return await handle_referral(update, context)
    
    # Handle view referral statistics
    elif query.data == VIEW_REFERRAL_STATS:
        try:
            stats = await affiliate_client.get_referral_stats(user.id)
            
            # Extract statistics
            total_referrals = stats.get("total_referrals", 0)
            active_referrals = stats.get("active_referrals", 0)
            conversion_rate = stats.get("conversion_rate", 0)
            total_earnings = stats.get("total_earnings", 0)
            available_commission = stats.get("available_commission", 0)
            withdrawn_commission = stats.get("withdrawn_commission", 0)
            monthly_earnings = stats.get("monthly_earnings", {})
            
            # Format monetary values
            formatted_earnings = f"{int(total_earnings):,}" if total_earnings else "0"
            formatted_available = f"{int(available_commission):,}" if available_commission else "0"
            formatted_withdrawn = f"{int(withdrawn_commission):,}" if withdrawn_commission else "0"
            
            # Prepare response message
            message = f"📊 *آمار تفصیلی معرفی دوستان*\n\n"
            message += f"👥 کل معرفی‌ها: {total_referrals}\n"
            message += f"👤 کاربران فعال: {active_referrals}\n"
            message += f"📈 نرخ تبدیل: {conversion_rate:.1f}%\n\n"
            
            message += f"💰 *مالی:*\n"
            message += f"💵 کل درآمد: {formatted_earnings} تومان\n"
            message += f"💸 قابل برداشت: {formatted_available} تومان\n"
            message += f"🏦 برداشت شده: {formatted_withdrawn} تومان\n\n"
            
            if monthly_earnings:
                message += f"📅 *درآمد ماهانه:*\n"
                sorted_months = sorted(monthly_earnings.items(), key=lambda x: x[0], reverse=True)
                for month, amount in sorted_months[:3]:  # Show last 3 months
                    formatted_month_amount = f"{int(amount):,}" if amount else "0"
                    message += f"- {month}: {formatted_month_amount} تومان\n"
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ]),
                parse_mode="Markdown"
            )
            
            return VIEWING_REFERRAL_STATS
            
        except Exception as e:
            logger.error(f"Error in handle_affiliate_callback (VIEW_REFERRAL_STATS): {e}")
            await query.edit_message_text(
                "❌ خطا در دریافت آمار تفصیلی. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ])
            )
            return VIEWING_REFERRAL_INFO
    
    # Handle view referral transactions
    elif query.data == VIEW_REFERRAL_TRANSACTIONS:
        try:
            transactions = await affiliate_client.get_referral_transactions(user.id)
            
            message = f"📜 *تاریخچه تراکنش‌های معرفی دوستان*\n\n"
            
            if not transactions:
                message += "هنوز هیچ تراکنشی ثبت نشده است."
            else:
                for i, tx in enumerate(transactions[:10], 1):  # Show max 10 transactions
                    amount = tx.get("amount", 0)
                    date = tx.get("date", "نامشخص")
                    referred_user = tx.get("referred_user", "ناشناس")
                    status = tx.get("status", "نامشخص")
                    
                    formatted_amount = f"{int(amount):,}" if amount else "0"
                    status_emoji = "✅" if status == "completed" else "⏳" if status == "pending" else "❌"
                    
                    message += f"{i}. {status_emoji} {formatted_amount} تومان - {date}\n"
                    message += f"   👤 کاربر: {referred_user}\n"
                
                if len(transactions) > 10:
                    message += f"\n... و {len(transactions) - 10} تراکنش دیگر"
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ]),
                parse_mode="Markdown"
            )
            
            return VIEWING_TRANSACTIONS
            
        except Exception as e:
            logger.error(f"Error in handle_affiliate_callback (VIEW_REFERRAL_TRANSACTIONS): {e}")
            await query.edit_message_text(
                "❌ خطا در دریافت تاریخچه تراکنش‌ها. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ])
            )
            return VIEWING_REFERRAL_INFO
    
    # Handle withdraw commission
    elif query.data == WITHDRAW_COMMISSION:
        try:
            referral_info = await affiliate_client.get_user_referral_info(user.id)
            available_commission = referral_info.get("available_commission", 0)
            
            if available_commission <= 0:
                await query.edit_message_text(
                    "❌ شما کمیسیون قابل برداشتی ندارید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                    ])
                )
                return VIEWING_REFERRAL_INFO
            
            formatted_available = f"{int(available_commission):,}" if available_commission else "0"
            
            # Create preset amounts for quick selection (25%, 50%, 75%, 100% of available)
            amounts = [
                int(available_commission * 0.25),
                int(available_commission * 0.5),
                int(available_commission * 0.75),
                available_commission
            ]
            
            message = f"💸 *برداشت کمیسیون به کیف پول*\n\n"
            message += f"موجودی قابل برداشت: {formatted_available} تومان\n\n"
            message += "لطفاً مبلغ مورد نظر برای برداشت را انتخاب کنید:"
            
            keyboard = []
            for amount in amounts:
                if amount <= 0:
                    continue
                formatted = f"{int(amount):,}"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{formatted} تومان", 
                        callback_data=f"{WITHDRAW_AMOUNT_PREFIX}{amount}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return WITHDRAW_AMOUNT_SELECTION
            
        except Exception as e:
            logger.error(f"Error in handle_affiliate_callback (WITHDRAW_COMMISSION): {e}")
            await query.edit_message_text(
                "❌ خطا در بررسی موجودی کمیسیون. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ])
            )
            return VIEWING_REFERRAL_INFO
    
    # Handle withdraw amount selection
    elif query.data.startswith(WITHDRAW_AMOUNT_PREFIX):
        amount_str = query.data[len(WITHDRAW_AMOUNT_PREFIX):]
        try:
            amount = float(amount_str)
            
            # Store amount in context
            context.user_data["withdraw_amount"] = amount
            
            formatted_amount = f"{int(amount):,}" if amount else "0"
            
            message = f"💸 *برداشت کمیسیون*\n\n"
            message += f"مبلغ انتخابی: {formatted_amount} تومان\n\n"
            message += f"این مبلغ به کیف پول شما در MoonVPN اضافه خواهد شد.\n"
            message += f"آیا از برداشت این مبلغ اطمینان دارید؟"
            
            keyboard = [
                [InlineKeyboardButton("✅ بله، برداشت شود", callback_data=CONFIRM_WITHDRAW)],
                [InlineKeyboardButton("❌ خیر، انصراف", callback_data=WITHDRAW_COMMISSION)]  # Go back to amount selection
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return WITHDRAW_CONFIRMATION
            
        except ValueError:
            logger.error(f"Invalid amount in WITHDRAW_AMOUNT_PREFIX: {amount_str}")
            await query.edit_message_text(
                "❌ مبلغ نامعتبر برای برداشت.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=WITHDRAW_COMMISSION)]
                ])
            )
            return WITHDRAW_AMOUNT_SELECTION
    
    # Handle withdraw confirmation
    elif query.data == CONFIRM_WITHDRAW:
        # Get amount from context
        amount = context.user_data.get("withdraw_amount", 0)
        
        if amount <= 0:
            await query.edit_message_text(
                "❌ مبلغ برداشت نامعتبر است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ])
            )
            return VIEWING_REFERRAL_INFO
        
        try:
            result = await affiliate_client.withdraw_commission(user.id, amount)
            
            success = result.get("success", False)
            new_balance = result.get("new_wallet_balance", 0)
            
            if success:
                formatted_amount = f"{int(amount):,}" if amount else "0"
                formatted_balance = f"{int(new_balance):,}" if new_balance else "0"
                
                message = f"✅ *برداشت با موفقیت انجام شد*\n\n"
                message += f"مبلغ: {formatted_amount} تومان\n"
                message += f"موجودی فعلی کیف پول: {formatted_balance} تومان\n\n"
                message += "از اعتماد شما به MoonVPN سپاسگزاریم. 🙏"
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                    ]),
                    parse_mode="Markdown"
                )
            else:
                error_message = result.get("message", "خطای نامشخص")
                await query.edit_message_text(
                    f"❌ *خطا در برداشت کمیسیون*\n\n{error_message}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                    ]),
                    parse_mode="Markdown"
                )
            
            return VIEWING_REFERRAL_INFO
            
        except Exception as e:
            logger.error(f"Error in handle_affiliate_callback (CONFIRM_WITHDRAW): {e}")
            await query.edit_message_text(
                "❌ خطا در برداشت کمیسیون. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
                ])
            )
            return VIEWING_REFERRAL_INFO
    
    else:
        # Unknown callback data
        logger.warning(f"Unknown callback data in affiliate handler: {query.data}")
        await query.edit_message_text(
            "❌ درخواست نامعتبر.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_referral_info")]
            ])
        )
        return VIEWING_REFERRAL_INFO

async def cancel_affiliate_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the affiliate flow."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "عملیات لغو شد. به منوی اصلی بازگشتید.",
            reply_markup=None
        )
    else:
        await update.message.reply_text(
            "عملیات لغو شد. به منوی اصلی بازگشتید.",
            reply_markup=main_menu_keyboard()
        )
    
    return ConversationHandler.END

def get_affiliate_handlers():
    """Returns the handlers for the affiliate flow."""
    return [
        # Handler for the "Referral" button in main menu
        MessageHandler(filters.Text([BTN_REFERRAL]), handle_referral),
        
        # Command handler for /referral
        CommandHandler("referral", handle_referral),
        
        # Conversation handler for the affiliate flow
        ConversationHandler(
            entry_points=[
                MessageHandler(filters.Text([BTN_REFERRAL]), handle_referral),
                CommandHandler("referral", handle_referral)
            ],
            states={
                VIEWING_REFERRAL_INFO: [
                    CallbackQueryHandler(handle_affiliate_callback)
                ],
                VIEWING_REFERRAL_STATS: [
                    CallbackQueryHandler(handle_affiliate_callback)
                ],
                VIEWING_TRANSACTIONS: [
                    CallbackQueryHandler(handle_affiliate_callback)
                ],
                WITHDRAW_AMOUNT_SELECTION: [
                    CallbackQueryHandler(handle_affiliate_callback)
                ],
                WITHDRAW_CONFIRMATION: [
                    CallbackQueryHandler(handle_affiliate_callback)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel_affiliate_flow),
                CallbackQueryHandler(cancel_affiliate_flow, pattern=f"^{CANCEL_CALLBACK}$")
            ],
            name="affiliate_flow",
            persistent=False
        )
    ] 