import logging
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, CommandHandler, MessageHandler, filters

from app.keyboards.main_menu import main_menu_keyboard, BTN_BECOME_SELLER
from app.utils import api_client
from api_client.seller import seller_client
from app.keyboards.payment import CANCEL_CALLBACK, get_cancel_keyboard

# Enable logging
logger = logging.getLogger(__name__)

# Define conversation states
(
    VIEWING_SELLER_INFO,
    VIEWING_REQUIREMENTS,
    CONFIRMING_UPGRADE,
    SELECTING_PAYMENT_METHOD,
    HANDLING_PAYMENT,
) = range(5)

# Define callback data patterns
SELLER_CALLBACK_PREFIX = "seller_"
VIEW_REQUIREMENTS = f"{SELLER_CALLBACK_PREFIX}requirements"
START_UPGRADE = f"{SELLER_CALLBACK_PREFIX}start_upgrade"
CONFIRM_UPGRADE = f"{SELLER_CALLBACK_PREFIX}confirm_upgrade"
TOP_UP_WALLET = f"{SELLER_CALLBACK_PREFIX}top_up"
VIEW_SELLER_PLANS = f"{SELLER_CALLBACK_PREFIX}plans"
VIEW_STATISTICS = f"{SELLER_CALLBACK_PREFIX}statistics"
TOP_UP_AMOUNT_PREFIX = f"{SELLER_CALLBACK_PREFIX}amount_"

async def handle_become_seller(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Become a Seller' button press."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if not chat_id or not user:
        logger.warning("handle_become_seller called without chat_id or user")
        return ConversationHandler.END
    
    logger.info(f"User {user.id} requested to become a seller")
    
    # First, check if user is already a seller
    user_info = await api_client.get_user_info(user.id)
    
    if not user_info:
        await update.effective_message.reply_text(
            "❌ خطا در دریافت اطلاعات کاربری. لطفاً بعداً تلاش کنید."
        )
        return ConversationHandler.END
    
    # Check if user is already a seller
    if user_info.get("role", {}).get("name") == "seller":
        # User is already a seller, show seller dashboard
        keyboard = [
            [InlineKeyboardButton("📊 آمار فروش", callback_data=VIEW_STATISTICS)],
            [InlineKeyboardButton("💰 قیمت‌های فروشندگان", callback_data=VIEW_SELLER_PLANS)],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")]
        ]
        
        await update.effective_message.reply_text(
            f"✅ {user.first_name} عزیز، شما در حال حاضر فروشنده هستید!\n\n"
            "از منوی زیر می‌توانید به امکانات فروشندگان دسترسی داشته باشید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return VIEWING_SELLER_INFO
    
    # User is not a seller, check eligibility and show requirements
    try:
        requirements = await seller_client.get_seller_requirements()
        eligibility = await seller_client.check_seller_eligibility(user.id)
        
        # Extract key info
        min_amount = requirements.get("minimum_topup_amount", 0)
        formatted_min_amount = f"{int(min_amount):,}" if min_amount else "نامشخص"
        benefits = requirements.get("benefits", [])
        is_eligible = eligibility.get("is_eligible", False)
        missing = eligibility.get("missing_requirements", [])
        
        # Current wallet balance
        wallet_balance = user_info.get("wallet_balance", 0)
        formatted_wallet = f"{int(wallet_balance):,}" if wallet_balance else "0"
        
        # Build response message
        message = f"🏪 *فروشنده شوید*\n\n"
        message += "به عنوان فروشنده، شما می‌توانید از مزایای زیر بهره‌مند شوید:\n\n"
        
        # List benefits
        for i, benefit in enumerate(benefits, 1):
            message += f"{i}. {benefit}\n"
        
        message += f"\n💰 شرایط فروشنده شدن: شارژ کیف پول به مبلغ حداقل *{formatted_min_amount} تومان*\n"
        message += f"👛 موجودی فعلی کیف پول شما: *{formatted_wallet} تومان*\n\n"
        
        # Show eligibility status and next steps
        if is_eligible:
            message += "✅ شما شرایط لازم برای فروشنده شدن را دارید!\n"
            message += "برای تبدیل شدن به فروشنده، روی دکمه «ارتقاء به فروشنده» کلیک کنید."
            
            keyboard = [
                [InlineKeyboardButton("🔄 ارتقاء به فروشنده", callback_data=START_UPGRADE)],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")]
            ]
        else:
            message += "❌ شما هنوز شرایط لازم برای فروشنده شدن را ندارید:\n"
            for req in missing:
                message += f"- {req}\n"
            
            amount_needed = max(0, min_amount - wallet_balance)
            formatted_amount_needed = f"{int(amount_needed):,}" if amount_needed else "0"
            
            message += f"\nبرای فروشنده شدن، نیاز به شارژ *{formatted_amount_needed} تومان* دیگر دارید."
            
            # Create buttons for suggested top-up amounts
            suggested_amounts = [
                amount_needed, 
                amount_needed + 100000, 
                amount_needed + 200000
            ]
            
            amount_buttons = []
            for amount in suggested_amounts:
                if amount <= 0:
                    continue
                formatted = f"{int(amount):,}"
                amount_buttons.append(
                    InlineKeyboardButton(
                        f"💰 شارژ {formatted} تومان", 
                        callback_data=f"{TOP_UP_AMOUNT_PREFIX}{amount}"
                    )
                )
            
            keyboard = []
            # Add amount buttons in rows of 2
            for i in range(0, len(amount_buttons), 2):
                row = amount_buttons[i:i+2]
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("👛 شارژ کیف پول", callback_data=TOP_UP_WALLET)])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")])
        
        await update.effective_message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return VIEWING_REQUIREMENTS
        
    except Exception as e:
        logger.error(f"Error in handle_become_seller: {e}")
        await update.effective_message.reply_text(
            "❌ خطا در دریافت اطلاعات فروشندگی. لطفاً بعداً تلاش کنید."
        )
        return ConversationHandler.END

async def handle_seller_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles seller button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not user or not chat_id:
        return ConversationHandler.END
    
    if query.data == "back_to_main_menu":
        await query.message.reply_text(
            "بازگشت به منوی اصلی...",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    elif query.data == VIEW_REQUIREMENTS:
        # Redirect to the main become_seller handler to show requirements
        return await handle_become_seller(update, context)
    
    elif query.data == START_UPGRADE:
        # Show confirmation message for upgrading to seller
        await query.edit_message_text(
            "🔄 *ارتقاء به فروشنده*\n\n"
            "آیا مطمئن هستید که می‌خواهید به فروشنده ارتقاء پیدا کنید؟\n\n"
            "پس از ارتقاء، شما می‌توانید از قیمت‌های ویژه فروشندگان استفاده کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ بله، فروشنده شوم", callback_data=CONFIRM_UPGRADE)],
                [InlineKeyboardButton("❌ خیر، منصرف شدم", callback_data="back_to_main_menu")]
            ]),
            parse_mode="Markdown"
        )
        return CONFIRMING_UPGRADE
    
    elif query.data == CONFIRM_UPGRADE:
        # Process upgrade to seller
        try:
            result = await seller_client.become_seller(user.id)
            
            if result.get("success", False):
                await query.edit_message_text(
                    "🎉 *تبریک! شما با موفقیت به فروشنده ارتقاء یافتید*\n\n"
                    "اکنون می‌توانید از مزایا و قیمت‌های ویژه فروشندگان بهره‌مند شوید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💰 مشاهده قیمت‌های فروشندگان", callback_data=VIEW_SELLER_PLANS)],
                        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")]
                    ]),
                    parse_mode="Markdown"
                )
                return VIEWING_SELLER_INFO
            else:
                # Something went wrong
                error_message = result.get("message", "خطای نامشخص")
                await query.edit_message_text(
                    f"❌ *خطا در ارتقاء به فروشنده*\n\n{error_message}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 تلاش مجدد", callback_data=VIEW_REQUIREMENTS)],
                        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")]
                    ]),
                    parse_mode="Markdown"
                )
                return VIEWING_REQUIREMENTS
        
        except Exception as e:
            logger.error(f"Error in handle_seller_button_press (CONFIRM_UPGRADE): {e}")
            await query.edit_message_text(
                "❌ خطا در ارتقاء به فروشنده. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 تلاش مجدد", callback_data=VIEW_REQUIREMENTS)],
                    [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")]
                ])
            )
            return VIEWING_REQUIREMENTS
    
    elif query.data == VIEW_SELLER_PLANS:
        # Show seller plans with price comparison
        try:
            plans = await seller_client.get_seller_plans()
            
            if not plans:
                await query.edit_message_text(
                    "در حال حاضر هیچ طرحی برای فروشندگان وجود ندارد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                    ])
                )
                return VIEWING_SELLER_INFO
            
            message = "💰 *قیمت‌های ویژه فروشندگان*\n\n"
            
            for plan in plans:
                name = plan.get("name", "نامشخص")
                regular_price = plan.get("price", 0)
                seller_price = plan.get("seller_price", 0)
                duration = plan.get("duration_days", "?")
                data_limit = plan.get("data_limit_gb", "?")
                
                # Calculate discount percentage
                discount_percent = 0
                if regular_price and seller_price < regular_price:
                    discount_percent = (regular_price - seller_price) / regular_price * 100
                
                # Format prices with commas
                formatted_regular = f"{int(regular_price):,}" if regular_price else "0"
                formatted_seller = f"{int(seller_price):,}" if seller_price else "0"
                
                message += f"🔹 *{name}*\n"
                message += f"   📅 مدت: {duration} روز\n"
                message += f"   📊 حجم: {data_limit} گیگابایت\n"
                message += f"   💰 قیمت عادی: {formatted_regular} تومان\n"
                message += f"   🏪 قیمت فروشنده: {formatted_seller} تومان\n"
                
                if discount_percent > 0:
                    message += f"   🎁 تخفیف: {discount_percent:.0f}%\n"
                
                message += "\n"
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                ]),
                parse_mode="Markdown"
            )
            return VIEWING_SELLER_INFO
            
        except Exception as e:
            logger.error(f"Error in handle_seller_button_press (VIEW_SELLER_PLANS): {e}")
            await query.edit_message_text(
                "❌ خطا در دریافت قیمت‌های فروشندگان. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                ])
            )
            return VIEWING_SELLER_INFO
    
    elif query.data == VIEW_STATISTICS:
        # Show seller statistics
        try:
            stats = await seller_client.get_seller_statistics(user.id)
            
            if not stats:
                await query.edit_message_text(
                    "در حال حاضر آماری برای نمایش وجود ندارد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                    ])
                )
                return VIEWING_SELLER_INFO
            
            # Extract statistics
            total_sales = stats.get("total_sales", 0)
            total_revenue = stats.get("total_revenue", 0)
            total_commission = stats.get("total_commission", 0)
            recent_sales = stats.get("recent_sales", [])
            
            # Format values
            formatted_sales = f"{total_sales:,}" if total_sales else "0"
            formatted_revenue = f"{int(total_revenue):,}" if total_revenue else "0"
            formatted_commission = f"{int(total_commission):,}" if total_commission else "0"
            
            message = "📊 *آمار فروش شما*\n\n"
            message += f"🛒 کل فروش: {formatted_sales} سرویس\n"
            message += f"💵 درآمد کل: {formatted_revenue} تومان\n"
            message += f"💰 کمیسیون: {formatted_commission} تومان\n\n"
            
            if recent_sales:
                message += "*فروش‌های اخیر:*\n"
                for sale in recent_sales[:5]:  # Show only the last 5 sales
                    sale_id = sale.get("id", "نامشخص")
                    sale_date = sale.get("date", "نامشخص")
                    sale_plan = sale.get("plan_name", "نامشخص")
                    sale_amount = sale.get("amount", 0)
                    
                    formatted_amount = f"{int(sale_amount):,}" if sale_amount else "0"
                    
                    message += f"🔹 {sale_plan} - {formatted_amount} تومان ({sale_date})\n"
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                ]),
                parse_mode="Markdown"
            )
            return VIEWING_SELLER_INFO
            
        except Exception as e:
            logger.error(f"Error in handle_seller_button_press (VIEW_STATISTICS): {e}")
            await query.edit_message_text(
                "❌ خطا در دریافت آمار فروش. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                ])
            )
            return VIEWING_SELLER_INFO
    
    elif query.data.startswith(TOP_UP_AMOUNT_PREFIX):
        # Handle wallet top-up with a specific amount
        amount_str = query.data[len(TOP_UP_AMOUNT_PREFIX):]
        try:
            amount = int(amount_str)
            
            # Store amount in context for payment handler
            context.user_data["topup_amount"] = amount
            
            # Show payment method selection
            # This part will be similar to buy_flow.py
            # We'll just redirect to the wallet top-up handler instead
            # of implementing it here
            
            # Get available payment methods
            payment_methods = await api_client.payments.get_available_payment_methods()
            
            if not payment_methods:
                await query.edit_message_text(
                    "❌ در حال حاضر هیچ روش پرداختی در دسترس نیست. لطفاً بعداً تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                    ])
                )
                return VIEWING_REQUIREMENTS
            
            formatted_amount = f"{amount:,}"
            
            message = f"💰 *شارژ کیف پول*\n\n"
            message += f"مبلغ: *{formatted_amount} تومان*\n\n"
            message += "لطفاً روش پرداخت را انتخاب کنید:"
            
            from app.keyboards.payment import generate_payment_method_keyboard
            
            # Create payment method keyboard
            keyboard = generate_payment_method_keyboard(payment_methods)
            
            # Add cancel button
            keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data=CANCEL_CALLBACK)])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            return SELECTING_PAYMENT_METHOD
            
        except ValueError:
            logger.error(f"Invalid amount in TOP_UP_AMOUNT_PREFIX: {amount_str}")
            await query.edit_message_text(
                "❌ مبلغ نامعتبر. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                ])
            )
            return VIEWING_REQUIREMENTS
    
    elif query.data == TOP_UP_WALLET:
        # Redirect to wallet top-up section
        # This should be handled by the wallet handler
        from app.handlers.wallet import handle_wallet_topup
        if handle_wallet_topup:
            return await handle_wallet_topup(update, context)
        else:
            await query.edit_message_text(
                "⚠️ بخش شارژ کیف پول هنوز پیاده‌سازی نشده است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=VIEW_REQUIREMENTS)]
                ])
            )
            return VIEWING_REQUIREMENTS
    
    else:
        # Unknown callback data
        logger.warning(f"Unknown callback data in seller handler: {query.data}")
        await query.edit_message_text(
            "خطای نامشخص. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")]
            ])
        )
        return ConversationHandler.END

async def cancel_seller_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the seller flow."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "عملیات لغو شد. به منوی اصلی بازگشتید.",
            reply_markup=None
        )
    else:
        await update.message.reply_text(
            "عملیات لغو شد. به منوی اصلی بازگشتید.",
            reply_markup=main_menu_keyboard()
        )
    
    return ConversationHandler.END

def get_seller_handlers():
    """Returns the handlers for the seller flow."""
    return [
        # Handler for the "Become a Seller" button in main menu
        MessageHandler(filters.Text([BTN_BECOME_SELLER]), handle_become_seller),
        
        # Command handler for /seller
        CommandHandler("seller", handle_become_seller),
        
        # Conversation handler for the seller flow
        ConversationHandler(
            entry_points=[
                MessageHandler(filters.Text([BTN_BECOME_SELLER]), handle_become_seller),
                CommandHandler("seller", handle_become_seller)
            ],
            states={
                VIEWING_SELLER_INFO: [
                    CallbackQueryHandler(handle_seller_button_press)
                ],
                VIEWING_REQUIREMENTS: [
                    CallbackQueryHandler(handle_seller_button_press)
                ],
                CONFIRMING_UPGRADE: [
                    CallbackQueryHandler(handle_seller_button_press)
                ],
                SELECTING_PAYMENT_METHOD: [
                    CallbackQueryHandler(handle_seller_button_press)
                ],
                HANDLING_PAYMENT: [
                    CallbackQueryHandler(handle_seller_button_press)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel_seller_flow),
                CallbackQueryHandler(cancel_seller_flow, pattern=f"^{CANCEL_CALLBACK}$")
            ],
            name="seller_flow",
            persistent=False
        )
    ] 