"""
سرویس مدیریت سفارشات و عملیات مربوط به آنها
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.order import Order
from db.models.enums import OrderStatus
from db.repositories.order_repo import OrderRepository
from db.schemas.order import OrderCreate, OrderUpdate
from core.services.notification_service import NotificationService
from core.services.payment_service import PaymentService
from db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

class OrderService:
    """سرویس مدیریت سفارشات با منطق کسب و کار مرتبط"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه سرویس"""
        self.session = session
        self.order_repo = OrderRepository(session)
        self.notification_service = NotificationService(session)
        self.payment_service = PaymentService(session)
        self.user_repo = UserRepository(session)
    
    async def create_order(
        self,
        user_id: int,
        plan_id: int,
        location_name: str,
        amount: Decimal,
        status: OrderStatus = OrderStatus.PENDING
    ) -> Optional[Order]:
        """
        Creates a new order and commits the transaction.
        """
        order_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "location_name": location_name,
            "amount": amount,
            "status": status,
        }
        try:
            order = await self.order_repo.create(order_data)
            await self.session.commit()
            await self.session.refresh(order)
            logger.info(f"Created and committed new order {order.id} for user {user_id}, plan {plan_id}")
            return order
        except Exception as e:
            logger.error(f"Failed to create order for user {user_id}, plan {plan_id}: {e}", exc_info=True)
            await self.session.rollback()
            return None
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order details by ID using the repository."""
        return await self.order_repo.get_by_id(order_id)
    
    async def get_user_orders(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Order]:
        """Get a list of orders for a user using the repository."""
        return await self.order_repo.get_by_user_id(user_id)
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """
        Update the status of an order using the repository and commit.
        """
        try:
            updated_order = await self.order_repo.update_status(order_id, new_status)
            if updated_order:
                 await self.session.commit()
                 await self.session.refresh(updated_order)
                 if new_status == OrderStatus.PAID:
                     logger.info(f"Order {order_id} status updated to PAID and committed. Further processing might be needed.")
                 return updated_order
            else:
                 logger.warning(f"Attempted to update status for non-existent order {order_id}")
                 return None
        except Exception as e:
             logger.error(f"Failed to update status for order {order_id} to {new_status}: {e}", exc_info=True)
             await self.session.rollback()
             return None
    
    async def attempt_payment_from_wallet(self, order_id: int) -> Tuple[bool, str]:
        """
        Attempts to pay for an order using the user's wallet balance via PaymentService.
        Updates order status based on payment result. Commits the entire transaction.
        """
        async with self.session.begin_nested():
            order = await self.get_order_by_id(order_id)
            if not order:
                return False, "سفارش یافت نشد."

            if order.status != OrderStatus.PENDING:
                return False, "وضعیت سفارش معتبر نیست (باید در انتظار پرداخت باشد)."

            logger.info(f"Attempting wallet payment for order {order_id}, amount {order.amount}")

            payment_success, payment_message = await self.payment_service.pay_from_wallet(
                user_id=order.user_id,
                amount=order.amount,
                description=f"Payment for Order #{order_id}",
                order_id=order.id
            )

            if payment_success:
                 logger.info(f"Wallet payment successful for order {order_id}. Transaction ID: {payment_message}")
                 updated_order_in_mem = await self.order_repo.update_status(order_id, OrderStatus.PAID)
                 if not updated_order_in_mem:
                     logger.error(f"Wallet payment successful for order {order_id}, but failed to stage order status update.")
                     raise Exception("Failed to stage order status update after payment")
                 
                 try:
                     await self.session.commit()
                     order = await self.get_order_by_id(order_id)
                     user = await self.user_repo.get_by_id(order.user_id)
                     current_balance = await self.payment_service.wallet_service.get_balance(order.user_id)
                     
                     if user and current_balance is not None:
                         success_message = (
                             f"✅ پرداخت سفارش با موفقیت انجام شد\n\n"
                             f"🔢 شناسه سفارش: #{order.id}\n"
                             f"💰 مبلغ پرداختی: {order.amount} تومان\n"
                             f"💼 موجودی فعلی: {Decimal(current_balance):.2f} تومان\n\n"
                             f"🕒 اکانت شما در حال آماده‌سازی است..."
                         )
                         await self.notification_service.notify_user(user.telegram_id, success_message)
                         admin_message = (
                             f"💲 پرداخت جدید از کیف پول:\n\n"
                             f"👤 کاربر: {user.telegram_id} (ID: {user.user_id})\n"
                             f"🔢 شناسه سفارش: #{order.id}\n"
                             f"💰 مبلغ: {order.amount} تومان"
                         )
                         await self.notification_service.notify_admin(admin_message)
                     return True, "پرداخت با موفقیت انجام و سفارش به‌روز شد."
                 except Exception as commit_err:
                     logger.error(f"Commit failed after successful wallet payment for order {order_id}: {commit_err}", exc_info=True)
                     return False, "پرداخت انجام شد اما در ثبت نهایی وضعیت سفارش خطایی رخ داد."
            else:
                 logger.warning(f"Wallet payment failed for order {order_id}: {payment_message}")
                 return False, payment_message

        return False, "خطای ناشناخته در فرآیند پرداخت با کیف پول." 