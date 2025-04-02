from typing import Dict, List, Optional, Union, Callable, Any
import re
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes
)

from api import api_client
from keyboards.admin_keyboards import get_admin_main_keyboard, get_admin_card_management_keyboard
from utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

# Define conversation states
(
    AWAITING_CARD_SELECTION,
    AWAITING_BANK_NAME,
    AWAITING_CARD_NUMBER,
    AWAITING_CARD_HOLDER,
    AWAITING_ACCOUNT_NUMBER,
    AWAITING_SHEBA_NUMBER,
    AWAITING_DESCRIPTION,
    AWAITING_PRIORITY,
    AWAITING_CONFIRMATION,
    AWAITING_TOGGLE_SELECTION,
    AWAITING_PRIORITY_SELECTION,
    AWAITING_PRIORITY_VALUE,
) = range(12)

# Define callback data patterns
CARD_CB_PATTERN = re.compile(r'^card_(\d+)$')
CONFIRM_ADD_CARD_PATTERN = re.compile(r'^confirm_add_card_(yes|no)$')
TOGGLE_CARD_PATTERN = re.compile(r'^toggle_card_(\d+)$')
SET_PRIORITY_PATTERN = re.compile(r'^set_priority_(\d+)$')
DELETE_CARD_PATTERN = re.compile(r'^delete_card_(\d+)$')
CONFIRM_DELETE_PATTERN = re.compile(r'^confirm_delete_(yes|no)_(\d+)$')

async def handle_admin_manage_cards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the admin_manage_cards callback and show the card management menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = get_admin_card_management_keyboard()
    await query.edit_message_text(
        text="🏦 مدیریت کارت‌های بانکی\n\n"
             "از منوی زیر گزینه‌ای را انتخاب کنید:",
        reply_markup=keyboard
    )
    return AWAITING_CARD_SELECTION

async def handle_admin_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the main admin menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = get_admin_main_keyboard()
    await query.edit_message_text(
        text="🔑 به پنل مدیریت خوش آمدید. لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=keyboard
    )
    return ConversationHandler.END

async def handle_admin_list_cards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the admin_list_cards callback and list all bank cards."""
    query = update.callback_query
    await query.answer()
    
    # Fetch bank cards from API
    cards = await api_client.get_bank_cards_for_payment()
    
    if not cards or len(cards) == 0:
        keyboard = get_admin_card_management_keyboard()
        await query.edit_message_text(
            text="❌ هیچ کارت بانکی یافت نشد.\n\n"
                 "برای اضافه کردن کارت جدید، از گزینه \"افزودن کارت جدید\" استفاده کنید.",
            reply_markup=keyboard
        )
        return AWAITING_CARD_SELECTION
    
    message_text = "📋 لیست کارت‌های بانکی:\n\n"
    
    keyboard = []
    
    for card in cards:
        # Format card details
        status = "✅ فعال" if card["is_active"] else "❌ غیرفعال"
        priority = f"🔢 اولویت: {card['priority']}"
        
        message_text += f"*{card['bank_name']}*\n"
        message_text += f"💳 شماره کارت: `{card['card_number'][-4:].rjust(16, '*')}`\n"
        message_text += f"👤 دارنده کارت: {card['card_holder_name']}\n"
        message_text += f"{status} | {priority}\n\n"
        
        # Add card to keyboard
        keyboard.append([
            InlineKeyboardButton(
                f"{card['bank_name']} - {card['card_number'][-4:]}",
                callback_data=f"card_{card['id']}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_cards")
    ])
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return AWAITING_CARD_SELECTION

async def handle_card_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selection of a specific card and show its details."""
    query = update.callback_query
    await query.answer()
    
    # Extract card ID from callback data
    match = CARD_CB_PATTERN.match(query.data)
    if not match:
        return AWAITING_CARD_SELECTION
    
    card_id = int(match.group(1))
    
    # Fetch card details from API
    card = await api_client.get_bank_card_details(card_id)
    
    if not card:
        await query.edit_message_text(
            text="❌ کارت بانکی یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_list_cards")
            ]])
        )
        return AWAITING_CARD_SELECTION
    
    # Format card details
    status = "✅ فعال" if card["is_active"] else "❌ غیرفعال"
    message_text = f"💳 *اطلاعات کارت بانکی*\n\n"
    message_text += f"🏦 بانک: *{card['bank_name']}*\n"
    message_text += f"💳 شماره کارت: `{card['card_number']}`\n"
    message_text += f"👤 دارنده کارت: {card['card_holder_name']}\n"
    
    if card.get("account_number"):
        message_text += f"🏦 شماره حساب: `{card['account_number']}`\n"
    
    if card.get("sheba_number"):
        message_text += f"🔢 شماره شبا: `{card['sheba_number']}`\n"
    
    message_text += f"🔢 اولویت: {card['priority']}\n"
    message_text += f"📊 وضعیت: {status}\n"
    
    if card.get("description"):
        message_text += f"📝 توضیحات: {card['description']}\n"
    
    # Add user and creator info if available
    if card.get("user_name"):
        message_text += f"👤 مالک: {card['user_name']}\n"
    
    if card.get("creator_name"):
        message_text += f"👤 ایجاد کننده: {card['creator_name']}\n"
    
    # Add timestamps
    if card.get("created_at"):
        created_at = datetime.fromisoformat(card["created_at"].replace("Z", "+00:00"))
        message_text += f"🕒 تاریخ ایجاد: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if card.get("updated_at"):
        updated_at = datetime.fromisoformat(card["updated_at"].replace("Z", "+00:00"))
        message_text += f"🕒 آخرین بروزرسانی: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # Create keyboard with actions
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 تغییر وضعیت فعال/غیرفعال", 
                callback_data=f"toggle_card_{card_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔢 تغییر اولویت", 
                callback_data=f"set_priority_{card_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ حذف کارت", 
                callback_data=f"delete_card_{card_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به لیست کارت‌ها", 
                callback_data="admin_list_cards"
            )
        ]
    ]
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return AWAITING_CARD_SELECTION

async def handle_toggle_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle the active status of a bank card."""
    query = update.callback_query
    await query.answer()
    
    # Extract card ID from callback data
    match = TOGGLE_CARD_PATTERN.match(query.data)
    if not match:
        return AWAITING_CARD_SELECTION
    
    card_id = int(match.group(1))
    
    # Toggle card status via API
    card = await api_client.toggle_bank_card_status(card_id)
    
    if not card:
        await query.edit_message_text(
            text="❌ خطا در تغییر وضعیت کارت.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"card_{card_id}")
            ]])
        )
        return AWAITING_CARD_SELECTION
    
    status = "فعال" if card["is_active"] else "غیرفعال"
    
    await query.edit_message_text(
        text=f"✅ وضعیت کارت با موفقیت به {status} تغییر کرد.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به جزئیات کارت", callback_data=f"card_{card_id}")
        ]])
    )
    
    return AWAITING_CARD_SELECTION

async def handle_set_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle setting priority for a bank card."""
    query = update.callback_query
    await query.answer()
    
    # Extract card ID from callback data
    match = SET_PRIORITY_PATTERN.match(query.data)
    if not match:
        return AWAITING_CARD_SELECTION
    
    card_id = int(match.group(1))
    context.user_data["priority_card_id"] = card_id
    
    await query.edit_message_text(
        text="🔢 لطفاً اولویت جدید کارت را وارد کنید (عدد صحیح بزرگتر یا مساوی 0):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data=f"card_{card_id}")
        ]])
    )
    
    return AWAITING_PRIORITY_VALUE

async def handle_priority_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the new priority value for a bank card."""
    message = update.message
    card_id = context.user_data.get("priority_card_id")
    
    if not card_id:
        await message.reply_text(
            "❌ خطا در پردازش درخواست. لطفاً مجدداً تلاش کنید."
        )
        return ConversationHandler.END
    
    # Validate priority value
    try:
        priority = int(message.text.strip())
        if priority < 0:
            raise ValueError("Priority must be greater than or equal to 0")
    except ValueError:
        await message.reply_text(
            "❌ لطفاً یک عدد صحیح بزرگتر یا مساوی 0 وارد کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"card_{card_id}")
            ]])
        )
        return AWAITING_PRIORITY_VALUE
    
    # Update card priority via API
    card = await api_client.update_bank_card_priority(card_id, priority)
    
    if not card:
        await message.reply_text(
            "❌ خطا در تغییر اولویت کارت.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"card_{card_id}")
            ]])
        )
        return AWAITING_CARD_SELECTION
    
    await message.reply_text(
        f"✅ اولویت کارت با موفقیت به {priority} تغییر کرد.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به جزئیات کارت", callback_data=f"card_{card_id}")
        ]])
    )
    
    # Clear user data
    context.user_data.pop("priority_card_id", None)
    
    return AWAITING_CARD_SELECTION

async def handle_delete_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle deleting a bank card."""
    query = update.callback_query
    await query.answer()
    
    # Extract card ID from callback data
    match = DELETE_CARD_PATTERN.match(query.data)
    if not match:
        return AWAITING_CARD_SELECTION
    
    card_id = int(match.group(1))
    
    await query.edit_message_text(
        text="⚠️ آیا از حذف این کارت بانکی اطمینان دارید؟\n"
             "این عمل قابل بازگشت نیست.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_delete_yes_{card_id}"),
                InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"confirm_delete_no_{card_id}")
            ]
        ])
    )
    
    return AWAITING_CARD_SELECTION

async def handle_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of bank card deletion."""
    query = update.callback_query
    await query.answer()
    
    # Extract confirmation and card ID from callback data
    match = CONFIRM_DELETE_PATTERN.match(query.data)
    if not match:
        return AWAITING_CARD_SELECTION
    
    confirm = match.group(1)
    card_id = int(match.group(2))
    
    if confirm == "no":
        # User cancelled deletion
        await query.edit_message_text(
            text="✅ حذف کارت لغو شد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات کارت", callback_data=f"card_{card_id}")
            ]])
        )
        return AWAITING_CARD_SELECTION
    
    # Delete card via API
    card = await api_client.delete_bank_card(card_id)
    
    if not card:
        await query.edit_message_text(
            text="❌ خطا در حذف کارت.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"card_{card_id}")
            ]])
        )
        return AWAITING_CARD_SELECTION
    
    await query.edit_message_text(
        text="✅ کارت بانکی با موفقیت حذف شد.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به لیست کارت‌ها", callback_data="admin_list_cards")
        ]])
    )
    
    return AWAITING_CARD_SELECTION

async def handle_admin_add_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the admin_add_card callback and start the add card flow."""
    query = update.callback_query
    await query.answer()
    
    # Clear any previous card data
    context.user_data.clear()
    
    await query.edit_message_text(
        text="➕ افزودن کارت بانکی جدید\n\n"
             "لطفاً نام بانک را وارد کنید (مثال: ملت، ملی، صادرات و...):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_BANK_NAME

async def handle_bank_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process bank name input for new card."""
    message = update.message
    bank_name = message.text.strip()
    
    if not bank_name:
        await message.reply_text(
            "❌ نام بانک نمی‌تواند خالی باشد. لطفاً مجدداً وارد کنید:"
        )
        return AWAITING_BANK_NAME
    
    # Store bank name in context
    context.user_data["bank_name"] = bank_name
    
    await message.reply_text(
        "💳 لطفاً شماره کارت را بدون فاصله یا خط تیره وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_CARD_NUMBER

async def handle_card_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process card number input for new card."""
    message = update.message
    card_number = message.text.strip().replace(" ", "").replace("-", "")
    
    # Validate card number
    if not card_number.isdigit() or not (16 <= len(card_number) <= 19):
        await message.reply_text(
            "❌ شماره کارت نامعتبر است. لطفاً یک شماره کارت 16 تا 19 رقمی وارد کنید:"
        )
        return AWAITING_CARD_NUMBER
    
    # Store card number in context
    context.user_data["card_number"] = card_number
    
    await message.reply_text(
        "👤 لطفاً نام و نام خانوادگی دارنده کارت را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_CARD_HOLDER

async def handle_card_holder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process card holder name input for new card."""
    message = update.message
    card_holder_name = message.text.strip()
    
    if not card_holder_name:
        await message.reply_text(
            "❌ نام دارنده کارت نمی‌تواند خالی باشد. لطفاً مجدداً وارد کنید:"
        )
        return AWAITING_CARD_HOLDER
    
    # Store card holder name in context
    context.user_data["card_holder_name"] = card_holder_name
    
    await message.reply_text(
        "🏦 لطفاً شماره حساب را وارد کنید (اختیاری، برای رد کردن این مرحله عدد 0 را وارد کنید):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_ACCOUNT_NUMBER

async def handle_account_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process account number input for new card."""
    message = update.message
    account_number = message.text.strip()
    
    # Check if user wants to skip
    if account_number == "0":
        account_number = None
    
    # Store account number in context
    context.user_data["account_number"] = account_number
    
    await message.reply_text(
        "🔢 لطفاً شماره شبا را با فرمت IR و 24 رقم وارد کنید "
        "(اختیاری، برای رد کردن این مرحله عدد 0 را وارد کنید):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_SHEBA_NUMBER

async def handle_sheba_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process SHEBA number input for new card."""
    message = update.message
    sheba_number = message.text.strip().replace(" ", "")
    
    # Check if user wants to skip
    if sheba_number == "0":
        sheba_number = None
    elif sheba_number:
        # Validate SHEBA format
        if not sheba_number.startswith("IR") or len(sheba_number) != 26:
            await message.reply_text(
                "❌ فرمت شماره شبا نامعتبر است. لطفاً یک شماره شبا با فرمت IR و 24 رقم وارد کنید "
                "(یا برای رد کردن عدد 0 را وارد کنید):"
            )
            return AWAITING_SHEBA_NUMBER
    
    # Store SHEBA number in context
    context.user_data["sheba_number"] = sheba_number
    
    await message.reply_text(
        "📝 لطفاً توضیحات کارت را وارد کنید "
        "(اختیاری، برای رد کردن این مرحله عدد 0 را وارد کنید):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_DESCRIPTION

async def handle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process description input for new card."""
    message = update.message
    description = message.text.strip()
    
    # Check if user wants to skip
    if description == "0":
        description = None
    
    # Store description in context
    context.user_data["description"] = description
    
    await message.reply_text(
        "🔢 لطفاً اولویت کارت را وارد کنید (عدد صحیح بزرگتر یا مساوی 0، پیش‌فرض: 0):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_cards")
        ]])
    )
    
    return AWAITING_PRIORITY

async def handle_priority_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process priority input for new card."""
    message = update.message
    priority_text = message.text.strip()
    
    # Validate priority
    try:
        priority = int(priority_text)
        if priority < 0:
            raise ValueError("Priority must be greater than or equal to 0")
    except ValueError:
        await message.reply_text(
            "❌ لطفاً یک عدد صحیح بزرگتر یا مساوی 0 وارد کنید:"
        )
        return AWAITING_PRIORITY
    
    # Store priority in context
    context.user_data["priority"] = priority
    
    # Show summary and confirmation
    card_data = context.user_data
    summary = "📋 *خلاصه اطلاعات کارت جدید:*\n\n"
    summary += f"🏦 بانک: *{card_data['bank_name']}*\n"
    summary += f"💳 شماره کارت: `{card_data['card_number']}`\n"
    summary += f"👤 دارنده کارت: {card_data['card_holder_name']}\n"
    
    if card_data.get("account_number"):
        summary += f"🏦 شماره حساب: `{card_data['account_number']}`\n"
    
    if card_data.get("sheba_number"):
        summary += f"🔢 شماره شبا: `{card_data['sheba_number']}`\n"
    
    if card_data.get("description"):
        summary += f"📝 توضیحات: {card_data['description']}\n"
    
    summary += f"🔢 اولویت: {card_data['priority']}\n\n"
    summary += "آیا از افزودن این کارت بانکی اطمینان دارید؟"
    
    await message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ بله، کارت اضافه شود", callback_data="confirm_add_card_yes"),
                InlineKeyboardButton("❌ خیر، انصراف", callback_data="confirm_add_card_no")
            ]
        ]),
        parse_mode="Markdown"
    )
    
    return AWAITING_CONFIRMATION

async def handle_confirm_add_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation for adding a new card."""
    query = update.callback_query
    await query.answer()
    
    # Extract confirmation from callback data
    match = CONFIRM_ADD_CARD_PATTERN.match(query.data)
    if not match:
        return AWAITING_CARD_SELECTION
    
    confirm = match.group(1)
    
    if confirm == "no":
        # User cancelled adding card
        await query.edit_message_text(
            text="❌ افزودن کارت لغو شد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به مدیریت کارت‌ها", callback_data="admin_manage_cards")
            ]])
        )
        # Clear user data
        context.user_data.clear()
        return AWAITING_CARD_SELECTION
    
    # Add card via API
    card_data = context.user_data
    card = await api_client.create_bank_card(
        bank_name=card_data["bank_name"],
        card_number=card_data["card_number"],
        card_holder_name=card_data["card_holder_name"],
        account_number=card_data.get("account_number"),
        sheba_number=card_data.get("sheba_number"),
        description=card_data.get("description"),
        # Pass user_id=None to use the admin's ID as default owner
    )
    
    if not card:
        await query.edit_message_text(
            text="❌ خطا در افزودن کارت.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_cards")
            ]])
        )
        return AWAITING_CARD_SELECTION
    
    await query.edit_message_text(
        text=f"✅ کارت بانکی جدید با موفقیت اضافه شد.\n\n"
             f"🏦 بانک: {card['bank_name']}\n"
             f"💳 شماره کارت: {card['card_number'][-4:].rjust(16, '*')}\n",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 مشاهده لیست کارت‌ها", callback_data="admin_list_cards")
            ],
            [
                InlineKeyboardButton("➕ افزودن کارت دیگر", callback_data="admin_add_card")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت به مدیریت کارت‌ها", callback_data="admin_manage_cards")
            ]
        ])
    )
    
    # Clear user data
    context.user_data.clear()
    
    return AWAITING_CARD_SELECTION

# Create conversation handler for card management
admin_card_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$")
    ],
    states={
        AWAITING_CARD_SELECTION: [
            CallbackQueryHandler(handle_admin_back_to_main, pattern="^admin_back_to_main$"),
            CallbackQueryHandler(handle_admin_list_cards, pattern="^admin_list_cards$"),
            CallbackQueryHandler(handle_admin_add_card, pattern="^admin_add_card$"),
            CallbackQueryHandler(handle_card_selection, pattern=CARD_CB_PATTERN),
            CallbackQueryHandler(handle_toggle_card, pattern=TOGGLE_CARD_PATTERN),
            CallbackQueryHandler(handle_set_priority, pattern=SET_PRIORITY_PATTERN),
            CallbackQueryHandler(handle_delete_card, pattern=DELETE_CARD_PATTERN),
            CallbackQueryHandler(handle_confirm_delete, pattern=CONFIRM_DELETE_PATTERN),
            CallbackQueryHandler(handle_confirm_add_card, pattern=CONFIRM_ADD_CARD_PATTERN),
        ],
        AWAITING_BANK_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bank_name_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_CARD_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_card_number_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_CARD_HOLDER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_card_holder_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_ACCOUNT_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account_number_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_SHEBA_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sheba_number_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_PRIORITY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_priority_input),
            CallbackQueryHandler(handle_admin_manage_cards, pattern="^admin_manage_cards$"),
        ],
        AWAITING_PRIORITY_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_priority_value),
            CallbackQueryHandler(callback=handle_card_selection, pattern=CARD_CB_PATTERN),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_admin_back_to_main, pattern="^admin_back_to_main$"),
    ],
    name="admin_card_management",
    persistent=False,
)

# Export handlers
__all__ = ["admin_card_handler"] 