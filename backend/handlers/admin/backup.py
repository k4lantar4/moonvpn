"""
Backup management handler for admin panel.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import os
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from bot.services import backup_service
from bot.utils import (
    build_navigation_keyboard,
    format_size,
    format_date
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_BACKUP_ACTION = 1
CONFIRMING_BACKUP = 2
SELECTING_RESTORE_FILE = 3
CONFIRMING_RESTORE = 4

async def backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show backup management menu."""
    query = update.callback_query
    await query.answer()
    
    # Get backup stats
    stats = await backup_service.get_backup_stats()
    
    message = (
        "🔄 <b>مدیریت بکاپ</b>\n\n"
        "📊 <b>آمار بکاپ‌ها:</b>\n"
        f"• تعداد کل: {stats['total_backups']}\n"
        f"• حجم کل: {format_size(stats['total_size'])}\n"
        f"• آخرین بکاپ: {format_date(stats['last_backup'])}\n"
        f"• وضعیت: {stats['status']}\n\n"
        "🗂 <b>تنظیمات فعلی:</b>\n"
        f"• مسیر ذخیره: {stats['backup_path']}\n"
        f"• زمان‌بندی: {stats['schedule']}\n"
        f"• نگهداری: {stats['retention']} روز\n"
        f"• فشرده‌سازی: {stats['compression']}"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=[
            ("📥 بکاپ جدید", "backup_create"),
            ("📤 بازیابی", "backup_restore"),
            ("📋 لیست بکاپ‌ها", "backup_list"),
            ("⚙️ تنظیمات", "backup_settings"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_BACKUP_ACTION

async def create_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start backup creation process."""
    query = update.callback_query
    await query.answer()
    
    # Get backup info
    backup_info = await backup_service.get_backup_info()
    
    message = (
        "📥 <b>ایجاد بکاپ جدید</b>\n\n"
        "اطلاعات بکاپ:\n"
        f"• نام فایل: {backup_info['filename']}\n"
        f"• حجم تقریبی: {format_size(backup_info['estimated_size'])}\n"
        f"• مسیر ذخیره: {backup_info['path']}\n\n"
        "آیا از ایجاد بکاپ جدید اطمینان دارید؟"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=[
            ("✅ تأیید", "backup_confirm"),
            ("❌ انصراف", "backup_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return CONFIRMING_BACKUP

async def confirm_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create new backup after confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Show progress message
    progress_message = await query.edit_message_text(
        "⏳ در حال ایجاد بکاپ...\n"
        "لطفاً صبر کنید...",
        parse_mode='HTML'
    )
    
    try:
        # Create backup
        result = await backup_service.create_backup()
        
        message = (
            "✅ <b>بکاپ با موفقیت ایجاد شد</b>\n\n"
            f"• نام فایل: {result['filename']}\n"
            f"• حجم: {format_size(result['size'])}\n"
            f"• تاریخ: {format_date(result['created_at'])}\n"
            f"• مسیر: {result['path']}"
        )
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        message = (
            "❌ <b>خطا در ایجاد بکاپ</b>\n\n"
            f"علت: {str(e)}"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=[("🔙 بازگشت", "backup_menu")]
    )
    
    await progress_message.edit_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_BACKUP_ACTION

async def list_backups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of available backups."""
    query = update.callback_query
    await query.answer()
    
    # Get page from callback data or default to 1
    page = int(query.data.split('_')[-1]) if '_' in query.data else 1
    
    # Get backups for current page
    backups = await backup_service.get_backups(page=page)
    total_pages = backups['total_pages']
    
    message = (
        "📋 <b>لیست بکاپ‌ها</b>\n\n"
        f"📄 صفحه {page} از {total_pages}\n\n"
    )
    
    for backup in backups['items']:
        message += (
            f"📦 <b>{backup['filename']}</b>\n"
            f"📅 تاریخ: {format_date(backup['created_at'])}\n"
            f"💾 حجم: {format_size(backup['size'])}\n"
            f"🔐 نوع: {backup['type']}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=page,
        total_pages=total_pages,
        base_callback="backup_list",
        extra_buttons=[("🔙 بازگشت", "backup_menu")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_BACKUP_ACTION

async def show_restore_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show backup restore options."""
    query = update.callback_query
    await query.answer()
    
    # Get recent backups
    backups = await backup_service.get_recent_backups()
    
    message = (
        "📤 <b>بازیابی بکاپ</b>\n\n"
        "⚠️ <b>هشدار:</b> بازیابی بکاپ باعث حذف اطلاعات فعلی خواهد شد.\n"
        "لطفاً فایل بکاپ مورد نظر را انتخاب کنید:\n\n"
    )
    
    # Create keyboard with backup files
    buttons = []
    for backup in backups:
        buttons.append((
            f"📦 {backup['filename']} - {format_date(backup['created_at'])}",
            f"backup_select_{backup['id']}"
        ))
    
    buttons.append(("🔙 بازگشت", "backup_menu"))
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=buttons
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_RESTORE_FILE

async def confirm_restore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm backup restoration."""
    query = update.callback_query
    await query.answer()
    
    # Get backup ID from callback data
    backup_id = query.data.split('_')[-1]
    
    # Get backup info
    backup = await backup_service.get_backup_info(backup_id)
    
    message = (
        "⚠️ <b>تأیید بازیابی بکاپ</b>\n\n"
        "آیا از بازیابی این بکاپ اطمینان دارید؟\n"
        "این عملیات قابل بازگشت نیست!\n\n"
        f"• نام فایل: {backup['filename']}\n"
        f"• تاریخ: {format_date(backup['created_at'])}\n"
        f"• حجم: {format_size(backup['size'])}\n"
        f"• نوع: {backup['type']}"
    )
    
    # Store backup ID in context
    context.user_data['restore_backup_id'] = backup_id
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=[
            ("✅ تأیید و بازیابی", "backup_restore_confirm"),
            ("❌ انصراف", "backup_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return CONFIRMING_RESTORE

async def restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restore selected backup."""
    query = update.callback_query
    await query.answer()
    
    # Get backup ID from context
    backup_id = context.user_data.get('restore_backup_id')
    if not backup_id:
        message = "❌ خطا: شناسه بکاپ یافت نشد."
        keyboard = build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="backup",
            buttons=[("🔙 بازگشت", "backup_menu")]
        )
        
        await query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return SELECTING_BACKUP_ACTION
    
    # Show progress message
    progress_message = await query.edit_message_text(
        "⏳ در حال بازیابی بکاپ...\n"
        "لطفاً صبر کنید...",
        parse_mode='HTML'
    )
    
    try:
        # Restore backup
        result = await backup_service.restore_backup(backup_id)
        
        message = (
            "✅ <b>بکاپ با موفقیت بازیابی شد</b>\n\n"
            f"• نام فایل: {result['filename']}\n"
            f"• تاریخ بکاپ: {format_date(result['created_at'])}\n"
            f"• تاریخ بازیابی: {format_date(datetime.now())}\n"
            f"• وضعیت: {result['status']}"
        )
        
    except Exception as e:
        logger.error(f"Backup restoration failed: {e}")
        message = (
            "❌ <b>خطا در بازیابی بکاپ</b>\n\n"
            f"علت: {str(e)}"
        )
    
    # Clear backup ID from context
    context.user_data.pop('restore_backup_id', None)
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=[("🔙 بازگشت", "backup_menu")]
    )
    
    await progress_message.edit_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_BACKUP_ACTION

async def show_backup_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show backup settings."""
    query = update.callback_query
    await query.answer()
    
    # Get current settings
    settings = await backup_service.get_backup_settings()
    
    message = (
        "⚙️ <b>تنظیمات بکاپ</b>\n\n"
        "🗂 <b>ذخیره‌سازی:</b>\n"
        f"• مسیر: {settings['backup_path']}\n"
        f"• فرمت: {settings['format']}\n"
        f"• فشرده‌سازی: {settings['compression']}\n\n"
        "⏱ <b>زمان‌بندی:</b>\n"
        f"• دوره: {settings['schedule']}\n"
        f"• ساعت: {settings['time']}\n"
        f"• نگهداری: {settings['retention']} روز\n\n"
        "🔄 <b>همگام‌سازی:</b>\n"
        f"• آپلود خودکار: {'فعال' if settings['auto_upload'] else 'غیرفعال'}\n"
        f"• مقصد: {settings['upload_destination']}"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="backup",
        buttons=[
            ("🗂 ذخیره‌سازی", "backup_storage_settings"),
            ("⏱ زمان‌بندی", "backup_schedule_settings"),
            ("🔄 همگام‌سازی", "backup_sync_settings"),
            ("🔙 بازگشت", "backup_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_BACKUP_ACTION

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

backup_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(backup_menu, pattern="^admin_backup$")
    ],
    states={
        SELECTING_BACKUP_ACTION: [
            CallbackQueryHandler(create_backup, pattern="^backup_create$"),
            CallbackQueryHandler(show_restore_options, pattern="^backup_restore$"),
            CallbackQueryHandler(list_backups, pattern="^backup_list"),
            CallbackQueryHandler(show_backup_settings, pattern="^backup_settings$"),
            CallbackQueryHandler(backup_menu, pattern="^backup_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        CONFIRMING_BACKUP: [
            CallbackQueryHandler(confirm_backup, pattern="^backup_confirm$"),
            CallbackQueryHandler(backup_menu, pattern="^backup_menu$")
        ],
        SELECTING_RESTORE_FILE: [
            CallbackQueryHandler(confirm_restore, pattern="^backup_select_"),
            CallbackQueryHandler(backup_menu, pattern="^backup_menu$")
        ],
        CONFIRMING_RESTORE: [
            CallbackQueryHandler(restore_backup, pattern="^backup_restore_confirm$"),
            CallbackQueryHandler(backup_menu, pattern="^backup_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 