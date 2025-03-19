"""
MoonVPN Telegram Bot - Buy Handler Implementation.

This module provides handlers for purchasing VPN subscriptions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from models.user import User
from core.database import get_subscription_plans, get_active_servers
from core.utils.formatting import format_number, format_currency
from core.utils.i18n import get_text
from core.utils.formatting import allowed_group_filter, maintenance_mode_check

# States
SELECT_PACKAGE, SELECT_SERVER, CONFIRM_PURCHASE, PROCESS_PAYMENT = range(4)

# Callback patterns
PATTERN_BUY = "buy"
PATTERN_PACKAGE = "package_"
PATTERN_SERVER = "server_"
PATTERN_CONFIRM = "confirm_purchase"
PATTERN_CANCEL = "cancel_purchase"
PATTERN_PAYMENT = "payment_"
PATTERN_BACK = "back_to_"

logger = logging.getLogger(__name__)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /buy command.
    
    This command starts the purchase flow.
    """
    return await buy_handler(update, context)

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the buy button callback.
    
    This function displays available subscription packages.
    """
    user = update.effective_user
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    # Get subscription plans from database
    plans = get_subscription_plans()
    
    if not plans:
        # No plans available
        text = (
            "⚠️ <b>در حال حاضر هیچ پکیجی برای خرید موجود نیست.</b>\n\n"
            "لطفاً بعداً مراجعه کنید یا با پشتیبانی تماس بگیرید."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        return ConversationHandler.END
    
    # Create a beautiful message with package options
    text = (
        "🛒 <b>خرید اشتراک VPN</b>\n\n"
        "لطفاً یکی از پکیج‌های زیر را انتخاب کنید:\n\n"
    )
    
    # Create keyboard with package options
    keyboard = []
    
    # Group packages by duration for better UI
    durations = {}
    for plan in plans:
        duration = plan.get('duration_days', 0)
        if duration not in durations:
            durations[duration] = []
        durations[duration].append(plan)
    
    # Add packages to keyboard grouped by duration
    for duration, duration_plans in sorted(durations.items()):
        # Add a header for this duration group
        if duration == 30:
            text += f"📅 <b>پکیج‌های یک ماهه:</b>\n"
        elif duration == 90:
            text += f"📅 <b>پکیج‌های سه ماهه:</b>\n"
        elif duration == 180:
            text += f"📅 <b>پکیج‌های شش ماهه:</b>\n"
        elif duration == 365:
            text += f"📅 <b>پکیج‌های یک ساله:</b>\n"
        else:
            text += f"📅 <b>پکیج‌های {duration} روزه:</b>\n"
        
        # Add plans for this duration
        for plan in sorted(duration_plans, key=lambda x: x.get('price', 0)):
            plan_id = plan.get('id')
            name = plan.get('name', 'بدون نام')
            price = plan.get('price', 0)
            traffic = plan.get('traffic_gb', 0)
            
            # Add plan details to text
            text += f"• <b>{name}</b>: {format_number(traffic)} گیگابایت - {format_currency(price)}\n"
            
            # Add button for this plan
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 {name} - {format_currency(price)}",
                    callback_data=f"{PATTERN_PACKAGE}{plan_id}"
                )
            ])
        
        # Add a separator between duration groups
        text += "\n"
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SELECT_PACKAGE

async def select_package_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle package selection.
    
    This function displays available servers for the selected package.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract package ID from callback data
    package_id = int(query.data.replace(PATTERN_PACKAGE, ""))
    
    # Store selected package ID in context
    context.user_data['selected_package_id'] = package_id
    
    # Get package details
    plans = get_subscription_plans()
    selected_package = next((plan for plan in plans if plan.get('id') == package_id), None)
    
    if not selected_package:
        # Package not found
        await query.edit_message_text(
            text="⚠️ پکیج انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست پکیج‌ها", callback_data=PATTERN_BUY)
            ]])
        )
        return SELECT_PACKAGE
    
    # Store selected package details in context
    context.user_data['selected_package'] = selected_package
    
    # Get active servers
    servers = get_active_servers()
    
    if not servers:
        # No servers available
        await query.edit_message_text(
            text="⚠️ در حال حاضر هیچ سروری در دسترس نیست. لطفاً بعداً مراجعه کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست پکیج‌ها", callback_data=PATTERN_BUY)
            ]])
        )
        return SELECT_PACKAGE
    
    # Create a beautiful message with server options
    package_name = selected_package.get('name', 'بدون نام')
    package_price = selected_package.get('price', 0)
    package_traffic = selected_package.get('traffic_gb', 0)
    package_duration = selected_package.get('duration_days', 30)
    
    text = (
        f"🌍 <b>انتخاب سرور برای پکیج {package_name}</b>\n\n"
        f"<b>جزئیات پکیج:</b>\n"
        f"• ترافیک: {format_number(package_traffic)} گیگابایت\n"
        f"• مدت زمان: {format_number(package_duration)} روز\n"
        f"• قیمت: {format_currency(package_price)}\n\n"
        f"لطفاً یکی از سرورهای زیر را انتخاب کنید:\n\n"
    )
    
    # Create keyboard with server options
    keyboard = []
    
    # Group servers by location for better UI
    locations = {}
    for server in servers:
        location = server.get('location', 'نامشخص')
        if location not in locations:
            locations[location] = []
        locations[location].append(server)
    
    # Add servers to keyboard grouped by location
    for location, location_servers in sorted(locations.items()):
        # Add a header for this location group
        text += f"🌐 <b>سرورهای {location}:</b>\n"
        
        # Add servers for this location
        for server in location_servers:
            server_id = server.get('id')
            name = server.get('name', 'بدون نام')
            
            # Add server details to text
            text += f"• {name}\n"
            
            # Add button for this server
            keyboard.append([
                InlineKeyboardButton(
                    f"🖥️ {name} ({location})",
                    callback_data=f"{PATTERN_SERVER}{server_id}"
                )
            ])
        
        # Add a separator between location groups
        text += "\n"
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به لیست پکیج‌ها", callback_data=PATTERN_BUY)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return SELECT_SERVER

async def select_server_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle server selection.
    
    This function displays a confirmation message for the selected package and server.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract server ID from callback data
    server_id = int(query.data.replace(PATTERN_SERVER, ""))
    
    # Store selected server ID in context
    context.user_data['selected_server_id'] = server_id
    
    # Get server details
    servers = get_active_servers()
    selected_server = next((server for server in servers if server.get('id') == server_id), None)
    
    if not selected_server:
        # Server not found
        await query.edit_message_text(
            text="⚠️ سرور انتخاب شده یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به لیست سرورها", callback_data=f"{PATTERN_PACKAGE}{context.user_data.get('selected_package_id')}")
            ]])
        )
        return SELECT_SERVER
    
    # Store selected server details in context
    context.user_data['selected_server'] = selected_server
    
    # Get package details
    selected_package = context.user_data.get('selected_package', {})
    
    # Create a beautiful confirmation message
    package_name = selected_package.get('name', 'بدون نام')
    package_price = selected_package.get('price', 0)
    package_traffic = selected_package.get('traffic_gb', 0)
    package_duration = selected_package.get('duration_days', 30)
    
    server_name = selected_server.get('name', 'بدون نام')
    server_location = selected_server.get('location', 'نامشخص')
    
    # Calculate expiry date
    expiry_date = datetime.now() + timedelta(days=package_duration)
    expiry_date_str = expiry_date.strftime("%Y/%m/%d")
    
    text = (
        f"🔍 <b>تأیید خرید</b>\n\n"
        f"لطفاً جزئیات خرید خود را بررسی و تأیید کنید:\n\n"
        f"<b>جزئیات پکیج:</b>\n"
        f"• نام پکیج: {package_name}\n"
        f"• ترافیک: {format_number(package_traffic)} گیگابایت\n"
        f"• مدت زمان: {format_number(package_duration)} روز\n"
        f"• تاریخ انقضا: {expiry_date_str}\n\n"
        f"<b>جزئیات سرور:</b>\n"
        f"• نام سرور: {server_name}\n"
        f"• موقعیت: {server_location}\n\n"
        f"<b>قیمت نهایی: {format_currency(package_price)}</b>\n\n"
        f"آیا مایل به ادامه خرید هستید؟"
    )
    
    # Create keyboard with confirmation options
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید و پرداخت", callback_data=PATTERN_CONFIRM),
            InlineKeyboardButton("❌ انصراف", callback_data=PATTERN_CANCEL)
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به انتخاب سرور", callback_data=f"{PATTERN_PACKAGE}{context.user_data.get('selected_package_id')}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return CONFIRM_PURCHASE

async def confirm_purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle purchase confirmation.
    
    This function displays payment options for the confirmed purchase.
    """
    query = update.callback_query
    await query.answer()
    
    # Get package and server details from context
    selected_package = context.user_data.get('selected_package', {})
    selected_server = context.user_data.get('selected_server', {})
    
    package_name = selected_package.get('name', 'بدون نام')
    package_price = selected_package.get('price', 0)
    
    # Create a beautiful payment message
    text = (
        f"💰 <b>پرداخت</b>\n\n"
        f"شما در حال خرید پکیج <b>{package_name}</b> به مبلغ <b>{format_currency(package_price)}</b> هستید.\n\n"
        f"لطفاً روش پرداخت خود را انتخاب کنید:"
    )
    
    # Create keyboard with payment options
    keyboard = [
        [
            InlineKeyboardButton("💳 کارت به کارت", callback_data=f"{PATTERN_PAYMENT}card"),
            InlineKeyboardButton("💸 درگاه پرداخت", callback_data=f"{PATTERN_PAYMENT}gateway")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به تأیید خرید", callback_data=f"{PATTERN_SERVER}{context.user_data.get('selected_server_id')}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    return PROCESS_PAYMENT

async def process_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle payment processing.
    
    This function processes the selected payment method.
    """
    query = update.callback_query
    await query.answer()
    
    # Extract payment method from callback data
    payment_method = query.data.replace(PATTERN_PAYMENT, "")
    
    # Store payment method in context
    context.user_data['payment_method'] = payment_method
    
    # Get package details from context
    selected_package = context.user_data.get('selected_package', {})
    package_price = selected_package.get('price', 0)
    
    if payment_method == "card":
        # Card to card payment
        text = (
            f"💳 <b>پرداخت کارت به کارت</b>\n\n"
            f"لطفاً مبلغ <b>{format_currency(package_price)}</b> را به شماره کارت زیر واریز کنید:\n\n"
            f"<code>6037-9979-5289-7485</code>\n"
            f"به نام: <b>محمد محمدی</b>\n\n"
            f"پس از واریز، تصویر رسید پرداخت را به پشتیبانی ارسال کنید یا شناسه پیگیری را وارد کنید.\n\n"
            f"شناسه سفارش شما: <code>ORD-{datetime.now().strftime('%Y%m%d')}-{update.effective_user.id}</code>"
        )
        
        # Create keyboard with support options
        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 ارسال به پشتیبانی", url="https://t.me/moonvpn_support")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت به انتخاب روش پرداخت", callback_data=PATTERN_CONFIRM)
            ],
            [
                InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        # End conversation
        return ConversationHandler.END
    
    elif payment_method == "gateway":
        # Payment gateway
        text = (
            f"💸 <b>پرداخت از طریق درگاه</b>\n\n"
            f"برای پرداخت مبلغ <b>{format_currency(package_price)}</b> از طریق درگاه پرداخت، روی دکمه زیر کلیک کنید.\n\n"
            f"شناسه سفارش شما: <code>ORD-{datetime.now().strftime('%Y%m%d')}-{update.effective_user.id}</code>"
        )
        
        # Create keyboard with payment link
        keyboard = [
            [
                InlineKeyboardButton("💰 پرداخت آنلاین", url=f"https://moonvpn.ir/pay?amount={package_price}&user_id={update.effective_user.id}")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت به انتخاب روش پرداخت", callback_data=PATTERN_CONFIRM)
            ],
            [
                InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        # End conversation
        return ConversationHandler.END
    
    else:
        # Invalid payment method
        await query.edit_message_text(
            text="⚠️ روش پرداخت نامعتبر است. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به انتخاب روش پرداخت", callback_data=PATTERN_CONFIRM)
            ]])
        )
        
        return PROCESS_PAYMENT

async def cancel_purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle purchase cancellation.
    
    This function cancels the purchase process.
    """
    query = update.callback_query
    await query.answer()
    
    # Clear purchase data from context
    if 'selected_package_id' in context.user_data:
        del context.user_data['selected_package_id']
    if 'selected_package' in context.user_data:
        del context.user_data['selected_package']
    if 'selected_server_id' in context.user_data:
        del context.user_data['selected_server_id']
    if 'selected_server' in context.user_data:
        del context.user_data['selected_server']
    
    # Send cancellation message
    await query.edit_message_text(
        text="❌ خرید لغو شد. می‌توانید از منوی اصلی گزینه دیگری را انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )
    
    return ConversationHandler.END

def get_buy_handlers() -> List[Any]:
    """Return all handlers related to the buy feature."""
    
    # Create conversation handler for buy flow
    buy_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("buy", buy_command),
            CallbackQueryHandler(buy_handler, pattern=f"^{PATTERN_BUY}$")
        ],
        states={
            SELECT_PACKAGE: [
                CallbackQueryHandler(select_package_handler, pattern=f"^{PATTERN_PACKAGE}\\d+$"),
                CallbackQueryHandler(buy_handler, pattern=f"^{PATTERN_BUY}$")
            ],
            SELECT_SERVER: [
                CallbackQueryHandler(select_server_handler, pattern=f"^{PATTERN_SERVER}\\d+$"),
                CallbackQueryHandler(select_package_handler, pattern=f"^{PATTERN_PACKAGE}\\d+$")
            ],
            CONFIRM_PURCHASE: [
                CallbackQueryHandler(confirm_purchase_handler, pattern=f"^{PATTERN_CONFIRM}$"),
                CallbackQueryHandler(cancel_purchase_handler, pattern=f"^{PATTERN_CANCEL}$"),
                CallbackQueryHandler(select_server_handler, pattern=f"^{PATTERN_SERVER}\\d+$")
            ],
            PROCESS_PAYMENT: [
                CallbackQueryHandler(process_payment_handler, pattern=f"^{PATTERN_PAYMENT}\\w+$"),
                CallbackQueryHandler(confirm_purchase_handler, pattern=f"^{PATTERN_CONFIRM}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_purchase_handler, pattern=f"^{PATTERN_CANCEL}$"),
            CommandHandler("cancel", cancel_purchase_handler)
        ],
        name="buy_conversation",
        persistent=False
    )
    
    return [buy_conv_handler] 