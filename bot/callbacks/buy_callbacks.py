"""
کالبک‌های مربوط به فرآیند خرید اشتراک
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from core.services.plan_service import PlanService
from core.services.panel_service import PanelService
from core.services.location_service import LocationService
from core.services.inbound_service import InboundService

from bot.states.buy_states import BuyState
from bot.keyboards.buy_keyboards import get_locations_keyboard, get_plans_keyboard
from bot.buttons.inbound_buttons import get_inbounds_keyboard

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_buy_callbacks(router: Router, session_pool):
    """ثبت callback handler های مربوط به فرایند خرید"""
    
    @router.callback_query(F.data.startswith("select_plan:"))
    async def plan_selected(callback: CallbackQuery, state: FSMContext):
        """انتخاب پلن توسط کاربر"""
        try:
            plan_id = int(callback.data.split(":")[1])
            # ذخیره پلن انتخاب شده
            await state.update_data(plan_id=plan_id)
            async with session_pool() as session:
                # دریافت لیست لوکیشن‌های فعال از سرویس لوکیشن
                location_service = LocationService(session)
                locations = await location_service.get_available_locations()
                if not locations:
                    await callback.message.edit_text(
                        "⚠️ در حال حاضر هیچ لوکیشن فعالی موجود نیست.\n"
                        "لطفا بعدا مجددا تلاش کنید."
                    )
                    return
                # نمایش لیست لوکیشن‌ها
                await callback.message.edit_text(
                    "🌍 لطفا لوکیشن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_locations_keyboard(locations)
                )
                await state.set_state(BuyState.select_location)
        except Exception as e:
            logger.error(f"Error in plan selection: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)

    @router.callback_query(F.data.startswith("select_location:"))
    async def location_selected(callback: CallbackQuery, state: FSMContext):
        """
        انتخاب لوکیشن توسط کاربر
        """
        try:
            panel_id = int(callback.data.split(":")[1])
            
            # ذخیره پنل انتخاب شده
            await state.update_data(panel_id=panel_id)
            
            async with session_pool() as session:
                # دریافت لیست inbound‌های فعال پنل
                inbound_service = InboundService(session)
                inbounds = await inbound_service.get_active_inbounds()
                
                if not inbounds:
                    await callback.message.edit_text(
                        "⚠️ فعلاً اینباندی موجود نیست."
                    )
                    return
                
                # نمایش لیست inbound‌ها
                data = await state.get_data()
                await callback.message.edit_text(
                    "🔌 لطفا پروتکل مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_inbounds_keyboard(inbounds, panel_id, data["plan_id"])
                )
                
                await state.set_state(BuyState.select_inbound)
                
        except Exception as e:
            logger.error(f"Error in location selection: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)

    @router.callback_query(F.data.startswith("select_inbound:"))
    async def inbound_selected(callback: CallbackQuery, state: FSMContext):
        """
        انتخاب inbound توسط کاربر
        """
        try:
            # دریافت اطلاعات از callback data
            _, plan_id, panel_id, inbound_id = callback.data.split(":")
            plan_id = int(plan_id)
            panel_id = int(panel_id)
            inbound_id = int(inbound_id)
            
            # ذخیره اطلاعات انتخاب شده
            await state.update_data(inbound_id=inbound_id)
            
            async with session_pool() as session:
                # دریافت اطلاعات پلن و پنل
                plan_service = PlanService(session)
                panel_service = PanelService(session)
                inbound_service = InboundService(session)
                
                plan = await plan_service.get_plan_by_id(plan_id)
                panel = await panel_service.get_panel_by_id(panel_id)
                inbound = await inbound_service.get_inbound(inbound_id)
                
                if not all([plan, panel, inbound]):
                    await callback.message.edit_text(
                        "❌ خطا در دریافت اطلاعات. لطفا دوباره تلاش کنید."
                    )
                    return
                
                # نمایش خلاصه سفارش
                summary = (
                    "📋 خلاصه سفارش شما:\n\n"
                    f"🔹 پلن: {plan.name}\n"
                    f"🔹 مدت: {plan.duration_days} روز\n"
                    f"🔹 حجم: {plan.traffic_gb} گیگابایت\n"
                    f"🔹 قیمت: {int(plan.price):,} تومان\n"
                    f"🔹 لوکیشن: {panel.flag_emoji} {panel.location_name}\n"
                    f"🔹 پروتکل: {inbound.protocol.upper()} - پورت {inbound.port}\n\n"
                    "آیا از انتخاب خود مطمئن هستید؟"
                )
                
                # دکمه‌های تایید یا بازگشت
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ تایید و ادامه", callback_data="confirm_purchase")],
                    [InlineKeyboardButton(text="🔙 بازگشت به انتخاب پروتکل", callback_data=f"back_to_inbounds:{plan_id}:{panel_id}")]
                ])
                
                await callback.message.edit_text(summary, reply_markup=keyboard)
                await state.set_state(BuyState.confirm_purchase)
                
        except Exception as e:
            logger.error(f"Error in inbound selection: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)

    @router.callback_query(F.data == "confirm_purchase")
    async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
        """
        تایید نهایی خرید
        """
        try:
            # دریافت اطلاعات ذخیره شده
            data = await state.get_data()
            
            async with session_pool() as session:
                # ایجاد سفارش جدید
                from core.services.order_service import OrderService
                order_service = OrderService(session)
                
                order = await order_service.create_order(
                    user_id=callback.from_user.id,
                    plan_id=data["plan_id"],
                    panel_id=data["panel_id"],
                    inbound_id=data["inbound_id"]
                )
                
                # نمایش روش‌های پرداخت
                from bot.buttons.buy_buttons import get_payment_keyboard
                await callback.message.edit_text(
                    f"💳 لطفا روش پرداخت را انتخاب کنید:\n\n"
                    f"🔹 شناسه سفارش: {order.id}\n"
                    f"🔹 مبلغ قابل پرداخت: {int(order.amount):,} تومان",
                    reply_markup=get_payment_keyboard(str(order.id))
                )
                
                await state.set_state(BuyState.payment)
                
        except Exception as e:
            logger.error(f"Error in purchase confirmation: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)

    # Back buttons
    @router.callback_query(F.data == "back_to_plans")
    async def back_to_plans(callback: CallbackQuery, state: FSMContext):
        """بازگشت به لیست پلن‌ها"""
        try:
            async with session_pool() as session:
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    await callback.message.edit_text("هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.")
                    return
                
                await callback.message.edit_text(
                    "🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                await state.set_state(BuyState.select_plan)
                
        except Exception as e:
            logger.error(f"Error in back to plans: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)

    @router.callback_query(F.data.startswith("back_to_locations:"))
    async def back_to_locations(callback: CallbackQuery, state: FSMContext):
        """بازگشت به لیست لوکیشن‌ها"""
        try:
            plan_id = int(callback.data.split(":")[1])
            # ذخیره پلن انتخاب شده
            await state.update_data(plan_id=plan_id)
            async with session_pool() as session:
                # دریافت لیست لوکیشن‌های فعال از سرویس لوکیشن
                location_service = LocationService(session)
                locations = await location_service.get_available_locations()
                if not locations:
                    await callback.message.edit_text(
                        "⚠️ در حال حاضر هیچ لوکیشن فعالی موجود نیست.\n"
                        "لطفا بعدا مجددا تلاش کنید."
                    )
                    return
                # نمایش لیست لوکیشن‌ها
                await callback.message.edit_text(
                    "🌍 لطفا لوکیشن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_locations_keyboard(locations)
                )
                await state.set_state(BuyState.select_location)
        except Exception as e:
            logger.error(f"Error in back to locations: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)

    @router.callback_query(F.data.startswith("back_to_inbounds:"))
    async def back_to_inbounds(callback: CallbackQuery, state: FSMContext):
        """بازگشت به لیست inbound‌ها"""
        try:
            _, plan_id, panel_id = callback.data.split(":")
            plan_id = int(plan_id)
            panel_id = int(panel_id)
            
            await state.update_data(plan_id=plan_id, panel_id=panel_id)
            
            async with session_pool() as session:
                inbound_service = InboundService(session)
                inbounds = await inbound_service.get_active_inbounds()
                
                await callback.message.edit_text(
                    "🔌 لطفا پروتکل مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_inbounds_keyboard(inbounds, panel_id, plan_id)
                )
                
                await state.set_state(BuyState.select_inbound)
                
        except Exception as e:
            logger.error(f"Error in back to inbounds: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True) 