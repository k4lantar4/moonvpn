"""
Discount code management handler for admin panel.
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

from bot.services import discount_service
from bot.utils import (
    get_discount_message,
    build_navigation_keyboard,
    format_date,
    format_number
)

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_DISCOUNT_ACTION = 1
ENTERING_DISCOUNT_CODE = 2
ENTERING_DISCOUNT_TYPE = 3
ENTERING_DISCOUNT_VALUE = 4
ENTERING_DISCOUNT_LIMIT = 5
ENTERING_DISCOUNT_EXPIRY = 6
CONFIRMING_ACTION = 7

async def discounts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show discounts management menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="discounts",
        buttons=[
            ("➕ کد تخفیف جدید", "discounts_new"),
            ("📋 لیست کدها", "discounts_list"),
            ("📊 آمار تخفیف‌ها", "discounts_stats"),
            ("🔙 بازگشت", "back_to_admin")
        ]
    )
    
    message = (
        "🎫 <b>مدیریت کدهای تخفیف</b>\n\n"
        "از این بخش می‌توانید کدهای تخفیف را مدیریت کنید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_DISCOUNT_ACTION

async def new_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start creating new discount code."""
    query = update.callback_query
    await query.answer()
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="discounts",
        buttons=[("🔙 بازگشت", "discounts_menu")]
    )
    
    message = (
        "🎫 <b>کد تخفیف جدید</b>\n\n"
        "لطفاً کد تخفیف مورد نظر را وارد کنید:\n"
        "• حداقل 4 کاراکتر\n"
        "• فقط حروف انگلیسی و اعداد\n"
        "• بدون فاصله"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_DISCOUNT_CODE

async def list_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of discount codes."""
    query = update.callback_query
    await query.answer()
    
    # Get page from callback data or default to 1
    page = int(query.data.split('_')[-1]) if '_' in query.data else 1
    
    # Get discounts for current page
    discounts = await discount_service.get_discounts(page=page)
    total_pages = discounts['total_pages']
    
    # Format message
    message = (
        "📋 <b>لیست کدهای تخفیف</b>\n\n"
        f"📄 صفحه {page} از {total_pages}\n\n"
    )
    
    for discount in discounts['items']:
        message += (
            f"🎫 کد: <code>{discount['code']}</code>\n"
            f"💰 مقدار: {format_number(discount['value'])}{'%' if discount['type'] == 'percent' else ' تومان'}\n"
            f"📊 استفاده شده: {discount['used_count']}/{discount['usage_limit'] or '∞'}\n"
            f"📅 انقضا: {format_date(discount['expiry_date'])}\n"
            f"✅ فعال: {'بله' if discount['is_active'] else 'خیر'}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=page,
        total_pages=total_pages,
        base_callback="discounts_list"
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_DISCOUNT_ACTION

async def show_discount_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show discount statistics."""
    query = update.callback_query
    await query.answer()
    
    # Get discount stats
    stats = await discount_service.get_stats()
    
    # Format message
    message = (
        "📊 <b>آمار کدهای تخفیف</b>\n\n"
        f"🎫 کل کدها: {stats['total_codes']}\n"
        f"✅ کدهای فعال: {stats['active_codes']}\n"
        f"❌ کدهای منقضی: {stats['expired_codes']}\n"
        f"💰 مجموع تخفیف: {format_number(stats['total_discount'])} تومان\n"
        f"👥 تعداد استفاده: {stats['total_uses']}\n\n"
        "📅 <b>آمار استفاده:</b>\n"
        f"• امروز: {stats['used_today']} بار\n"
        f"• این هفته: {stats['used_this_week']} بار\n"
        f"• این ماه: {stats['used_this_month']} بار\n\n"
        "🔝 <b>پرکاربردترین کدها:</b>\n"
    )
    
    for code in stats['top_codes']:
        message += (
            f"• {code['code']}:\n"
            f"  - استفاده: {code['uses']} بار\n"
            f"  - تخفیف: {format_number(code['total_discount'])} تومان\n"
        )
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="discounts",
        buttons=[("🔙 بازگشت", "discounts_menu")]
    )
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return SELECTING_DISCOUNT_ACTION

async def process_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered discount code."""
    message = update.message
    code = message.text.strip().upper()
    
    # Validate code format
    if not code.isalnum() or len(code) < 4:
        await message.reply_text(
            "❌ کد تخفیف نامعتبر است.\n"
            "• حداقل 4 کاراکتر\n"
            "• فقط حروف انگلیسی و اعداد\n"
            "• بدون فاصله",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
        return ENTERING_DISCOUNT_CODE
    
    # Check if code exists
    if await discount_service.code_exists(code):
        await message.reply_text(
            "❌ این کد تخفیف قبلاً ثبت شده است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
        return ENTERING_DISCOUNT_CODE
    
    # Store code in context
    context.user_data['new_discount'] = {'code': code}
    
    # Ask for discount type
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="discounts",
        buttons=[
            ("💰 مبلغ ثابت", "discount_type_fixed"),
            ("📊 درصدی", "discount_type_percent"),
            ("🔙 بازگشت", "discounts_menu")
        ]
    )
    
    await message.reply_text(
        "🎫 <b>نوع تخفیف</b>\n\n"
        "لطفاً نوع تخفیف را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_DISCOUNT_TYPE

async def process_discount_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process selected discount type."""
    query = update.callback_query
    await query.answer()
    
    discount_type = query.data.split('_')[-1]
    context.user_data['new_discount']['type'] = discount_type
    
    keyboard = build_navigation_keyboard(
        current_page=1,
        total_pages=1,
        base_callback="discounts",
        buttons=[("🔙 بازگشت", "discounts_menu")]
    )
    
    message = (
        "💰 <b>مقدار تخفیف</b>\n\n"
        "لطفاً مقدار تخفیف را وارد کنید:\n"
    )
    
    if discount_type == 'fixed':
        message += "• به تومان\n• فقط عدد"
    else:
        message += "• به درصد (1-100)\n• فقط عدد"
    
    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    return ENTERING_DISCOUNT_VALUE

async def process_discount_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered discount value."""
    message = update.message
    try:
        value = int(message.text.strip())
        discount_type = context.user_data['new_discount']['type']
        
        if discount_type == 'percent' and (value < 1 or value > 100):
            raise ValueError("Invalid percentage")
        elif discount_type == 'fixed' and value < 1000:
            raise ValueError("Invalid amount")
        
        context.user_data['new_discount']['value'] = value
        
        keyboard = build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="discounts",
            buttons=[("🔙 بازگشت", "discounts_menu")]
        )
        
        await message.reply_text(
            "🔢 <b>محدودیت استفاده</b>\n\n"
            "لطفاً تعداد دفعات مجاز استفاده را وارد کنید:\n"
            "• عدد صحیح\n"
            "• برای نامحدود 0 وارد کنید",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return ENTERING_DISCOUNT_LIMIT
        
    except ValueError:
        await message.reply_text(
            "❌ مقدار وارد شده نامعتبر است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
        return ENTERING_DISCOUNT_VALUE

async def process_discount_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered usage limit."""
    message = update.message
    try:
        limit = int(message.text.strip())
        if limit < 0:
            raise ValueError("Invalid limit")
        
        context.user_data['new_discount']['usage_limit'] = limit or None
        
        keyboard = build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="discounts",
            buttons=[("🔙 بازگشت", "discounts_menu")]
        )
        
        await message.reply_text(
            "📅 <b>تاریخ انقضا</b>\n\n"
            "لطفاً تعداد روز اعتبار را وارد کنید:\n"
            "• عدد صحیح\n"
            "• برای نامحدود 0 وارد کنید",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return ENTERING_DISCOUNT_EXPIRY
        
    except ValueError:
        await message.reply_text(
            "❌ عدد وارد شده نامعتبر است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
        return ENTERING_DISCOUNT_LIMIT

async def process_discount_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process entered expiry days."""
    message = update.message
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError("Invalid days")
        
        context.user_data['new_discount']['expiry_days'] = days or None
        
        # Show confirmation
        discount = context.user_data['new_discount']
        preview = (
            "🎫 <b>تأیید کد تخفیف</b>\n\n"
            f"کد: <code>{discount['code']}</code>\n"
            f"نوع: {'مبلغ ثابت' if discount['type'] == 'fixed' else 'درصدی'}\n"
            f"مقدار: {format_number(discount['value'])}{'%' if discount['type'] == 'percent' else ' تومان'}\n"
            f"محدودیت استفاده: {discount['usage_limit'] or 'نامحدود'}\n"
            f"مدت اعتبار: {discount['expiry_days'] or 'نامحدود'} روز\n\n"
            "آیا از ایجاد این کد تخفیف اطمینان دارید؟"
        )
        
        keyboard = build_navigation_keyboard(
            current_page=1,
            total_pages=1,
            base_callback="discounts",
            buttons=[
                ("✅ تأیید", "discounts_confirm"),
                ("❌ انصراف", "discounts_menu")
            ]
        )
        
        await message.reply_text(
            text=preview,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return CONFIRMING_ACTION
        
    except ValueError:
        await message.reply_text(
            "❌ عدد وارد شده نامعتبر است.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
        return ENTERING_DISCOUNT_EXPIRY

async def create_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create new discount code."""
    query = update.callback_query
    await query.answer()
    
    discount = context.user_data.get('new_discount')
    if not discount:
        await query.edit_message_text(
            "❌ خطا: اطلاعات کد تخفیف یافت نشد.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
        return SELECTING_DISCOUNT_ACTION
    
    try:
        # Create discount code
        result = await discount_service.create_discount(**discount)
        
        # Show success message
        message = get_discount_message(result)
        
        # Clear stored data
        context.user_data.pop('new_discount', None)
        
        await query.edit_message_text(
            text=message,
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error creating discount: {e}")
        await query.edit_message_text(
            "❌ خطا در ایجاد کد تخفیف.",
            reply_markup=build_navigation_keyboard(
                current_page=1,
                total_pages=1,
                base_callback="discounts",
                buttons=[("🔙 بازگشت", "discounts_menu")]
            )
        )
    
    return SELECTING_DISCOUNT_ACTION

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin panel."""
    query = update.callback_query
    await query.answer()
    
    from core.handlers.bot.admin import admin_menu
    return await admin_menu(update, context)

discounts_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(discounts_menu, pattern="^admin_discounts$")
    ],
    states={
        SELECTING_DISCOUNT_ACTION: [
            CallbackQueryHandler(new_discount, pattern="^discounts_new$"),
            CallbackQueryHandler(list_discounts, pattern="^discounts_list"),
            CallbackQueryHandler(show_discount_stats, pattern="^discounts_stats$"),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$"),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
        ],
        ENTERING_DISCOUNT_CODE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_discount_code),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$")
        ],
        ENTERING_DISCOUNT_TYPE: [
            CallbackQueryHandler(process_discount_type, pattern="^discount_type_(fixed|percent)$"),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$")
        ],
        ENTERING_DISCOUNT_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_discount_value),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$")
        ],
        ENTERING_DISCOUNT_LIMIT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_discount_limit),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$")
        ],
        ENTERING_DISCOUNT_EXPIRY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_discount_expiry),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$")
        ],
        CONFIRMING_ACTION: [
            CallbackQueryHandler(create_discount, pattern="^discounts_confirm$"),
            CallbackQueryHandler(discounts_menu, pattern="^discounts_menu$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$")
    ],
    map_to_parent={
        ConversationHandler.END: 'SELECTING_ADMIN_ACTION'
    }
) 