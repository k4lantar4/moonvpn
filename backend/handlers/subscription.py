"""
Subscription management handler for the MoonVPN Telegram bot.

This module implements handlers for subscription-related operations including:
- Viewing available plans
- Selecting plans
- Managing subscriptions
- Renewal operations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from core.utils.i18n import get_text, format_number, format_date
from core.database import (
    get_user,
    get_subscription_plans,
    get_subscription_plan,
    get_server,
    get_servers,
    get_user_accounts,
)
from core.config import settings
from core.database import get_db
from core.models.account import Account
from core.models.subscription_plan import SubscriptionPlan
from core.models.server import Server
from core.utils.helpers import require_auth
from services.account_service import AccountService
from core.models.user import User
from core.models.vpn_account import VPNAccount
from core.models.transaction import Transaction
from core.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECTING_ACTION,
    SELECTING_PLAN,
    SELECTING_SERVER,
    CONFIRMING_PURCHASE,
    SELECTING_PAYMENT_METHOD,
    PROCESSING_PAYMENT,
    EXTENDING_ACCOUNT,
) = range(7)

# Callback data patterns
SUBSCRIPTION_PLANS = "subscription_plans"
SELECT_PLAN = f"{SUBSCRIPTION_PLANS}_select"
SELECT_SERVER = f"{SUBSCRIPTION_PLANS}_server"
CONFIRM_PURCHASE = f"{SUBSCRIPTION_PLANS}_confirm"
SELECT_PAYMENT = f"{SUBSCRIPTION_PLANS}_payment"
PROCESS_PURCHASE = f"{SUBSCRIPTION_PLANS}_process"
CANCEL_PURCHASE = f"{SUBSCRIPTION_PLANS}_cancel"
EXTEND_ACCOUNT = f"{SUBSCRIPTION_PLANS}_extend"

@require_auth
async def subscription_plans_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available subscription plans."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user's accounts
    accounts = get_user_accounts(user_id)
    has_accounts = bool(accounts)
    
    # Create message
    message = get_text("subscription_plans_header", language_code)
    
    # Get available plans
    plans = get_subscription_plans()
    
    if not plans:
        # No plans available
        message += "\n\n" + get_text("no_plans_available", language_code)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_menu", language_code),
                    callback_data="back_to_main"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    # Add plans to message
    message += "\n\n"
    
    for plan in plans:
        # Skip disabled plans
        if not plan.get("is_active", True):
            continue
        
        plan_id = plan.get("id")
        name = plan.get("name", "Unknown")
        description = plan.get("description", "")
        duration_days = plan.get("duration_days", 30)
        traffic_limit_gb = plan.get("traffic_limit_gb", 0)
        price = plan.get("price", 0)
        
        # Format plan information
        message += f"🔹 *{name}*\n"
        
        if description:
            message += f"   {description}\n"
            
        message += f"   ⏱️ {duration_days} {get_text('days', language_code)}\n"
        message += f"   📊 {traffic_limit_gb} GB\n"
        message += f"   💰 {format_number(price, language_code)} {get_text('currency', language_code)}\n\n"
    
    # Create keyboard with plan buttons
    keyboard = []
    
    for plan in plans:
        # Skip disabled plans
        if not plan.get("is_active", True):
            continue
        
        plan_id = plan.get("id")
        name = plan.get("name", "Unknown")
        price = plan.get("price", 0)
        
        # Format price for display
        price_formatted = format_number(price, language_code)
        
        keyboard.append([
            InlineKeyboardButton(
                f"{name} - {price_formatted} {get_text('currency', language_code)}",
                callback_data=f"{SELECT_PLAN}:{plan_id}"
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
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return SELECTING_PLAN

@require_auth
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract plan ID from callback data
    callback_data = query.data
    plan_id = int(callback_data.split(":")[-1])
    
    # Store plan ID in context
    context.user_data["selected_plan_id"] = plan_id
    
    # Get plan details
    plan = get_subscription_plan(plan_id)
    
    if not plan:
        # Plan not found
        await query.edit_message_text(
            get_text("plan_not_found", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Store plan details in context
    context.user_data["selected_plan"] = plan
    
    # Get available servers
    servers = get_servers()
    active_servers = [s for s in servers if s.get("is_active", True)]
    
    if not active_servers:
        # No servers available
        await query.edit_message_text(
            get_text("no_servers_available", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Create message with server selection
    plan_name = plan.get("name", "Unknown")
    duration_days = plan.get("duration_days", 30)
    traffic_limit_gb = plan.get("traffic_limit_gb", 0)
    price = plan.get("price", 0)
    
    # Format price for display
    price_formatted = format_number(price, language_code)
    
    message = get_text("select_server_header", language_code).format(
        plan_name=plan_name,
        duration=duration_days,
        traffic=traffic_limit_gb,
        price=price_formatted,
        currency=get_text("currency", language_code)
    )
    
    # Create keyboard with server buttons
    keyboard = []
    
    for server in active_servers:
        server_id = server.get("id")
        name = server.get("name", "Unknown")
        location = server.get("location", "")
        
        button_text = f"{name}"
        if location:
            button_text += f" ({location})"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{SELECT_SERVER}:{server_id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_plans", language_code),
            callback_data=SUBSCRIPTION_PLANS
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_SERVER

@require_auth
async def select_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle server selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract server ID from callback data
    callback_data = query.data
    server_id = int(callback_data.split(":")[-1])
    
    # Store server ID in context
    context.user_data["selected_server_id"] = server_id
    
    # Get plan and server details
    plan_id = context.user_data.get("selected_plan_id")
    plan = context.user_data.get("selected_plan") or get_subscription_plan(plan_id)
    server = get_server(server_id)
    
    if not plan or not server:
        # Plan or server not found
        await query.edit_message_text(
            get_text("selection_error", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Format plan and server details for confirmation
    plan_name = plan.get("name", "Unknown")
    duration_days = plan.get("duration_days", 30)
    traffic_limit_gb = plan.get("traffic_limit_gb", 0)
    price = plan.get("price", 0)
    server_name = server.get("name", "Unknown")
    server_location = server.get("location", "")
    
    # Calculate expiry date
    expiry_date = datetime.now() + timedelta(days=duration_days)
    expiry_formatted = format_date(expiry_date.isoformat(), language_code)
    
    # Format price for display
    price_formatted = format_number(price, language_code)
    
    # Create account name (will be used when creating the account)
    location_display = server_location or server_name
    account_name = f"{location_display} - {plan_name}"
    
    # Store account name in context
    context.user_data["account_name"] = account_name
    
    # Create confirmation message
    message = get_text("confirm_purchase_header", language_code).format(
        plan_name=plan_name,
        server_name=server_name,
        location=server_location,
        duration=duration_days,
        traffic=traffic_limit_gb,
        price=price_formatted,
        currency=get_text("currency", language_code),
        expiry=expiry_formatted
    )
    
    # Create keyboard with confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton(
                f"✅ {get_text('confirm_purchase', language_code)}",
                callback_data=CONFIRM_PURCHASE
            ),
            InlineKeyboardButton(
                f"❌ {get_text('cancel', language_code)}",
                callback_data=CANCEL_PURCHASE
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return CONFIRMING_PURCHASE

@require_auth
async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle purchase confirmation."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user's balance
    user = get_user(user_id)
    balance = user.get("balance", 0) if user else 0
    
    # Get plan details
    plan_id = context.user_data.get("selected_plan_id")
    plan = context.user_data.get("selected_plan") or get_subscription_plan(plan_id)
    
    if not plan:
        # Plan not found
        await query.edit_message_text(
            get_text("plan_not_found", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Get plan price
    price = plan.get("price", 0)
    
    # Check if user has enough balance
    if balance >= price:
        # User has enough balance, process purchase directly
        return await process_purchase_with_balance(update, context)
    
    # User doesn't have enough balance, show payment options
    price_formatted = format_number(price, language_code)
    balance_formatted = format_number(balance, language_code)
    remaining = price - balance
    remaining_formatted = format_number(remaining, language_code)
    
    message = get_text("insufficient_balance", language_code).format(
        balance=balance_formatted,
        price=price_formatted,
        remaining=remaining_formatted,
        currency=get_text("currency", language_code)
    )
    
    # Store required payment amount in context
    context.user_data["payment_amount"] = remaining
    
    # Create keyboard with payment options
    keyboard = [
        [
            InlineKeyboardButton(
                f"💳 {get_text('card_payment', language_code)}",
                callback_data=f"{SELECT_PAYMENT}_card"
            )
        ]
    ]
    
    # Add Zarinpal option if enabled
    if "zarinpal_enabled" in context.bot_data and context.bot_data["zarinpal_enabled"]:
        keyboard[0].append(
            InlineKeyboardButton(
                f"🛒 {get_text('zarinpal_payment', language_code)}",
                callback_data=f"{SELECT_PAYMENT}_zarinpal"
            )
        )
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton(
            f"❌ {get_text('cancel', language_code)}",
            callback_data=CANCEL_PURCHASE
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PAYMENT_METHOD

@require_auth
async def select_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract payment method from callback data
    callback_data = query.data
    payment_method = callback_data.split("_")[-1]
    
    # Store payment method in context
    context.user_data["payment_method"] = payment_method
    
    # Get payment amount
    amount = context.user_data.get("payment_amount", 0)
    
    # Create message based on payment method
    if payment_method == "card":
        # Get card details
        card_number = context.bot_data.get("card_number", "6037997599999999")
        card_holder = context.bot_data.get("card_holder", "Card Holder")
        bank_name = context.bot_data.get("bank_name", "Bank")
        
        # Format amount for display
        amount_formatted = format_number(amount, language_code)
        
        message = get_text("card_payment_instructions", language_code).format(
            amount=amount_formatted,
            currency=get_text("currency", language_code),
            card_number=card_number,
            card_holder=card_holder,
            bank_name=bank_name
        )
        
        # Add instructions to send receipt
        message += "\n\n" + get_text("send_receipt", language_code)
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    f"❌ {get_text('cancel', language_code)}",
                    callback_data=CANCEL_PURCHASE
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Wait for receipt
        return PROCESSING_PAYMENT
        
    elif payment_method == "zarinpal":
        # TODO: Implement Zarinpal payment
        # For now, show not implemented message
        
        message = get_text("zarinpal_not_implemented", language_code)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_plans", language_code),
                    callback_data=SUBSCRIPTION_PLANS
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECTING_PLAN
    
    # Unknown payment method
    await query.edit_message_text(
        get_text("error_general", language_code),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    get_text("back_to_plans", language_code),
                    callback_data=SUBSCRIPTION_PLANS
                )
            ]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PLAN

@require_auth
async def process_purchase_with_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process purchase using user's balance."""
    query = update.callback_query
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get plan and server details
    plan_id = context.user_data.get("selected_plan_id")
    server_id = context.user_data.get("selected_server_id")
    account_name = context.user_data.get("account_name")
    
    # Get plan and server
    plan = context.user_data.get("selected_plan") or get_subscription_plan(plan_id)
    server = get_server(server_id)
    
    if not plan or not server:
        # Plan or server not found
        await query.edit_message_text(
            get_text("selection_error", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Get plan details
    price = plan.get("price", 0)
    
    # Get user's balance
    user = get_user(user_id)
    balance = user.get("balance", 0) if user else 0
    
    # Check if user has enough balance
    if balance < price:
        # User doesn't have enough balance
        await query.edit_message_text(
            get_text("insufficient_balance_error", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Update user's balance
    new_balance = balance - price
    success = update_user(
        user_id=user_id,
        balance=new_balance
    )
    
    if not success:
        # Failed to update user's balance
        await query.edit_message_text(
            get_text("balance_update_error", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Create account
    try:
        # Initialize account service
        account_service = AccountService()
        
        # Get duration and traffic from plan
        duration_days = plan.get("duration_days", 30)
        traffic_limit_gb = plan.get("traffic_limit_gb", 0)
        
        # Generate email
        email = f"user{user_id}_{int(datetime.now().timestamp())}@moonvpn.com"
        
        # Create account
        account = await account_service.create_account(
            user_id=user_id,
            server_id=server_id,
            subscription_plan_id=plan_id,
            name=account_name,
            email=email,
            expiry_days=duration_days,
            traffic_limit_gb=traffic_limit_gb
        )
        
        if not account:
            # Failed to create account
            # Refund user's balance
            update_user(
                user_id=user_id,
                balance=balance
            )
            
            await query.edit_message_text(
                get_text("account_creation_error", language_code),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            get_text("back_to_plans", language_code),
                            callback_data=SUBSCRIPTION_PLANS
                        )
                    ]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            return SELECTING_PLAN
        
        # Create transaction record
        transaction_id = create_transaction(
            user_id=user_id,
            amount=price,
            payment_method="balance",
            description=f"Purchase of {account_name}",
            status="completed"
        )
        
        # Send success message
        message = get_text("purchase_success", language_code).format(
            plan_name=plan.get("name", "Unknown"),
            server_name=server.get("name", "Unknown"),
            account_id=account.id,
            expiry_date=format_date(account.expiry_date.isoformat(), language_code),
            traffic=traffic_limit_gb,
            new_balance=format_number(new_balance, language_code),
            currency=get_text("currency", language_code)
        )
        
        # Create keyboard with account actions
        keyboard = [
            [
                InlineKeyboardButton(
                    f"📋 {get_text('show_config', language_code)}",
                    callback_data=f"accounts_view:{account.id}"
                ),
                InlineKeyboardButton(
                    f"📱 {get_text('qr_code', language_code)}",
                    callback_data=f"accounts_qr:{account.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    get_text("back_to_menu", language_code),
                    callback_data="back_to_main"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Clear context data
        for key in ["selected_plan_id", "selected_plan", "selected_server_id", "account_name"]:
            if key in context.user_data:
                del context.user_data[key]
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        
        # Refund user's balance
        update_user(
            user_id=user_id,
            balance=balance
        )
        
        await query.edit_message_text(
            get_text("error_general", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECTING_PLAN

@require_auth
async def process_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment receipt."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get receipt from message
    receipt = update.message.text.strip()
    
    # Create transaction record
    payment_method = context.user_data.get("payment_method", "card")
    amount = context.user_data.get("payment_amount", 0)
    
    transaction_id = create_transaction(
        user_id=user_id,
        amount=amount,
        payment_method=payment_method,
        description="Purchase of subscription plan",
        receipt_number=receipt,
        status="pending_verification"
    )
    
    if not transaction_id:
        # Failed to create transaction
        await update.message.reply_text(
            get_text("transaction_creation_error", language_code),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_text("back_to_plans", language_code),
                        callback_data=SUBSCRIPTION_PLANS
                    )
                ]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECTING_PLAN
    
    # Store transaction details in context
    context.user_data["transaction_id"] = transaction_id
    
    # Get plan and server details
    plan_id = context.user_data.get("selected_plan_id")
    server_id = context.user_data.get("selected_server_id")
    account_name = context.user_data.get("account_name")
    
    # Store purchase details in transaction metadata
    update_transaction(
        transaction_id=transaction_id,
        metadata={
            "plan_id": plan_id,
            "server_id": server_id,
            "account_name": account_name
        }
    )
    
    # Send confirmation message
    message = get_text("receipt_received", language_code).format(
        transaction_id=transaction_id,
        receipt=receipt
    )
    
    # Add message about admin verification
    message += "\n\n" + get_text("admin_verification_required", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_menu", language_code),
                callback_data="back_to_main"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Notify admins about new payment
    await notify_admins_about_payment(transaction_id, context.bot)
    
    # Clear context data
    for key in ["selected_plan_id", "selected_plan", "selected_server_id", "account_name",
                "payment_method", "payment_amount", "transaction_id"]:
        if key in context.user_data:
            del context.user_data[key]
    
    return ConversationHandler.END

@require_auth
async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel purchase process."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Clear context data
    for key in ["selected_plan_id", "selected_plan", "selected_server_id", "account_name",
                "payment_method", "payment_amount", "transaction_id"]:
        if key in context.user_data:
            del context.user_data[key]
    
    # Send cancellation message
    message = get_text("purchase_cancelled", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_plans", language_code),
                callback_data=SUBSCRIPTION_PLANS
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PLAN

async def notify_admins_about_payment(transaction_id: str, bot) -> None:
    """Notify admins about new payment."""
    # Get transaction
    transaction = get_transaction(transaction_id)
    
    if not transaction:
        return
    
    # Get admin users
    admins = get_all_users(is_admin=True)
    
    if not admins:
        return
    
    # Get user who made the payment
    user_id = transaction.get("user_id")
    user = get_user(user_id)
    
    if not user:
        return
    
    # Get transaction metadata
    metadata = transaction.get("metadata", {})
    plan_id = metadata.get("plan_id")
    server_id = metadata.get("server_id")
    
    # Get plan and server details
    plan = get_subscription_plan(plan_id) if plan_id else None
    server = get_server(server_id) if server_id else None
    
    # Format amount
    amount = transaction.get("amount", 0)
    
    # Create notification message
    message = f"🔔 *New Subscription Payment*\n\n"
    message += f"User: {user.get('first_name')} (@{user.get('username')})\n"
    message += f"Amount: {format_number(amount)} {get_text('currency', 'en')}\n"
    message += f"Transaction ID: `{transaction_id}`\n"
    message += f"Receipt: `{transaction.get('receipt_number', 'N/A')}`\n\n"
    
    # Add plan and server info if available
    if plan:
        message += f"Plan: {plan.get('name', 'Unknown')}\n"
    if server:
        message += f"Server: {server.get('name', 'Unknown')}\n\n"
    
    message += f"Please verify this payment in the admin panel."
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "Verify Payment",
                callback_data=f"admin_verify:{transaction_id}"
            ),
            InlineKeyboardButton(
                "Reject Payment",
                callback_data=f"admin_reject:{transaction_id}"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send notification to all admins
    for admin in admins:
        try:
            admin_id = admin.get("id")
            
            # Skip if admin is the user who made the payment
            if admin_id == user_id:
                continue
                
            # Send message to admin
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Error sending payment notification to admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying admin about payment: {e}")

def get_subscription_handler() -> ConversationHandler:
    """Get the subscription handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(subscription_plans_menu, pattern=f"^{SUBSCRIPTION_PLANS}$")
        ],
        states={
            SELECTING_PLAN: [
                CallbackQueryHandler(select_plan, pattern=f"^{SELECT_PLAN}:"),
                CallbackQueryHandler(subscription_plans_menu, pattern=f"^{SUBSCRIPTION_PLANS}$"),
            ],
            SELECTING_SERVER: [
                CallbackQueryHandler(select_server, pattern=f"^{SELECT_SERVER}:"),
                CallbackQueryHandler(subscription_plans_menu, pattern=f"^{SUBSCRIPTION_PLANS}$"),
            ],
            CONFIRMING_PURCHASE: [
                CallbackQueryHandler(confirm_purchase, pattern=f"^{CONFIRM_PURCHASE}$"),
                CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
            ],
            SELECTING_PAYMENT_METHOD: [
                CallbackQueryHandler(select_payment_method, pattern=f"^{SELECT_PAYMENT}_"),
                CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
            ],
            PROCESSING_PAYMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_receipt),
                CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(subscription_plans_menu, pattern=f"^{SUBSCRIPTION_PLANS}$"),
            CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
        ],
        per_message=False,
    ) 