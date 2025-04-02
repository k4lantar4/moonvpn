import logging
from typing import Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from app.keyboards.main_menu import main_menu_keyboard, BTN_SELLER_PRICES
from api_client.seller import seller_client
from app.utils import api_client

# Enable logging
logger = logging.getLogger(__name__)

# Define callback data patterns
PRICE_CALLBACK_PREFIX = "price_"
VIEW_PLAN_DETAILS = f"{PRICE_CALLBACK_PREFIX}details_"
BECOME_SELLER = f"{PRICE_CALLBACK_PREFIX}become_seller"

async def handle_price_comparison(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the 'Special Prices' button in main menu."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not user or not chat_id:
        logger.warning("handle_price_comparison called without user or chat_id")
        return
    
    logger.info(f"User {user.id} requested special price comparison")
    
    try:
        # Get seller plans with both regular and seller prices
        plans = await seller_client.get_seller_plans()
        
        if not plans:
            await update.effective_message.reply_text(
                "⚠️ در حال حاضر هیچ طرحی برای نمایش وجود ندارد. لطفاً بعداً تلاش کنید.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        # Get user info to check if they are a seller
        user_info = await api_client.get_user_info(user.id)
        is_seller = user_info.get("role", {}).get("name") == "seller" if user_info else False
        
        message = "💰 *قیمت‌های ویژه فروشندگان*\n\n"
        
        if is_seller:
            message += "✅ *شما فروشنده هستید و می‌توانید از قیمت‌های ویژه استفاده کنید.*\n\n"
        else:
            message += "🔔 با تبدیل شدن به فروشنده، می‌توانید از تخفیف‌های ویژه برخوردار شوید!\n\n"
        
        # Create keyboard for plan details
        keyboard = []
        
        # First sort plans by duration (shortest first)
        plans.sort(key=lambda p: p.get("duration_days", 0))
        
        # Group plans by category
        plan_categories = {}
        for plan in plans:
            category = plan.get("category", "سایر")
            if category not in plan_categories:
                plan_categories[category] = []
            plan_categories[category].append(plan)
        
        # Format plans by category
        for category, category_plans in plan_categories.items():
            message += f"*{category}:*\n"
            
            for plan in category_plans:
                plan_id = plan.get("id")
                name = plan.get("name", "نامشخص")
                regular_price = plan.get("price", 0)
                seller_price = plan.get("seller_price", 0)
                duration = plan.get("duration_days", "?")
                
                # Calculate discount percentage
                discount_percent = 0
                if regular_price and seller_price < regular_price:
                    discount_percent = (regular_price - seller_price) / regular_price * 100
                
                # Format prices with commas
                formatted_regular = f"{int(regular_price):,}" if regular_price else "0"
                formatted_seller = f"{int(seller_price):,}" if seller_price else "0"
                
                message += f"🔹 *{name}* ({duration} روز)\n"
                message += f"   💲 قیمت عادی: {formatted_regular} تومان\n"
                message += f"   🏪 قیمت فروشنده: {formatted_seller} تومان\n"
                
                if discount_percent > 0:
                    message += f"   🎁 تخفیف: {discount_percent:.0f}%\n"
                
                message += "\n"
                
                # Add button for plan details
                if plan_id:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"جزئیات {name}", 
                            callback_data=f"{VIEW_PLAN_DETAILS}{plan_id}"
                        )
                    ])
        
        # Add button to become a seller if user is not already a seller
        if not is_seller:
            keyboard.append([
                InlineKeyboardButton("🏪 فروشنده شوید", callback_data=BECOME_SELLER)
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main_menu")
        ])
        
        await update.effective_message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_price_comparison: {e}")
        await update.effective_message.reply_text(
            "❌ خطا در دریافت اطلاعات قیمت‌ها. لطفاً بعداً تلاش کنید.",
            reply_markup=main_menu_keyboard()
        )

async def handle_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callbacks from price comparison section."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if not user:
        return
    
    # Handle main menu return
    if query.data == "back_to_main_menu":
        await query.message.reply_text(
            "بازگشت به منوی اصلی...",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Handle view plan details
    elif query.data.startswith(VIEW_PLAN_DETAILS):
        try:
            plan_id = int(query.data[len(VIEW_PLAN_DETAILS):])
            
            # Get all plans
            plans = await seller_client.get_seller_plans()
            
            # Find the specific plan
            plan = next((p for p in plans if p.get("id") == plan_id), None)
            
            if not plan:
                await query.edit_message_text(
                    "❌ طرح مورد نظر یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_price_comparison")]
                    ])
                )
                return
            
            # Extract plan details
            name = plan.get("name", "نامشخص")
            description = plan.get("description", "")
            regular_price = plan.get("price", 0)
            seller_price = plan.get("seller_price", 0)
            duration = plan.get("duration_days", "?")
            data_limit = plan.get("data_limit_gb", "?")
            max_connections = plan.get("max_connections", "?")
            category = plan.get("category", "سایر")
            
            # Calculate discount percentage
            discount_percent = 0
            if regular_price and seller_price < regular_price:
                discount_percent = (regular_price - seller_price) / regular_price * 100
            
            # Format prices with commas
            formatted_regular = f"{int(regular_price):,}" if regular_price else "0"
            formatted_seller = f"{int(seller_price):,}" if seller_price else "0"
            
            # Create detailed message
            message = f"🔎 *جزئیات طرح: {name}*\n\n"
            
            if description:
                message += f"{description}\n\n"
            
            message += f"📋 *مشخصات:*\n"
            message += f"🏷️ دسته: {category}\n"
            message += f"📅 مدت: {duration} روز\n"
            message += f"📊 حجم: {data_limit} گیگابایت\n"
            message += f"👥 حداکثر اتصالات همزمان: {max_connections}\n\n"
            
            message += f"💰 *قیمت‌ها:*\n"
            message += f"💲 قیمت عادی: {formatted_regular} تومان\n"
            message += f"🏪 قیمت فروشنده: {formatted_seller} تومان\n"
            
            if discount_percent > 0:
                message += f"🎁 تخفیف: {discount_percent:.0f}%\n"
            
            # Get user info to add appropriate buttons
            user_info = await api_client.get_user_info(user.id)
            is_seller = user_info.get("role", {}).get("name") == "seller" if user_info else False
            
            keyboard = []
            
            # Add button to purchase plan
            from app.keyboards.buy_service import PLAN_CALLBACK_PREFIX
            keyboard.append([
                InlineKeyboardButton("🛒 خرید", callback_data=f"{PLAN_CALLBACK_PREFIX}{plan_id}")
            ])
            
            # Add button to become a seller if user is not already a seller
            if not is_seller:
                keyboard.append([
                    InlineKeyboardButton("🏪 فروشنده شوید", callback_data=BECOME_SELLER)
                ])
            
            keyboard.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_price_comparison")
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error in handle_price_callback (VIEW_PLAN_DETAILS): {e}")
            await query.edit_message_text(
                "❌ خطا در دریافت جزئیات طرح. لطفاً بعداً تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_price_comparison")]
                ])
            )
    
    # Handle become seller button
    elif query.data == BECOME_SELLER:
        # Redirect to seller handler
        from app.handlers.seller_handlers import handle_become_seller
        
        # Need to recreate an update object with message instead of callback query
        # to properly call the handler
        text_message = await query.message.reply_text(
            "در حال انتقال به بخش فروشندگان..."
        )
        
        # Create a new context for the message
        new_update = Update(
            update_id=update.update_id,
            message=text_message
        )
        
        return await handle_become_seller(new_update, context)
    
    # Handle back to price comparison
    elif query.data == "back_to_price_comparison":
        await handle_price_comparison(update, context)

def get_price_comparison_handlers():
    """Returns handlers for price comparison feature."""
    return [
        MessageHandler(filters.Text([BTN_SELLER_PRICES]), handle_price_comparison),
        CommandHandler("prices", handle_price_comparison),
        CallbackQueryHandler(handle_price_callback, pattern=f"^{PRICE_CALLBACK_PREFIX}|^back_to_price_comparison$")
    ] 