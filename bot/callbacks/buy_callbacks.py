"""
کالبک‌های مربوط به فرآیند خرید اشتراک
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from core.services.plan_service import PlanService
from core.services.order_service import OrderService
from core.services.payment_service import PaymentService
from core.services.location_service import LocationService
from core.services.inbound_service import InboundService

from bot.states.buy_states import BuyState
from bot.keyboards.buy_keyboards import (
    get_plans_keyboard,
    get_locations_keyboard,
    get_inbounds_keyboard,
    get_confirm_purchase_keyboard,
    get_payment_keyboard
)

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_buy_callbacks(router: Router):
    """ثبت callback handler های مربوط به فرایند خرید"""
    
    @router.callback_query(F.data.startswith("plan:"))
    async def plan_selected(callback: CallbackQuery, state: FSMContext):
        """
        انتخاب پلن توسط کاربر
        """
        plan_id = int(callback.data.split(":")[1])
        
        # ذخیره پلن انتخاب شده
        await state.update_data(plan_id=plan_id)
        
        # دریافت لیست لوکیشن‌های فعال
        locations = await LocationService.get_active_locations()
        
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

    @router.callback_query(F.data.startswith("location:"))
    async def location_selected(callback: CallbackQuery, state: FSMContext):
        """
        انتخاب لوکیشن توسط کاربر
        """
        location_id = int(callback.data.split(":")[1])
        
        # ذخیره لوکیشن انتخاب شده
        await state.update_data(location_id=location_id)
        
        # دریافت لیست پروتکل‌های فعال
        inbounds = await InboundService.get_active_inbounds()
        
        if not inbounds:
            await callback.message.edit_text(
                "⚠️ در حال حاضر هیچ پروتکلی فعال نیست.\n"
                "لطفا بعدا مجددا تلاش کنید."
            )
            return
        
        # نمایش لیست پروتکل‌ها
        await callback.message.edit_text(
            "🔒 لطفا پروتکل مورد نظر خود را انتخاب کنید:",
            reply_markup=get_inbounds_keyboard(inbounds)
        )
        
        await state.set_state(BuyState.select_inbound)

    @router.callback_query(F.data.startswith("inbound:"))
    async def inbound_selected(callback: CallbackQuery, state: FSMContext):
        """
        انتخاب پروتکل توسط کاربر
        """
        inbound_id = int(callback.data.split(":")[1])
        
        # ذخیره پروتکل انتخاب شده
        await state.update_data(inbound_id=inbound_id)
        
        # دریافت اطلاعات انتخاب شده
        data = await state.get_data()
        plan = await PlanService.get_plan(data["plan_id"])
        location = await LocationService.get_location(data["location_id"])
        inbound = await InboundService.get_inbound(inbound_id)
        
        # نمایش خلاصه سفارش
        await callback.message.edit_text(
            "📋 خلاصه سفارش شما:\n\n"
            f"پلن: {plan.name}\n"
            f"مدت: {plan.duration} روز\n"
            f"قیمت: {plan.price:,} تومان\n"
            f"لوکیشن: {location.name}\n"
            f"پروتکل: {inbound.name}\n\n"
            "آیا از انتخاب خود مطمئن هستید؟",
            reply_markup=get_confirm_purchase_keyboard()
        )
        
        await state.set_state(BuyState.confirm_purchase)

    @router.callback_query(F.data == "confirm_purchase")
    async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
        """
        تایید نهایی خرید
        """
        # دریافت اطلاعات سفارش
        data = await state.get_data()
        
        # ایجاد سفارش جدید
        order = await OrderService.create_order(
            user_id=callback.from_user.id,
            plan_id=data["plan_id"],
            location_id=data["location_id"],
            inbound_id=data["inbound_id"]
        )
        
        # نمایش روش‌های پرداخت
        await callback.message.edit_text(
            "💳 لطفا روش پرداخت را انتخاب کنید:",
            reply_markup=get_payment_keyboard(order.id)
        )
        
        await state.set_state(BuyState.payment)

    @router.callback_query(F.data.startswith("pay:"))
    async def process_payment(callback: CallbackQuery, state: FSMContext):
        """
        پردازش پرداخت
        """
        payment_method = callback.data.split(":")[1]
        order_id = int(callback.data.split(":")[2])
        
        # دریافت اطلاعات سفارش
        order = await OrderService.get_order(order_id)
        
        if payment_method == "bank":
            # ایجاد لینک پرداخت درگاه بانکی
            payment_url = await PaymentService.create_bank_payment(order)
            
            await callback.message.edit_text(
                "🏦 در حال انتقال به درگاه بانکی...\n"
                "لطفا صبر کنید."
            )
            
            # هدایت به درگاه پرداخت
            await callback.answer(url=payment_url)
            
        elif payment_method == "wallet":
            # پرداخت از کیف پول
            success = await PaymentService.process_wallet_payment(order)
            
            if success:
                await callback.message.edit_text(
                    "✅ پرداخت با موفقیت انجام شد.\n"
                    "اکانت شما به زودی فعال خواهد شد."
                )
            else:
                await callback.message.edit_text(
                    "❌ موجودی کیف پول شما کافی نیست.\n"
                    "لطفا ابتدا کیف پول خود را شارژ کنید."
                )
        
        await state.clear()

    @router.callback_query(F.data == "cancel_purchase")
    async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
        """
        لغو فرآیند خرید
        """
        await callback.message.edit_text(
            "❌ فرآیند خرید لغو شد."
        )
        await state.clear()

    @router.callback_query(F.data == "refresh_plans")
    async def refresh_plans(callback: CallbackQuery):
        """
        بروزرسانی لیست پلن‌ها
        """
        # دریافت لیست پلن‌های فعال
        plans = await PlanService.get_active_plans()
        
        if not plans:
            await callback.message.edit_text(
                "⚠️ در حال حاضر هیچ پلن فعالی موجود نیست.\n"
                "لطفا بعدا مجددا تلاش کنید."
            )
            return
        
        # نمایش لیست به‌روز شده پلن‌ها
        await callback.message.edit_text(
            "🛍 به فروشگاه MoonVPN خوش آمدید!\n\n"
            "لطفا یکی از پلن‌های زیر را انتخاب کنید:",
            reply_markup=get_plans_keyboard(plans)
        )

    @router.callback_query(F.data == "back_to_plans")
    async def back_to_plans(callback: CallbackQuery, state: FSMContext):
        """
        بازگشت به لیست پلن‌ها
        """
        await state.clear()
        await refresh_plans(callback)

    @router.callback_query(F.data == "back_to_locations")
    async def back_to_locations(callback: CallbackQuery, state: FSMContext):
        """
        بازگشت به لیست لوکیشن‌ها
        """
        # دریافت لیست لوکیشن‌های فعال
        locations = await LocationService.get_active_locations()
        
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