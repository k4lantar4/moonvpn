"""
MoonVPN Telegram Bot - Connection Guide.

This module provides functionality to show connection guides for different devices and applications.
"""

import logging
from typing import List, Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    CommandHandler, 
    ConversationHandler
)

from bot.constants import CallbackPatterns, States

logger = logging.getLogger(__name__)

# Connection guide states
(
    GUIDE_MAIN,
    SHOWING_PLATFORM,
    SHOWING_APP,
    SHOWING_STEPS
) = range(4)

# Guide image URLs
GUIDE_MAIN_IMAGE = "https://example.com/path/to/guide_main.jpg"  # Replace with actual image
ANDROID_GUIDE_IMAGE = "https://example.com/path/to/android_guide.jpg"  # Replace with actual image
IOS_GUIDE_IMAGE = "https://example.com/path/to/ios_guide.jpg"  # Replace with actual image
WINDOWS_GUIDE_IMAGE = "https://example.com/path/to/windows_guide.jpg"  # Replace with actual image
MAC_GUIDE_IMAGE = "https://example.com/path/to/mac_guide.jpg"  # Replace with actual image
LINUX_GUIDE_IMAGE = "https://example.com/path/to/linux_guide.jpg"  # Replace with actual image

async def connection_guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the main connection guide menu."""
    message = update.message or update.callback_query.message
    
    guide_text = (
        "📱 <b>راهنمای اتصال به VPN</b>\n\n"
        "برای مشاهده راهنمای اتصال، لطفا ابتدا سیستم عامل مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for platforms
    keyboard = [
        [
            InlineKeyboardButton("📱 Android (اندروید)", callback_data=f"{CallbackPatterns.HELP}_connection_android"),
            InlineKeyboardButton("📱 iOS (آیفون/آیپد)", callback_data=f"{CallbackPatterns.HELP}_connection_ios")
        ],
        [
            InlineKeyboardButton("💻 Windows (ویندوز)", callback_data=f"{CallbackPatterns.HELP}_connection_windows"),
            InlineKeyboardButton("💻 macOS (مک)", callback_data=f"{CallbackPatterns.HELP}_connection_mac")
        ],
        [
            InlineKeyboardButton("💻 Linux (لینوکس)", callback_data=f"{CallbackPatterns.HELP}_connection_linux"),
            InlineKeyboardButton("🌐 روتر و تجهیزات", callback_data=f"{CallbackPatterns.HELP}_connection_router")
        ],
        [InlineKeyboardButton("🔙 بازگشت به راهنما", callback_data=CallbackPatterns.HELP)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=guide_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=guide_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=GUIDE_MAIN_IMAGE,
                    caption=guide_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending guide with image: {e}")
                await message.reply_text(
                    text=guide_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in connection guide command: {e}")
    
    return GUIDE_MAIN

async def show_android_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show Android connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Guide text for Android
    guide_text = (
        "📱 <b>راهنمای اتصال در Android (اندروید)</b>\n\n"
        "برای استفاده از VPN در دستگاه‌های اندروید، می‌توانید از برنامه‌های زیر استفاده کنید:\n\n"
        "لطفا برنامه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for Android apps
    keyboard = [
        [
            InlineKeyboardButton("V2rayNG", callback_data=f"{CallbackPatterns.HELP}_app_v2rayng"),
            InlineKeyboardButton("Nekobox", callback_data=f"{CallbackPatterns.HELP}_app_nekobox_android")
        ],
        [
            InlineKeyboardButton("SagerNet", callback_data=f"{CallbackPatterns.HELP}_app_sagernet"),
            InlineKeyboardButton("Matsuri", callback_data=f"{CallbackPatterns.HELP}_app_matsuri")
        ],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب سیستم عامل", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=ANDROID_GUIDE_IMAGE,
                    caption=guide_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=guide_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing Android guide: {e}")
    
    return SHOWING_PLATFORM

async def show_ios_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show iOS connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Guide text for iOS
    guide_text = (
        "📱 <b>راهنمای اتصال در iOS (آیفون/آیپد)</b>\n\n"
        "برای استفاده از VPN در دستگاه‌های iOS، می‌توانید از برنامه‌های زیر استفاده کنید:\n\n"
        "لطفا برنامه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for iOS apps
    keyboard = [
        [
            InlineKeyboardButton("Shadowrocket", callback_data=f"{CallbackPatterns.HELP}_app_shadowrocket"),
            InlineKeyboardButton("Stash", callback_data=f"{CallbackPatterns.HELP}_app_stash")
        ],
        [
            InlineKeyboardButton("V2Box", callback_data=f"{CallbackPatterns.HELP}_app_v2box"),
            InlineKeyboardButton("Sing-box", callback_data=f"{CallbackPatterns.HELP}_app_singbox_ios")
        ],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب سیستم عامل", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=IOS_GUIDE_IMAGE,
                    caption=guide_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=guide_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing iOS guide: {e}")
    
    return SHOWING_PLATFORM

async def show_windows_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show Windows connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Guide text for Windows
    guide_text = (
        "💻 <b>راهنمای اتصال در Windows (ویندوز)</b>\n\n"
        "برای استفاده از VPN در ویندوز، می‌توانید از برنامه‌های زیر استفاده کنید:\n\n"
        "لطفا برنامه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for Windows apps
    keyboard = [
        [
            InlineKeyboardButton("V2rayN", callback_data=f"{CallbackPatterns.HELP}_app_v2rayn"),
            InlineKeyboardButton("Nekoray", callback_data=f"{CallbackPatterns.HELP}_app_nekoray")
        ],
        [
            InlineKeyboardButton("Clash for Windows", callback_data=f"{CallbackPatterns.HELP}_app_clash_windows"),
            InlineKeyboardButton("Sing-box", callback_data=f"{CallbackPatterns.HELP}_app_singbox_win")
        ],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب سیستم عامل", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=WINDOWS_GUIDE_IMAGE,
                    caption=guide_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=guide_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing Windows guide: {e}")
    
    return SHOWING_PLATFORM

async def show_mac_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show macOS connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Guide text for macOS
    guide_text = (
        "💻 <b>راهنمای اتصال در macOS (مک)</b>\n\n"
        "برای استفاده از VPN در macOS، می‌توانید از برنامه‌های زیر استفاده کنید:\n\n"
        "لطفا برنامه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for macOS apps
    keyboard = [
        [
            InlineKeyboardButton("V2rayU", callback_data=f"{CallbackPatterns.HELP}_app_v2rayu"),
            InlineKeyboardButton("ClashX", callback_data=f"{CallbackPatterns.HELP}_app_clashx")
        ],
        [
            InlineKeyboardButton("Sing-box", callback_data=f"{CallbackPatterns.HELP}_app_singbox_mac"),
            InlineKeyboardButton("V2Box", callback_data=f"{CallbackPatterns.HELP}_app_v2box_mac")
        ],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب سیستم عامل", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=MAC_GUIDE_IMAGE,
                    caption=guide_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=guide_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing macOS guide: {e}")
    
    return SHOWING_PLATFORM

async def show_linux_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show Linux connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Guide text for Linux
    guide_text = (
        "💻 <b>راهنمای اتصال در Linux (لینوکس)</b>\n\n"
        "برای استفاده از VPN در لینوکس، می‌توانید از برنامه‌های زیر استفاده کنید:\n\n"
        "لطفا برنامه مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for Linux apps
    keyboard = [
        [
            InlineKeyboardButton("Qv2ray", callback_data=f"{CallbackPatterns.HELP}_app_qv2ray"),
            InlineKeyboardButton("Sing-box", callback_data=f"{CallbackPatterns.HELP}_app_singbox_linux")
        ],
        [
            InlineKeyboardButton("V2rayA", callback_data=f"{CallbackPatterns.HELP}_app_v2raya"),
            InlineKeyboardButton("Clash for Linux", callback_data=f"{CallbackPatterns.HELP}_app_clash_linux")
        ],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب سیستم عامل", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=LINUX_GUIDE_IMAGE,
                    caption=guide_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=guide_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing Linux guide: {e}")
    
    return SHOWING_PLATFORM

async def show_router_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show router connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Guide text for routers
    guide_text = (
        "🌐 <b>راهنمای اتصال در روترها و تجهیزات شبکه</b>\n\n"
        "برای استفاده از VPN در روترها و تجهیزات شبکه، می‌توانید از یکی از روش‌های زیر استفاده کنید:\n\n"
        "لطفا نوع روتر یا تجهیزات مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for router options
    keyboard = [
        [
            InlineKeyboardButton("OpenWrt", callback_data=f"{CallbackPatterns.HELP}_app_openwrt"),
            InlineKeyboardButton("Merlin", callback_data=f"{CallbackPatterns.HELP}_app_merlin")
        ],
        [
            InlineKeyboardButton("Padavan", callback_data=f"{CallbackPatterns.HELP}_app_padavan"),
            InlineKeyboardButton("TP-Link", callback_data=f"{CallbackPatterns.HELP}_app_tplink")
        ],
        [InlineKeyboardButton("🔙 بازگشت به انتخاب سیستم عامل", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=guide_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing router guide: {e}")
    
    return SHOWING_PLATFORM

async def show_app_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show app-specific connection guide."""
    query = update.callback_query
    await query.answer()
    
    # Extract app from callback data
    app_name = query.data.split("_")[2]
    
    # Get appropriate guide text and steps for the app
    guide_info = get_app_guide(app_name)
    
    if not guide_info:
        # Fallback for unsupported app
        await query.edit_message_text(
            "❌ راهنمای این برنامه در حال حاضر در دسترس نیست. لطفا با پشتیبانی تماس بگیرید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.HELP}_connection")
            ]]),
            parse_mode="HTML"
        )
        return SHOWING_APP
    
    guide_title = guide_info["title"]
    guide_steps = guide_info["steps"]
    guide_image = guide_info.get("image")
    download_link = guide_info.get("download_link")
    
    # Create message with guide steps
    guide_text = f"📋 <b>{guide_title}</b>\n\n"
    
    if download_link:
        guide_text += f"📥 <b>دانلود برنامه:</b> <a href='{download_link}'>اینجا کلیک کنید</a>\n\n"
    
    guide_text += "<b>مراحل اتصال:</b>\n\n"
    
    for i, step in enumerate(guide_steps, 1):
        guide_text += f"{i}. {step}\n\n"
    
    # Create keyboard for navigation
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.HELP}_connection")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if guide_image and hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=guide_image,
                    caption=guide_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=guide_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing app guide: {e}")
    
    return SHOWING_APP

def get_app_guide(app_name: str) -> Dict[str, Any]:
    """Get guide information for a specific app."""
    guides = {
        "v2rayng": {
            "title": "راهنمای اتصال با V2rayNG (اندروید)",
            "download_link": "https://play.google.com/store/apps/details?id=com.v2ray.ang",
            "image": ANDROID_GUIDE_IMAGE,
            "steps": [
                "برنامه V2rayNG را از Google Play یا لینک بالا دانلود و نصب کنید.",
                "برنامه را باز کنید و روی علامت + در پایین صفحه کلیک کنید.",
                "گزینه 'Import config from clipboard' را انتخاب کنید.",
                "کد QR یا لینک کانفیگ خود را از بخش 'اکانت های من' در ربات کپی کنید.",
                "برنامه به صورت خودکار کانفیگ را تشخیص داده و اضافه می‌کند.",
                "روی کانفیگ اضافه شده کلیک کنید تا انتخاب شود.",
                "گزینه V در پایین صفحه را بزنید تا به VPN متصل شوید.",
                "پس از اتصال، علامت V سبز رنگ می‌شود."
            ]
        },
        "shadowrocket": {
            "title": "راهنمای اتصال با Shadowrocket (آیفون/آیپد)",
            "download_link": "https://apps.apple.com/us/app/shadowrocket/id932747118",
            "image": IOS_GUIDE_IMAGE,
            "steps": [
                "برنامه Shadowrocket را از App Store خریداری و نصب کنید.",
                "برنامه را باز کنید.",
                "به بخش 'اکانت های من' در ربات بروید و روی دکمه 'مشاهده کانفیگ' کلیک کنید.",
                "روی لینک کانفیگ کلیک کنید تا به صورت خودکار در Shadowrocket باز شود.",
                "در صفحه افزودن کانفیگ، روی 'Add Configuration' کلیک کنید.",
                "به صفحه اصلی برنامه برگردید و کانفیگ اضافه شده را انتخاب کنید.",
                "دکمه 'Connect' را بزنید تا به VPN متصل شوید.",
                "پس از درخواست دسترسی، 'Allow' را انتخاب کنید."
            ]
        },
        "v2rayn": {
            "title": "راهنمای اتصال با V2rayN (ویندوز)",
            "download_link": "https://github.com/2dust/v2rayN/releases/latest",
            "image": WINDOWS_GUIDE_IMAGE,
            "steps": [
                "برنامه V2rayN را از لینک بالا دانلود و از حالت فشرده خارج کنید.",
                "فایل اجرایی v2rayN.exe را اجرا کنید.",
                "روی آیکون برنامه در نوار وظیفه راست کلیک کرده و گزینه 'Import from clipboard' را انتخاب کنید.",
                "کانفیگ خود را از بخش 'اکانت های من' در ربات کپی کنید.",
                "برنامه به صورت خودکار کانفیگ را تشخیص داده و اضافه می‌کند.",
                "روی کانفیگ اضافه شده راست کلیک کرده و 'Set as active server' را انتخاب کنید.",
                "در منوی سیستم، گزینه 'System proxy' و سپس 'Http proxy' را انتخاب کنید.",
                "برای اتصال، آیکون برنامه در نوار وظیفه باید سبز رنگ شود."
            ]
        },
        # Add more app guides as needed
    }
    
    return guides.get(app_name)

async def connection_guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from connection guide."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    parts = callback_data.split("_")
    
    # Check if this is a connection guide callback
    if len(parts) < 2 or parts[1] != "connection":
        return await connection_guide_command(update, context)
    
    # Show platform-specific guide if provided
    if len(parts) > 2:
        platform = parts[2]
        
        if platform == "android":
            return await show_android_guide(update, context)
        elif platform == "ios":
            return await show_ios_guide(update, context)
        elif platform == "windows":
            return await show_windows_guide(update, context)
        elif platform == "mac":
            return await show_mac_guide(update, context)
        elif platform == "linux":
            return await show_linux_guide(update, context)
        elif platform == "router":
            return await show_router_guide(update, context)
    
    # Default - show main connection guide
    return await connection_guide_command(update, context)

async def app_guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks for app-specific guides."""
    return await show_app_guide(update, context)

def get_connection_guide_handlers() -> List:
    """Return all handlers related to connection guides."""
    
    connection_guide_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("connection_guide", connection_guide_command),
            CallbackQueryHandler(connection_guide_callback, pattern=f"^{CallbackPatterns.HELP}_connection")
        ],
        states={
            GUIDE_MAIN: [
                CallbackQueryHandler(connection_guide_callback, pattern=f"^{CallbackPatterns.HELP}_connection"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.HELP}$")
            ],
            SHOWING_PLATFORM: [
                CallbackQueryHandler(connection_guide_callback, pattern=f"^{CallbackPatterns.HELP}_connection"),
                CallbackQueryHandler(app_guide_callback, pattern=f"^{CallbackPatterns.HELP}_app_")
            ],
            SHOWING_APP: [
                CallbackQueryHandler(connection_guide_callback, pattern=f"^{CallbackPatterns.HELP}_connection")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.HELP}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="connection_guide_conversation",
        persistent=False
    )
    
    return [connection_guide_conversation]