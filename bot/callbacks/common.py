# مدیریت دکمه‌های inline مثل بازگشت، جزئیات پلن

"""
کال‌بک‌های تعاملی برای منوهای بات
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

from core.services.plan_service import PlanService
from core.services.user_service import UserService
from bot.buttons.plan_buttons import get_plans_keyboard, get_plan_details_keyboard
from db.models.order import Order, OrderStatus

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_callbacks(router: Router, session_pool):
    """ثبت تمام callback handlers در روتر"""
    
    @router.callback_query(F.data.startswith("select_plan:"))
    async def select_plan_callback(callback: CallbackQuery):
        """انتخاب پلن و نمایش جزئیات آن"""
        session = None # مقداردهی اولیه
        try:
            plan_id = int(callback.data.split(":")[-1])
            logger.info(f"User {callback.from_user.id} selected plan ID: {plan_id}")
            
            session = session_pool()
            plan_service = PlanService(session)
            plan = plan_service.get_plan_by_id(plan_id)
            
            if not plan:
                await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                return

            # نمایش اطلاعات کامل پلن
            details = (
                f"🔹 نام پلن: {plan.name}\n"
                f"🔹 حجم: {plan.traffic} گیگابایت\n"
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
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in select_plan_callback")
    
    @router.callback_query(F.data.startswith("confirm_plan:"))
    async def confirm_plan_callback(callback: CallbackQuery):
        """تأیید خرید پلن و ایجاد سفارش جدید"""
        session = None # مقداردهی اولیه
        try:
            plan_id = int(callback.data.split(":")[-1])
            telegram_user_id = callback.from_user.id
            logger.info(f"User {telegram_user_id} confirmed plan ID: {plan_id}")
            
            session = session_pool()
            
            user_service = UserService(session)
            db_user = user_service.get_user_by_telegram_id(telegram_user_id)
            
            if not db_user:
                logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                return
            
            plan_service = PlanService(session)
            plan = plan_service.get_plan_by_id(plan_id)
            
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
            session.commit()
            logger.info(f"Created new order ID: {new_order.id} for user {telegram_user_id} (DB ID: {db_user.id})")
            
            text = (
                f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
                f"🔹 شناسه سفارش: {new_order.id}\n"
                f"🔹 نام پلن: {plan.name}\n"
                f"🔹 مبلغ: {int(plan.price):,} تومان\n\n"
                f"سفارش شما در انتظار پرداخت است. لطفاً روش پرداخت را انتخاب کنید."
            )
            
            await callback.message.edit_text(text=text)
            
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in confirm_plan_callback for user {callback.from_user.id}: {e}", exc_info=True)
            if session:
                try:
                    session.rollback()
                    logger.info("Session rolled back due to error in confirm_plan_callback.")
                except Exception as rb_err:
                    logger.error(f"Error during rollback: {rb_err}", exc_info=True)
            await callback.answer("خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in confirm_plan_callback")
    
    @router.callback_query(F.data == "back_to_plans")
    async def back_to_plans_callback(callback: CallbackQuery):
        """بازگشت به لیست پلن‌ها"""
        session = None # مقداردهی اولیه
        try:
            session = session_pool()
            plan_service = PlanService(session)
            plans = plan_service.get_all_active_plans()
            
            await callback.message.edit_text(
                text="🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
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
