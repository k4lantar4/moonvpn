"""
سرویس مدیریت سفارشات و عملیات مربوط به آنها
"""

import logging
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.order import Order, OrderStatus
from db.models.user import User
from db.models.transaction import Transaction, TransactionType, TransactionStatus
from core.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class OrderService:
    """سرویس مدیریت سفارشات با منطق کسب و کار مرتبط"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه سرویس"""
        self.session = session
        self.notification_service = NotificationService(session)
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        دریافت اطلاعات یک سفارش با شناسه آن
        
        Args:
            order_id: شناسه سفارش
        
        Returns:
            اطلاعات سفارش یا None در صورت عدم وجود
        """
        query = select(Order).where(Order.id == order_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """
        دریافت تمام سفارشات یک کاربر
        
        Args:
            user_id: شناسه کاربر
        
        Returns:
            لیست سفارشات کاربر
        """
        query = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """
        به‌روزرسانی وضعیت سفارش
        
        Args:
            order_id: شناسه سفارش
            new_status: وضعیت جدید
            
        Returns:
            سفارش به‌روزرسانی شده یا None در صورت عدم وجود
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        
        order.status = new_status
        
        # اگر وضعیت پردازش یا انجام شده باشد، تاریخ پردازش را ثبت کنیم
        if new_status in [OrderStatus.PROCESSING, OrderStatus.DONE]:
            order.processed_at = datetime.now()
        
        await self.session.commit()
        await self.session.refresh(order)
        return order
    
    async def pay_with_balance(self, order_id: int) -> Tuple[bool, str]:
        """
        پرداخت سفارش با استفاده از موجودی کیف پول کاربر
        
        Args:
            order_id: شناسه سفارش
            
        Returns:
            tuple[bool, str]: وضعیت موفقیت و پیام متناسب
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            logger.error(f"Order with ID {order_id} not found")
            return False, "سفارش مورد نظر یافت نشد"
        
        if order.status != OrderStatus.PENDING:
            logger.error(f"Order {order_id} is not in PENDING status")
            return False, "این سفارش قبلاً پرداخت شده است"
        
        # دریافت اطلاعات کاربر
        user_result = await self.session.execute(select(User).where(User.id == order.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            logger.error(f"User with ID {order.user_id} for order {order_id} not found")
            return False, "کاربر مرتبط با سفارش یافت نشد"
        
        # بررسی موجودی کافی
        if user.balance < order.amount:
            logger.info(f"Insufficient balance for user {user.id} to pay order {order_id}: {user.balance} < {order.amount}")
            return False, "موجودی کیف پول کافی نیست"
        
        try:
            # ایجاد تراکنش خرید
            transaction = Transaction(
                user_id=user.id,
                order_id=order.id,
                amount=order.amount,
                type=TransactionType.PURCHASE,
                status=TransactionStatus.SUCCESS,
                created_at=datetime.now()
            )
            self.session.add(transaction)
            
            # کاهش موجودی کاربر
            user.balance -= order.amount
            
            # تغییر وضعیت سفارش به پرداخت شده
            order.status = OrderStatus.PAID
            
            # ثبت تغییرات در دیتابیس
            await self.session.commit()
            
            # ارسال نوتیفیکیشن به کاربر
            success_message = (
                f"✅ پرداخت سفارش با موفقیت انجام شد\n\n"
                f"🔢 شناسه سفارش: #{order.id}\n"
                f"💰 مبلغ پرداختی: {order.amount} تومان\n"
                f"💼 موجودی فعلی: {user.balance} تومان\n\n"
                f"🕒 اکانت شما در حال آماده‌سازی است و بزودی برای شما ارسال خواهد شد."
            )
            await self.notification_service.notify_user(user.telegram_id, success_message)
            
            # ارسال نوتیفیکیشن به ادمین
            admin_message = (
                f"💲 پرداخت جدید از کیف پول:\n\n"
                f"👤 کاربر: {user.telegram_id}\n"
                f"🔢 شناسه سفارش: #{order.id}\n"
                f"💰 مبلغ: {order.amount} تومان"
            )
            await self.notification_service.notify_admin(admin_message)
            
            logger.info(f"Order {order_id} paid successfully with user balance")
            return True, "پرداخت با موفقیت انجام شد"
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error processing payment for order {order_id}: {str(e)}", exc_info=True)
            return False, f"خطا در پردازش پرداخت: {str(e)}" 