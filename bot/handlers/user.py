"""
User handlers for the Telegram bot.

This module provides handlers for user interactions including:
- Plan purchases
- Account management
- Wallet operations
"""

import logging
import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, CallbackQueryHandler, filters
)

from core.config import get_settings
from core.database import get_db
from core.i18n import get_text
from bot.keyboards import (
    get_main_keyboard, 
    get_plans_keyboard,
    get_plan_list_keyboard,
    get_locations_keyboard,
    get_protocols_keyboard,
    get_payment_methods_keyboard,
    get_confirm_purchase_keyboard,
    get_cancel_keyboard
)
from bot.states import PurchaseStates

# Setup logging
logger = logging.getLogger(__name__)
settings = get_settings()

# Helper Functions
async def get_categories() -> List[Dict[str, Any]]:
    """Get all plan categories from the database."""
    categories = []
    async for db_session in get_db():
        result = await db_session.execute("SELECT * FROM plan_categories WHERE is_active = 1")
        categories = result.fetchall()
    return categories

async def get_plans_by_category(category_id: int) -> List[Dict[str, Any]]:
    """Get all plans for a specific category."""
    plans = []
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT * FROM plans WHERE category_id = :category_id AND is_active = 1",
            {"category_id": category_id}
        )
        plans = result.fetchall()
    return plans

async def get_plan_details(plan_id: int) -> Optional[Dict[str, Any]]:
    """Get details of a specific plan."""
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT p.*, c.name as category_name FROM plans p "
            "JOIN plan_categories c ON p.category_id = c.id "
            "WHERE p.id = :plan_id",
            {"plan_id": plan_id}
        )
        plan = result.first()
    return plan if plan else None

async def get_locations() -> List[Dict[str, Any]]:
    """Get all available locations."""
    locations = []
    async for db_session in get_db():
        result = await db_session.execute("SELECT * FROM locations WHERE is_active = 1")
        locations = result.fetchall()
    return locations

async def get_protocols() -> List[Dict[str, Any]]:
    """Get all available protocols."""
    protocols = []
    async for db_session in get_db():
        result = await db_session.execute("SELECT * FROM protocols WHERE is_active = 1")
        protocols = result.fetchall()
    return protocols

async def get_user_wallet_balance(user_id: int) -> Decimal:
    """Get user's wallet balance."""
    balance = Decimal('0.0')
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT balance FROM wallets WHERE user_id = :user_id",
            {"user_id": user_id}
        )
        wallet = result.first()
        if wallet:
            balance = Decimal(str(wallet.balance))
    return balance

async def get_bank_card() -> Optional[Dict[str, Any]]:
    """Get bank card information for card-to-card payment."""
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT * FROM bank_cards WHERE is_active = 1 LIMIT 1"
        )
        card = result.first()
    return card if card else None

# Purchase flow handlers
async def start_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the purchase process by showing plan categories."""
    user = update.effective_user
    logger.info(f"User {user.id} started the purchase flow")
    
    # Get user's language preference
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    
    # Get categories
    categories = await get_categories()
    
    if not categories:
        await update.message.reply_text(
            "متأسفانه در حال حاضر هیچ دسته‌بندی فعالی وجود ندارد. لطفاً بعداً دوباره تلاش کنید."
        )
        return ConversationHandler.END
    
    # Show categories keyboard
    keyboard = get_plans_keyboard(categories)
    
    await update.message.reply_text(
        get_text("select_category", lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PurchaseStates.SELECT_PLAN

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show plans for selected category."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    category_id = int(query.data.split("_")[1])
    
    # Store category_id in context
    context.user_data["category_id"] = category_id
    
    # Get user's language
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    
    # Get category name
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT name FROM plan_categories WHERE id = :id",
            {"id": category_id}
        )
        category = result.first()
    
    category_name = category.name if category else "Unknown"
    
    # Get plans for this category
    plans = await get_plans_by_category(category_id)
    
    if not plans:
        await query.edit_message_text(
            "متأسفانه در حال حاضر هیچ پلنی در این دسته‌بندی وجود ندارد. لطفاً دسته‌بندی دیگری را انتخاب کنید."
        )
        return PurchaseStates.SELECT_CATEGORY
    
    # Show plans keyboard
    keyboard = get_plan_list_keyboard(plans, category_id)
    
    await query.edit_message_text(
        get_text("select_plan", lang, category_name=category_name),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PurchaseStates.SELECT_LOCATION

async def select_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available locations."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    plan_id = int(query.data.split("_")[1])
    
    # Store plan_id in context
    context.user_data["plan_id"] = plan_id
    
    # Get user's language
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    
    # Get locations
    locations = await get_locations()
    
    if not locations:
        await query.edit_message_text(
            "متأسفانه در حال حاضر هیچ موقعیتی در دسترس نیست. لطفاً بعداً دوباره تلاش کنید."
        )
        return ConversationHandler.END
    
    # Show locations keyboard
    keyboard = get_locations_keyboard(locations)
    
    await query.edit_message_text(
        get_text("select_location", lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PurchaseStates.SELECT_PROTOCOL

async def select_protocol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available protocols."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    location_id = int(query.data.split("_")[1])
    
    # Store location_id in context
    context.user_data["location_id"] = location_id
    
    # Get user's language
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    
    # Get protocols
    protocols = await get_protocols()
    
    if not protocols:
        await query.edit_message_text(
            "متأسفانه در حال حاضر هیچ پروتکلی در دسترس نیست. لطفاً بعداً دوباره تلاش کنید."
        )
        return ConversationHandler.END
    
    # Show protocols keyboard
    keyboard = get_protocols_keyboard(protocols)
    
    await query.edit_message_text(
        get_text("select_protocol", lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PurchaseStates.CONFIRM_PURCHASE

async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show purchase summary and ask for confirmation."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    protocol_id = int(query.data.split("_")[1])
    
    # Store protocol_id in context
    context.user_data["protocol_id"] = protocol_id
    
    # Get user's language
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    
    # Get plan details
    plan = await get_plan_details(context.user_data["plan_id"])
    
    # Get location name
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT name FROM locations WHERE id = :id",
            {"id": context.user_data["location_id"]}
        )
        location = result.first()
    
    location_name = location.name if location else "Unknown"
    
    # Get protocol name
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT name FROM protocols WHERE id = :id",
            {"id": protocol_id}
        )
        protocol = result.first()
    
    protocol_name = protocol.name if protocol else "Unknown"
    
    # Store for later use
    context.user_data["plan_name"] = plan.name
    context.user_data["category_name"] = plan.category_name
    context.user_data["location_name"] = location_name
    context.user_data["protocol_name"] = protocol_name
    context.user_data["price"] = float(plan.price)
    
    # Show confirmation
    keyboard = get_confirm_purchase_keyboard()
    
    await query.edit_message_text(
        get_text("confirm_purchase", lang,
                plan_name=plan.name,
                category_name=plan.category_name,
                location_name=location_name,
                protocol_name=protocol_name,
                price=plan.price),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PurchaseStates.SELECT_PAYMENT_METHOD

async def select_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment method options."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_purchase":
        # ردیابی کلیک روی دکمه تایید خرید
        user = update.effective_user
        
        # Get user's language
        async for db_session in get_db():
            result = await db_session.execute(
                "SELECT lang FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": user.id}
            )
            user_data = result.first()
        
        lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
        
        # Show payment methods keyboard
        keyboard = get_payment_methods_keyboard()
        
        await query.edit_message_text(
            get_text("select_payment_method", lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return PurchaseStates.PROCESS_PAYMENT
    else:
        return PurchaseStates.CONFIRM_PURCHASE

async def process_wallet_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment from wallet."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "payment_wallet":
        user = update.effective_user
        
        # Get user's language
        async for db_session in get_db():
            result = await db_session.execute(
                "SELECT lang FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": user.id}
            )
            user_data = result.first()
        
        lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
        
        # Check wallet balance
        balance = await get_user_wallet_balance(user.id)
        price = Decimal(str(context.user_data["price"]))
        
        if balance < price:
            # Insufficient funds
            await query.edit_message_text(
                get_text("insufficient_funds", lang),
                reply_markup=InlineKeyboardMarkup(get_cancel_keyboard())
            )
            return PurchaseStates.SELECT_PAYMENT_METHOD
        
        # Deduct from wallet
        async for db_session in get_db():
            await db_session.execute(
                "UPDATE wallets SET balance = balance - :amount WHERE user_id = :user_id",
                {"amount": price, "user_id": user.id}
            )
            
            # Add transaction record
            await db_session.execute(
                "INSERT INTO transactions (user_id, amount, type, description) VALUES (:user_id, :amount, 'debit', :description)",
                {
                    "user_id": user.id,
                    "amount": price,
                    "description": f"خرید اشتراک {context.user_data['plan_name']}"
                }
            )
            
            await db_session.commit()
        
        # Show processing message
        await query.edit_message_text(get_text("payment_successful", lang))
        
        # Create account
        return await create_account(update, context)
    else:
        return PurchaseStates.SELECT_PAYMENT_METHOD

async def process_card_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process card-to-card payment."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "payment_card":
        user = update.effective_user
        
        # Get user's language
        async for db_session in get_db():
            result = await db_session.execute(
                "SELECT lang FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": user.id}
            )
            user_data = result.first()
        
        lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
        
        # Get bank card info
        card = await get_bank_card()
        
        if not card:
            await query.edit_message_text(
                "متأسفانه در حال حاضر امکان پرداخت کارت به کارت وجود ندارد. لطفاً روش دیگری را انتخاب کنید."
            )
            return PurchaseStates.SELECT_PAYMENT_METHOD
        
        context.user_data["card_number"] = card.card_number
        context.user_data["card_owner"] = card.owner_name
        
        # Ask user to make payment
        await query.edit_message_text(
            get_text("card_payment_info", lang,
                    amount=context.user_data["price"],
                    card_number=card.card_number,
                    card_owner=card.owner_name),
            reply_markup=InlineKeyboardMarkup(get_cancel_keyboard())
        )
        
        return PurchaseStates.VERIFY_PAYMENT
    else:
        return PurchaseStates.SELECT_PAYMENT_METHOD

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify payment receipt or tracking number."""
    user = update.effective_user
    
    # Get user's language
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    
    # In a real implementation, you would verify the receipt
    # For demo purposes, we'll accept all payments
    await update.message.reply_text(get_text("payment_confirmation", lang))
    
    # Wait a bit to simulate verification
    await update.message.reply_text(get_text("payment_successful", lang))
    
    # Create account
    return await create_account(update, context)

async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create account in the panel and send details to user."""
    user = update.effective_user
    
    # Get user's language
    async for db_session in get_db():
        result = await db_session.execute(
            "SELECT lang, id FROM users WHERE telegram_id = :telegram_id",
            {"telegram_id": user.id}
        )
        user_data = result.first()
    
    lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
    user_id = user_data.id
    
    # Get plan details (again, to ensure we have latest data)
    plan = await get_plan_details(context.user_data["plan_id"])
    
    # Here you would actually create the account in your VPN panel
    # For demo purposes, we'll simulate account creation
    
    # Generate unique username and password
    username = f"user_{user.id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    password = f"pass_{user.id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Calculate expiration date
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=plan.duration)
    
    # Save service to database
    async for db_session in get_db():
        await db_session.execute(
            """
            INSERT INTO services 
            (user_id, plan_id, location_id, protocol_id, username, password, 
             expiry_date, total_traffic, remaining_traffic, status)
            VALUES
            (:user_id, :plan_id, :location_id, :protocol_id, :username, :password,
             :expiry_date, :total_traffic, :total_traffic, 'active')
            """,
            {
                "user_id": user_id,
                "plan_id": context.user_data["plan_id"],
                "location_id": context.user_data["location_id"],
                "protocol_id": context.user_data["protocol_id"],
                "username": username,
                "password": password,
                "expiry_date": expiry_date,
                "total_traffic": plan.traffic_gb
            }
        )
        await db_session.commit()
    
    # Generate connection details
    connection_details = f"""
Server: srv{context.user_data["location_id"]}.moonvpn.com
Port: 443
Username: {username}
Password: {password}
Protocol: {context.user_data["protocol_name"]}
    """
    
    # Clear user data now that purchase is complete
    purchase_data = context.user_data.copy()
    context.user_data.clear()
    
    # Send account details
    await update.message.reply_text(
        get_text("account_created", lang,
                connection_details=connection_details,
                duration=plan.duration,
                expiry_date=expiry_date.strftime("%Y-%m-%d"),
                traffic=plan.traffic_gb)
    )
    
    return ConversationHandler.END

async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the purchase process."""
    query = update.callback_query
    if query:
        await query.answer()
        
        # Get user's language
        user = update.effective_user
        async for db_session in get_db():
            result = await db_session.execute(
                "SELECT lang FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": user.id}
            )
            user_data = result.first()
        
        lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
        
        await query.edit_message_text(get_text("operation_cancelled", lang))
    else:
        # For text message cancellations
        user = update.effective_user
        async for db_session in get_db():
            result = await db_session.execute(
                "SELECT lang FROM users WHERE telegram_id = :telegram_id",
                {"telegram_id": user.id}
            )
            user_data = result.first()
        
        lang = user_data.lang if user_data else settings.DEFAULT_LANGUAGE
        
        await update.message.reply_text(get_text("operation_cancelled", lang))
    
    context.user_data.clear()
    return ConversationHandler.END

# Setup handlers
def setup_handlers(application):
    """Set up user-related handlers."""
    # Purchase conversation handler
    purchase_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(🛒 خرید اشتراک|🛒 Buy Subscription)$'), start_purchase)],
        states={
            PurchaseStates.SELECT_CATEGORY: [
                CallbackQueryHandler(start_purchase, pattern='^back_to_categories$'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.SELECT_PLAN: [
                CallbackQueryHandler(select_plan, pattern='^category_'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.SELECT_LOCATION: [
                CallbackQueryHandler(select_location, pattern='^plan_'),
                CallbackQueryHandler(select_plan, pattern='^back_to_plans_'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.SELECT_PROTOCOL: [
                CallbackQueryHandler(select_protocol, pattern='^location_'),
                CallbackQueryHandler(select_location, pattern='^back_to_locations$'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.CONFIRM_PURCHASE: [
                CallbackQueryHandler(select_payment_method, pattern='^confirm_purchase$'),
                CallbackQueryHandler(select_protocol, pattern='^back_to_protocols$'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.SELECT_PAYMENT_METHOD: [
                CallbackQueryHandler(select_payment_method, pattern='^back_to_payment$'),
                CallbackQueryHandler(confirm_purchase, pattern='^back_to_confirm$'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.PROCESS_PAYMENT: [
                CallbackQueryHandler(process_wallet_payment, pattern='^payment_wallet$'),
                CallbackQueryHandler(process_card_payment, pattern='^payment_card$'),
                CallbackQueryHandler(select_payment_method, pattern='^back_to_payment$'),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ],
            PurchaseStates.VERIFY_PAYMENT: [
                MessageHandler(filters.TEXT | filters.PHOTO, verify_payment),
                CallbackQueryHandler(cancel_purchase, pattern='^cancel$')
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_purchase),
            MessageHandler(filters.Regex('^(❌ لغو|❌ Cancel)$'), cancel_purchase)
        ],
        name="purchase_conversation",
        persistent=False
    )
    
    application.add_handler(purchase_handler)
    
    logger.info("User handlers registered")
