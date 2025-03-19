"""
V2Ray account management handler for the Telegram bot.

This module implements handlers for managing V2Ray accounts including:
- Account creation
- Account renewal
- Traffic monitoring
- Account configuration
"""

import logging
import uuid
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
from telegram.constants import ParseMode

from core.utils.i18n import get_text
from core.utils.formatting import format_number, format_date
from models import User, VPNAccount, SubscriptionPlan, Server
from services import AccountService, PaymentService
from core.utils.helpers import require_auth
from bot.constants import (
    SELECTING_ACTION,
    ACCOUNT_CREATED,
    ACCOUNTS_CB,
    VIEW_ACCOUNTS,
    CREATE_ACCOUNT,
    VIEW_DETAILS,
    CONFIRM_PURCHASE,
    RENEW_ACCOUNT,
    CONFIRM_RENEW,
    BACK_CB,
    END,
    SELECTING_FEATURE,
)
from .start import back_to_main, start_command

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECTING_ACTION,
    SELECTING_PLAN,
    CONFIRMING_PURCHASE,
    PROCESSING_PAYMENT,
) = range(4)

# Callback data patterns
ACCOUNTS_CB = "accounts"
CREATE_ACCOUNT = f"{ACCOUNTS_CB}_create"
VIEW_ACCOUNTS = f"{ACCOUNTS_CB}_view"
RENEW_ACCOUNT = f"{ACCOUNTS_CB}_renew"
VIEW_DETAILS = f"{ACCOUNTS_CB}_details"
CONFIRM_PURCHASE = f"{ACCOUNTS_CB}_confirm"
CANCEL_PURCHASE = f"{ACCOUNTS_CB}_cancel"

# Get plans from database
def get_plans() -> Dict[str, Dict[str, Any]]:
    """Get subscription plans from database."""
    plans_dict = {}
    plans = SubscriptionPlan.get_active()
    
    for plan in plans:
        plans_dict[str(plan.id)] = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "days": plan.duration_days,
            "gb": plan.traffic_gb,
            "price": plan.price,
            "features": plan.description.split("\n") if plan.description else []
        }
    
    # If no plans in database, use default plans
    if not plans_dict:
        plans_dict = {
            "1": {
                "id": 1,
                "name": "اشتراک یک ماهه",
                "description": "اشتراک پایه یک ماهه با ترافیک نامحدود",
                "days": 30,
                "gb": 0,  # Unlimited
                "price": 175000,
                "features": ["ترافیک نامحدود", "سرعت بالا", "امنیت کامل", "پشتیبانی 24/7"]
            },
            "2": {
                "id": 2,
                "name": "اشتراک سه ماهه",
                "description": "اشتراک سه ماهه با ترافیک نامحدود و تخفیف ویژه",
                "days": 90,
                "gb": 0,  # Unlimited
                "price": 450000,
                "features": ["ترافیک نامحدود", "سرعت بالا", "امنیت کامل", "پشتیبانی 24/7", "تخفیف 15%"]
            },
            "3": {
                "id": 3,
                "name": "اشتراک شش ماهه",
                "description": "اشتراک شش ماهه با ترافیک نامحدود و تخفیف ویژه",
                "days": 180,
                "gb": 0,  # Unlimited
                "price": 850000,
                "features": ["ترافیک نامحدود", "سرعت بالا", "امنیت کامل", "پشتیبانی 24/7", "تخفیف 20%"]
            }
        }
    
    return plans_dict

# Get plans
PLANS = get_plans()

@require_auth
async def accounts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the accounts menu."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Get language preference
    language_code = context.user_data.get("language", "en")
    
    # Get user accounts
    accounts = VPNAccount.get_by_user_id(user_id)
    
    # Check if user has accounts
    has_accounts = bool(accounts)
    
    # Get available servers for account creation
    servers = Server.get_active_servers()
    can_create = bool(servers)
    
    # Create menu message
    if has_accounts:
        menu_text = get_text("accounts_menu_with_accounts", language_code).format(
            count=len(accounts)
        )
    else:
        menu_text = get_text("accounts_menu_no_accounts", language_code)
    
    # Build keyboard
    keyboard = []
    
    # View accounts button
    if has_accounts:
        keyboard.append([
            InlineKeyboardButton(
                f"📋 {get_text('view_accounts', language_code)}",
                callback_data=VIEW_ACCOUNTS
            )
        ])
    
    # Create account button
    create_text = get_text("create_account", language_code)
    if not can_create:
        create_text += f" ({get_text('not_available', language_code)})"
        
    keyboard.append([
        InlineKeyboardButton(
            f"➕ {create_text}",
            callback_data=CREATE_ACCOUNT if can_create else "none"
        )
    ])
    
    # QR scanner button (for account configuration)
    keyboard.append([
        InlineKeyboardButton(
            f"📱 {get_text('scan_qr', language_code)}",
            callback_data=f"{ACCOUNTS_CB}_scan_qr"
        )
    ])
    
    # Add service transfer button
    if has_accounts:
        keyboard.append([
            InlineKeyboardButton(
                f"🔄 {get_text('transfer_service', language_code)}",
                callback_data=f"{ACCOUNTS_CB}_transfer"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_menu", language_code),
            callback_data="back_to_main"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    if query:
        await query.edit_message_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return SELECTING_ACTION

@require_auth
async def view_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display user's accounts."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Get language preference
    language_code = context.user_data.get("language", "en")
    
    # Get user accounts
    accounts = VPNAccount.get_by_user_id(user_id)
    
    if not accounts:
        # No accounts found, show message
        await query.edit_message_text(
            get_text("no_accounts", language_code),
            reply_markup=InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                        f"➕ {get_text('create_account', language_code)}",
                callback_data=CREATE_ACCOUNT
            )
        ],
        [
            InlineKeyboardButton(
                        get_text("back", language_code),
                        callback_data=ACCOUNTS_CB
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_ACTION
    
    # Create message with accounts list
    message = get_text("your_accounts", language_code) + "\n\n"
    
    # Create keyboard
    keyboard = []
    
    # Add account buttons with status indicators
    for i, account in enumerate(accounts):
        # Get status emoji
        status_emoji = "✅" if account.is_active else "⛔"
        
        # Get expiry days left
        days_left = account.days_left()
        traffic_percent = account.get_usage_percent()
        
        # Format button text with key info
        button_text = f"{status_emoji} {account.name} | {days_left}d | {traffic_percent}%"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{VIEW_DETAILS}:{account.id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back", language_code),
            callback_data=ACCOUNTS_CB
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_ACTION

@require_auth
async def view_account_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display details for a specific account."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Get language preference
    language_code = context.user_data.get("language", "en")
    
    # Get account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Get account
    account = VPNAccount.get_by_id(account_id)
    
    if not account or account.user_id != user_id:
        # Account not found or doesn't belong to user
        await query.edit_message_text(
            get_text("account_not_found", language_code),
            reply_markup=InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                        get_text("back", language_code),
                        callback_data=VIEW_ACCOUNTS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_ACTION
    
    # Store account_id in context for future use
    context.user_data["selected_account_id"] = account_id
    
    # Create message with account details
    message = get_text("account_details", language_code) + "\n\n"
    
    # Get key account information
    name = account.name
    status = get_text("active", language_code) if account.is_active else get_text("disabled", language_code)
    expiry_date = format_date(account.expiry_date.isoformat(), language_code)
    days_left = account.days_left()
    
    # Traffic information
    used_traffic = format_number(account.used_traffic_gb, language_code)
    total_traffic = format_number(account.total_traffic_gb, language_code)
    usage_percent = account.get_usage_percent()
    
    # Server information
    server_name = account.server.name if account.server else get_text("unknown", language_code)
    
    # Add account info to message
    message += f"*{get_text('account_id', language_code)}:* `{account.id}`\n"
    message += f"*{get_text('account_name', language_code)}:* `{name}`\n"
    message += f"*{get_text('account_status', language_code)}:* `{status}`\n"
    message += f"*{get_text('account_expiry', language_code)}:* `{expiry_date} ({days_left} {get_text('days', language_code)})`\n"
    message += f"*{get_text('account_traffic', language_code)}:* `{used_traffic}/{total_traffic} GB ({usage_percent}%)`\n"
    message += f"*{get_text('account_server', language_code)}:* `{server_name}`\n\n"
    
    # Add usage bar
    bar_length = 10
    filled_blocks = int(usage_percent / 100 * bar_length)
    empty_blocks = bar_length - filled_blocks
    
    usage_bar = "▓" * filled_blocks + "░" * empty_blocks
    message += f"*{get_text('traffic_usage', language_code)}:* `{usage_bar}` {usage_percent}%\n\n"
    
    # Create keyboard with actions
    keyboard = []
    
    # Get account info and configuration button
    keyboard.append([
        InlineKeyboardButton(
            f"📲 {get_text('get_config', language_code)}",
            callback_data=f"{ACCOUNTS_CB}_config:{account_id}"
        )
    ])
    
    # Add renewal button
    if days_left < 10:
        # Highlight renewal for accounts close to expiry
        keyboard.append([
            InlineKeyboardButton(
                f"🔄 {get_text('renew_account', language_code)} ⚠️",
                callback_data=f"{RENEW_ACCOUNT}:{account_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                f"🔄 {get_text('renew_account', language_code)}",
                callback_data=f"{RENEW_ACCOUNT}:{account_id}"
            )
        ])
    
    # Add add traffic button if usage is high
    if usage_percent > 70:
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {get_text('add_traffic', language_code)} ⚠️",
                callback_data=f"{ACCOUNTS_CB}_add_traffic:{account_id}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {get_text('add_traffic', language_code)}",
                callback_data=f"{ACCOUNTS_CB}_add_traffic:{account_id}"
            )
        ])
    
    # Add change server button
    keyboard.append([
        InlineKeyboardButton(
            f"🌐 {get_text('change_server', language_code)}",
            callback_data=f"{ACCOUNTS_CB}_change_server:{account_id}"
        )
    ])
    
    # Add back and delete buttons
    keyboard.append([
        InlineKeyboardButton(
            get_text("back", language_code),
            callback_data=VIEW_ACCOUNTS
        ),
        InlineKeyboardButton(
            f"🗑️ {get_text('delete_account', language_code)}",
            callback_data=f"{ACCOUNTS_CB}_delete:{account_id}"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_ACTION

@require_auth
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle account creation - show available plans."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Check if user has wallet balance for any plan
    user = User.get_by_id(user_id)
    wallet_balance = user.balance if user else 0
    
    # Create message with available plans
    message = get_text("available_plans", language_code) + "\n\n"
    
    # Add plans to message and keyboard
    keyboard = []
    
    for plan_id, plan in PLANS.items():
        plan_name = plan["name"]
        plan_days = plan["days"]
        plan_gb = plan["gb"]
        plan_price = plan["price"]
        
        # Format plan details
        if plan_gb == 0:
            plan_gb_text = get_text("unlimited_traffic", language_code)
        else:
            plan_gb_text = f"{plan_gb} GB"
        
        message += f"*{plan_name}*\n"
        message += f"📆 {plan_days} " + get_text("days", language_code) + "\n"
        message += f"📊 {plan_gb_text}\n"
        message += f"💰 {format_number(plan_price, language_code)} " + get_text("currency", language_code) + "\n\n"
        
        # Check if user can afford this plan
        can_afford = wallet_balance >= plan_price
        button_text = f"{plan_name} ({format_number(plan_price, language_code)} " + get_text("currency", language_code) + ")"
        
        # Add to keyboard if affordable or not
        if can_afford:
            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"{ACCOUNTS_CB}_plan:{plan_id}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    button_text + " ❌",
                    callback_data=f"{ACCOUNTS_CB}_plan:insufficient:{plan_id}"
                )
            ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_accounts", language_code),
            callback_data=ACCOUNTS_CB
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PLAN

@require_auth
async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm account purchase."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get selected plan from callback data
    callback_data = query.data
    plan_id = callback_data.split(":")[-1]
    
    # Check if this is the insufficient funds callback
    if "insufficient" in callback_data:
        # Show payment options
        plan = PLANS.get(plan_id)
        plan_price = plan["price"]
        user = User.get_by_id(user_id)
        wallet_balance = user.balance if user else 0
        
        missing_amount = plan_price - wallet_balance
        
        # Message about insufficient funds
        message = get_text("insufficient_funds", language_code).format(
            balance=format_number(wallet_balance, language_code),
            price=format_number(plan_price, language_code),
            missing=format_number(missing_amount, language_code)
        )
        
        # Keyboard for adding funds
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("add_funds", language_code),
                    callback_data="payments"
                )
            ],
            [
                InlineKeyboardButton(
                    get_text("back_to_plans", language_code),
                    callback_data=CREATE_ACCOUNT
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECTING_PLAN
    
    # Get plan details
    plan = PLANS.get(plan_id)
    if not plan:
        # Invalid plan
        await query.edit_message_text(
            text=get_text("invalid_plan", language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Store selected plan in context
    context.user_data["selected_plan"] = plan_id
    
    # Confirm purchase
    message = get_text("confirm_purchase", language_code).format(
        plan_name=plan["name"],
        days=plan["days"],
        gb=plan["gb"] if plan["gb"] > 0 else get_text("unlimited", language_code),
        price=format_number(plan["price"], language_code)
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("confirm", language_code),
                callback_data=CONFIRM_PURCHASE
            ),
            InlineKeyboardButton(
                get_text("cancel", language_code),
                callback_data=CANCEL_PURCHASE
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return CONFIRMING_PURCHASE

@require_auth
async def process_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process account purchase."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get selected plan
    plan_id = context.user_data.get("selected_plan")
    if not plan_id or plan_id not in PLANS:
        await query.edit_message_text(
            text=get_text("invalid_plan", language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    plan = PLANS[plan_id]
    
    # Verify user has sufficient balance
    user = User.get_by_id(user_id)
    wallet_balance = user.balance if user else 0
    
    if wallet_balance < plan["price"]:
        # Insufficient funds
        message = get_text("insufficient_funds", language_code).format(
            balance=format_number(wallet_balance, language_code),
            price=format_number(plan["price"], language_code),
            missing=format_number(plan["price"] - wallet_balance, language_code)
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("add_funds", language_code),
                    callback_data="payments"
                )
            ],
            [
                InlineKeyboardButton(
                    get_text("back_to_accounts", language_code),
                    callback_data=ACCOUNTS_CB
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECTING_PLAN
    
    # Process payment
    payment_result = PaymentService.process_wallet_payment(
        user_id=user_id,
        amount=plan["price"],
        description=f"Purchase of {plan['name']} plan"
    )
    
    if not payment_result.get("success"):
        # Payment failed
        await query.edit_message_text(
            text=get_text("payment_failed", language_code) + f"\n{payment_result.get('error')}",
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Create account
    account = AccountService.create_account(
        user_id=user_id,
        plan_id=plan_id,
        server_id=None  # Use best server
    )
    
    if not account:
        # Account creation failed
        await query.edit_message_text(
            text=get_text("account_creation_error", language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Show account details to user
    expiry_date = account.expiry_date
    traffic_limit = account.traffic_limit
    
    if traffic_limit == 0:
        traffic_text = get_text("unlimited", language_code)
    else:
        traffic_limit_gb = traffic_limit / (1024 * 1024 * 1024)  # Convert bytes to GB
        traffic_text = f"{traffic_limit_gb:.2f} GB"
    
    message = get_text("account_created", language_code).format(
        plan_name=plan["name"],
        expiry_date=format_date(expiry_date.isoformat(), language_code),
        traffic=traffic_text
    )
    
    # Get account config
    config_result = AccountService.get_account_config(account.id)
    
    # Create QR code if a configuration URL is available
    if config_result.get("success"):
        message += "\n\n" + get_text("account_config_info", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("view_accounts", language_code),
                callback_data=VIEW_ACCOUNTS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_accounts", language_code),
                callback_data=ACCOUNTS_CB
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # If there's a configuration URL, send it as a separate message with QR code
    if config_result.get("success"):
        config = config_result.get("config", {})
        qrcode_url = config_result.get("qrcode")
        
        if qrcode_url:
            # Send QR code
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=qrcode_url,
                caption=get_text("account_config_url", language_code).format(url=config.get("subscription_url", "")),
                parse_mode=ParseMode.MARKDOWN
            )
        
    return ACCOUNT_CREATED

@require_auth
async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel account purchase."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Clear selected plan
    if "selected_plan" in context.user_data:
        del context.user_data["selected_plan"]
    
    # Return to accounts menu
    return await accounts_menu(update, context)

# Register handlers
def get_accounts_handler():
    """Get accounts conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(accounts_menu, pattern=f"^{ACCOUNTS_CB}$"),
            CommandHandler("accounts", accounts_menu)
        ],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(view_accounts, pattern=f"^{VIEW_ACCOUNTS}$"),
                CallbackQueryHandler(create_account, pattern=f"^{CREATE_ACCOUNT}$"),
                CallbackQueryHandler(view_account_details, pattern=f"^{VIEW_DETAILS}:"),
                CallbackQueryHandler(back_to_main, pattern=f"^{BACK_CB}$"),
            ],
            SELECTING_PLAN: [
                CallbackQueryHandler(confirm_purchase, pattern=f"^{ACCOUNTS_CB}_plan:"),
                CallbackQueryHandler(accounts_menu, pattern=f"^{ACCOUNTS_CB}$"),
            ],
            CONFIRMING_PURCHASE: [
                CallbackQueryHandler(process_purchase, pattern=f"^{CONFIRM_PURCHASE}$"),
                CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
            ],
            ACCOUNT_CREATED: [
                CallbackQueryHandler(view_accounts, pattern=f"^{VIEW_ACCOUNTS}$"),
                CallbackQueryHandler(accounts_menu, pattern=f"^{ACCOUNTS_CB}$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(back_to_main, pattern=f"^{BACK_CB}$"),
        ],
        name="accounts",
        persistent=False,
    ) 