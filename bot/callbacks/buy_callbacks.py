"""
کال‌بک‌های مربوط به فرایند خرید و دریافت کانفیگ
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from core.services.panel_service import PanelService
from core.services.plan_service import PlanService
from core.services.account_service import AccountService
from core.services.user_service import UserService
from core.services.order_service import OrderService
from core.services.payment_service import PaymentService
from db.models.order import Order, OrderStatus
from db.models.inbound import Inbound
from db.models.transaction import TransactionType

from bot.buttons.buy_buttons import get_locations_keyboard, get_inbounds_keyboard, get_confirm_purchase_keyboard
from bot.buttons.plan_buttons import get_plans_keyboard
from bot.buttons.inbound_buttons import get_panel_locations_keyboard

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_buy_callbacks(router: Router, session_pool):
    """ثبت callback handler های مربوط به فرایند خرید"""
    
    @router.callback_query(F.data.startswith("select_plan:"))
    async def handle_plan_selection(callback: CallbackQuery):
        """پردازش انتخاب پلن"""
        try:
            plan_id = int(callback.data.split(":")[1])
            
            # ایجاد جلسه دیتابیس
            session = session_pool()
            
            try:
                # دریافت پنل‌های فعال
                panel_service = PanelService(session)
                panels = panel_service.get_all_panels(active_only=True)
                
                if not panels:
                    await callback.message.edit_text(
                        "⚠️ در حال حاضر هیچ سروری برای ارائه سرویس در دسترس نیست.\n"
                        "لطفاً بعداً دوباره تلاش کنید."
                    )
                    return
                
                # نمایش لیست لوکیشن‌ها
                await callback.message.edit_text(
                    "🌍 لطفاً لوکیشن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_panel_locations_keyboard(panels)
                )
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in plan selection: {e}")
            await callback.message.edit_text(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            )
    
    @router.callback_query(F.data.startswith("select_location:"))
    async def handle_location_selection(callback: CallbackQuery):
        """پردازش انتخاب لوکیشن"""
        try:
            panel_id = int(callback.data.split(":")[1])
            
            # ایجاد جلسه دیتابیس
            session = session_pool()
            
            try:
                # دریافت inbound‌های فعال پنل
                panel_service = PanelService(session)
                inbounds = session.query(Inbound).filter(
                    Inbound.panel_id == panel_id,
                    Inbound.status == "active"
                ).all()
                
                if not inbounds:
                    await callback.message.edit_text(
                        "⚠️ فعلاً اینباندی برای لوکیشن انتخاب‌شده موجود نیست.\n"
                        "لطفاً لوکیشن دیگری را انتخاب کنید یا بعداً تلاش کنید.",
                        reply_markup=get_panel_locations_keyboard(panel_service.get_all_panels(active_only=True))
                    )
                    return
                
                # نمایش لیست inbound‌ها
                await callback.message.edit_text(
                    "🔌 لطفاً پروتکل مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_inbounds_keyboard(inbounds, panel_id, plan_id)
                )
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in location selection: {e}")
            await callback.message.edit_text(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            )
    
    @router.callback_query(F.data.startswith("select_inbound:"))
    async def handle_inbound_selection(callback: CallbackQuery):
        """پردازش انتخاب inbound"""
        try:
            # دریافت پارامترها از callback data
            _, plan_id, panel_id, inbound_id = callback.data.split(":")
            plan_id = int(plan_id)
            panel_id = int(panel_id)
            inbound_id = int(inbound_id)
            
            # ایجاد جلسه دیتابیس
            async with session_pool() as session:
                # دریافت اطلاعات پلن و پنل
                plan_service = PlanService(session)
                panel_service = PanelService(session)
                payment_service = PaymentService(session)
                
                plan = await plan_service.get_plan_by_id(plan_id)
                panel = await panel_service.get_panel_by_id(panel_id)
                
                # دریافت inbound با استفاده از select
                from sqlalchemy import select
                query = select(Inbound).where(Inbound.id == inbound_id)
                result = await session.execute(query)
                inbound = result.scalar_one_or_none()
                
                if not all([plan, panel, inbound]):
                    await callback.message.edit_text(
                        "⚠️ خطا در دریافت اطلاعات. لطفاً دوباره تلاش کنید."
                    )
                    return
                
                # دریافت موجودی کیف پول
                balance = await payment_service.get_user_balance(callback.from_user.id)
                
                # نمایش خلاصه سفارش و درخواست تایید
                summary = (
                    f"📋 خلاصه سفارش:\n\n"
                    f"🔹 پلن: {plan.name}\n"
                    f"🔹 مدت: {plan.duration_days} روز\n"
                    f"🔹 حجم: {plan.traffic} گیگابایت\n"
                    f"🔹 لوکیشن: {panel.flag_emoji} {panel.location}\n"
                    f"🔹 پروتکل: {inbound.protocol.upper()}\n"
                    f"💰 قیمت: {plan.price:,} تومان\n\n"
                    f"موجودی فعلی: {balance:,} تومان\n"
                )
                
                # ایجاد دکمه‌های تایید یا بازگشت
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ تایید و پرداخت",
                        callback_data=f"confirm_purchase:{plan_id}:{panel_id}:{inbound_id}"
                    )],
                    [InlineKeyboardButton(
                        text="🔙 بازگشت به انتخاب پروتکل",
                        callback_data=f"back_to_inbounds:{plan_id}:{panel_id}"
                    )]
                ])
                
                await callback.message.edit_text(summary, reply_markup=keyboard)
                
        except Exception as e:
            logger.error(f"Error in inbound selection: {e}")
            await callback.message.edit_text(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            )
    
    @router.callback_query(F.data.startswith("back_to_locations:"))
    async def handle_back_to_locations(callback: CallbackQuery):
        """بازگشت به لیست لوکیشن‌ها"""
        try:
            plan_id = int(callback.data.split(":")[1])
            
            # ایجاد جلسه دیتابیس
            session = session_pool()
            
            try:
                # دریافت پنل‌های فعال
                panel_service = PanelService(session)
                panels = panel_service.get_all_panels(active_only=True)
                
                # نمایش لیست لوکیشن‌ها
                await callback.message.edit_text(
                    "🌍 لطفاً لوکیشن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_panel_locations_keyboard(panels)
                )
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in back to locations: {e}")
            await callback.message.edit_text(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            )
    
    @router.callback_query(F.data.startswith("back_to_inbounds:"))
    async def handle_back_to_inbounds(callback: CallbackQuery):
        """بازگشت به لیست inbound‌ها"""
        try:
            # دریافت پارامترها از callback data
            _, plan_id, panel_id = callback.data.split(":")
            plan_id = int(plan_id)
            panel_id = int(panel_id)
            
            # ایجاد جلسه دیتابیس
            session = session_pool()
            
            try:
                # دریافت inbound‌های فعال پنل
                inbounds = session.query(Inbound).filter(
                    Inbound.panel_id == panel_id,
                    Inbound.status == "active"
                ).all()
                
                # نمایش لیست inbound‌ها
                await callback.message.edit_text(
                    "🔌 لطفاً پروتکل مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_inbounds_keyboard(inbounds, panel_id, plan_id)
                )
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in back to inbounds: {e}")
            await callback.message.edit_text(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            )
    
    @router.callback_query(F.data == "back_to_plans")
    async def back_to_plans_callback(callback: CallbackQuery):
        """بازگشت به لیست پلن‌ها"""
        session = None
        try:
            session = session_pool()
            plan_service = PlanService(session)
            plans = plan_service.get_all_active_plans()
            
            await callback.message.edit_text(
                text="📱 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plans_keyboard(plans)
            )
            
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in back_to_plans_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in back_to_plans_callback")

    @router.callback_query(F.data.startswith("confirm_purchase:"))
    async def handle_confirm_purchase(callback: CallbackQuery):
        """پردازش تایید و پرداخت سفارش"""
        try:
            # دریافت پارامترها از callback data
            _, plan_id, panel_id, inbound_id = callback.data.split(":")
            plan_id = int(plan_id)
            panel_id = int(panel_id)
            inbound_id = int(inbound_id)
            
            # ایجاد جلسه دیتابیس
            async with session_pool() as session:
                try:
                    # دریافت سرویس‌های مورد نیاز
                    plan_service = PlanService(session)
                    panel_service = PanelService(session)
                    user_service = UserService(session)
                    payment_service = PaymentService(session)
                    order_service = OrderService(session)
                    account_service = AccountService(session)
                    
                    # دریافت اطلاعات کاربر
                    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                    if not user:
                        await callback.message.edit_text(
                            "⚠️ خطا در شناسایی کاربر. لطفاً از دستور /start استفاده کنید."
                        )
                        return
                    
                    # دریافت اطلاعات پلن و پنل
                    plan = await plan_service.get_plan_by_id(plan_id)
                    panel = await panel_service.get_panel_by_id(panel_id)
                    
                    # دریافت inbound
                    from sqlalchemy import select
                    query = select(Inbound).where(Inbound.id == inbound_id)
                    result = await session.execute(query)
                    inbound = result.scalar_one_or_none()
                    
                    if not all([plan, panel, inbound]):
                        await callback.message.edit_text(
                            "⚠️ خطا در دریافت اطلاعات. لطفاً دوباره تلاش کنید."
                        )
                        return
                    
                    # بررسی موجودی کیف پول
                    balance = await payment_service.get_user_balance(callback.from_user.id)
                    if balance < plan.price:
                        await callback.message.edit_text(
                            f"⚠️ موجودی کیف پول شما کافی نیست.\n\n"
                            f"💰 موجودی فعلی: {balance:,} تومان\n"
                            f"💳 مبلغ مورد نیاز: {plan.price:,} تومان\n\n"
                            "برای شارژ کیف پول از دستور /wallet استفاده کنید."
                        )
                        return
                    
                    # ایجاد سفارش
                    order = await order_service.create_order(
                        user_id=user.id,
                        plan_id=plan_id,
                        panel_id=panel_id,
                        inbound_id=inbound_id,
                        amount=plan.price,
                        status=OrderStatus.PENDING
                    )
                    
                    # ایجاد اکانت کلاینت
                    client_account = await account_service.create_client_account(
                        user_id=user.id,
                        order_id=order.id,
                        panel_id=panel_id,
                        inbound_id=inbound_id,
                        traffic_limit=plan.traffic,
                        expire_days=plan.duration_days
                    )
                    
                    if not client_account:
                        # در صورت خطا در ایجاد اکانت، لغو سفارش
                        await order_service.update_order_status(order.id, OrderStatus.FAILED)
                        await callback.message.edit_text(
                            "⚠️ خطا در ایجاد اکانت. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                        )
                        return
                    
                    # ایجاد تراکنش و کسر از موجودی
                    transaction = await payment_service.create_transaction(
                        user_id=user.id,
                        amount=plan.price,
                        transaction_type=TransactionType.PURCHASE,
                        order_id=order.id
                    )
                    
                    # به‌روزرسانی وضعیت سفارش به تکمیل شده
                    await order_service.update_order_status(order.id, OrderStatus.COMPLETED)
                    
                    # ارسال پیام موفقیت
                    success_message = (
                        f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
                        f"📋 شماره سفارش: #{order.id}\n"
                        f"🔹 پلن: {plan.name}\n"
                        f"🔹 مدت: {plan.duration_days} روز\n"
                        f"🔹 حجم: {plan.traffic} گیگابایت\n"
                        f"🔹 لوکیشن: {panel.flag_emoji} {panel.location}\n"
                        f"🔹 پروتکل: {inbound.protocol.upper()}\n"
                        f"💰 مبلغ پرداخت شده: {plan.price:,} تومان\n\n"
                        f"🔰 کانفیگ شما به زودی از طریق همین ربات ارسال خواهد شد."
                    )
                    
                    await callback.message.edit_text(success_message)
                    
                except Exception as e:
                    logger.error(f"Error in confirm purchase: {e}", exc_info=True)
                    await callback.message.edit_text(
                        "⚠️ خطایی در پردازش سفارش رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                    )
                    
        except Exception as e:
            logger.error(f"Error in confirm purchase: {e}", exc_info=True)
            await callback.message.edit_text(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            ) 