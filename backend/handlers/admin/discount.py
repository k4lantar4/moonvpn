"""
Discount code management handlers for admin panel.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from bot.services.payment_service import PaymentService
from core.utils.helpers import format_number
from core.utils.helpers import admin_only

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_DISCOUNT_ACTION, ADDING_DISCOUNT_CODE, ADDING_DISCOUNT_VALUE = range(3)
ADDING_DISCOUNT_TYPE, ADDING_DISCOUNT_EXPIRY, ADDING_DISCOUNT_DESCRIPTION = range(3, 6)
CONFIRMING_DISCOUNT_DELETE = 6

payment_service = PaymentService()

@admin_only
async def discount_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show discount code management menu."""
    query = update.callback_query
    await query.answer()
    
    # Get all discount codes
    discount_codes = payment_service.get_discount_codes()
    
    message = "🏷️ <b>مدیریت کدهای تخفیف</b>\n\n"
    
    if not discount_codes:
        message += "هیچ کد تخفیفی ثبت نشده است."
    else:
        for code in discount_codes:
            status_emoji = "✅" if code['status'] == 'active' else "❌"
            expiry = datetime.strptime(code['expiry_date'], '%Y-%m-%d').strftime('%Y/%m/%d')
            value = f"{code['value']}{'٪' if code['type'] == 'percent' else ' تومان'}"
            
            message += (
                f"{status_emoji} <b>{code['code']}</b>\n"
                f"📊 {value} | 📅 {expiry}\n"
                f"👥 {code['current_uses']}/{code['max_uses'] or '∞'} بار استفاده\n"
                f"💬 {code['description']}\n\n"
            )
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کد تخفیف", callback_data="add_discount")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_discounts")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]
    ]
    
    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    return SELECTING_DISCOUNT_ACTION

async def add_discount_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start adding a new discount code."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "🏷️ <b>افزودن کد تخفیف جدید</b>\n\n"
        "لطفاً کد تخفیف را وارد کنید.\n"
        "مثال: SUMMER2024\n\n"
        "برای انصراف از دستور /cancel استفاده کنید.",
        parse_mode=ParseMode.HTML
    )
    
    return ADDING_DISCOUNT_CODE

async def add_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered discount code."""
    code = update.message.text.strip().upper()
    
    if len(code) < 3 or len(code) > 20:
        await update.message.reply_text(
            "❌ کد تخفیف باید بین 3 تا 20 کاراکتر باشد.\n"
            "لطفاً مجدداً تلاش کنید:"
        )
        return ADDING_DISCOUNT_CODE
    
    # Store code in context
    context.user_data['new_discount'] = {'code': code}
    
    # Ask for discount type
    keyboard = [
        [
            InlineKeyboardButton("درصدی", callback_data="discount_type_percent"),
            InlineKeyboardButton("مقداری", callback_data="discount_type_fixed")
        ],
        [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_add_discount")]
    ]
    
    await update.message.reply_text(
        "🔢 <b>نوع تخفیف را انتخاب کنید:</b>\n\n"
        "• درصدی: درصدی از مبلغ کل\n"
        "• مقداری: مبلغ ثابت",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    return ADDING_DISCOUNT_TYPE

async def add_discount_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the selected discount type."""
    query = update.callback_query
    await query.answer()
    
    discount_type = query.data.split('_')[2]  # discount_type_percent -> percent
    context.user_data['new_discount']['type'] = discount_type
    
    type_text = "درصد" if discount_type == "percent" else "تومان"
    
    await query.message.edit_text(
        f"💯 <b>مقدار تخفیف را وارد کنید ({type_text}):</b>\n\n"
        f"{'عدد بین 1 تا 100 وارد کنید' if discount_type == 'percent' else 'مبلغ را به تومان وارد کنید'}\n\n"
        "برای انصراف از دستور /cancel استفاده کنید.",
        parse_mode=ParseMode.HTML
    )
    
    return ADDING_DISCOUNT_VALUE

async def add_discount_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered discount value."""
    try:
        value = float(update.message.text.strip())
        discount_type = context.user_data['new_discount']['type']
        
        if discount_type == 'percent' and (value <= 0 or value > 100):
            raise ValueError("درصد تخفیف باید بین 1 تا 100 باشد")
        elif discount_type == 'fixed' and value <= 0:
            raise ValueError("مبلغ تخفیف باید بزرگتر از صفر باشد")
        
        context.user_data['new_discount']['value'] = value
        
        await update.message.reply_text(
            "📅 <b>تاریخ انقضای کد تخفیف را وارد کنید:</b>\n\n"
            "فرمت: YYYY-MM-DD\n"
            "مثال: 2024-12-31\n\n"
            "برای انصراف از دستور /cancel استفاده کنید.",
            parse_mode=ParseMode.HTML
        )
        
        return ADDING_DISCOUNT_EXPIRY
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}\n"
            "لطفاً مجدداً تلاش کنید:"
        )
        return ADDING_DISCOUNT_VALUE

async def add_discount_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered expiry date."""
    try:
        expiry_date = datetime.strptime(update.message.text.strip(), '%Y-%m-%d')
        if expiry_date < datetime.now():
            raise ValueError("تاریخ انقضا نمی‌تواند در گذشته باشد")
        
        context.user_data['new_discount']['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
        
        await update.message.reply_text(
            "💬 <b>توضیحات کد تخفیف را وارد کنید:</b>\n\n"
            "این توضیحات برای شناسایی بهتر کد تخفیف استفاده می‌شود.\n\n"
            "برای انصراف از دستور /cancel استفاده کنید.",
            parse_mode=ParseMode.HTML
        )
        
        return ADDING_DISCOUNT_DESCRIPTION
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ تاریخ نامعتبر است: {str(e)}\n"
            "لطفاً با فرمت YYYY-MM-DD وارد کنید:"
        )
        return ADDING_DISCOUNT_EXPIRY

async def add_discount_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the entered description and create the discount code."""
    description = update.message.text.strip()
    
    if len(description) < 3:
        await update.message.reply_text(
            "❌ توضیحات باید حداقل 3 کاراکتر باشد.\n"
            "لطفاً مجدداً تلاش کنید:"
        )
        return ADDING_DISCOUNT_DESCRIPTION
    
    # Get all discount info
    discount_info = context.user_data['new_discount']
    discount_info['description'] = description
    
    # Create discount code
    success, result = payment_service.create_discount_code(
        code=discount_info['code'],
        discount_type=discount_info['type'],
        value=discount_info['value'],
        description=discount_info['description'],
        expiry_date=discount_info['expiry_date']
    )
    
    if success:
        value = f"{discount_info['value']}{'٪' if discount_info['type'] == 'percent' else ' تومان'}"
        message = (
            "✅ <b>کد تخفیف با موفقیت ایجاد شد</b>\n\n"
            f"🏷️ کد: <code>{discount_info['code']}</code>\n"
            f"📊 مقدار تخفیف: {value}\n"
            f"📅 تاریخ انقضا: {discount_info['expiry_date']}\n"
            f"💬 توضیحات: {discount_info['description']}"
        )
    else:
        message = f"❌ خطا در ایجاد کد تخفیف:\n{result}"
    
    # Clear user data
    if 'new_discount' in context.user_data:
        del context.user_data['new_discount']
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی تخفیف‌ها", callback_data="admin_discount_codes")]]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    return SELECTING_DISCOUNT_ACTION

async def cancel_add_discount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel adding a new discount code."""
    query = update.callback_query
    await query.answer()
    
    # Clear user data
    if 'new_discount' in context.user_data:
        del context.user_data['new_discount']
    
    # Return to discount menu
    return await discount_menu(update, context)

# Create discount management conversation handler
discount_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(discount_menu, pattern="^admin_discount_codes$")],
    states={
        SELECTING_DISCOUNT_ACTION: [
            CallbackQueryHandler(add_discount_start, pattern="^add_discount$"),
            CallbackQueryHandler(discount_menu, pattern="^refresh_discounts$"),
            CallbackQueryHandler(cancel_add_discount, pattern="^admin_back_to_menu$")
        ],
        ADDING_DISCOUNT_CODE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_discount_code),
            CallbackQueryHandler(cancel_add_discount, pattern="^cancel_add_discount$")
        ],
        ADDING_DISCOUNT_TYPE: [
            CallbackQueryHandler(add_discount_type, pattern="^discount_type_"),
            CallbackQueryHandler(cancel_add_discount, pattern="^cancel_add_discount$")
        ],
        ADDING_DISCOUNT_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_discount_value),
            CallbackQueryHandler(cancel_add_discount, pattern="^cancel_add_discount$")
        ],
        ADDING_DISCOUNT_EXPIRY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_discount_expiry),
            CallbackQueryHandler(cancel_add_discount, pattern="^cancel_add_discount$")
        ],
        ADDING_DISCOUNT_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_discount_description),
            CallbackQueryHandler(cancel_add_discount, pattern="^cancel_add_discount$")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_add_discount)]
) 