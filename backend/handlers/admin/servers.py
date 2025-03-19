"""
Server management handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from bot.services import vpn_service
from bot.utils import (
    get_server_stats_message,
    build_navigation_keyboard,
    format_date,
    format_bytes
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_SERVER_ACTION = 1
ENTERING_SERVER_NAME = 2
ENTERING_SERVER_HOST = 3
ENTERING_SERVER_PORT = 4
ENTERING_SERVER_LOCATION = 5
CONFIRMING_ACTION = 6

async def servers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show servers management menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="servers",
        buttons=[
            ("➕ سرور جدید", "servers_new"),
            ("📋 لیست سرورها", "servers_list"),
            ("📊 آمار سرورها", "servers_stats"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    message = (
        "🌐 <b>مدیریت سرورها</b>\n\n"
        "از این بخش می‌توانید سرورهای VPN را مدیریت کنید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SERVER_ACTION

async def new_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start creating new server."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="servers",
        buttons=[("🔙 بازگشت", "servers_menu")]
    )
    
    message = (
        "🌐 <b>سرور جدید</b>\n\n"
        "لطفاً نام سرور را وارد کنید:\n"
        "• حداقل 3 کاراکتر\n"
        "• فقط حروف انگلیسی، اعداد و خط تیره"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_SERVER_NAME

async def list_servers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of servers."""
    query = update.callback_query
    await query.answer()
    
    # Get page from callback data or default to 1
    page = int(query.data.split('_')[-1]) if '_' in query.data else 1
    
    # Get servers for current page
    servers = await vpn_service.get_servers(page=page)
    total_pages = servers['total_pages']
    
    # Format message
    message = (
        "📋 <b>لیست سرورها</b>\n\n"
        f"📄 صفحه {page} از {total_pages}\n\n"
    )
    
    for server in servers['items']:
        message += (
            f"🌐 نام: {server['name']}\n"
            f"🌍 موقعیت: {server['location']}\n"
            f"🖥️ هاست: <code>{server['host']}</code>\n"
            f"🔌 پورت: <code>{server['port']}</code>\n"
            f"👥 کاربران: {server['active_users']}\n"
            f"📊 مصرف: {format_bytes(server['total_traffic'])}\n"
            f"✅ وضعیت: {'فعال' if server['is_active'] else 'غیرفعال'}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=page,
        total_pages=total_pages,
        base_callback="servers_list"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SERVER_ACTION

async def show_server_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server statistics."""
    query = update.callback_query
    await query.answer()
    
    # Get server stats
    stats = await vpn_service.get_server_stats()
    
    # Format message
    message = (
        "📊 <b>آمار سرورها</b>\n\n"
        f"🌐 کل سرورها: {stats['total_servers']}\n"
        f"✅ سرورهای فعال: {stats['active_servers']}\n"
        f"❌ سرورهای غیرفعال: {stats['inactive_servers']}\n"
        f"👥 کل کاربران: {stats['total_users']}\n"
        f"📈 مصرف کل: {format_bytes(stats['total_traffic'])}\n\n"
        "🔝 <b>پرمصرف‌ترین سرورها:</b>\n"
    )
    
    for server in stats['top_servers']:
        message += (
            f"• {server['name']} ({server['location']}):\n"
            f"  - کاربران: {server['users']}\n"
            f"  - مصرف: {format_bytes(server['traffic'])}\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="servers",
        buttons=[("🔙 بازگشت", "servers_menu")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_SERVER_ACTION

async def process_server_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered server name."""
    message = update.message
    name = message.text.strip().lower()
    
    # Validate name format
    if not name.replace('-', '').isalnum() or len(name) < 3:
        await message.reply_text(
            "❌ نام سرور نامعتبر است.\n"
            "• حداقل 3 کاراکتر\n"
            "• فقط حروف انگلیسی، اعداد و خط تیره",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="servers",
                buttons=[("🔙 بازگشت", "servers_menu")]
            )
        )
        return ENTERING_SERVER_NAME
    
    # Check if name exists
    if await vpn_service.server_exists(name):
        await message.reply_text(
            "❌ این نام سرور قبلاً ثبت شده است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="servers",
                buttons=[("🔙 بازگشت", "servers_menu")]
            )
        )
        return ENTERING_SERVER_NAME
    
    # Store name in context
    context.user_data['new_server'] = {'name': name}
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="servers",
        buttons=[("🔙 بازگشت", "servers_menu")]
    )
    
    await message.reply_text(
        "🖥️ <b>آدرس سرور</b>\n\n"
        "لطفاً آدرس IP یا دامنه سرور را وارد کنید:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_SERVER_HOST

async def process_server_host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered server host."""
    message = update.message
    host = message.text.strip()
    
    # Store host in context
    context.user_data['new_server']['host'] = host
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="servers",
        buttons=[("🔙 بازگشت", "servers_menu")]
    )
    
    await message.reply_text(
        "🔌 <b>پورت سرور</b>\n\n"
        "لطفاً شماره پورت سرور را وارد کنید:\n"
        "• عدد بین 1 تا 65535",
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_SERVER_PORT

async def process_server_port(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered server port."""
    message = update.message
    try:
        port = int(message.text.strip())
        if port < 1 or port > 65535:
            raise ValueError("Invalid port")
        
        context.user_data['new_server']['port'] = port
        
        keyboard = build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="servers",
            buttons=[("🔙 بازگشت", "servers_menu")]
        )
        
        await message.reply_text(
            "🌍 <b>موقعیت سرور</b>\n\n"
            "لطفاً موقعیت سرور را وارد کنید:\n"
            "مثال: Germany, Netherlands, France",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return ENTERING_SERVER_LOCATION
        
    except ValueError:
        await message.reply_text(
            "❌ پورت وارد شده نامعتبر است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="servers",
                buttons=[("🔙 بازگشت", "servers_menu")]
            )
        )
        return ENTERING_SERVER_PORT

async def process_server_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered server location."""
    message = update.message
    location = message.text.strip()
    
    # Store location in context
    context.user_data['new_server']['location'] = location
    
    # Show confirmation
    server = context.user_data['new_server']
    preview = (
        "🌐 <b>تأیید سرور جدید</b>\n\n"
        f"نام: {server['name']}\n"
        f"آدرس: <code>{server['host']}</code>\n"
        f"پورت: <code>{server['port']}</code>\n"
        f"موقعیت: {server['location']}\n\n"
        "آیا از ایجاد این سرور اطمینان دارید؟"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="servers",
        buttons=[
            ("✅ تأیید", "servers_confirm"),
            ("❌ انصراف", "servers_menu")
        ]
    )
    
    await message.reply_text(
        text=preview,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return CONFIRMING_ACTION

async def create_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create new server."""
    query = update.callback_query
    await query.answer()
    
    server = context.user_data.get('new_server')
    if not server:
        await query.edit_message_text(
            "❌ خطا: اطلاعات سرور یافت نشد.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="servers",
                buttons=[("🔙 بازگشت", "servers_menu")]
            )
        )
        return SELECTING_SERVER_ACTION
    
    try:
        # Create server
        result = await vpn_service.create_server(**server)
        
        # Show success message
        message = get_server_stats_message(result)
        
        # Clear stored data
        context.user_data.pop('new_server', None)
        
        await query.edit_message_text(
            text=message,
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="servers",
                buttons=[("🔙 بازگشت", "servers_menu")]
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating server: {e}")
        await query.edit_message_text(
            "❌ خطا در ایجاد سرور.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="servers",
                buttons=[("🔙 بازگشت", "servers_menu")]
            )
        )
    
    return SELECTING_SERVER_ACTION

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

servers_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(servers_menu, pattern="^admin_servers$")
    ],
    states={
        SELECTING_SERVER_ACTION: [
            CallbackQueryHandler(new_server, pattern="^servers_new$"),
            CallbackQueryHandler(list_servers, pattern="^servers_list"),
            CallbackQueryHandler(show_server_stats, pattern="^servers_stats$"),
            CallbackQueryHandler(servers_menu, pattern="^servers_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        ENTERING_SERVER_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_server_name),
            CallbackQueryHandler(servers_menu, pattern="^servers_menu$")
        ],
        ENTERING_SERVER_HOST: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_server_host),
            CallbackQueryHandler(servers_menu, pattern="^servers_menu$")
        ],
        ENTERING_SERVER_PORT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_server_port),
            CallbackQueryHandler(servers_menu, pattern="^servers_menu$")
        ],
        ENTERING_SERVER_LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_server_location),
            CallbackQueryHandler(servers_menu, pattern="^servers_menu$")
        ],
        CONFIRMING_ACTION: [
            CallbackQueryHandler(create_server, pattern="^servers_confirm$"),
            CallbackQueryHandler(servers_menu, pattern="^servers_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 