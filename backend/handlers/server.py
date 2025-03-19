"""Server management handlers for the admin panel."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from services.server_manager import ServerManager, ServerStatus, ServerInfo
from core.utils.helpers import admin_only
from core.database import get_setting, update_setting
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Server management states
(
    SERVER_MENU,
    ADD_SERVER_URL,
    ADD_SERVER_USERNAME,
    ADD_SERVER_PASSWORD,
    ADD_SERVER_NAME,
    ADD_SERVER_LOCATION,
    REMOVE_SERVER_CONFIRM,
    SERVER_DETAILS,
) = range(8)

@admin_only
async def server_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display server management menu"""
    keyboard = [
        [InlineKeyboardButton("📊 مشاهده سرورها", callback_data="list_servers")],
        [InlineKeyboardButton("➕ افزودن سرور", callback_data="add_server")],
        [InlineKeyboardButton("🔄 همگام‌سازی", callback_data="sync_servers")],
        [InlineKeyboardButton("📈 وضعیت سیستم", callback_data="system_status")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🖥️ مدیریت سرورها\n\n"
        "از منوی زیر گزینه مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return SERVER_MENU

@admin_only
async def list_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all configured servers with their status"""
    server_manager = ServerManager()
    servers = await server_manager.get_all_servers()
    
    if not servers:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="server_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            "❌ هیچ سروری پیکربندی نشده است.",
            reply_markup=reply_markup
        )
        return SERVER_MENU
    
    message = "📋 لیست سرورها:\n\n"
    keyboard = []
    
    for server in servers:
        status_emoji = {
            ServerStatus.ONLINE: "🟢",
            ServerStatus.OFFLINE: "🔴",
            ServerStatus.MAINTENANCE: "🟡",
            ServerStatus.ERROR: "⚠️"
        }.get(server.status, "⚫️")
        
        message += (
            f"{status_emoji} *{server.name}*\n"
            f"📍 موقعیت: {server.location}\n"
            f"💾 حافظه: {server.memory_used:.1f}/{server.memory_total:.1f} GB\n"
            f"🔄 آخرین همگام‌سازی: {server.last_sync.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {server.name}",
            callback_data=f"server_details_{server.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="server_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SERVER_MENU

@admin_only
async def add_server_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add server process"""
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🌐 افزودن سرور جدید\n\n"
        "لطفاً آدرس پنل 3x-UI را وارد کنید:\n"
        "مثال: https://panel.example.com:2053",
        reply_markup=reply_markup
    )
    return ADD_SERVER_URL

@admin_only
async def add_server_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server URL input"""
    url = update.message.text.strip()
    context.user_data['new_server'] = {'url': url}
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👤 لطفاً نام کاربری پنل را وارد کنید:",
        reply_markup=reply_markup
    )
    return ADD_SERVER_USERNAME

@admin_only
async def add_server_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server username input"""
    username = update.message.text.strip()
    context.user_data['new_server']['username'] = username
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔑 لطفاً رمز عبور پنل را وارد کنید:",
        reply_markup=reply_markup
    )
    return ADD_SERVER_PASSWORD

@admin_only
async def add_server_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server password input"""
    password = update.message.text.strip()
    context.user_data['new_server']['password'] = password
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 لطفاً نام نمایشی سرور را وارد کنید:",
        reply_markup=reply_markup
    )
    return ADD_SERVER_NAME

@admin_only
async def add_server_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server name input"""
    name = update.message.text.strip()
    context.user_data['new_server']['name'] = name
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📍 لطفاً موقعیت سرور را وارد کنید (مثال: Germany):",
        reply_markup=reply_markup
    )
    return ADD_SERVER_LOCATION

@admin_only
async def add_server_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server location input and complete server addition"""
    location = update.message.text.strip()
    new_server = context.user_data['new_server']
    new_server['location'] = location
    
    server_manager = ServerManager()
    try:
        server = await server_manager.add_server(
            name=new_server['name'],
            host=new_server['url'].split('://')[1].split(':')[0],
            port=int(new_server['url'].split(':')[-1]),
            panel_url=new_server['url'],
            panel_username=new_server['username'],
            panel_password=new_server['password'],
            location=new_server['location']
        )
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="server_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ سرور {server.name} با موفقیت اضافه شد!\n\n"
            f"📍 موقعیت: {server.location}\n"
            f"🌐 آدرس: {server.panel_url}\n"
            f"⚡️ وضعیت: {server.status.value}",
            reply_markup=reply_markup
        )
    except Exception as e:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="server_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ خطا در افزودن سرور:\n{str(e)}",
            reply_markup=reply_markup
        )
    
    context.user_data.pop('new_server', None)
    return SERVER_MENU

@admin_only
async def server_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display detailed information about a server"""
    server_id = update.callback_query.data.split('_')[-1]
    server_manager = ServerManager()
    server = await server_manager.get_server(server_id)
    
    if not server:
        await update.callback_query.answer("❌ سرور یافت نشد!")
        return SERVER_MENU
    
    stats = await server_manager.get_server_stats(server_id)
    
    message = (
        f"🖥️ *{server.name}*\n\n"
        f"📍 موقعیت: {server.location}\n"
        f"🌐 آدرس: {server.panel_url}\n"
        f"⚡️ وضعیت: {server.status.value}\n\n"
        f"📊 آمار سیستم:\n"
        f"CPU: {stats['system']['load']:.1f}%\n"
        f"RAM: {stats['system']['memory']['percentage']:.1f}%\n"
        f"Disk: {stats['system']['disk']['percentage']:.1f}%\n\n"
        f"📈 ترافیک:\n"
        f"استفاده شده: {stats['traffic']['used'] / 1024 / 1024 / 1024:.2f} GB\n"
        f"کل: {stats['traffic']['total'] / 1024 / 1024 / 1024:.2f} GB\n"
        f"باقیمانده: {stats['traffic']['remaining'] / 1024 / 1024 / 1024:.2f} GB\n\n"
        f"🕒 آخرین همگام‌سازی: {server.last_sync.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 همگام‌سازی", callback_data=f"sync_server_{server_id}"),
            InlineKeyboardButton("❌ حذف", callback_data=f"remove_server_{server_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="list_servers")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SERVER_MENU

@admin_only
async def sync_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchronize all servers"""
    await update.callback_query.answer("🔄 در حال همگام‌سازی...")
    
    server_manager = ServerManager()
    try:
        servers = await server_manager.get_all_servers()
        success = 0
        failed = 0
        
        message = "🔄 نتیجه همگام‌سازی:\n\n"
        
        for server in servers:
            try:
                await server_manager._sync_server(server)
                success += 1
                message += f"✅ {server.name}: موفق\n"
            except Exception as e:
                failed += 1
                message += f"❌ {server.name}: {str(e)}\n"
        
        message += f"\nموفق: {success}\nناموفق: {failed}"
        
    except Exception as e:
        message = f"❌ خطا در همگام‌سازی:\n{str(e)}"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )
    return SERVER_MENU

@admin_only
async def remove_server_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm server removal"""
    server_id = update.callback_query.data.split('_')[-1]
    server_manager = ServerManager()
    server = await server_manager.get_server(server_id)
    
    if not server:
        await update.callback_query.answer("❌ سرور یافت نشد!")
        return SERVER_MENU
    
    keyboard = [
        [
            InlineKeyboardButton("✅ بله", callback_data=f"remove_server_confirmed_{server_id}"),
            InlineKeyboardButton("❌ خیر", callback_data=f"server_details_{server_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"⚠️ آیا از حذف سرور {server.name} اطمینان دارید؟\n"
        "این عمل غیرقابل بازگشت است!",
        reply_markup=reply_markup
    )
    return REMOVE_SERVER_CONFIRM

@admin_only
async def remove_server_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove server after confirmation"""
    server_id = update.callback_query.data.split('_')[-1]
    server_manager = ServerManager()
    
    try:
        server = await server_manager.get_server(server_id)
        if not server:
            raise Exception("سرور یافت نشد!")
        
        success = await server_manager.remove_server(server_id)
        if success:
            message = f"✅ سرور {server.name} با موفقیت حذف شد."
        else:
            message = "❌ خطا در حذف سرور!"
    except Exception as e:
        message = f"❌ خطا در حذف سرور:\n{str(e)}"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )
    return SERVER_MENU

@admin_only
async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display overall system status"""
    server_manager = ServerManager()
    servers = await server_manager.get_all_servers()
    
    total_servers = len(servers)
    online_servers = len([s for s in servers if s.status == ServerStatus.ONLINE])
    maintenance_servers = len([s for s in servers if s.status == ServerStatus.MAINTENANCE])
    offline_servers = len([s for s in servers if s.status == ServerStatus.OFFLINE])
    
    total_memory = sum(s.memory_total for s in servers)
    used_memory = sum(s.memory_used for s in servers)
    memory_percent = (used_memory / total_memory * 100) if total_memory > 0 else 0
    
    message = (
        "📊 وضعیت کلی سیستم\n\n"
        f"🖥️ سرورها:\n"
        f"کل: {total_servers}\n"
        f"آنلاین: {online_servers} 🟢\n"
        f"تعمیرات: {maintenance_servers} 🟡\n"
        f"آفلاین: {offline_servers} 🔴\n\n"
        f"💾 حافظه کل:\n"
        f"استفاده شده: {used_memory:.1f} GB\n"
        f"کل: {total_memory:.1f} GB\n"
        f"درصد: {memory_percent:.1f}%\n\n"
        f"🕒 آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="server_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup
    )
    return SERVER_MENU

# Server management handlers
server_handlers = [
    CallbackQueryHandler(server_menu, pattern="^server_menu$"),
    CallbackQueryHandler(list_servers, pattern="^list_servers$"),
    CallbackQueryHandler(add_server_start, pattern="^add_server$"),
    CallbackQueryHandler(sync_servers, pattern="^sync_servers$"),
    CallbackQueryHandler(system_status, pattern="^system_status$"),
    CallbackQueryHandler(server_details, pattern="^server_details_"),
    CallbackQueryHandler(remove_server_confirm, pattern="^remove_server_"),
    CallbackQueryHandler(remove_server_confirmed, pattern="^remove_server_confirmed_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_url, ADD_SERVER_URL),
    MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_username, ADD_SERVER_USERNAME),
    MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_password, ADD_SERVER_PASSWORD),
    MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_name, ADD_SERVER_NAME),
    MessageHandler(filters.TEXT & ~filters.COMMAND, add_server_location, ADD_SERVER_LOCATION),
] 