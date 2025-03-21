import logging
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, CommandHandler

from bot.constants import CallbackPatterns

logger = logging.getLogger(__name__)

# Configuration for free services
FREE_VPN_IMAGE = "https://example.com/path/to/free_vpn_image.jpg"  # Replace with actual image
FREE_PROXY_IMAGE = "https://example.com/path/to/free_proxy_image.jpg"  # Replace with actual image

# States
SHOWING_FREE_VPN, SHOWING_FREE_PROXY = range(2)

async def free_vpn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display free VPN options."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Free VPN message
    free_vpn_text = (
        "🎁 *وی‌پی‌ان رایگان* 🎁\n\n"
        "کاربر گرامی، شما می‌توانید از سرویس رایگان ما استفاده کنید.\n\n"
        "⚠️ *محدودیت‌های سرویس رایگان:*\n"
        "• حجم محدود (300 مگابایت)\n"
        "• سرعت محدود\n"
        "• زمان اتصال محدود (1 ساعت)\n"
        "• بدون پشتیبانی اختصاصی\n\n"
        "برای استفاده از امکانات کامل و بدون محدودیت، می‌توانید اشتراک ویژه تهیه کنید."
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📥 دریافت کانفیگ رایگان", callback_data=f"{CallbackPatterns.FREE_VPN}_get"),
            InlineKeyboardButton("🔄 بروزرسانی کانفیگ", callback_data=f"{CallbackPatterns.FREE_VPN}_refresh")
        ],
        [
            InlineKeyboardButton("📚 راهنمای اتصال", callback_data=f"{CallbackPatterns.HELP}_connection"),
            InlineKeyboardButton("🛍️ خرید اشتراک ویژه", callback_data=CallbackPatterns.BUY_ACCOUNT)
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Try to send with image
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=free_vpn_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=free_vpn_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        else:
            try:
                await message.reply_photo(
                    photo=FREE_VPN_IMAGE,
                    caption=free_vpn_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error sending free VPN image: {e}")
                await message.reply_text(
                    text=free_vpn_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Error in free VPN command: {e}")
    
    return SHOWING_FREE_VPN

async def free_proxy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display free proxy options."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Free proxy message
    free_proxy_text = (
        "🔄 *پروکسی رایگان* 🔄\n\n"
        "کاربر گرامی، شما می‌توانید از پروکسی رایگان ما استفاده کنید.\n\n"
        "⚠️ *محدودیت‌های پروکسی رایگان:*\n"
        "• تعداد کاربر محدود\n"
        "• سرعت محدود\n"
        "• بدون پشتیبانی از برخی اپلیکیشن‌ها\n"
        "• بدون پشتیبانی اختصاصی\n\n"
        "برای استفاده از امکانات کامل و بدون محدودیت، می‌توانید اشتراک ویژه تهیه کنید."
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📥 دریافت پروکسی MTProto", callback_data=f"{CallbackPatterns.FREE_PROXY}_mtproto"),
            InlineKeyboardButton("📥 دریافت پروکسی SOCKS5", callback_data=f"{CallbackPatterns.FREE_PROXY}_socks")
        ],
        [
            InlineKeyboardButton("📚 راهنمای اتصال", callback_data=f"{CallbackPatterns.HELP}_connection"),
            InlineKeyboardButton("🛍️ خرید اشتراک ویژه", callback_data=CallbackPatterns.BUY_ACCOUNT)
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Try to send with image
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=free_proxy_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=free_proxy_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        else:
            try:
                await message.reply_photo(
                    photo=FREE_PROXY_IMAGE,
                    caption=free_proxy_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error sending free proxy image: {e}")
                await message.reply_text(
                    text=free_proxy_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Error in free proxy command: {e}")
    
    return SHOWING_FREE_PROXY

async def free_vpn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free VPN callbacks."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split("_")[2] if len(query.data.split("_")) > 2 else ""
    
    if action == "get":
        # Generate and send a free VPN config
        await query.message.reply_text(
            "🎁 *کانفیگ رایگان شما آماده شد!*\n\n"
            "`vmess://eyJhZGQiOiJmcmVlLWV4YW1wbGUuY29tIiwiYWlkIjoiMCIsImhvc3QiOiIiLCJpZCI6IjEyMzQ1Njc4LWFiY2QtMTIzNC01Njc4LTEyMzQ1Njc4YWJjZCIsIm5ldCI6IndzIiwicGF0aCI6Ii9mcmVlIiwicG9ydCI6IjQ0MyIsInBzIjoiTW9vblZQTiBGcmVlIiwic2N5IjoiYXV0byIsInNuaSI6ImZyZWUtZXhhbXBsZS5jb20iLCJ0bHMiOiJ0bHMiLCJ0eXBlIjoibm9uZSIsInYiOiIyIn0=`\n\n"
            "*توجه:* این کانفیگ تنها برای ۱ ساعت معتبر است و حجم آن ۳۰۰ مگابایت می‌باشد.\n\n"
            "برای راهنمای اتصال روی 'راهنمای اتصال' کلیک کنید.",
            parse_mode="Markdown"
        )
        return SHOWING_FREE_VPN
    
    elif action == "refresh":
        # Refresh the free VPN config
        await query.message.reply_text(
            "🔄 *کانفیگ رایگان شما بروزرسانی شد!*\n\n"
            "`vmess://eyJhZGQiOiJmcmVlLXJlZnJlc2hlZC5jb20iLCJhaWQiOiIwIiwiaG9zdCI6IiIsImlkIjoiODc2NTQzMjEtZGNiYS00MzIxLTg3NjUtODc2NTQzMjFkY2JhIiwibmV0Ijoid3MiLCJwYXRoIjoiL2ZyZWVyZWZyZXNoIiwicG9ydCI6IjQ0MyIsInBzIjoiTW9vblZQTiBGcmVlIFJlZnJlc2hlZCIsInNjeSI6ImF1dG8iLCJzbmkiOiJmcmVlLXJlZnJlc2hlZC5jb20iLCJ0bHMiOiJ0bHMiLCJ0eXBlIjoibm9uZSIsInYiOiIyIn0=`\n\n"
            "*توجه:* این کانفیگ تنها برای ۱ ساعت معتبر است و حجم آن ۳۰۰ مگابایت می‌باشد.",
            parse_mode="Markdown"
        )
        return SHOWING_FREE_VPN
    
    # Default: return to free VPN menu
    return await free_vpn_command(update, context)

async def free_proxy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle free proxy callbacks."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split("_")[2] if len(query.data.split("_")) > 2 else ""
    
    if action == "mtproto":
        # Send MTProto proxy
        await query.message.reply_text(
            "🔄 *پروکسی MTProto رایگان*\n\n"
            "`https://t.me/proxy?server=mtproto.example.com&port=443&secret=ee000000000000000000000000000000000000000000000000000000000000000`\n\n"
            "برای استفاده، روی لینک بالا کلیک کنید تا به صورت خودکار در تلگرام اضافه شود.",
            parse_mode="Markdown"
        )
        return SHOWING_FREE_PROXY
    
    elif action == "socks":
        # Send SOCKS5 proxy
        await query.message.reply_text(
            "🔄 *پروکسی SOCKS5 رایگان*\n\n"
            "سرور: `socks.example.com`\n"
            "پورت: `1080`\n"
            "نام کاربری: `free`\n"
            "رمز عبور: `moonvpn`\n\n"
            "این پروکسی را می‌توانید در تنظیمات شبکه سیستم خود یا در برنامه‌های مختلف استفاده کنید.",
            parse_mode="Markdown"
        )
        return SHOWING_FREE_PROXY
    
    # Default: return to free proxy menu
    return await free_proxy_command(update, context)

def get_free_vpn_handlers() -> List:
    """Return handlers for free VPN and proxy features."""
    free_vpn_conv = ConversationHandler(
        entry_points=[
            CommandHandler("free_vpn", free_vpn_command),
            CallbackQueryHandler(free_vpn_command, pattern=f"^{CallbackPatterns.FREE_VPN}$")
        ],
        states={
            SHOWING_FREE_VPN: [
                CallbackQueryHandler(free_vpn_callback, pattern=f"^{CallbackPatterns.FREE_VPN}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
                CallbackQueryHandler(lambda u, c: SHOWING_FREE_VPN, pattern=f"^{CallbackPatterns.BUY_ACCOUNT}$"),
                CallbackQueryHandler(lambda u, c: SHOWING_FREE_VPN, pattern=f"^{CallbackPatterns.HELP}_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="free_vpn_conversation",
        persistent=False
    )
    
    free_proxy_conv = ConversationHandler(
        entry_points=[
            CommandHandler("free_proxy", free_proxy_command),
            CallbackQueryHandler(free_proxy_command, pattern=f"^{CallbackPatterns.FREE_PROXY}$")
        ],
        states={
            SHOWING_FREE_PROXY: [
                CallbackQueryHandler(free_proxy_callback, pattern=f"^{CallbackPatterns.FREE_PROXY}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
                CallbackQueryHandler(lambda u, c: SHOWING_FREE_PROXY, pattern=f"^{CallbackPatterns.BUY_ACCOUNT}$"),
                CallbackQueryHandler(lambda u, c: SHOWING_FREE_PROXY, pattern=f"^{CallbackPatterns.HELP}_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="free_proxy_conversation",
        persistent=False
    )
    
    return [free_vpn_conv, free_proxy_conv] 