"""
سرویس مدیریت سفارشات و عملیات مربوط به آنها
"""

import logging
from typing import Optional, List, Tuple, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.order import Order
from db.models.enums import OrderStatus
from db.repositories.order_repo import OrderRepository
from db.schemas.order import OrderCreate, OrderUpdate
from core.services.notification_service import NotificationService
# Fix the circular import
# from core.services.payment_service import PaymentService, InsufficientFundsError
from core.services.account_service import AccountService
from core.services.panel_service import PanelService
from core.services.client_service import ClientService
from core.services.inbound_service import InboundService
from db.repositories.user_repo import UserRepository
from db.repositories.plan_repo import PlanRepository
from db.models.transaction import Transaction
from db.models.client_account import ClientAccount

logger = logging.getLogger(__name__)

class OrderError(Exception):
    """پایه خطاهای سفارش"""
    pass

class OrderCreationError(OrderError):
    """خطای ایجاد سفارش"""
    pass

class PaymentProcessingError(OrderError):
    """خطای پردازش پرداخت"""
    pass

class AccountProvisioningError(OrderError):
    """خطای ایجاد اکانت"""
    pass

# Define InsufficientFundsError here instead of importing it
class InsufficientFundsError(OrderError):
    """خطای کمبود موجودی کیف پول"""
    pass

class OrderService:
    """سرویس مدیریت سفارشات با منطق کسب و کار مرتبط"""
    
    def __init__(
        self, 
        session: AsyncSession,
        payment_service: Optional[Any] = None,
        account_service: Optional[AccountService] = None,
        panel_service: Optional[PanelService] = None,
        client_service: Optional[ClientService] = None,
        inbound_service: Optional[InboundService] = None
    ):
        """مقداردهی اولیه سرویس"""
        self.session = session
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)
        self.plan_repo = PlanRepository(session)
        self.notification_service = NotificationService(session)
        
        # Initialize dependent services if not provided
        self.payment_service = payment_service
        if not self.payment_service:
            # Import here to avoid circular import
            from core.services.payment_service import PaymentService
            self.payment_service = PaymentService(session)
        
        # For account_service, we need panel_service and client_service
        if not panel_service:
            panel_service = PanelService(session)
        self.panel_service = panel_service
        
        if not client_service:
            client_service = ClientService(
                session=session,
                client_repo=None,  # These will be initialized within the service
                order_repo=None,
                panel_repo=None,
                inbound_repo=None,
                user_repo=None,
                plan_repo=None,
                renewal_log_repo=None,
                panel_service=panel_service
            )
        self.client_service = client_service
        
        if not inbound_service:
            inbound_service = InboundService(session)
        self.inbound_service = inbound_service
        
        if not account_service:
            account_service = AccountService(
                session=session,
                client_service=client_service,
                panel_service=panel_service
            )
        self.account_service = account_service
    
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
        
        Args:
            user_id: شناسه کاربر
            plan_id: شناسه پلن
            location_name: نام لوکیشن
            amount: مبلغ سفارش
            status: وضعیت اولیه سفارش (پیش‌فرض: در انتظار پرداخت)
            
        Returns:
            شیء Order ایجاد شده یا None در صورت خطا
            
        Raises:
            OrderCreationError: در صورت بروز خطا در ایجاد سفارش
        """
        order_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "location_name": location_name,
            "amount": amount,
            "status": status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        try:
            # Create order in a transaction
            async with self.session.begin_nested() as nested:
                try:
                    order = await self.order_repo.create(order_data)
                    await self.session.flush()
                    logger.info(f"Created order {order.id} for user {user_id}, plan {plan_id}")
                    return order
                except Exception as e:
                    await nested.rollback()
                    logger.error(f"Failed to create order for user {user_id}, plan {plan_id}: {e}", exc_info=True)
                    raise OrderCreationError(f"Failed to create order: {str(e)}")
        except Exception as e:
            logger.error(f"Transaction error while creating order for user {user_id}, plan {plan_id}: {e}", exc_info=True)
            raise OrderCreationError(f"Transaction error: {str(e)}")
    
    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order details by ID using the repository."""
        return await self.order_repo.get_by_id(order_id)
    
    async def get_user_orders(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Order]:
        """Get a list of orders for a user using the repository."""
        return await self.order_repo.get_by_user_id(user_id, limit, offset)
    
    async def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """
        Update the status of an order using the repository and commit the transaction.
        
        Args:
            order_id: شناسه سفارش
            new_status: وضعیت جدید
            
        Returns:
            شیء Order بروزرسانی شده یا None در صورت خطا
            
        Raises:
            OrderError: در صورت بروز خطا در بروزرسانی وضعیت سفارش
        """
        try:
            # Update order status in a transaction
            async with self.session.begin_nested() as nested:
                try:
                    # First check if order exists
                    order = await self.get_order_by_id(order_id)
                    if not order:
                        logger.warning(f"Attempted to update status for non-existent order {order_id}")
                        return None
                        
                    # Update the order status
                    updated_order = await self.order_repo.update_status(order_id, new_status)
                    if updated_order:
                        await self.session.flush()
                        logger.info(f"Order {order_id} status updated to {new_status}")
                        return updated_order
                    else:
                        logger.warning(f"Failed to update status for order {order_id}")
                        return None
                except Exception as e:
                    await nested.rollback()
                    logger.error(f"Failed to update status for order {order_id} to {new_status}: {e}", exc_info=True)
                    raise OrderError(f"Failed to update order status: {str(e)}")
        except Exception as e:
            logger.error(f"Transaction error while updating order {order_id} status: {e}", exc_info=True)
            raise OrderError(f"Transaction error: {str(e)}")
    
    async def process_order_purchase(
        self,
        user_id: int,
        plan_id: int,
        location_name: str,
        payment_method: str = "wallet",  # "wallet" or "receipt"
        discount_code: Optional[str] = None,
        send_notifications: bool = True
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        پردازش کامل فرآیند خرید از ابتدا تا انتها در یک تراکنش اتمیک.
        این متد شامل ایجاد سفارش، پردازش پرداخت و ساخت اکانت است.
        
        Process the complete purchase flow in a single atomic transaction.
        This method orchestrates order creation, payment processing, and account provisioning.
        
        Args:
            user_id: شناسه کاربر
            plan_id: شناسه پلن
            location_name: نام لوکیشن
            payment_method: روش پرداخت ("wallet" یا "receipt")
            discount_code: کد تخفیف (اختیاری)
            send_notifications: ارسال نوتیفیکیشن به کاربر
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]:
            - موفقیت عملیات (bool)
            - پیام نتیجه (str)
            - داده‌های نتیجه شامل order، transaction و account (Dict)
            
        Raises:
            OrderError: در صورت بروز خطا در هر مرحله از فرآیند
        """
        logger.info(f"Starting order purchase process for user {user_id}, plan {plan_id}, location {location_name}")
        
        # Initialize result data
        result_data = {
            "order": None,
            "transaction": None,
            "account": None,
            "amount": None,
            "discount_applied": False,
            "discount_amount": Decimal('0')
        }
        
        # Start an atomic transaction for the entire process
        async with self.session.begin():
            try:
                # 1. Get plan details
                plan = await self.plan_repo.get_by_id(plan_id)
                if not plan:
                    logger.error(f"Plan with ID {plan_id} not found")
                    raise OrderError(f"پلن با شناسه {plan_id} یافت نشد")
                
                # Store original price
                original_amount = plan.price
                final_amount = original_amount
                result_data["amount"] = final_amount
                
                # 2. Apply discount if provided
                discount_code_obj = None
                if discount_code:
                    discount_success, discount_message, discounted_amount, discount_code_obj = (
                        await self.payment_service.validate_and_apply_discount(
                            code=discount_code,
                            user_id=user_id,
                            plan_id=plan_id,
                            original_amount=original_amount
                        )
                    )
                    
                    if discount_success:
                        final_amount = discounted_amount
                        result_data["amount"] = final_amount
                        result_data["discount_applied"] = True
                        result_data["discount_amount"] = original_amount - final_amount
                        logger.info(f"Discount applied for user {user_id}: original={original_amount}, final={final_amount}")
                    else:
                        logger.warning(f"Discount code validation failed for user {user_id}, code '{discount_code}': {discount_message}")
                        # Continue without discount
                
                # 3. Create order with PENDING status
                order = await self.create_order(
                    user_id=user_id,
                    plan_id=plan_id,
                    location_name=location_name,
                    amount=final_amount,
                    status=OrderStatus.PENDING
                )
                result_data["order"] = order
                logger.info(f"Order created: ID={order.id}, amount={final_amount}")
                
                # 4. Process payment based on method
                transaction = None
                if payment_method == "wallet":
                    try:
                        # Process wallet payment
                        payment_success, payment_message, transaction = await self.payment_service.pay_from_wallet(
                            user_id=user_id,
                            amount=final_amount,
                            description=f"Payment for Order #{order.id}",
                            order_id=order.id
                        )
                        
                        if not payment_success:
                            logger.error(f"Wallet payment failed for order {order.id}: {payment_message}")
                            raise PaymentProcessingError(f"پرداخت ناموفق: {payment_message}")
                            
                        result_data["transaction"] = transaction
                        logger.info(f"Payment successful for order {order.id}")
                        
                        # Update order status to PAID
                        await self.update_order_status(order.id, OrderStatus.PAID)
                        
                    except InsufficientFundsError as e:
                        # Handle insufficient funds specifically
                        logger.warning(f"Insufficient funds for order {order.id}: {str(e)}")
                        raise PaymentProcessingError("موجودی کیف پول کافی نیست.")
                        
                elif payment_method == "receipt":
                    # For receipt payment, we just mark the order as PENDING_RECEIPT
                    # It will be processed when admin approves the receipt
                    await self.update_order_status(order.id, OrderStatus.PENDING_RECEIPT)
                    logger.info(f"Order {order.id} status set to PENDING_RECEIPT for manual receipt approval")
                    
                    # For receipt payment, we stop here and return success with no account
                    # The account will be provisioned when the receipt is approved
                    return True, "سفارش شما ثبت شد. پس از بارگذاری و تأیید رسید، اکانت شما ایجاد خواهد شد.", result_data
                    
                else:
                    logger.error(f"Invalid payment method '{payment_method}' for order {order.id}")
                    raise PaymentProcessingError(f"روش پرداخت '{payment_method}' نامعتبر است")
                
                # 5. Find suitable panel and inbound based on location
                suitable_panel = await self.panel_service.get_suitable_panel_for_location(location_name)
                if not suitable_panel:
                    logger.error(f"No suitable panel found for location '{location_name}'")
                    raise AccountProvisioningError(f"پنل مناسب برای لوکیشن '{location_name}' یافت نشد")
                
                suitable_inbound = await self.inbound_service.get_suitable_inbound(suitable_panel.id)
                if not suitable_inbound:
                    logger.error(f"No suitable inbound found on panel {suitable_panel.id}")
                    # Payment successful but no suitable inbound found - rollback handled by session
                    raise AccountProvisioningError(f"اینباند مناسب برای پنل یافت نشد")
                
                # 6. Provision the account
                try:
                    account = await self.account_service.provision_account(
                        user_id=user_id,
                        plan=plan,
                        inbound=suitable_inbound,
                        panel=suitable_panel,
                        order_id=order.id
                    )
                    
                    if not account:
                        # Payment successful but account creation failed - rollback handled by session
                        logger.error(f"Failed to provision account for order {order.id}")
                        raise AccountProvisioningError("ایجاد اکانت با خطا مواجه شد")
                    
                    result_data["account"] = account
                    logger.info(f"Account provisioned successfully for order {order.id}, account ID: {account.id}")
                    
                    # 7. Update order status to COMPLETED
                    await self.update_order_status(order.id, OrderStatus.COMPLETED)
                
                except Exception as account_error:
                    logger.error(f"Account creation failed after successful payment: {account_error}", exc_info=True)
                    # Since we're in a transaction, this will be rolled back automatically
                    raise AccountProvisioningError(f"خطا در ایجاد اکانت پس از پرداخت موفق: {str(account_error)}")
                
                # 8. Send notifications if requested
                if send_notifications:
                    await self._send_purchase_notifications(
                        user_id=user_id,
                        order=order,
                        account=account,
                        transaction=transaction,
                        discount_applied=result_data["discount_applied"],
                        discount_amount=result_data["discount_amount"]
                    )
                
                # Successful completion of all steps
                return True, "خرید با موفقیت انجام شد. اکانت شما آماده استفاده است.", result_data
                
            except OrderCreationError as e:
                logger.error(f"Order creation error: {e}", exc_info=True)
                # Transaction will be rolled back automatically
                return False, f"خطا در ایجاد سفارش: {str(e)}", result_data
                
            except PaymentProcessingError as e:
                logger.error(f"Payment processing error: {e}", exc_info=True)
                # Transaction will be rolled back automatically
                return False, f"خطا در پردازش پرداخت: {str(e)}", result_data
                
            except AccountProvisioningError as e:
                logger.error(f"Account provisioning error: {e}", exc_info=True)
                # Transaction will be rolled back automatically - no manual refund needed
                return False, f"خطا در ایجاد اکانت: {str(e)}", result_data
                
            except Exception as e:
                logger.error(f"Unexpected error in order purchase process: {e}", exc_info=True)
                # Transaction will be rolled back automatically
                return False, f"خطای سیستمی در فرآیند خرید: {str(e)}", result_data
    
    async def attempt_payment_from_wallet(self, order_id: int) -> Tuple[bool, str]:
        """
        Attempts to pay for an order using the user's wallet balance.
        Updates order status based on payment result and provisions account if successful.
        
        این متد برای حفظ سازگاری با کد قبلی باقی مانده اما به فرم جدید process_order_purchase هدایت می‌شود.
        
        Args:
            order_id: شناسه سفارش
            
        Returns:
            Tuple[bool, str]: نتیجه عملیات و پیام مرتبط
        """
        logger.info(f"Attempting wallet payment for order {order_id} (legacy method)")
        
        # Get order details
        order = await self.get_order_by_id(order_id)
        if not order:
            return False, "سفارش یافت نشد."

        if order.status != OrderStatus.PENDING:
            return False, "وضعیت سفارش معتبر نیست (باید در انتظار پرداخت باشد)."
            
        # Get user and plan details for the order
        user = await self.user_repo.get_by_id(order.user_id)
        plan = await self.plan_repo.get_by_id(order.plan_id)
        
        if not user or not plan:
            return False, "اطلاعات کاربر یا پلن یافت نشد."
            
        try:
            success, message, result_data = await self.process_order_purchase(
                user_id=order.user_id,
                plan_id=order.plan_id,
                location_name=order.location_name,
                payment_method="wallet",
                discount_code=None,  # No discount here as price already set in order
                send_notifications=True
            )
            
            return success, message
        except Exception as e:
            logger.error(f"Error in attempt_payment_from_wallet for order {order_id}: {e}", exc_info=True)
            return False, f"خطا در پردازش پرداخت: {str(e)}"
    
    async def process_receipt_approval(self, order_id: int, approved_by_user_id: int) -> Tuple[bool, str, Optional[ClientAccount]]:
        """
        پردازش تأیید رسید و ایجاد اکانت برای سفارش‌های پرداخت با رسید.
        
        Process receipt approval for orders with receipt payment method.
        Updates order status, provisions account, and sends notifications.
        
        Args:
            order_id: شناسه سفارش
            approved_by_user_id: شناسه کاربر (ادمین) تأیید کننده
            
        Returns:
            Tuple[bool, str, Optional[ClientAccount]]: نتیجه عملیات، پیام و اکانت ایجاد شده
        """
        logger.info(f"Processing receipt approval for order {order_id} by admin {approved_by_user_id}")
        
        # Get order details
        order = await self.get_order_by_id(order_id)
        if not order:
            logger.error(f"Order {order_id} not found for receipt approval")
            return False, "سفارش یافت نشد.", None
            
        if order.status != OrderStatus.PENDING_RECEIPT:
            logger.error(f"Invalid order status for receipt approval: {order.status}")
            return False, f"وضعیت سفارش برای تأیید رسید معتبر نیست: {order.status}", None
            
        # Start a transaction for the approval process
        async with self.session.begin():
            try:
                # 1. Update order status to PAID
                await self.update_order_status(order.id, OrderStatus.PAID)
                logger.info(f"Order {order.id} status updated to PAID after receipt approval")
                
                # 2. Get required data
                user = await self.user_repo.get_by_id(order.user_id)
                plan = await self.plan_repo.get_by_id(order.plan_id)
                
                if not user or not plan:
                    logger.error(f"User {order.user_id} or plan {order.plan_id} not found")
                    raise OrderError("اطلاعات کاربر یا پلن یافت نشد")
                
                # 3. Find suitable panel and inbound
                suitable_panel = await self.panel_service.get_suitable_panel_for_location(order.location_name)
                if not suitable_panel:
                    logger.error(f"No suitable panel found for location '{order.location_name}'")
                    raise AccountProvisioningError(f"پنل مناسب برای لوکیشن '{order.location_name}' یافت نشد")
                
                suitable_inbound = await self.inbound_service.get_suitable_inbound(suitable_panel.id)
                if not suitable_inbound:
                    logger.error(f"No suitable inbound found on panel {suitable_panel.id}")
                    raise AccountProvisioningError(f"اینباند مناسب برای پنل یافت نشد")
                
                # 4. Provision the account - this should be an atomic operation
                try:
                    account = await self.account_service.provision_account(
                        user_id=user.id,
                        plan=plan,
                        inbound=suitable_inbound,
                        panel=suitable_panel,
                        order_id=order.id
                    )
                    
                    if not account:
                        logger.error(f"Failed to provision account for order {order.id}")
                        raise AccountProvisioningError("ایجاد اکانت با خطا مواجه شد")
                    
                    logger.info(f"Account provisioned successfully for order {order.id}, account ID: {account.id}")
                    
                    # 5. Update order status to COMPLETED only if account creation was successful
                    await self.update_order_status(order.id, OrderStatus.COMPLETED)
                
                except Exception as account_error:
                    logger.error(f"Account creation failed after receipt approval: {account_error}", exc_info=True)
                    # Since we're in a transaction, this will be rolled back automatically
                    raise AccountProvisioningError(f"خطا در ایجاد اکانت پس از تأیید رسید: {str(account_error)}")
                
                # 6. Send notifications
                await self._send_receipt_approval_notifications(
                    user_id=user.id,
                    order=order,
                    account=account,
                    approved_by_user_id=approved_by_user_id
                )
                
                return True, "رسید تأیید و اکانت با موفقیت ایجاد شد.", account
                
            except OrderError as e:
                logger.error(f"Order error in receipt approval for order {order_id}: {e}", exc_info=True)
                # Transaction will be rolled back automatically
                return False, f"خطا در پردازش تأیید رسید: {str(e)}", None
                
            except AccountProvisioningError as e:
                logger.error(f"Account provisioning error in receipt approval for order {order_id}: {e}", exc_info=True)
                # Transaction will be rolled back automatically
                return False, f"خطا در ایجاد اکانت: {str(e)}", None
                
            except Exception as e:
                logger.error(f"Unexpected error in process_receipt_approval for order {order_id}: {e}", exc_info=True)
                # Transaction will be rolled back automatically
                return False, f"خطای سیستمی در پردازش تأیید رسید: {str(e)}", None
    
    async def _send_purchase_notifications(
        self,
        user_id: int,
        order: Order,
        account: ClientAccount,
        transaction: Optional[Transaction] = None,
        discount_applied: bool = False,
        discount_amount: Decimal = Decimal('0')
    ) -> None:
        """
        Send notifications to the user about a successful purchase.
        
        Args:
            user_id: شناسه کاربر
            order: شیء سفارش
            account: شیء اکانت ایجاد شده
            transaction: شیء تراکنش (اختیاری)
            discount_applied: آیا تخفیف اعمال شده است
            discount_amount: مقدار تخفیف
        """
        try:
            # Get user details
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.telegram_id:
                logger.warning(f"Can't send notification to user {user_id} - user not found or no telegram_id")
                return

            # Get plan details
            plan = await self.plan_repo.get_by_id(order.plan_id)
            if not plan:
                logger.warning(f"Can't get plan details for notification to user {user_id}, plan {order.plan_id}")
                plan_info = "پلن خریداری شده"
            else:
                plan_info = f"{plan.name} ({plan.data_limit}GB / {plan.duration_days} روز)"

            # Format the purchase notification
            message_parts = [
                f"✅ خرید شما با موفقیت انجام شد!",
                f"",
                f"🔹 سفارش: #{order.id}",
                f"🔹 پلن: {plan_info}",
                f"🔹 لوکیشن: {order.location_name}",
            ]

            if discount_applied:
                discount_formatted = f"{discount_amount:,.0f} تومان"
                message_parts.append(f"🔹 تخفیف: {discount_formatted}")

            amount_formatted = f"{order.amount:,.0f} تومان"
            message_parts.append(f"🔹 مبلغ پرداختی: {amount_formatted}")

            if transaction:
                message_parts.append(f"🔹 شناسه تراکنش: #{transaction.id}")

            message_parts.extend([
                f"",
                f"🔗 لینک اشتراک:",
                f"<code>{account.subscription_url}</code>",
                f"",
                f"🔄 برای تمدید اشتراک می‌توانید از منوی «خرید و تمدید» اقدام نمایید."
            ])

            # Send the notification
            message = "\n".join(message_parts)
            await self.notification_service.send_message(
                user_id=user.telegram_id,
                text=message,
                parse_mode="HTML"
            )

            # Optionally, also send QR code if available
            qr_base64 = getattr(account, 'qr_base64', None)
            if not qr_base64 and getattr(account, 'qr_code_path', None):
                # تلاش برای تولید base64 از فایل در صورت نبود مقدار
                import os, base64
                qr_path = account.qr_code_path
                if os.path.exists(qr_path):
                    with open(qr_path, "rb") as f:
                        qr_base64 = base64.b64encode(f.read()).decode("utf-8")
            if qr_base64:
                await self.notification_service.send_photo_base64(
                    user_id=user.telegram_id,
                    base64_data=qr_base64,
                    caption="QR Code اشتراک شما"
                )

            logger.info(f"Purchase notifications sent to user {user_id} for order {order.id}")
        except Exception as e:
            # Don't let notification errors affect the main purchase process
            logger.error(f"Error sending purchase notifications to user {user_id}: {e}", exc_info=True)
            # We don't raise the exception here to avoid affecting the main transaction

    async def _send_receipt_approval_notifications(
        self,
        user_id: int,
        order: Order,
        account: ClientAccount,
        approved_by_user_id: int
    ) -> None:
        """
        Send notifications about receipt approval and account creation.
        
        Args:
            user_id: شناسه کاربر
            order: شیء سفارش
            account: شیء اکانت ایجاد شده
            approved_by_user_id: شناسه کاربر (ادمین) تأیید کننده
        """
        try:
            # Get user details
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.telegram_id:
                logger.warning(f"Can't send notification to user {user_id} - user not found or no telegram_id")
                return

            # Get plan details
            plan = await self.plan_repo.get_by_id(order.plan_id)
            if not plan:
                logger.warning(f"Can't get plan details for notification to user {user_id}, plan {order.plan_id}")
                plan_info = "پلن خریداری شده"
            else:
                plan_info = f"{plan.name} ({plan.data_limit}GB / {plan.duration_days} روز)"

            # Format the approved receipt notification
            message_parts = [
                f"✅ رسید پرداخت شما تأیید شد!",
                f"",
                f"🔹 سفارش: #{order.id}",
                f"🔹 پلن: {plan_info}",
                f"🔹 لوکیشن: {order.location_name}",
                f"🔹 مبلغ: {order.amount:,.0f} تومان",
                f"",
                f"🔗 لینک اشتراک:",
                f"<code>{account.subscription_url}</code>",
                f"",
                f"🔄 برای تمدید اشتراک می‌توانید از منوی «خرید و تمدید» اقدام نمایید."
            ]

            # Send the notification
            message = "\n".join(message_parts)
            await self.notification_service.send_message(
                user_id=user.telegram_id,
                text=message,
                parse_mode="HTML"
            )

            # Optionally, also send QR code if available
            qr_base64 = getattr(account, 'qr_base64', None)
            if not qr_base64 and getattr(account, 'qr_code_path', None):
                # تلاش برای تولید base64 از فایل در صورت نبود مقدار
                import os, base64
                qr_path = account.qr_code_path
                if os.path.exists(qr_path):
                    with open(qr_path, "rb") as f:
                        qr_base64 = base64.b64encode(f.read()).decode("utf-8")
            if qr_base64:
                await self.notification_service.send_photo_base64(
                    user_id=user.telegram_id,
                    base64_data=qr_base64,
                    caption="QR Code اشتراک شما"
                )

            # Notify admin/approver if different from system
            admin = await self.user_repo.get_by_id(approved_by_user_id)
            if admin and admin.telegram_id and admin.id != user.id:
                admin_message = f"✓ تأیید رسید برای سفارش #{order.id} انجام و اکانت کاربر ایجاد شد."
                await self.notification_service.send_message(
                    user_id=admin.telegram_id,
                    text=admin_message
                )

            logger.info(f"Receipt approval notifications sent to user {user_id} for order {order.id}")
        except Exception as e:
            # Don't let notification errors affect the main approval process
            logger.error(f"Error sending receipt approval notifications: {e}", exc_info=True)
            # We don't raise the exception here to avoid affecting the main transaction 