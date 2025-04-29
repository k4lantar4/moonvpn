"""
کالبک‌های مربوط به فرآیند خرید اشتراک
"""

import logging
import json
from datetime import datetime
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
from core.services.settings_service import SettingsService

from db.models.enums import OrderStatus

from bot.states.buy_states import BuyState
from bot.buttons.buy_buttons import (
    get_plans_keyboard, 
    get_location_selection_keyboard, 
    get_plan_selection_keyboard, 
    confirm_purchase_buttons, 
    get_payment_keyboard,
    get_payment_status_keyboard,
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
            # بررسی وجود پلن با استفاده از سرویس پلن
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
                logger.warning(f"No active locations available for user {callback.from_user.id}")
                await callback.message.edit_text(
                    "⚠️ در حال حاضر هیچ لوکیشن فعالی موجود نیست.\n"
                    "لطفا بعدا مجددا تلاش کنید."
                )
                return
                
            # نمایش لیست لوکیشن‌ها با کیبورد ایمن
            await callback.message.edit_text(
                f"🌍 پلن انتخابی: <b>{plan.name}</b>\n\n"
                f"💰 قیمت: {int(plan.price):,} تومان\n"
                f"⏱ مدت: {getattr(plan, 'duration_days', 'نامشخص')} روز\n"
                f"📊 حجم: {getattr(plan, 'traffic_gb', 'نامشخص')} گیگابایت\n\n"
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
            # بررسی وجود پنل با استفاده از سرویس پنل
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not panel:
                logger.error(f"Selected panel ID {panel_id} not found")
                await callback.message.edit_text(
                    "❌ لوکیشن انتخاب شده یافت نشد یا غیرفعال شده است.\n"
                    "لطفا مجددا تلاش کنید."
                )
                return
            
            # دریافت لیست inbound‌های فعال پنل با استفاده از سرویس اینباند
            inbound_service = InboundService(session)
            inbounds = await inbound_service.get_inbounds_by_panel_id(panel_id)
            
            if not inbounds:
                logger.warning(f"No active inbounds available for panel {panel_id}")
                # بازگشت به صفحه انتخاب لوکیشن
                location_service = LocationService(session)
                locations = await location_service.get_available_locations()
                await callback.message.edit_text(
                    f"⚠️ هیچ پروتکلی برای لوکیشن {panel.location_name} موجود نیست.\n"
                    "لطفا لوکیشن دیگری انتخاب کنید.",
                    reply_markup=get_location_selection_keyboard(locations)
                )
                return
            
            # دریافت اطلاعات پلن برای نمایش در پیام
            plan_service = PlanService(session)
            plan = await plan_service.get_plan_by_id(plan_id)
            
            plan_info = ""
            if plan:
                plan_info = f"🔹 پلن: {plan.name}\n"
            
            # نمایش لیست inbound‌ها با کیبورد ایمن
            await callback.message.edit_text(
                f"🔘 مرحله انتخاب پروتکل\n\n"
                f"{plan_info}"
                f"🔹 لوکیشن: {panel.flag_emoji} {panel.location_name}\n\n"
                "لطفا پروتکل مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plan_selection_keyboard(inbounds, panel_id, plan_id)
            )
            
            await state.set_state(BuyState.select_inbound)
            logger.info(f"User {callback.from_user.id} selected location {panel_id} ({panel.location_name})")
            
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
    انتخاب inbound توسط کاربر و نمایش جزئیات اکانت + دکمه پرداخت
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
            # دریافت اطلاعات پلن، پنل و اینباند با استفاده از سرویس‌ها
            plan_service = PlanService(session)
            panel_service = PanelService(session)
            inbound_service = InboundService(session)
            user_service = UserService(session)
            order_service = OrderService(session)
            
            plan = await plan_service.get_plan_by_id(plan_id)
            panel = await panel_service.get_panel_by_id(panel_id)
            inbound = await inbound_service.get_inbound(inbound_id)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not all([plan, panel, inbound, user]):
                missing = []
                if not plan:
                    missing.append("پلن")
                if not panel:
                    missing.append("لوکیشن")
                if not inbound:
                    missing.append("پروتکل")
                if not user:
                    missing.append("کاربر")
                logger.error(f"One or more entities not found: Plan {plan_id}, Panel {panel_id}, Inbound {inbound_id}, User {callback.from_user.id}")
                await callback.message.edit_text(
                    f"❌ خطا در دریافت اطلاعات. {', '.join(missing)} انتخابی یافت نشد یا تغییر کرده است.\n"
                    "لطفا دوباره تلاش کنید."
                )
                return
            
            # ایجاد سفارش با وضعیت PENDING
            order = await order_service.create_order(
                user_id=user.id,
                plan_id=plan_id,
                location_name=panel.location_name,
                amount=plan.price,
                status=OrderStatus.PENDING
            )
            if not order:
                logger.error(f"Failed to create order for user {user.id}")
                await callback.message.edit_text(
                    "❌ خطا در ایجاد سفارش.\n"
                    "لطفا دوباره تلاش کنید."
                )
                return
            await state.update_data(order_id=order.id)
            
            # نمایش خلاصه سفارش با اطلاعات کامل
            summary = (
                "📋 خلاصه سفارش شما:\n\n"
                f"🔹 پلن: {plan.name}\n"
            )
            if hasattr(plan, 'duration_days') and plan.duration_days:
                summary += f"🔹 مدت: {plan.duration_days} روز\n"
            if hasattr(plan, 'traffic_gb') and plan.traffic_gb:
                summary += f"🔹 حجم: {plan.traffic_gb} گیگابایت\n"
            if hasattr(plan, 'price'):
                price_display = f"{int(plan.price):,} تومان" if plan.price else "رایگان"
                summary += f"🔹 قیمت: {price_display}\n"
            flag_emoji = getattr(panel, 'flag_emoji', '🏴')
            location_name = getattr(panel, 'location_name', 'نامشخص')
            summary += f"🔹 لوکیشن: {flag_emoji} {location_name}\n"
            protocol = getattr(inbound, 'protocol', 'نامشخص').upper()
            port = getattr(inbound, 'port', 'نامشخص')
            summary += f"🔹 پروتکل: {protocol} - پورت {port}\n\n"
            summary += f"🔹 شناسه سفارش: <code>{order.id}</code>\n"
            summary += f"\nلطفا روش پرداخت را انتخاب کنید:"
            
            # دکمه‌های پرداخت
            await callback.message.edit_text(
                summary,
                reply_markup=get_payment_keyboard(str(order.id)),
                parse_mode="HTML"
            )
            await state.set_state(BuyState.select_payment)
            logger.info(f"User {callback.from_user.id} selected inbound {inbound_id} and order {order.id} created. Waiting for payment.")
    except ValueError as e:
        logger.error(f"Invalid IDs in callback data: {callback.data}, error: {e}")
        await callback.answer("شناسه‌های ارسالی نامعتبر هستند", show_alert=True)
    except Exception as e:
        logger.error(f"Error in inbound selection: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # بازگشت به صفحه انتخاب پلن با نمایش خطا
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            await callback.message.edit_text(
                "❌ خطایی رخ داد. لطفا دوباره از ابتدا شروع کنید:",
                reply_markup=get_plans_keyboard(plans)
            )

async def confirm_purchase(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    تایید نهایی خرید توسط کاربر
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
        
        # ذخیره اطلاعات نهایی در state
        await state.update_data(
            plan_id=plan_id, 
            panel_id=panel_id, 
            inbound_id=inbound_id,
            confirmed_at=datetime.now().isoformat()
        )
        
        user_id = callback.from_user.id
        
        async with session_pool() as session:
            # دریافت اطلاعات کاربر
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user:
                logger.error(f"User {user_id} not found in database")
                await callback.message.edit_text(
                    "❌ خطا: اطلاعات کاربری شما یافت نشد.\n"
                    "لطفا با استفاده از دستور /start دوباره ثبت‌نام کنید."
                )
                return
                
            # دریافت اطلاعات پلن، پنل و اینباند
            plan_service = PlanService(session)
            panel_service = PanelService(session)
            
            plan = await plan_service.get_plan_by_id(plan_id)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not all([plan, panel]):
                logger.error(f"Plan {plan_id} or Panel {panel_id} not found")
                await callback.message.edit_text(
                    "❌ خطا: اطلاعات پلن یا لوکیشن یافت نشد.\n"
                    "لطفا دوباره از ابتدا شروع کنید."
                )
                return
                
            # ایجاد سفارش موقت
            order_service = OrderService(session)
            # نمایش پیام در حال پردازش
            processing_message = await callback.message.edit_text(
                "🔄 در حال پردازش سفارش شما...\n"
                "لطفا چند لحظه صبر کنید."
            )
            try:
                order = await order_service.create_order(
                    user_id=user.id,
                    plan_id=plan_id,
                    location_name=panel.location_name,
                    amount=plan.price,
                    status=OrderStatus.PENDING
                )
                if not order:
                    logger.error(f"Failed to create order for user {user_id}")
                    await callback.message.edit_text(
                        "❌ خطا در ایجاد سفارش.\n"
                        "لطفا دوباره تلاش کنید."
                    )
                    return
                await state.update_data(order_id=order.id)
                balance = getattr(user, 'balance', 0)
                payment_message = (
                    f"✅ سفارش شما با موفقیت ثبت شد.\n\n"
                    f"🔹 شناسه سفارش: <code>{order.id}</code>\n"
                    f"🔹 تاریخ: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"🔹 مبلغ: {int(order.amount):,} تومان\n\n"
                    f"💰 موجودی کیف پول شما: {int(balance):,} تومان\n\n"
                    "لطفا روش پرداخت را انتخاب کنید:"
                )
                await callback.message.edit_text(
                    payment_message,
                    reply_markup=get_payment_keyboard(str(order.id))
                )
                await state.set_state(BuyState.select_payment)
                logger.info(f"Created order {order.id} for user {user_id}, plan {plan_id}, panel {panel_id}")
            except Exception as e:
                logger.error(f"Error creating order: {e}", exc_info=True)
                await callback.message.edit_text(
                    "❌ خطا در ایجاد سفارش.\n"
                    "لطفا دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
                return
                
    except ValueError as e:
        logger.error(f"Invalid IDs in callback data: {callback.data}, error: {e}")
        await callback.answer("شناسه‌های ارسالی نامعتبر هستند", show_alert=True)
    except Exception as e:
        logger.error(f"Error in purchase confirmation: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست", show_alert=True)
        # بازگشت به صفحه انتخاب پلن با نمایش خطا
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            await callback.message.edit_text(
                "❌ خطایی رخ داد. لطفا دوباره از ابتدا شروع کنید:",
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
            
        payment_method = parts[2]  # "wallet", "card", "online"
        payment_id = parts[3]  # order_id
        
        user_id = callback.from_user.id
        
        # بررسی معتبر بودن روش پرداخت
        valid_methods = ["wallet", "card", "online"]
        if payment_method not in valid_methods:
            logger.error(f"Invalid payment method: {payment_method}")
            await callback.answer("روش پرداخت نامعتبر است", show_alert=True)
            return
            
        # نمایش پیام در حال پردازش
        await callback.message.edit_text(
            "🔄 در حال پردازش پرداخت...\n"
            "لطفا چند لحظه صبر کنید."
        )
        
        try:
            order_id = int(payment_id)
        except ValueError:
            logger.error(f"Invalid order ID: {payment_id}")
            await callback.answer("شناسه سفارش نامعتبر است", show_alert=True)
            return
        
        async with session_pool() as session:
            # دریافت اطلاعات سفارش
            order_service = OrderService(session)
            
            # دریافت اطلاعات کاربر
            user_service = UserService(session)
            
            # دریافت سرویس نوتیفیکیشن
            notification_service = NotificationService(session)
            
            # دریافت سرویس تنظیمات
            settings_service = SettingsService(session)
            
            order = await order_service.get_order_by_id(order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                await callback.message.edit_text(
                    "❌ سفارش مورد نظر یافت نشد.\n"
                    "لطفا دوباره از طریق منوی اصلی اقدام کنید.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
                    ])
                )
                return
            
            # بررسی مطابقت کاربر با سفارش
            if order.user_id != user_id:
                logger.warning(f"User {user_id} tried to pay for order {order_id} belonging to user {order.user_id}")
                await callback.answer("این سفارش متعلق به شما نیست", show_alert=True)
                return
            
            # دریافت اطلاعات کاربر
            user = await user_service.get_user_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                await callback.message.edit_text(
                    "❌ اطلاعات کاربری شما یافت نشد.\n"
                    "لطفا دوباره از طریق منوی اصلی اقدام کنید.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
                    ])
                )
                return
                
            # پردازش براساس روش پرداخت
            if payment_method == "wallet":
                # پرداخت از کیف پول
                success, message = await order_service.attempt_payment_from_wallet(order_id)
                
                if success:
                    # پرداخت موفق - نمایش اطلاعات نهایی
                    await callback.message.edit_text(
                        f"✅ پرداخت از کیف پول با موفقیت انجام شد.\n\n"
                        f"🔹 شناسه سفارش: <code>{order_id}</code>\n"
                        f"🔹 مبلغ: {int(order.amount):,} تومان\n\n"
                        "اکانت شما به زودی فعال خواهد شد.\n"
                        "برای مشاهده اکانت‌های خود از دستور /myaccounts استفاده کنید.",
                        reply_markup=get_payment_status_keyboard(order_id)
                    )
                    
                    # ارسال نوتیفیکیشن به ادمین
                    await notification_service.notify_admin(
                        f"💰 پرداخت از کیف پول انجام شد\n"
                        f"کاربر: {user_id} (@{user.username or 'بدون یوزرنیم'})\n"
                        f"سفارش: {order_id}\n"
                        f"مبلغ: {int(order.amount):,} تومان"
                    )
                    
                    await state.clear()
                    logger.info(f"Wallet payment successful for order {order_id} by user {user_id}")
                else:
                    # پرداخت ناموفق - نمایش خطا
                    await callback.message.edit_text(
                        f"❌ {message}\n\n"
                        f"🔹 شناسه سفارش: <code>{order_id}</code>\n"
                        f"🔹 مبلغ: {int(order.amount):,} تومان\n\n"
                        "لطفا روش دیگری برای پرداخت انتخاب کنید:",
                        reply_markup=get_payment_keyboard(str(order_id))
                    )
                    logger.warning(f"Wallet payment failed for order {order_id} by user {user_id}: {message}")
                    
            elif payment_method == "card":
                # پرداخت کارت به کارت
                # دریافت اطلاعات کارت‌های بانکی از تنظیمات
                bank_cards = await settings_service.get_setting_value("bank_cards", default="[]")
                
                try:
                    # تبدیل رشته JSON به لیست
                    cards = json.loads(bank_cards) if isinstance(bank_cards, str) else bank_cards
                    
                    if not cards:
                        await callback.message.edit_text(
                            "❌ در حال حاضر امکان پرداخت کارت به کارت وجود ندارد.\n"
                            "لطفا روش دیگری را انتخاب کنید:",
                            reply_markup=get_payment_keyboard(str(order_id))
                        )
                        return
                        
                    # ایجاد متن کارت‌ها
                    cards_text = "\n".join([f"🏦 {card.get('bank', 'نامشخص')}: <code>{card.get('number', '')}</code> - {card.get('owner', '')}" for card in cards])
                    
                    # به‌روزرسانی وضعیت سفارش
                    await order_service.update_order_status(order_id, OrderStatus.WAITING_FOR_RECEIPT)
                    
                    # نمایش اطلاعات پرداخت کارت به کارت
                    await callback.message.edit_text(
                        f"💳 پرداخت کارت به کارت\n\n"
                        f"🔹 شناسه سفارش: <code>{order_id}</code>\n"
                        f"🔹 مبلغ: {int(order.amount):,} تومان\n\n"
                        f"لطفا مبلغ فوق را به یکی از شماره کارت‌های زیر واریز کنید:\n\n"
                        f"{cards_text}\n\n"
                        "⚠️ پس از واریز، رسید پرداخت را با دستور /receipt ارسال کنید.\n"
                        "⚠️ حتما شناسه سفارش را در توضیحات واریز ذکر کنید.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
                        ])
                    )
                    
                    # ارسال نوتیفیکیشن به ادمین
                    await notification_service.notify_admin(
                        f"🧾 درخواست پرداخت کارت به کارت\n"
                        f"کاربر: {user_id} (@{user.username or 'بدون یوزرنیم'})\n"
                        f"سفارش: {order_id}\n"
                        f"مبلغ: {int(order.amount):,} تومان\n"
                        f"منتظر دریافت رسید..."
                    )
                    
                    await state.clear()
                    logger.info(f"Card payment instructions sent for order {order_id} to user {user_id}")
                
                except Exception as e:
                    logger.error(f"Error processing card payment: {e}", exc_info=True)
                    await callback.message.edit_text(
                        "❌ خطا در پردازش پرداخت کارت به کارت.\n"
                        "لطفا روش دیگری را انتخاب کنید یا با پشتیبانی تماس بگیرید:",
                        reply_markup=get_payment_keyboard(str(order_id))
                    )
            
            elif payment_method == "online":
                # پرداخت آنلاین - در حال حاضر پیاده‌سازی نشده
                await callback.message.edit_text(
                    "🔄 درگاه پرداخت آنلاین در حال راه‌اندازی است.\n"
                    "لطفا از روش دیگری برای پرداخت استفاده کنید:",
                    reply_markup=get_payment_keyboard(str(order_id))
                )
                logger.info(f"Online payment requested for order {order_id} by user {user_id} - not implemented yet")
            
            else:
                logger.warning(f"Unknown payment method: {payment_method}")
                await callback.answer("روش پرداخت نامعتبر است", show_alert=True)
                await callback.message.edit_text(
                    "❌ روش پرداخت انتخابی نامعتبر است.\n"
                    "لطفا روش دیگری را انتخاب کنید:",
                    reply_markup=get_payment_keyboard(str(order_id))
                )
                
    except ValueError as e:
        logger.error(f"Invalid order ID in payment: {callback.data}, error: {e}")
        await callback.answer("شناسه سفارش نامعتبر است", show_alert=True)
    except Exception as e:
        logger.error(f"Error in payment method handling: {e}", exc_info=True)
        await callback.answer("خطا در پردازش درخواست پرداخت", show_alert=True)
        await callback.message.edit_text(
            "❌ خطا در پردازش پرداخت.\n"
            "لطفا دوباره از طریق منوی اصلی اقدام کنید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
            ])
        )

async def back_to_plans(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    بازگشت به مرحله انتخاب پلن
    """
    try:
        # پاکسازی داده‌های قبلی
        await state.clear()
        
        # بازیابی لیست پلن‌ها
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            
            if not plans:
                await callback.message.edit_text(
                    "⚠️ در حال حاضر هیچ پلن فعالی موجود نیست.\n"
                    "لطفا بعدا مجددا تلاش کنید."
                )
                return
                
            # نمایش لیست پلن‌ها
            await callback.message.edit_text(
                "🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plans_keyboard(plans)
            )
            
            # تنظیم وضعیت به انتخاب پلن
            await state.set_state(BuyState.select_plan)
            logger.info(f"User {callback.from_user.id} went back to plan selection")
            
    except Exception as e:
        logger.error(f"Error in back_to_plans: {e}", exc_info=True)
        await callback.answer("خطا در بازگشت به مرحله قبل", show_alert=True)
        # بازگشت به منوی اصلی در صورت خطا
        await callback.message.edit_text(
            "❌ خطایی رخ داد. لطفا از منوی اصلی شروع کنید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
            ])
        )

async def back_to_locations(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    بازگشت به مرحله انتخاب لوکیشن
    """
    try:
        # استخراج شناسه پلن از کالبک دیتا
        parts = callback.data.split(":")
        plan_id = None
        
        # اگر شناسه پلن در کالبک دیتا موجود نیست، از state دریافت شود
        if len(parts) < 4:
            user_data = await state.get_data()
            plan_id = user_data.get("plan_id")
        else:
            try:
                plan_id = int(parts[3])
            except (ValueError, TypeError):
                user_data = await state.get_data()
                plan_id = user_data.get("plan_id")
        
        if not plan_id:
            logger.error(f"Plan ID not found for user {callback.from_user.id}")
            await callback.answer("خطا: پلن انتخاب نشده است", show_alert=True)
            # بازگشت به مرحله انتخاب پلن
            return await back_to_plans(callback, state, session_pool)
        
        # به‌روزرسانی داده‌های state
        await state.update_data(plan_id=plan_id)
        
        async with session_pool() as session:
            # دریافت اطلاعات پلن
            plan_service = PlanService(session)
            plan = await plan_service.get_plan_by_id(plan_id)
            
            if not plan:
                logger.error(f"Plan {plan_id} not found in database")
                await callback.answer("پلن انتخابی یافت نشد", show_alert=True)
                # بازگشت به مرحله انتخاب پلن
                return await back_to_plans(callback, state, session_pool)
            
            # دریافت لیست لوکیشن‌ها
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
                f"💰 قیمت: {int(plan.price):,} تومان\n"
                f"⏱ مدت: {getattr(plan, 'duration_days', 'نامشخص')} روز\n"
                f"📊 حجم: {getattr(plan, 'traffic_gb', 'نامشخص')} گیگابایت\n\n"
                "لطفا لوکیشن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_location_selection_keyboard(locations)
            )
            
            # تنظیم وضعیت به انتخاب لوکیشن
            await state.set_state(BuyState.select_location)
            logger.info(f"User {callback.from_user.id} went back to location selection for plan {plan_id}")
            
    except Exception as e:
        logger.error(f"Error in back_to_locations: {e}", exc_info=True)
        await callback.answer("خطا در بازگشت به مرحله قبل", show_alert=True)
        # بازگشت به مرحله انتخاب پلن در صورت خطا
        await back_to_plans(callback, state, session_pool)

async def back_to_inbounds(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    بازگشت به مرحله انتخاب اینباند/پروتکل
    """
    try:
        # استخراج شناسه پلن و پنل از کالبک دیتا
        parts = callback.data.split(":")
        
        if len(parts) < 5:
            logger.error(f"Invalid callback data format: {callback.data}")
            # دریافت داده‌ها از state
            user_data = await state.get_data()
            plan_id = user_data.get("plan_id")
            panel_id = user_data.get("panel_id")
        else:
            try:
                plan_id = int(parts[3])
                panel_id = int(parts[4])
            except (ValueError, TypeError):
                # دریافت داده‌ها از state
                user_data = await state.get_data()
                plan_id = user_data.get("plan_id")
                panel_id = user_data.get("panel_id")
        
        if not all([plan_id, panel_id]):
            logger.error(f"Plan ID or Panel ID not found for user {callback.from_user.id}")
            await callback.answer("خطا: اطلاعات ناقص است", show_alert=True)
            
            # اگر فقط plan_id موجود است، به مرحله انتخاب لوکیشن برگردد
            if plan_id:
                return await back_to_locations(callback, state, session_pool)
            else:
                # در غیر این صورت به مرحله انتخاب پلن برگردد
                return await back_to_plans(callback, state, session_pool)
        
        # به‌روزرسانی داده‌های state
        await state.update_data(plan_id=plan_id, panel_id=panel_id)
        
        async with session_pool() as session:
            # دریافت اطلاعات پلن و پنل
            plan_service = PlanService(session)
            panel_service = PanelService(session)
            
            plan = await plan_service.get_plan_by_id(plan_id)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not all([plan, panel]):
                missing = []
                if not plan:
                    missing.append("پلن")
                if not panel:
                    missing.append("لوکیشن")
                
                logger.error(f"Plan {plan_id} or Panel {panel_id} not found in database")
                await callback.answer(f"{', '.join(missing)} انتخابی یافت نشد", show_alert=True)
                
                # بازگشت به مرحله مناسب
                if not plan:
                    return await back_to_plans(callback, state, session_pool)
                else:
                    return await back_to_locations(callback, state, session_pool)
            
            # دریافت لیست اینباندها
            inbound_service = InboundService(session)
            inbounds = await inbound_service.get_inbounds_by_panel_id(panel_id)
            
            if not inbounds:
                logger.warning(f"No active inbounds available for panel {panel_id}")
                # بازگشت به صفحه انتخاب لوکیشن
                location_service = LocationService(session)
                locations = await location_service.get_available_locations()
                await callback.message.edit_text(
                    f"⚠️ هیچ پروتکلی برای لوکیشن {panel.location_name} موجود نیست.\n"
                    "لطفا لوکیشن دیگری انتخاب کنید.",
                    reply_markup=get_location_selection_keyboard(locations)
                )
                return
                
            # نمایش لیست اینباندها
            plan_info = ""
            if plan:
                plan_info = f"🔹 پلن: {plan.name}\n"
                
            await callback.message.edit_text(
                f"🔘 مرحله انتخاب پروتکل\n\n"
                f"{plan_info}"
                f"🔹 لوکیشن: {panel.flag_emoji} {panel.location_name}\n\n"
                "لطفا پروتکل مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plan_selection_keyboard(inbounds, panel_id, plan_id)
            )
            
            # تنظیم وضعیت به انتخاب اینباند
            await state.set_state(BuyState.select_inbound)
            logger.info(f"User {callback.from_user.id} went back to inbound selection for plan {plan_id}, panel {panel_id}")
            
    except Exception as e:
        logger.error(f"Error in back_to_inbounds: {e}", exc_info=True)
        await callback.answer("خطا در بازگشت به مرحله قبل", show_alert=True)
        # تلاش برای بازگشت به مرحله انتخاب لوکیشن
        try:
            user_data = await state.get_data()
            plan_id = user_data.get("plan_id")
            if plan_id:
                await back_to_locations(callback, state, session_pool)
            else:
                await back_to_plans(callback, state, session_pool)
        except Exception:
            # در صورت خطا، بازگشت به منوی اصلی
            await callback.message.edit_text(
                "❌ خطایی رخ داد. لطفا از منوی اصلی شروع کنید.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
                ])
            )

async def refresh_plans(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    بروزرسانی لیست پلن‌ها
    """
    try:
        # پاکسازی داده‌های قبلی
        await state.clear()
        
        # نمایش پیام در حال بارگذاری
        await callback.message.edit_text(
            "🔄 در حال بارگذاری لیست پلن‌ها...\n"
            "لطفا چند لحظه صبر کنید."
        )
        
        # بازیابی لیست پلن‌ها
        async with session_pool() as session:
            plan_service = PlanService(session)
            plans = await plan_service.get_all_active_plans()
            
            # دریافت اطلاعات کاربر برای نمایش موجودی
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            balance_message = ""
            if user and hasattr(user, 'balance'):
                balance_message = f"💰 موجودی کیف پول شما: {int(user.balance):,} تومان\n\n"
            
            if not plans:
                await callback.message.edit_text(
                    f"{balance_message}⚠️ در حال حاضر هیچ پلن فعالی موجود نیست.\n"
                    "لطفا بعدا مجددا تلاش کنید."
                )
                return
                
            # نمایش لیست پلن‌ها
            await callback.message.edit_text(
                f"{balance_message}🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plans_keyboard(plans)
            )
            
            # تنظیم وضعیت به انتخاب پلن
            await state.set_state(BuyState.select_plan)
            logger.info(f"User {callback.from_user.id} refreshed plans list")
            
    except Exception as e:
        logger.error(f"Error in refresh_plans: {e}", exc_info=True)
        await callback.answer("خطا در بروزرسانی لیست پلن‌ها", show_alert=True)
        # بازگشت به منوی اصلی در صورت خطا
        await callback.message.edit_text(
            "❌ خطایی رخ داد. لطفا از منوی اصلی شروع کنید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
            ])
        )

async def cancel_payment(callback: CallbackQuery, state: FSMContext, session_pool):
    """
    انصراف از پرداخت
    """
    try:
        # دریافت اطلاعات سفارش از state
        user_data = await state.get_data()
        order_id = user_data.get("order_id")
        
        if order_id:
            async with session_pool() as session:
                # به‌روزرسانی وضعیت سفارش به لغو شده
                order_service = OrderService(session)
                await order_service.update_order_status(order_id, OrderStatus.CANCELLED)
                logger.info(f"Order {order_id} cancelled by user {callback.from_user.id}")
        
        # پاکسازی وضعیت
        await state.clear()
        
        # نمایش پیام تایید انصراف
        await callback.message.edit_text(
            "✅ انصراف از پرداخت با موفقیت انجام شد.\n"
            "شما می‌توانید مجددا از دستور /buy برای خرید اشتراک استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
            ])
        )
        logger.info(f"User {callback.from_user.id} cancelled payment")
        
    except Exception as e:
        logger.error(f"Error in cancel_payment: {e}", exc_info=True)
        await callback.answer("خطا در انصراف از پرداخت", show_alert=True)
        # نمایش پیام خطا و بازگشت به منوی اصلی
        await callback.message.edit_text(
            "❌ خطایی در انصراف از پرداخت رخ داد.\n"
            "لطفا از منوی اصلی شروع کنید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data="start")]
            ])
        )

def register_buy_callbacks(router: Router, session_pool):
    """ثبت کالبک‌های مربوط به فرآیند خرید"""
    
    # کالبک انتخاب پلن
    @router.callback_query(F.data.startswith("buy:plan:"))
    async def _plan_selected_wrapper(callback: CallbackQuery, state: FSMContext):
        await plan_selected(callback, state, session_pool)
    
    # کالبک انتخاب لوکیشن
    @router.callback_query(F.data.startswith("buy:loc:"))
    async def _location_selected_wrapper(callback: CallbackQuery, state: FSMContext):
        await location_selected(callback, state, session_pool)
    
    # کالبک انتخاب اینباند/پروتکل
    @router.callback_query(F.data.startswith("buy:inb:"))
    async def _inbound_selected_wrapper(callback: CallbackQuery, state: FSMContext):
        await inbound_selected(callback, state, session_pool)
    
    # کالبک تایید نهایی خرید
    @router.callback_query(F.data.startswith("buy:confirm:"))
    async def _confirm_purchase_wrapper(callback: CallbackQuery, state: FSMContext):
        await confirm_purchase(callback, state, session_pool)
    
    # کالبک انتخاب روش پرداخت
    @router.callback_query(F.data.startswith("buy:pay:"))
    async def _handle_payment_method_wrapper(callback: CallbackQuery, state: FSMContext):
        await handle_payment_method(callback, state, session_pool)
    
    # کالبک بازگشت به لیست پلن‌ها
    @router.callback_query(F.data == BUY_CB["BACK_TO_PLANS"])
    async def _back_to_plans_wrapper(callback: CallbackQuery, state: FSMContext):
        await back_to_plans(callback, state, session_pool)
    
    # کالبک بازگشت به انتخاب لوکیشن
    @router.callback_query(F.data.startswith("buy:back:loc:"))
    async def _back_to_locations_wrapper(callback: CallbackQuery, state: FSMContext):
        await back_to_locations(callback, state, session_pool)
    
    # کالبک بازگشت به انتخاب اینباند
    @router.callback_query(F.data.startswith("buy:back:inb:"))
    async def _back_to_inbounds_wrapper(callback: CallbackQuery, state: FSMContext):
        await back_to_inbounds(callback, state, session_pool)
    
    # کالبک بروزرسانی لیست پلن‌ها
    @router.callback_query(F.data == BUY_CB["REFRESH_PLANS"])
    async def _refresh_plans_wrapper(callback: CallbackQuery, state: FSMContext):
        await refresh_plans(callback, state, session_pool)
    
    # کالبک انصراف از پرداخت
    @router.callback_query(F.data == BUY_CB["CANCEL_PAYMENT"])
    async def _cancel_payment_wrapper(callback: CallbackQuery, state: FSMContext):
        await cancel_payment(callback, state, session_pool)
    
    # کالبک بررسی وضعیت پرداخت
    @router.callback_query(F.data.startswith("payment:check:"))
    async def _payment_check_wrapper(callback: CallbackQuery, state: FSMContext):
        # این کالبک در آینده پیاده‌سازی خواهد شد
        await callback.answer("در حال حاضر وضعیت پرداخت از طریق /myaccounts قابل مشاهده است", show_alert=True) 