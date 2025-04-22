# مدیریت دکمه‌های inline مثل بازگشت، جزئیات پلن

"""
کال‌بک‌های تعاملی برای منوهای بات
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from aiogram.fsm.context import FSMContext

from core.services.plan_service import PlanService
from core.services.user_service import UserService
from core.services.order_service import OrderService
from bot.buttons.plan_buttons import get_plans_keyboard, get_plan_details_keyboard
from db.models.order import Order, OrderStatus
from bot.states.buy_states import BuyState

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_callbacks(router: Router, session_pool):
    """ثبت تمام callback handlers در روتر"""
    
    @router.callback_query(F.data == "buy_plans")
    async def buy_plans_callback(callback: CallbackQuery, state: FSMContext):
        """شروع فرایند خرید پلن از طریق کیبورد اینلاین"""
        try:
            async with session_pool() as session:
                # دریافت پلن‌های فعال
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    await callback.message.edit_text("هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.")
                    return
                
                # نمایش لیست پلن‌ها با دکمه‌های انتخاب
                await callback.message.edit_text(
                    text="🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                # تنظیم وضعیت به انتخاب پلن
                await state.set_state(BuyState.select_plan)
                
        except Exception as e:
            logger.error(f"Error in buy_plans callback: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)
    
    @router.callback_query(F.data.startswith("select_plan:"))
    async def select_plan_callback(callback: CallbackQuery):
        """انتخاب پلن و نمایش جزئیات آن"""
        try:
            plan_id = int(callback.data.split(":")[-1])
            logger.info(f"User {callback.from_user.id} selected plan ID: {plan_id}")
            
            async with session_pool() as session:
                plan_service = PlanService(session)
                plan = await plan_service.get_plan_by_id(plan_id)
                
                if not plan:
                    await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                    return

                # نمایش اطلاعات کامل پلن
                details = (
                    f"🔹 نام پلن: {plan.name}\n"
                    f"🔹 حجم: {plan.traffic_gb} گیگابایت\n"
                    f"🔹 مدت اعتبار: {plan.duration_days} روز\n"
                    f"🔹 قیمت: {int(plan.price):,} تومان\n\n"
                    f"برای ادامه خرید، دکمه تأیید را انتخاب کنید."
                )
                
                await callback.message.edit_text(
                    text=details,
                    reply_markup=get_plan_details_keyboard(plan_id)
                )
                
                await callback.answer()
                
        except Exception as e:
            logger.error(f"Error in select_plan_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data.startswith("confirm_plan:"))
    async def confirm_plan_callback(callback: CallbackQuery):
        """تأیید خرید پلن و ایجاد سفارش جدید"""
        try:
            plan_id = int(callback.data.split(":")[-1])
            telegram_user_id = callback.from_user.id
            logger.info(f"User {telegram_user_id} confirmed plan ID: {plan_id}")
            
            async with session_pool() as session:
                user_service = UserService(session)
                db_user = await user_service.get_user_by_telegram_id(telegram_user_id)
                
                if not db_user:
                    logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                    await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                    return
                
                plan_service = PlanService(session)
                plan = await plan_service.get_plan_by_id(plan_id)
                
                if not plan:
                    await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                    return
                
                new_order = Order(
                    user_id=db_user.id,
                    plan_id=plan_id,
                    amount=plan.price,
                    status=OrderStatus.PENDING,
                    created_at=datetime.utcnow()
                )
                
                session.add(new_order)
                await session.commit()
                await session.refresh(new_order)
                logger.info(f"Created new order ID: {new_order.id} for user {telegram_user_id} (DB ID: {db_user.id})")
                
                # پیام موفقیت ثبت سفارش
                text = (
                    f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
                    f"🔹 شناسه سفارش: {new_order.id}\n"
                    f"🔹 نام پلن: {plan.name}\n"
                    f"🔹 مبلغ: {int(plan.price):,} تومان\n\n"
                    f"سفارش شما در انتظار پرداخت است. لطفاً روش پرداخت را انتخاب کنید."
                )
                
                # ایجاد دکمه‌های پرداخت
                payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💰 پرداخت با کیف پول", callback_data=f"pay_with_wallet:{new_order.id}")],
                    [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")]
                ])
                
                await callback.message.edit_text(
                    text=text,
                    reply_markup=payment_keyboard
                )
                
                await callback.answer()
                
        except Exception as e:
            logger.error(f"Error in confirm_plan_callback for user {callback.from_user.id}: {e}", exc_info=True)
            await callback.answer("خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data == "back_to_plans")
    async def back_to_plans_callback(callback: CallbackQuery):
        """بازگشت به لیست پلن‌ها"""
        try:
            async with session_pool() as session:
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    await callback.message.edit_text("هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.")
                    return
                
                await callback.message.edit_text(
                    text="🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                await callback.answer()
                
        except Exception as e:
            logger.error(f"Error in back_to_plans_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data == "back_to_main")
    async def back_to_main_callback(callback: CallbackQuery):
        """بازگشت به منوی اصلی"""
        try:
            await callback.message.delete()
            await callback.message.answer("به منوی اصلی بازگشتید. از دکمه‌های زیر استفاده کنید.")
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in back_to_main_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data.startswith("pay_with_wallet:"))
    async def pay_with_wallet_callback(callback: CallbackQuery):
        """پرداخت سفارش با استفاده از موجودی کیف پول"""
        try:
            # استخراج order_id از callback_data
            order_id = int(callback.data.split(":")[-1])
            telegram_user_id = callback.from_user.id
            
            logger.info(f"User {telegram_user_id} is paying order {order_id} with wallet balance")
            
            # پیام موقت برای نشان دادن وضعیت پردازش
            await callback.message.edit_text(
                "⏳ در حال پردازش پرداخت...\n"
                "لطفاً چند لحظه صبر کنید."
            )
            
            async with session_pool() as session:
                # دریافت اطلاعات کاربر
                user_service = UserService(session)
                db_user = await user_service.get_user_by_telegram_id(telegram_user_id)
                
                if not db_user:
                    logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                    await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                    return
                
                # پرداخت با کیف پول
                order_service = OrderService(session)
                success, message = await order_service.pay_with_balance(order_id)
                
                if not success:
                    # دریافت اطلاعات سفارش برای نمایش مبلغ مورد نیاز
                    order = await order_service.get_order_by_id(order_id)
                    
                    # اگر موجودی کافی نیست، پیغام مناسب ارسال می‌شود
                    await callback.message.edit_text(
                        f"❌ {message}\n\n"
                        f"موجودی فعلی: {int(db_user.balance):,} تومان\n"
                        f"مبلغ لازم: {int(order.amount):,} تومان\n\n"
                        "لطفاً ابتدا کیف پول خود را شارژ کنید.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💰 شارژ کیف پول", callback_data="deposit_wallet")],
                            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")]
                        ])
                    )
                    return
                    
                # اگر پرداخت موفقیت‌آمیز بود
                await callback.message.edit_text(
                    "✅ پرداخت با موفقیت انجام شد!\n\n"
                    "سفارش شما در حال پردازش است. کانفیگ VPN شما به زودی آماده خواهد شد.\n"
                    "لطفاً منتظر بمانید...",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                    ])
                )
                
        except Exception as e:
            logger.error(f"Error in pay_with_wallet_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
            # بازگشت به منوی اصلی در صورت خطا
            await callback.message.edit_text(
                "❌ متأسفانه در پردازش پرداخت خطایی رخ داد.\n"
                "لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")]
                ])
            )
