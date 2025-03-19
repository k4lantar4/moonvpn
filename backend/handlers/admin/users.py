"""
User management handler for admin panel.
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

from bot.services import user_service
from bot.utils import (
    get_user_stats_message,
    build_navigation_keyboard,
    format_date,
    format_bytes
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_USER_ACTION = 1
ENTERING_USER_ID = 2
CONFIRMING_ACTION = 3

async def users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show users management menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="users",
        buttons=[
            ("👥 لیست کاربران", "users_list"),
            ("🔍 جستجوی کاربر", "users_search"),
            ("📊 آمار کاربران", "users_stats"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    message = (
        "👥 <b>مدیریت کاربران</b>\n\n"
        "از این بخش می‌توانید کاربران را مدیریت کنید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_USER_ACTION

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of users."""
    query = update.callback_query
    await query.answer()
    
    # Get page from callback data or default to 1
    page = int(query.data.split('_')[-1]) if '_' in query.data else 1
    
    # Get users for current page
    users = await user_service.get_users(page=page)
    total_pages = users['total_pages']
    
    # Format message
    message = (
        "👥 <b>لیست کاربران</b>\n\n"
        f"📄 صفحه {page} از {total_pages}\n\n"
    )
    
    for user in users['items']:
        message += (
            f"👤 {user.get('first_name', 'کاربر')} "
            f"(@{user.get('username', 'بدون نام کاربری')})\n"
            f"🆔 شناسه: <code>{user['id']}</code>\n"
            f"📅 عضویت: {format_date(user['joined_date'])}\n"
            f"✅ اشتراک فعال: {user['active_accounts']}\n"
            f"📊 مصرف کل: {format_bytes(user['total_traffic'])}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=page,
        total_pages=total_pages,
        base_callback="users_list"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_USER_ACTION

async def search_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user search interface."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="users",
        buttons=[("🔙 بازگشت", "users_menu")]
    )
    
    message = (
        "🔍 <b>جستجوی کاربر</b>\n\n"
        "لطفاً شناسه تلگرام یا نام کاربری مورد نظر را وارد کنید:"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_USER_ID

async def show_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user details."""
    message = update.message
    user_id = message.text.strip()
    
    # Get user details
    user = await user_service.get_user(user_id)
    if not user:
        await message.reply_text(
            "❌ کاربر مورد نظر یافت نشد.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="users",
                buttons=[("🔙 بازگشت", "users_menu")]
            )
        )
        return SELECTING_USER_ACTION
    
    # Store user ID in context for actions
    context.user_data['target_user_id'] = user['id']
    
    # Format message
    stats_message = get_user_stats_message(user)
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="users",
        buttons=[
            ("🚫 مسدود کردن", "users_block"),
            ("✅ رفع مسدودی", "users_unblock"),
            ("❌ حذف کاربر", "users_delete"),
            ("🔙 بازگشت", "users_menu")
        ]
    )
    
    await message.reply_text(
        text=stats_message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_USER_ACTION

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user statistics."""
    query = update.callback_query
    await query.answer()
    
    # Get user stats
    stats = await user_service.get_stats()
    
    # Format message
    message = (
        "📊 <b>آمار کاربران</b>\n\n"
        f"👥 کل کاربران: {stats['total_users']}\n"
        f"✅ کاربران فعال: {stats['active_users']}\n"
        f"❌ کاربران غیرفعال: {stats['inactive_users']}\n"
        f"🚫 کاربران مسدود: {stats['blocked_users']}\n"
        f"📈 میانگین مصرف: {format_bytes(stats['average_traffic'])}\n\n"
        "📅 <b>آمار عضویت:</b>\n"
        f"• امروز: {stats['joined_today']} کاربر\n"
        f"• این هفته: {stats['joined_this_week']} کاربر\n"
        f"• این ماه: {stats['joined_this_month']} کاربر\n\n"
        "🌐 <b>آمار سرورها:</b>\n"
    )
    
    for server in stats['servers']:
        message += (
            f"• {server['name']}:\n"
            f"  - کاربران: {server['users']}\n"
            f"  - مصرف: {format_bytes(server['traffic'])}\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="users",
        buttons=[("🔙 بازگشت", "users_menu")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_USER_ACTION

async def confirm_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm user action."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[1]
    user_id = context.user_data.get('target_user_id')
    
    if not user_id:
        await query.edit_message_text(
            "❌ خطا: کاربر مورد نظر یافت نشد.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="users",
                buttons=[("🔙 بازگشت", "users_menu")]
            )
        )
        return SELECTING_USER_ACTION
    
    # Get user details
    user = await user_service.get_user(user_id)
    if not user:
        await query.edit_message_text(
            "❌ خطا: کاربر مورد نظر یافت نشد.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="users",
                buttons=[("🔙 بازگشت", "users_menu")]
            )
        )
        return SELECTING_USER_ACTION
    
    # Store action in context
    context.user_data['user_action'] = action
    
    # Format confirmation message
    action_messages = {
        'block': 'مسدود کردن',
        'unblock': 'رفع مسدودی',
        'delete': 'حذف'
    }
    
    message = (
        f"⚠️ <b>تأیید {action_messages[action]}</b>\n\n"
        f"آیا از {action_messages[action]} کاربر زیر اطمینان دارید؟\n\n"
        f"👤 {user.get('first_name', 'کاربر')} "
        f"(@{user.get('username', 'بدون نام کاربری')})\n"
        f"🆔 شناسه: <code>{user['id']}</code>"
    )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="users",
        buttons=[
            ("✅ تأیید", "users_confirm"),
            ("❌ انصراف", "users_menu")
        ]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return CONFIRMING_ACTION

async def execute_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Execute confirmed user action."""
    query = update.callback_query
    await query.answer()
    
    action = context.user_data.get('user_action')
    user_id = context.user_data.get('target_user_id')
    
    if not action or not user_id:
        await query.edit_message_text(
            "❌ خطا: اطلاعات عملیات ناقص است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="users",
                buttons=[("🔙 بازگشت", "users_menu")]
            )
        )
        return SELECTING_USER_ACTION
    
    # Execute action
    try:
        if action == 'block':
            await user_service.block_user(user_id)
            message = "✅ کاربر با موفقیت مسدود شد."
        elif action == 'unblock':
            await user_service.unblock_user(user_id)
            message = "✅ مسدودیت کاربر با موفقیت رفع شد."
        elif action == 'delete':
            await user_service.delete_user(user_id)
            message = "✅ کاربر با موفقیت حذف شد."
        else:
            message = "❌ عملیات نامعتبر است."
    except Exception as e:
        logger.error(f"Error executing user action: {e}")
        message = "❌ خطا در اجرای عملیات."
    
    # Clear stored data
    context.user_data.pop('user_action', None)
    context.user_data.pop('target_user_id', None)
    
    await query.edit_message_text(
        text=message,
        reply_markup=build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="users",
            buttons=[("🔙 بازگشت", "users_menu")]
        ),
        parse_mode='HTML'
    )
    
    return SELECTING_USER_ACTION

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

users_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(users_menu, pattern="^admin_users$")
    ],
    states={
        SELECTING_USER_ACTION: [
            CallbackQueryHandler(list_users, pattern="^users_list"),
            CallbackQueryHandler(search_users, pattern="^users_search$"),
            CallbackQueryHandler(show_user_stats, pattern="^users_stats$"),
            CallbackQueryHandler(users_menu, pattern="^users_menu$"),
            CallbackQueryHandler(confirm_user_action, pattern="^users_(block|unblock|delete)$"),
            CallbackQueryHandler(execute_user_action, pattern="^users_confirm$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        ENTERING_USER_ID: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, show_user),
            CallbackQueryHandler(users_menu, pattern="^users_menu$")
        ],
        CONFIRMING_ACTION: [
            CallbackQueryHandler(execute_user_action, pattern="^users_confirm$"),
            CallbackQueryHandler(users_menu, pattern="^users_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 