"""Purchase plan handlers for user."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.plan_service import PlanService
from bot.services.location_service import LocationService
from bot.keyboards.reply import get_back_button
from bot.keyboards.inline.purchase import (
    get_plan_categories_keyboard,
    get_plans_keyboard,
    get_locations_keyboard,
)

logger = logging.getLogger(__name__)

# Define states for the purchase flow
class PurchaseStates(StatesGroup):
    """States for the purchase flow."""
    select_category = State()  # User is selecting a plan category
    select_plan = State()      # User is selecting a specific plan
    select_location = State()  # User is selecting a location
    confirm_order = State()    # User is confirming the order

# Create router
router = Router(name="user-purchase")

@router.message(F.text == "🛒 خرید پلن")
async def show_plan_categories(message: Message, session: AsyncSession, state: FSMContext):
    """Handle the user pressing the 'Buy Plan' button."""
    try:
        # Get plan service
        plan_service = PlanService(db=session)
        
        # Get categories
        categories = await plan_service.get_plan_categories()
        
        # Build keyboard with categories
        keyboard = get_plan_categories_keyboard(categories)
        
        # Set state
        await state.set_state(PurchaseStates.select_category)
        
        # Respond to user
        await message.answer(
            "🛒 <b>خرید پلن</b>\n\n"
            "لطفاً یکی از دسته‌بندی‌های زیر را انتخاب کنید یا همه پلن‌ها را مشاهده نمایید:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing plan categories: {e}", exc_info=True)
        await message.answer(
            "⚠️ متأسفانه مشکلی در نمایش دسته‌بندی‌ها پیش آمد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=get_back_button()
        )

@router.callback_query(F.data.startswith("plan_category:"))
async def show_plans_by_category(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handle the user selecting a plan category."""
    try:
        # Get category ID from callback data
        _, category_id = callback.data.split(":")
        
        # Store in state
        await state.update_data(selected_category_id=category_id)
        
        # Get plan service
        plan_service = PlanService(db=session)
        
        # Get plans for this category
        if category_id == "all":
            plans = await plan_service.get_active_plans()
            category_name = "همه پلن‌ها"
        else:
            plans = await plan_service.get_plans_by_category(int(category_id))
            category = await plan_service.get_category_by_id(int(category_id))
            category_name = category.name if category else "دسته انتخاب شده"
        
        # Build keyboard with plans
        keyboard = get_plans_keyboard(plans)
        
        # Set state
        await state.set_state(PurchaseStates.select_plan)
        
        # Respond to user
        await callback.message.edit_text(
            f"🛒 <b>دسته‌بندی: {category_name}</b>\n\n"
            "لطفاً یکی از پلن‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Answer callback to remove loading state
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing plans for category: {e}", exc_info=True)
        await callback.message.edit_text(
            "⚠️ متأسفانه مشکلی در نمایش پلن‌ها پیش آمد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=get_plan_categories_keyboard([])  # Empty fallback keyboard
        )
        await callback.answer("خطا در بارگیری پلن‌ها")

@router.callback_query(F.data.startswith("plan:"))
async def select_location(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handle the user selecting a plan."""
    try:
        # Get plan ID from callback data
        _, plan_id = callback.data.split(":")
        
        # Store in state
        await state.update_data(selected_plan_id=int(plan_id))
        
        # Get plan details
        plan_service = PlanService(db=session)
        plan = await plan_service.get_plan_by_id(int(plan_id))
        
        if not plan:
            await callback.message.edit_text(
                "⚠️ پلن انتخاب شده معتبر نیست. لطفاً دوباره تلاش کنید.",
                reply_markup=get_plan_categories_keyboard([])
            )
            await callback.answer("پلن نامعتبر")
            return
        
        # Store plan details in state
        await state.update_data(
            selected_plan_name=plan.name,
            selected_plan_price=plan.price,
            selected_plan_days=plan.days,
            selected_plan_data_limit=plan.data_limit
        )
        
        # Get locations
        location_service = LocationService(db=session)
        locations = await location_service.get_active_locations()
        
        # Build keyboard with locations
        keyboard = get_locations_keyboard(locations)
        
        # Set state
        await state.set_state(PurchaseStates.select_location)
        
        # Format plan details nicely
        data_limit_display = f"{plan.data_limit} گیگابایت" if plan.data_limit else "نامحدود"
        days_display = f"{plan.days} روز"
        price_display = f"{plan.price:,} تومان"
        
        # Respond to user
        await callback.message.edit_text(
            f"✅ <b>پلن {plan.name} انتخاب شد</b>\n\n"
            f"💰 قیمت: {price_display}\n"
            f"⏱ مدت: {days_display}\n"
            f"📊 حجم: {data_limit_display}\n\n"
            "🌎 لطفاً لوکیشن مورد نظر خود را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Answer callback to remove loading state
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in select_location: {e}", exc_info=True)
        await callback.message.edit_text(
            "⚠️ متأسفانه مشکلی در پردازش انتخاب شما پیش آمد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=get_plan_categories_keyboard([])
        )
        await callback.answer("خطا در پردازش")

# Additional handlers would continue the flow:
# - select_location -> show_order_summary
# - handle_discount_code
# - confirm_order -> process_payment
# These will be implemented in the next phase 