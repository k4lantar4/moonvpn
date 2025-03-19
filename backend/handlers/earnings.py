import logging
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, CommandHandler

from core.database.models.user import User
from bot.constants import CallbackPatterns, States

logger = logging.getLogger(__name__)

# Conversation states
(
    SHOWING_EARNINGS, 
    SHOWING_REFERRALS,
    SHOWING_WITHDRAW
) = range(3)

# Earnings image URL
EARNINGS_IMAGE = "https://example.com/path/to/earnings_image.jpg"  # Replace with actual image URL or file_id

async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /earnings command and show the earnings dashboard."""
    user = update.effective_user
    
    # Get user from database
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("❌ شما در سیستم ثبت نشده اید. لطفا دستور /start را ارسال کنید.")
        return ConversationHandler.END
    
    # Generate a referral link using bot username and user's telegram ID
    bot_username = (await update.get_bot().get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    
    # Get user's referral stats
    referral_count = 0  # TODO: Implement referral count from database
    earnings = 0  # TODO: Implement earnings from database
    
    # Create message
    message = (
        f"💰 <b>کسب درآمد در MoonVPN</b>\n\n"
        f"با دعوت دوستان خود به MoonVPN، به ازای هر خرید آنها <b>30%</b> کمیسیون دریافت کنید!\n\n"
        f"🔗 <b>لینک دعوت شما:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 <b>آمار شما:</b>\n"
        f"👥 تعداد زیرمجموعه‌ها: {referral_count} نفر\n"
        f"💵 درآمد کل: {earnings} تومان\n\n"
        f"برای دریافت اطلاعات بیشتر، از منوی زیر استفاده کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("👥 لیست زیرمجموعه‌ها", callback_data=f"{CallbackPatterns.EARNINGS}_referrals"),
            InlineKeyboardButton("💳 برداشت وجه", callback_data=f"{CallbackPatterns.EARNINGS}_withdraw")
        ],
        [
            InlineKeyboardButton("📋 راهنمای کسب درآمد", callback_data=f"{CallbackPatterns.EARNINGS}_guide"),
            InlineKeyboardButton("🔍 مشاهده تراکنش‌ها", callback_data=f"{CallbackPatterns.EARNINGS}_transactions")
        ],
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with image
    try:
        await update.message.reply_photo(
            photo=EARNINGS_IMAGE,
            caption=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending earnings with image: {e}")
        # Fallback to text-only
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return SHOWING_EARNINGS

async def earnings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from the earnings menu."""
    query = update.callback_query
    await query.answer()
    
    # Parse the callback data
    callback_data = query.data
    action = callback_data.split("_")[1] if "_" in callback_data else ""
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    if not db_user:
        await query.edit_message_text("❌ شما در سیستم ثبت نشده اید. لطفا دستور /start را ارسال کنید.")
        return ConversationHandler.END
    
    if action == "referrals":
        return await show_referrals(update, context)
    elif action == "withdraw":
        return await show_withdraw(update, context)
    elif action == "guide":
        return await show_guide(update, context)
    elif action == "transactions":
        return await show_transactions(update, context)
    else:
        # Generate a referral link
        bot_username = (await update.get_bot().get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
        
        # Get user's referral stats
        referral_count = 0  # TODO: Implement referral count from database
        earnings = 0  # TODO: Implement earnings from database
        
        # Create message
        message = (
            f"💰 <b>کسب درآمد در MoonVPN</b>\n\n"
            f"با دعوت دوستان خود به MoonVPN، به ازای هر خرید آنها <b>30%</b> کمیسیون دریافت کنید!\n\n"
            f"🔗 <b>لینک دعوت شما:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            f"📊 <b>آمار شما:</b>\n"
            f"👥 تعداد زیرمجموعه‌ها: {referral_count} نفر\n"
            f"💵 درآمد کل: {earnings} تومان\n\n"
            f"برای دریافت اطلاعات بیشتر، از منوی زیر استفاده کنید:"
        )
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("👥 لیست زیرمجموعه‌ها", callback_data=f"{CallbackPatterns.EARNINGS}_referrals"),
                InlineKeyboardButton("💳 برداشت وجه", callback_data=f"{CallbackPatterns.EARNINGS}_withdraw")
            ],
            [
                InlineKeyboardButton("📋 راهنمای کسب درآمد", callback_data=f"{CallbackPatterns.EARNINGS}_guide"),
                InlineKeyboardButton("🔍 مشاهده تراکنش‌ها", callback_data=f"{CallbackPatterns.EARNINGS}_transactions")
            ],
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to edit message
        try:
            if query.message.photo:
                await query.edit_message_caption(
                    caption=message,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Error updating earnings message: {e}")
        
        return SHOWING_EARNINGS

async def show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user's referrals."""
    query = update.callback_query
    
    # TODO: Get actual referrals from database
    # For now, we'll use placeholder data
    referrals = [
        {"username": "user1", "joined": "2023-01-15", "purchases": 2, "commission": 15000},
        {"username": "user2", "joined": "2023-02-20", "purchases": 1, "commission": 7500},
        # Add more sample data as needed
    ]
    
    if not referrals:
        message = (
            "👥 <b>لیست زیرمجموعه‌های شما</b>\n\n"
            "شما هنوز هیچ زیرمجموعه‌ای ندارید.\n"
            "با اشتراک‌گذاری لینک دعوت خود، دوستان خود را به MoonVPN دعوت کنید."
        )
    else:
        # Create a message with referral list
        message = "👥 <b>لیست زیرمجموعه‌های شما</b>\n\n"
        
        for i, ref in enumerate(referrals, 1):
            message += (
                f"{i}. @{ref['username']}\n"
                f"   تاریخ پیوستن: {ref['joined']}\n"
                f"   تعداد خرید: {ref['purchases']}\n"
                f"   کمیسیون: {ref['commission']} تومان\n\n"
            )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.EARN_MONEY)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return SHOWING_REFERRALS

async def show_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show withdrawal options."""
    query = update.callback_query
    
    # TODO: Get actual balance from database
    balance = 0  # Placeholder
    
    message = (
        "💳 <b>برداشت وجه</b>\n\n"
        f"موجودی قابل برداشت: {balance} تومان\n\n"
    )
    
    if balance < 50000:
        message += "❌ حداقل مبلغ قابل برداشت ۵۰,۰۰۰ تومان می‌باشد."
        can_withdraw = False
    else:
        message += "لطفا روش برداشت وجه خود را انتخاب کنید:"
        can_withdraw = True
    
    # Create keyboard
    keyboard = []
    
    if can_withdraw:
        keyboard.extend([
            [
                InlineKeyboardButton("💳 کارت به کارت", callback_data=f"{CallbackPatterns.EARNINGS}_withdraw_card"),
                InlineKeyboardButton("💰 کیف پول", callback_data=f"{CallbackPatterns.EARNINGS}_withdraw_wallet")
            ]
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.EARN_MONEY)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return SHOWING_WITHDRAW

async def show_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show earnings guide."""
    query = update.callback_query
    
    message = (
        "📋 <b>راهنمای کسب درآمد در MoonVPN</b>\n\n"
        "با استفاده از برنامه معرف (Referral) در MoonVPN، می‌توانید به راحتی کسب درآمد کنید.\n\n"
        "<b>نحوه کار:</b>\n"
        "1️⃣ لینک دعوت خود را با دوستان به اشتراک بگذارید\n"
        "2️⃣ وقتی دوستان شما از طریق لینک شما ثبت‌نام کنند، به عنوان زیرمجموعه شما ثبت می‌شوند\n"
        "3️⃣ با هر خرید آنها، <b>30%</b> مبلغ به عنوان کمیسیون به حساب شما افزوده می‌شود\n"
        "4️⃣ زمانی که موجودی شما به حداقل ۵۰,۰۰۰ تومان رسید، می‌توانید درخواست برداشت وجه دهید\n\n"
        "<b>مزایای طرح معرف:</b>\n"
        "✅ بدون محدودیت در تعداد معرفی\n"
        "✅ کمیسیون دائمی از تمام خریدهای زیرمجموعه‌ها\n"
        "✅ امکان برداشت وجه به صورت کارت به کارت یا کیف پول\n"
        "✅ پنل کاربری اختصاصی برای مدیریت زیرمجموعه‌ها و درآمدها"
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.EARN_MONEY)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return SHOWING_EARNINGS

async def show_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show commission transactions."""
    query = update.callback_query
    
    # TODO: Get actual transactions from database
    # For now, we'll use placeholder data
    transactions = [
        {"date": "2023-03-15", "amount": 7500, "description": "کمیسیون خرید @user1"},
        {"date": "2023-03-20", "amount": 7500, "description": "کمیسیون خرید @user1"},
        {"date": "2023-04-05", "amount": 7500, "description": "کمیسیون خرید @user2"},
        # Add more sample data as needed
    ]
    
    if not transactions:
        message = (
            "🔍 <b>تراکنش‌های کمیسیون</b>\n\n"
            "شما هنوز هیچ تراکنش کمیسیونی ندارید.\n"
            "با اشتراک‌گذاری لینک دعوت خود، دوستان خود را به MoonVPN دعوت کنید."
        )
    else:
        # Create a message with transaction list
        message = "🔍 <b>تراکنش‌های کمیسیون</b>\n\n"
        
        for i, tx in enumerate(transactions, 1):
            message += (
                f"{i}. تاریخ: {tx['date']}\n"
                f"   مبلغ: {tx['amount']} تومان\n"
                f"   توضیحات: {tx['description']}\n\n"
            )
        
        # Calculate total
        total = sum(tx['amount'] for tx in transactions)
        message += f"💰 جمع کل: {total} تومان"
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.EARN_MONEY)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return SHOWING_EARNINGS

def get_earnings_handlers() -> List:
    """Return all handlers related to the earnings feature."""
    
    earnings_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("earnings", earnings_command),
            CallbackQueryHandler(earnings_callback, pattern=f"^{CallbackPatterns.EARN_MONEY}$")
        ],
        states={
            SHOWING_EARNINGS: [
                CallbackQueryHandler(earnings_callback, pattern=f"^{CallbackPatterns.EARNINGS}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$")
            ],
            SHOWING_REFERRALS: [
                CallbackQueryHandler(earnings_callback, pattern=f"^{CallbackPatterns.EARN_MONEY}$")
            ],
            SHOWING_WITHDRAW: [
                CallbackQueryHandler(earnings_callback, pattern=f"^{CallbackPatterns.EARN_MONEY}$"),
                CallbackQueryHandler(lambda u, c: u.callback_query.answer("این قابلیت به زودی اضافه خواهد شد!"), 
                                     pattern=f"^{CallbackPatterns.EARNINGS}_withdraw_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="earnings_conversation",
        persistent=False
    )
    
    return [earnings_conversation] 