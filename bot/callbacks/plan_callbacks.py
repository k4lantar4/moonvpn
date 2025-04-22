"""
پردازش کالبک‌های مربوط به انتخاب پلن
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.plan_service import PlanService
from core.services.payment_service import PaymentService
from db.models.plan import Plan

router = Router()
logger = logging.getLogger(__name__)

def register_plan_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]):
    """ثبت فرمان callback های مربوط به پلن"""
    
    @router.callback_query(F.data.startswith("select_plan:"))
    async def handle_plan_selection(callback: CallbackQuery):
        """پردازش انتخاب پلن توسط کاربر"""
        try:
            # استخراج شناسه پلن از کالبک
            plan_id = int(callback.data.split(":")[1])
            
            async with session_pool() as session:
                # دریافت اطلاعات پلن
                plan_service = PlanService(session)
                plan = await plan_service.get_plan_by_id(plan_id)
                
                if not plan:
                    await callback.answer("❌ پلن مورد نظر یافت نشد", show_alert=True)
                    return
                    
                # ایجاد لینک پرداخت
                payment_service = PaymentService(session)
                payment_link = await payment_service.create_payment_link(
                    user_id=callback.from_user.id,
                    plan_id=plan.id,
                    amount=plan.price
                )
                
                # ارسال پیام با لینک پرداخت
                await callback.message.edit_text(
                    f"🛍 پلن انتخابی شما:\n\n"
                    f"📦 نام: {plan.name}\n"
                    f"💾 حجم: {plan.traffic_gb} گیگابایت\n"
                    f"⏱ مدت: {plan.duration_days} روز\n"
                    f"💰 قیمت: {plan.price:,} تومان\n\n"
                    f"برای پرداخت روی لینک زیر کلیک کنید:\n"
                    f"{payment_link}"
                )
                
                await callback.answer()
                
        except Exception as e:
            logger.error(f"Error in plan selection: {e}")
            await callback.answer("❌ خطا در پردازش درخواست", show_alert=True) 