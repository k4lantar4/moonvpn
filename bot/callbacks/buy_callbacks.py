"""
کالبک‌های مربوط به فرآیند خرید اشتراک
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.services.plan_service import PlanService
from core.services.panel_service import PanelService
from core.services.location_service import LocationService
from core.services.inbound_service import InboundService
from core.services.order_service import OrderService
from core.services.user_service import UserService
from core.services.payment_service import PaymentService
from core.services.notification_service import NotificationService

from db.models.enums import OrderStatus

from bot.states.buy_states import BuyState
from bot.buttons.buy_buttons import (
    get_plans_keyboard, 
    get_location_selection_keyboard, 
    get_plan_selection_keyboard, 
    confirm_purchase_buttons, 
    get_payment_keyboard, 
    BUY_CB
)

# تنظیم لاگر
logger = logging.getLogger(__name__)

# تعریف هندلرهای کالبک خارج از تابع register_buy_callbacks
async def plan_selected(callback: CallbackQuery, state: FSMContext, session_pool):
    """انتخاب پلن توسط کاربر"""
    try:
        # استخراج شناسه پلن از دیتای کالبک
        parts = callback.data.split(":")
        if len(parts) < 3:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        plan_id = int(parts[2])
        
        # ذخیره پلن انتخاب شده
        await state.update_data(plan_id=plan_id)
        
        async with session_pool() as session:
            # بررسی وجود پلن
            plan_service = PlanService(session)
            plan = await plan_service.get_plan_by_id(plan_id)
            
            if not plan:
                logger.error(f"Selected plan ID {plan_id} not found")
                await callback.message.edit_text(
                    "❌ پلن انتخاب شده یافت نشد یا غیرفعال شده است.\n"
                    "لطفا مجددا تلاش کنید."
                )
                return
            
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
                f"🌍 پلن انتخابی: <b>{plan.name}</b>\n\n"
                "لطفا لوکیشن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_location_selection_keyboard(locations)
            )
            
            await state.set_state(BuyState.select_location)
            logger.info(f"User {callback.from_user.id} selected plan {plan_id} ({plan.name})")
            
    except ValueError as e:
        logger.error(f"Invalid plan ID in callback data: {callback.data}, error: {e}")
        await callback.answer("شناسه پلن نامعتبر است", show_alert=True)
    except Exception as e:
        logger.error(f"Error in plan selection: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # بازگشت به صفحه انتخاب پلن‌ها با نمایش خطا
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            await callback.message.edit_text(
                "❌ خطایی رخ داد. لطفا دوباره پلن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plans_keyboard(plans)
            )

async def location_selected(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    انتخاب لوکیشن توسط کاربر
    """
    try:
        # استخراج شناسه پنل از دیتای کالبک
        parts = callback.data.split(":")
        if len(parts) < 3:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        panel_id = int(parts[2])
        
        # ذخیره پنل انتخاب شده
        await state.update_data(panel_id=panel_id)
        
        # دریافت پلن آیدی از استیت
        user_data = await state.get_data()
        plan_id = user_data.get("plan_id")
        
        if not plan_id:
            logger.error(f"Plan ID not found in state for user {callback.from_user.id}")
            await callback.answer("خطا: پلن انتخاب نشده است", show_alert=True)
            return
        
        async with session_pool() as session:
            # بررسی وجود پنل
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not panel:
                logger.error(f"Selected panel ID {panel_id} not found")
                await callback.message.edit_text(
                    "❌ لوکیشن انتخاب شده یافت نشد یا غیرفعال شده است.\n"
                    "لطفا مجددا تلاش کنید."
                )
                return
            
            # دریافت لیست inbound‌های فعال پنل
            inbound_service = InboundService(session)
            inbounds = await inbound_service.get_inbounds_by_panel_id(panel_id)
            
            if not inbounds:
                # بازگشت به صفحه انتخاب لوکیشن
                location_service = LocationService(session)
                locations = await location_service.get_available_locations()
                await callback.message.edit_text(
                    f"⚠️ هیچ پروتکلی برای لوکیشن {panel.location} موجود نیست.\n"
                    "لطفا لوکیشن دیگری انتخاب کنید.",
                    reply_markup=get_location_selection_keyboard(locations)
                )
                return
            
            # نمایش لیست inbound‌ها
            await callback.message.edit_text(
                f"🔌 لوکیشن انتخابی: <b>{panel.flag_emoji} {panel.location}</b>\n\n"
                "لطفا پروتکل مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plan_selection_keyboard(inbounds, panel_id, plan_id)
            )
            
            await state.set_state(BuyState.select_inbound)
            logger.info(f"User {callback.from_user.id} selected location {panel_id} ({panel.location})")
            
    except ValueError as e:
        logger.error(f"Invalid panel ID in callback data: {callback.data}, error: {e}")
        await callback.answer("شناسه لوکیشن نامعتبر است", show_alert=True)
    except Exception as e:
        logger.error(f"Error in location selection: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # بازگشت به صفحه انتخاب پلن با نمایش خطا
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            await callback.message.edit_text(
                "❌ خطایی رخ داد. لطفا دوباره از ابتدا شروع کنید:",
                reply_markup=get_plans_keyboard(plans)
            )

async def inbound_selected(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    انتخاب inbound توسط کاربر
    """
    try:
        # استخراج اطلاعات از callback data
        parts = callback.data.split(":")
        if len(parts) < 5:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        plan_id = int(parts[2])
        panel_id = int(parts[3])
        inbound_id = int(parts[4])
        
        # ذخیره اطلاعات انتخاب شده
        await state.update_data(plan_id=plan_id, panel_id=panel_id, inbound_id=inbound_id)
        
        async with session_pool() as session:
            # دریافت اطلاعات پلن و پنل
            plan_service = PlanService(session)
            panel_service = PanelService(session)
            inbound_service = InboundService(session)
            
            plan = await plan_service.get_plan_by_id(plan_id)
            panel = await panel_service.get_panel_by_id(panel_id)
            inbound = await inbound_service.get_inbound(inbound_id)
            
            if not all([plan, panel, inbound]):
                logger.error(f"One or more entities not found: Plan {plan_id}, Panel {panel_id}, Inbound {inbound_id}")
                await callback.message.edit_text(
                    "❌ خطا در دریافت اطلاعات. یکی از موارد انتخابی یافت نشد یا تغییر کرده است.\n"
                    "لطفا دوباره تلاش کنید."
                )
                return
            
            # نمایش خلاصه سفارش
            summary = (
                "📋 خلاصه سفارش شما:\n\n"
                f"🔹 پلن: {plan.name}\n"
            )
            
            # اضافه کردن مدت اعتبار اگر موجود است
            if hasattr(plan, 'duration_days') and plan.duration_days:
                summary += f"🔹 مدت: {plan.duration_days} روز\n"
            
            # اضافه کردن حجم ترافیک اگر موجود است
            if hasattr(plan, 'traffic_gb') and plan.traffic_gb:
                summary += f"🔹 حجم: {plan.traffic_gb} گیگابایت\n"
            
            # اضافه کردن قیمت
            if hasattr(plan, 'price'):
                price_display = f"{int(plan.price):,} تومان" if plan.price else "رایگان"
                summary += f"🔹 قیمت: {price_display}\n"
            
            # اضافه کردن اطلاعات لوکیشن
            flag_emoji = getattr(panel, 'flag_emoji', '🏴')
            location_name = getattr(panel, 'location', 'نامشخص')
            summary += f"🔹 لوکیشن: {flag_emoji} {location_name}\n"
            
            # اضافه کردن اطلاعات پروتکل
            protocol = getattr(inbound, 'protocol', 'نامشخص').upper()
            port = getattr(inbound, 'port', 'نامشخص')
            summary += f"🔹 پروتکل: {protocol} - پورت {port}\n\n"
            
            summary += "آیا از انتخاب خود مطمئن هستید؟"
            
            # دکمه‌های تایید یا بازگشت
            await callback.message.edit_text(
                summary, 
                reply_markup=confirm_purchase_buttons(plan_id, panel_id, inbound_id)
            )
            
            await state.set_state(BuyState.confirm_purchase)
            logger.info(f"User {callback.from_user.id} selected inbound {inbound_id} (Protocol: {protocol})")
            
    except ValueError as e:
        logger.error(f"Invalid ID values in callback data: {callback.data}, error: {e}")
        await callback.answer("مقادیر شناسه نامعتبر است", show_alert=True)
    except Exception as e:
        logger.error(f"Error in inbound selection: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # بازگشت به حالت انتخاب پلن با نمایش خطا
        await back_to_plans(callback, state, session_pool)

async def confirm_purchase(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    تایید نهایی خرید
    """
    try:
        # استخراج اطلاعات از callback data
        parts = callback.data.split(":")
        if len(parts) < 5:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        plan_id = int(parts[2])
        panel_id = int(parts[3])
        inbound_id = int(parts[4])
        
        # ذخیره اطلاعات انتخاب شده (برای اطمینان)
        await state.update_data(plan_id=plan_id, panel_id=panel_id, inbound_id=inbound_id)
        
        async with session_pool() as session:
            # دریافت اطلاعات پلن برای تعیین قیمت
            plan_service = PlanService(session)
            panel_service = PanelService(session)
            plan = await plan_service.get_plan_by_id(plan_id)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not plan or not panel:
                logger.error(f"Plan {plan_id} or Panel {panel_id} not found during purchase confirmation")
                await callback.message.edit_text(
                    "❌ خطا: پلن یا لوکیشن انتخابی یافت نشد.\n"
                    "لطفا دوباره انتخاب کنید."
                )
                return
            
            # ایجاد سفارش جدید
            order_service = OrderService(session)
            
            order = await order_service.create_order(
                user_id=callback.from_user.id,
                plan_id=plan_id,
                location_name=panel.location,
                amount=plan.price
            )
            
            if not order:
                logger.error(f"Failed to create order for user {callback.from_user.id}")
                await callback.message.edit_text(
                    "❌ خطا در ایجاد سفارش.\n"
                    "لطفا بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
                return
            
            # ذخیره اطلاعات اضافی در استیت
            await state.update_data(order_id=order.id, inbound_id=inbound_id, panel_id=panel_id)
            
            # نمایش روش‌های پرداخت
            await callback.message.edit_text(
                f"💳 لطفا روش پرداخت را انتخاب کنید:\n\n"
                f"🔹 شناسه سفارش: {order.id}\n"
                f"🔹 مبلغ قابل پرداخت: {int(order.amount):,} تومان",
                reply_markup=get_payment_keyboard(str(order.id))
            )
            
            await state.set_state(BuyState.payment)
            logger.info(f"User {callback.from_user.id} confirmed purchase, order {order.id} created")
            
    except ValueError as e:
        logger.error(f"Invalid ID values in callback data: {callback.data}, error: {e}")
        await callback.answer("مقادیر شناسه نامعتبر است", show_alert=True)
    except Exception as e:
        logger.error(f"Error in purchase confirmation: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # بازگشت به حالت انتخاب پلن با نمایش خطا
        await state.clear()
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            await callback.message.edit_text(
                "❌ خطایی در فرآیند خرید رخ داد. لطفا مجددا تلاش کنید:",
                reply_markup=get_plans_keyboard(plans)
            )

async def handle_payment_method(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    پردازش انتخاب روش پرداخت
    """
    try:
        # استخراج اطلاعات از callback data
        parts = callback.data.split(":")
        if len(parts) < 4:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        payment_method = parts[2]
        order_id = parts[3]
        
        logger.info(f"User {callback.from_user.id} selected payment method: {payment_method} for order {order_id}")
        
        if payment_method == "wallet":
            # پرداخت از کیف پول
            async with session_pool() as session:
                order_service = OrderService(session)
                success, message = await order_service.attempt_payment_from_wallet(int(order_id))
                
                if success:
                    await callback.message.edit_text(
                        "✅ پرداخت از کیف پول با موفقیت انجام شد.\n"
                        "در حال آماده‌سازی سرویس شما هستیم..."
                    )
                    await state.clear()
                else:
                    await callback.answer(message, show_alert=True)
                    
        elif payment_method == "online":
            # پرداخت آنلاین
            await callback.message.edit_text(
                "⏳ در حال انتقال به درگاه پرداخت...\n"
                "لطفا چند لحظه صبر کنید."
            )
            
            try:
                # نمایش لینک پرداخت (در نسخه واقعی باید از سرویس پرداخت استفاده شود)
                async with session_pool() as session:
                    payment_service = PaymentService(session)
                    payment_url = await payment_service.generate_payment_link(int(order_id))
                    
                    if payment_url:
                        # ایجاد دکمه برای هدایت به صفحه پرداخت
                        buttons = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💳 انتقال به درگاه پرداخت", url=payment_url)],
                            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=BUY_CB["PAYMENT_METHOD"].format("back", order_id))]
                        ])
                        
                        await callback.message.edit_text(
                            "💳 برای پرداخت آنلاین روی دکمه زیر کلیک کنید:",
                            reply_markup=buttons
                        )
                    else:
                        raise Exception("Failed to generate payment URL")
                        
            except Exception as e:
                logger.error(f"Error in online payment: {e}")
                # نمایش پیام خطا
                await callback.message.edit_text(
                    "🔄 درگاه پرداخت در حال حاضر در دسترس نیست.\n"
                    "لطفا بعدا مجددا تلاش کنید یا از روش دیگری استفاده کنید.",
                    reply_markup=get_payment_keyboard(order_id)
                )
            
        elif payment_method == "card":
            # پرداخت کارت به کارت
            async with session_pool() as session:
                payment_service = PaymentService(session)
                card_info = await payment_service.get_card_info()
                
                if card_info:
                    card_number = card_info.get("card_number", "اطلاعات موجود نیست")
                    card_holder = card_info.get("card_holder", "اطلاعات موجود نیست")
                    
                    # دکمه‌های تایید پرداخت و بازگشت
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ پرداخت را انجام دادم", callback_data=f"payment_done:{order_id}")],
                        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=BUY_CB["PAYMENT_METHOD"].format("back", order_id))]
                    ])
                    
                    await callback.message.edit_text(
                        f"💳 اطلاعات کارت برای واریز:\n\n"
                        f"📝 شماره کارت: <code>{card_number}</code>\n"
                        f"👤 به نام: {card_holder}\n\n"
                        f"💰 مبلغ: طبق فاکتور (تراکنش را با مبلغ دقیق انجام دهید)\n"
                        f"🔢 شناسه سفارش: <code>{order_id}</code>\n\n"
                        "⚠️ پس از واریز، گزینه «پرداخت را انجام دادم» را انتخاب کنید.",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        "❌ اطلاعات کارت مقصد موجود نیست.\n"
                        "لطفا روش دیگری را انتخاب کنید یا با پشتیبانی تماس بگیرید.",
                        reply_markup=get_payment_keyboard(order_id)
                    )
        elif payment_method == "back":
            # بازگشت به صفحه روش‌های پرداخت
            await callback.message.edit_text(
                f"💳 لطفا روش پرداخت را انتخاب کنید:",
                reply_markup=get_payment_keyboard(order_id)
            )
        else:
            logger.warning(f"Unknown payment method: {payment_method}")
            await callback.answer("روش پرداخت نامعتبر است", show_alert=True)
            await callback.message.edit_text(
                "❌ روش پرداخت انتخابی معتبر نیست.\n"
                "لطفا یکی از روش‌های زیر را انتخاب کنید:",
                reply_markup=get_payment_keyboard(order_id)
            )
            
    except ValueError as e:
        logger.error(f"Invalid order ID in payment: {callback.data}, error: {e}")
        await callback.answer("شناسه سفارش نامعتبر است", show_alert=True)
    except Exception as e:
        logger.error(f"Error in payment method handling: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست پرداخت", show_alert=True)
        # بازگشت به صفحه انتخاب روش پرداخت
        try:
            await callback.message.edit_text(
                "❌ خطایی در فرآیند پرداخت رخ داد.\n"
                "لطفا دوباره روش پرداخت را انتخاب کنید:",
                reply_markup=get_payment_keyboard(parts[3] if len(parts) >= 4 else "unknown")
            )
        except Exception:
            # در صورت خطای بیشتر، برگشت به صفحه اصلی
            await back_to_plans(callback, state, session_pool)

async def back_to_plans(callback: CallbackQuery, state: FSMContext, session_pool):
    """بازگشت به لیست پلن‌ها"""
    try:
        # پاک کردن داده‌های قبلی
        await state.clear()
        
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            
            if not plans:
                await callback.message.edit_text(
                    "هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.\n"
                    "دستور /start را برای بازگشت به منوی اصلی وارد کنید."
                )
                return
            
            # دریافت موجودی کیف پول کاربر
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            balance_message = ""
            if user and hasattr(user, 'balance'):
                balance_message = f"💰 موجودی کیف پول شما: {int(user.balance):,} تومان\n\n"
            
            await callback.message.edit_text(
                balance_message + "🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plans_keyboard(plans)
            )
            
            await state.set_state(BuyState.select_plan)
            logger.info(f"User {callback.from_user.id} navigated back to plans list")
            
    except Exception as e:
        logger.error(f"Error in back to plans: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # تلاش مجدد برای بازگشت به منوی اصلی در صورت خطا
        await callback.message.edit_text("خطایی رخ داد. به منوی اصلی منتقل می‌شوید...")
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await callback.message.edit_text(
            "🏠 منوی اصلی",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 شروع مجدد", callback_data="start")
            ]])
        )

async def back_to_locations(callback: CallbackQuery, state: FSMContext, session_pool):
    """بازگشت به لیست لوکیشن‌ها"""
    try:
        # استخراج پلن آیدی از کالبک دیتا
        parts = callback.data.split(":")
        if len(parts) < 3:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        plan_id = int(parts[2])
        
        # ذخیره پلن انتخاب شده
        await state.update_data(plan_id=plan_id)
        
        async with session_pool() as session:
            # دریافت اطلاعات پلن
            plan_service = PlanService(session)
            plan = await plan_service.get_plan_by_id(plan_id)
            
            if not plan:
                logger.error(f"Plan {plan_id} not found during back navigation")
                await callback.answer("پلن مورد نظر یافت نشد", show_alert=True)
                await back_to_plans(callback, state, session_pool)
                return
            
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
                f"🌍 پلن انتخابی: <b>{plan.name}</b>\n\n"
                "لطفا لوکیشن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_location_selection_keyboard(locations)
            )
            
            await state.set_state(BuyState.select_location)
            logger.info(f"User {callback.from_user.id} navigated back to locations list")
            
    except ValueError as e:
        logger.error(f"Invalid plan ID in callback data: {callback.data}, error: {e}")
        await callback.answer("شناسه پلن نامعتبر است", show_alert=True)
        await back_to_plans(callback, state, session_pool)
    except Exception as e:
        logger.error(f"Error in back to locations: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        await back_to_plans(callback, state, session_pool)

async def back_to_inbounds(callback: CallbackQuery, state: FSMContext, session_pool):
    """بازگشت به لیست inbound‌ها"""
    try:
        # استخراج اطلاعات از callback data
        parts = callback.data.split(":")
        if len(parts) < 4:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("فرمت داده نامعتبر است", show_alert=True)
            return
            
        plan_id = int(parts[2])
        panel_id = int(parts[3])
        
        # ذخیره اطلاعات در state
        await state.update_data(plan_id=plan_id, panel_id=panel_id)
        
        async with session_pool() as session:
            # بررسی وجود پلن و پنل
            plan_service = PlanService(session)
            panel_service = PanelService(session)
            inbound_service = InboundService(session)
            
            plan = await plan_service.get_plan_by_id(plan_id)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not plan or not panel:
                logger.error(f"Plan {plan_id} or Panel {panel_id} not found during back navigation")
                await callback.answer("پلن یا لوکیشن مورد نظر یافت نشد", show_alert=True)
                await back_to_plans(callback, state, session_pool)
                return
            
            # دریافت لیست inbound‌های فعال پنل
            inbounds = await inbound_service.get_inbounds_by_panel_id(panel_id)
            
            if not inbounds:
                # بازگشت به صفحه انتخاب لوکیشن‌ها با پیام خطا
                location_service = LocationService(session)
                locations = await location_service.get_available_locations()
                await callback.message.edit_text(
                    f"⚠️ هیچ پروتکلی برای لوکیشن {panel.location} موجود نیست.\n"
                    "لطفا لوکیشن دیگری انتخاب کنید.",
                    reply_markup=get_location_selection_keyboard(locations)
                )
                await state.set_state(BuyState.select_location)
                return
            
            # نمایش لیست inbound‌ها
            await callback.message.edit_text(
                f"🔌 لوکیشن انتخابی: <b>{panel.flag_emoji} {panel.location}</b>\n\n"
                "لطفا پروتکل مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plan_selection_keyboard(inbounds, panel_id, plan_id)
            )
            
            await state.set_state(BuyState.select_inbound)
            logger.info(f"User {callback.from_user.id} navigated back to inbounds list")
            
    except ValueError as e:
        logger.error(f"Invalid ID values in callback data: {callback.data}, error: {e}")
        await callback.answer("مقادیر شناسه نامعتبر است", show_alert=True)
        await back_to_plans(callback, state, session_pool)
    except Exception as e:
        logger.error(f"Error in back to inbounds: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        await back_to_plans(callback, state, session_pool)

async def refresh_plans(callback: CallbackQuery, state: FSMContext, session_pool):
    """بروزرسانی لیست پلن‌ها"""
    try:
        await state.clear()
        await back_to_plans(callback, state, session_pool)
        logger.info(f"User {callback.from_user.id} refreshed plans list")
    except Exception as e:
        logger.error(f"Error in refresh plans: {e}", exc_info=True)
        await callback.answer("خطا در بروزرسانی لیست", show_alert=True)

async def cancel_payment(callback: CallbackQuery, state: FSMContext, session_pool):
    """انصراف از پرداخت"""
    try:
        # دریافت اطلاعات سفارش
        user_data = await state.get_data()
        order_id = user_data.get("order_id")
        
        # اگر سفارش موجود باشد، اطلاع‌رسانی کنیم
        if order_id:
            async with session_pool() as session:
                notification_service = NotificationService(session)
                await notification_service.notify_admin(
                    f"💸 انصراف از پرداخت:\n"
                    f"👤 کاربر: {callback.from_user.id}\n"
                    f"🔢 شناسه سفارش: #{order_id}"
                )
        
        await callback.message.edit_text(
            "❌ سفارش لغو شد.\n"
            "برای شروع مجدد می‌توانید از دستور /buy استفاده کنید."
        )
        await state.clear()
        logger.info(f"User {callback.from_user.id} canceled the payment process for order {order_id if order_id else 'Unknown'}")
    except Exception as e:
        logger.error(f"Error in cancel payment: {e}", exc_info=True)
        await callback.answer("خطا در لغو پرداخت", show_alert=True)

def register_buy_callbacks(router: Router, session_pool):
    """ثبت callback handler های مربوط به فرایند خرید"""
    
    # Plan selection handlers
    @router.callback_query(F.data.startswith("buy:plan:"))
    async def _plan_selected_wrapper(callback: CallbackQuery, state: FSMContext):
        await plan_selected(callback, state, session_pool)
    
    # Location selection handlers
    @router.callback_query(F.data.startswith("buy:loc:"))
    async def _location_selected_wrapper(callback: CallbackQuery, state: FSMContext):
        await location_selected(callback, state, session_pool)
    
    # Inbound selection handlers
    @router.callback_query(F.data.startswith("buy:inb:"))
    async def _inbound_selected_wrapper(callback: CallbackQuery, state: FSMContext):
        await inbound_selected(callback, state, session_pool)
    
    # Purchase confirmation handlers
    @router.callback_query(F.data.startswith("buy:confirm:"))
    async def _confirm_purchase_wrapper(callback: CallbackQuery, state: FSMContext):
        await confirm_purchase(callback, state, session_pool)
    
    # Payment method handlers
    @router.callback_query(F.data.startswith("buy:pay:"))
    async def _handle_payment_method_wrapper(callback: CallbackQuery, state: FSMContext):
        await handle_payment_method(callback, state, session_pool)
    
    # Back/navigation handlers
    @router.callback_query(F.data == BUY_CB["BACK_TO_PLANS"])
    async def _back_to_plans_wrapper(callback: CallbackQuery, state: FSMContext):
        await back_to_plans(callback, state, session_pool)
    
    @router.callback_query(F.data.startswith("buy:back:loc:"))
    async def _back_to_locations_wrapper(callback: CallbackQuery, state: FSMContext):
        await back_to_locations(callback, state, session_pool)
    
    @router.callback_query(F.data.startswith("buy:back:inb:"))
    async def _back_to_inbounds_wrapper(callback: CallbackQuery, state: FSMContext):
        await back_to_inbounds(callback, state, session_pool)
    
    # Refresh handlers
    @router.callback_query(F.data == BUY_CB["REFRESH_PLANS"])
    async def _refresh_plans_wrapper(callback: CallbackQuery, state: FSMContext):
        await refresh_plans(callback, state, session_pool)
    
    # Cancel handlers
    @router.callback_query(F.data == BUY_CB["CANCEL_PAYMENT"])
    async def _cancel_payment_wrapper(callback: CallbackQuery, state: FSMContext):
        await cancel_payment(callback, state, session_pool) 