"""
سرویس مدیریت کیف پول و تراکنش‌ها
"""

import logging
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from core.services.wallet_service import WalletService
from core.services.transaction_service import TransactionService
from core.services.notification_service import NotificationService
from db.repositories.user_repo import UserRepository
from db.repositories.receipt_log_repository import ReceiptLogRepository
from db.repositories.bank_card_repository import BankCardRepository
from db.repositories.discount_code_repo import DiscountCodeRepository
from db.models.transaction import Transaction
from db.models.receipt_log import ReceiptLog
from db.models.user import User
from db.models.bank_card import BankCard
from db.models.discount_code import DiscountCode
from bot.keyboards.receipt_keyboards import get_receipt_admin_keyboard
from bot.utils import format_currency

# Define constants for transaction types/status
TRANSACTION_TYPE_DEPOSIT = 'deposit'
TRANSACTION_TYPE_PURCHASE = 'purchase'
TRANSACTION_TYPE_REFUND = 'refund'
TRANSACTION_STATUS_PENDING = 'pending'
TRANSACTION_STATUS_SUCCESS = 'completed'
TRANSACTION_STATUS_FAILED = 'failed'

logger = logging.getLogger(__name__)

class PaymentError(Exception):
    """پایه خطاهای پرداخت"""
    pass

class InsufficientFundsError(PaymentError):
    """خطای کمبود موجودی کیف پول"""
    pass

class WalletAdjustmentError(PaymentError):
    """خطای تنظیم موجودی کیف پول"""
    pass

class TransactionRecordError(PaymentError):
    """خطای ثبت تراکنش"""
    pass

class DiscountCodeError(PaymentError):
    """خطای کد تخفیف"""
    pass

class PaymentService:
    """سرویس مدیریت پرداخت و تراکنش‌ها با منطق کسب و کار مرتبط"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه سرویس"""
        self.session = session
        self.wallet_service = WalletService(session)
        self.transaction_service = TransactionService(session)
        self.notification_service = NotificationService(session)
        self.user_repo = UserRepository(session)
        self.receipt_repo = ReceiptLogRepository(session)
        self.bank_card_repo = BankCardRepository(session)
        self.discount_repo = DiscountCodeRepository(session)
    
    async def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: str,
        status: str,
        description: Optional[str] = None,
        payment_method: Optional[str] = None,
        reference_id: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        related_entity_type: Optional[str] = None
    ) -> Optional[Transaction]:
        """
        Creates a new transaction using the transaction service.
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ تراکنش
            type: نوع تراکنش
            status: وضعیت تراکنش
            description: توضیحات تراکنش (اختیاری)
            payment_method: روش پرداخت (اختیاری)
            reference_id: شناسه مرجع (اختیاری)
            related_entity_id: شناسه موجودیت مرتبط (اختیاری)
            related_entity_type: نوع موجودیت مرتبط (اختیاری)
            
        Returns:
            Transaction: تراکنش ایجاد شده یا None در صورت خطا
        """
        try:
            transaction = await self.transaction_service.create_transaction(
                user_id=user_id,
                amount=amount,
                type=type,
                status=status,
                description=description,
                payment_method=payment_method,
                related_entity_id=related_entity_id,
                related_entity_type=related_entity_type
            )
            
            if transaction:
                logger.info(f"Created transaction {transaction.id} for user {user_id}: {amount} {type}")
                return transaction
            else:
                logger.error(f"Failed to create transaction for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating transaction for user {user_id}: {e}", exc_info=True)
            return None
        
    async def get_user_balance(self, user_id: int) -> Decimal:
        """
        دریافت موجودی کیف پول کاربر
        این متد از سرویس wallet استفاده می‌کند
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            موجودی کیف پول با نوع Decimal
        """
        balance = await self.wallet_service.get_balance(user_id)
        # اگر موجودی None بود، صفر برمی‌گرداند
        return Decimal(balance) if balance is not None else Decimal('0')
        
    async def process_incoming_payment(
        self,
        user_id: int,
        amount: Decimal,
        description: str = "Wallet recharge",
        gateway_ref: Optional[str] = None # Reference from payment gateway if applicable
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """
        Processes a successful incoming payment (e.g., from a gateway or manual confirmation).
        Creates a transaction, adjusts wallet balance, and notifies.
        
        This method uses flush instead of commit to be part of a larger transaction if needed.
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ واریزی
            description: توضیحات تراکنش
            gateway_ref: شناسه ارجاع درگاه پرداخت (اختیاری)
            
        Returns:
            Tuple[bool, str, Optional[Transaction]]: 
            - موفقیت عملیات (bool)
            - پیام نتیجه (str)
            - تراکنش ثبت شده یا None در صورت خطا (Transaction)
        """
        logger.info(f"Processing incoming payment for user {user_id}: amount={amount}, description='{description}'")
        
        try:
            # Create transaction record first but mark as pending
            transaction = await self.transaction_service.create_transaction(
                user_id=user_id,
                amount=float(amount), 
                type=TRANSACTION_TYPE_DEPOSIT,
                status=TRANSACTION_STATUS_PENDING,  # Start as pending until wallet is updated
                description=description,
                reference_id=gateway_ref
            )
            
            if not transaction:
                logger.error(f"Failed to create transaction record for user {user_id}, amount {amount}")
                raise TransactionRecordError("خطا در ثبت تراکنش")

            # Adjust user's wallet balance
            balance_adjusted = await self.wallet_service.adjust_balance(user_id, float(amount))
            if not balance_adjusted:
                logger.error(f"Failed to adjust wallet balance for user {user_id}, amount {amount}")
                # Update transaction to failed status - no need to raise exception as we'll return error
                await self.transaction_service.update_transaction_status(
                    transaction_id=transaction.id,
                    status=TRANSACTION_STATUS_FAILED,
                    details={"error": "Failed to adjust wallet balance"}
                )
                await self.session.flush()
                return False, "خطا در بروزرسانی موجودی کیف پول", None

            # Mark transaction as successful
            await self.transaction_service.update_transaction_status(
                transaction_id=transaction.id,
                status=TRANSACTION_STATUS_SUCCESS
            )
            
            # Flush to make changes visible in the current transaction
            await self.session.flush()
            
            logger.info(f"Payment processed successfully for user {user_id}: amount={amount}, transaction_id={transaction.id}")
            return True, f"پرداخت با موفقیت انجام شد. شناسه تراکنش: {transaction.id}", transaction

        except Exception as e:
            logger.error(f"Error in process_incoming_payment for user {user_id}: {e}", exc_info=True)
            # If error occurs during the process, changes will be rolled back
            return False, f"خطای سیستمی: {str(e)}", None

    async def pay_from_wallet(
        self,
        user_id: int,
        amount: Decimal,
        description: str,
        order_id: Optional[int] = None # Link transaction to an order if applicable
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """
        Attempts to pay a specific amount from the user's wallet.
        Checks balance, adjusts balance, creates transaction.
        
        This method uses flush instead of commit to be part of a larger transaction.
        It includes improved atomic operations and error handling with proper compensation.
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ پرداختی
            description: توضیحات تراکنش
            order_id: شناسه سفارش مرتبط (اختیاری)
            
        Returns:
            Tuple[bool, str, Optional[Transaction]]: 
            - موفقیت عملیات (bool)
            - پیام نتیجه (str)
            - تراکنش ثبت شده یا None در صورت خطا (Transaction)
            
        Raises:
            InsufficientFundsError: اگر موجودی کافی نباشد
        """
        logger.info(f"Attempting wallet payment for user {user_id}: amount={amount}, order_id={order_id}")
        
        # For zero amount payments (e.g., after 100% discount), skip the actual transaction
        if amount == Decimal('0'):
            logger.info(f"Zero amount payment for user {user_id}, order {order_id} - skipping actual transaction")
            return True, "پرداخت با موفقیت انجام شد (مبلغ صفر)", None
            
        # 1. Check balance
        current_balance = await self.wallet_service.get_balance(user_id)
        if current_balance is None:
            logger.error(f"Could not retrieve balance for user {user_id}")
            return False, "خطا در دریافت موجودی کیف پول", None
            
        if Decimal(current_balance) < amount:
            logger.warning(f"Insufficient funds for user {user_id}: balance={current_balance}, required={amount}")
            raise InsufficientFundsError("موجودی کیف پول کافی نیست")

        # 2. First create transaction as pending to record the intent
        transaction = await self.transaction_service.create_transaction(
            user_id=user_id,
            amount=-float(amount),
            type=TRANSACTION_TYPE_PURCHASE,
            status=TRANSACTION_STATUS_PENDING, # Start as pending until balance is adjusted
            description=description,
            payment_method='wallet',
            related_entity_id=order_id,
            related_entity_type='order' if order_id else None
        )
            
        if not transaction:
            logger.error(f"Failed to create transaction record for user {user_id}, amount -{amount}")
            return False, "خطا در ثبت تراکنش", None

        try:
            # 3. Adjust balance (negative amount for withdrawal)
            balance_adjusted = await self.wallet_service.adjust_balance(user_id, -float(amount))
            if not balance_adjusted:
                logger.error(f"Failed to adjust wallet balance for user {user_id}, amount -{amount}")
                # Update transaction to failed
                await self.transaction_service.update_transaction_status(
                    transaction_id=transaction.id,
                    status=TRANSACTION_STATUS_FAILED,
                    details={"error": "Failed to adjust wallet balance"}
                )
                await self.session.flush()
                return False, "خطا در کسر مبلغ از کیف پول", None

            # 4. Mark transaction as successful now that balance was adjusted
            await self.transaction_service.update_transaction_status(
                transaction_id=transaction.id,
                status=TRANSACTION_STATUS_SUCCESS
            )
            
            # Flush to make changes visible in the current transaction
            await self.session.flush()
            
            logger.info(f"Wallet payment successful for user {user_id}: amount={amount}, transaction_id={transaction.id}")
            return True, str(transaction.id), transaction

        except Exception as e:
            logger.error(f"Error in pay_from_wallet for user {user_id}: {e}", exc_info=True)
            # Mark the transaction as failed
            try:
                await self.transaction_service.update_transaction_status(
                    transaction_id=transaction.id,
                    status=TRANSACTION_STATUS_FAILED,
                    details={"error": str(e)}
                )
                await self.session.flush()
            except Exception as update_error:
                logger.error(f"Error updating transaction status to failed: {update_error}", exc_info=True)
                
            return False, f"خطای سیستمی: {str(e)}", None

    async def validate_and_apply_discount(
        self,
        code: str,
        user_id: int,
        plan_id: int,
        original_amount: Decimal
    ) -> Tuple[bool, str, Decimal, Optional[DiscountCode]]:
        """
        Validates a discount code and calculates the discounted amount if valid.
        
        Args:
            code: کد تخفیف
            user_id: شناسه کاربر
            plan_id: شناسه پلن
            original_amount: مبلغ اصلی
            
        Returns:
            Tuple[bool, str, Decimal, Optional[DiscountCode]]:
            - موفقیت عملیات (bool)
            - پیام نتیجه (str) 
            - مبلغ پس از اعمال تخفیف (Decimal)
            - شیء کد تخفیف یا None اگر نامعتبر باشد (DiscountCode)
        """
        if not code or not code.strip():
            return True, "بدون کد تخفیف", original_amount, None
            
        logger.info(f"Validating discount code '{code}' for user {user_id}, plan {plan_id}, amount {original_amount}")
        
        try:
            # Get the discount code from repository
            discount = await self.discount_repo.get_by_code(code)
            
            if not discount:
                logger.warning(f"Discount code '{code}' not found")
                return False, "کد تخفیف نامعتبر است", original_amount, None
                
            # Check if code is expired
            if discount.expires_at and discount.expires_at < datetime.utcnow():
                logger.warning(f"Discount code '{code}' expired on {discount.expires_at}")
                return False, "کد تخفیف منقضی شده است", original_amount, None
                
            # Check if code has reached usage limit
            if discount.max_uses and discount.use_count >= discount.max_uses:
                logger.warning(f"Discount code '{code}' reached maximum usage limit of {discount.max_uses}")
                return False, "کد تخفیف به حداکثر تعداد استفاده رسیده است", original_amount, None
                
            # Check if code is valid for this user (if user-specific)
            if discount.user_id and discount.user_id != user_id:
                logger.warning(f"Discount code '{code}' is specific to user {discount.user_id}, not {user_id}")
                return False, "این کد تخفیف برای شما معتبر نیست", original_amount, None
                
            # Check if code is valid for this plan (if plan-specific)
            # This assumes discount.plans is a list of plan_ids or a relationship that can be queried
            if discount.plan_ids and str(plan_id) not in discount.plan_ids.split(','):
                logger.warning(f"Discount code '{code}' not valid for plan {plan_id}")
                return False, "این کد تخفیف برای این پلن معتبر نیست", original_amount, None
                
            # Calculate discounted amount
            discounted_amount = original_amount
            if discount.discount_type == 'percentage' and discount.discount_value:
                # Apply percentage discount
                discount_percentage = Decimal(discount.discount_value)
                if discount_percentage > 100:
                    discount_percentage = 100  # Cap at 100%
                discount_amount = (discount_percentage / 100) * original_amount
                discounted_amount = original_amount - discount_amount
            elif discount.discount_type == 'fixed' and discount.discount_value:
                # Apply fixed amount discount
                discount_amount = Decimal(discount.discount_value)
                if discount_amount > original_amount:
                    discount_amount = original_amount  # Cap at original amount
                discounted_amount = original_amount - discount_amount
                
            # Ensure we don't go below zero
            if discounted_amount < 0:
                discounted_amount = Decimal('0')
                
            logger.info(f"Discount code '{code}' applied successfully: original={original_amount}, discounted={discounted_amount}")
            
            # Increment usage count (we'll flush this later)
            discount.use_count += 1
            await self.session.flush()
            
            return True, "کد تخفیف با موفقیت اعمال شد", discounted_amount, discount
            
        except Exception as e:
            logger.error(f"Error applying discount code '{code}': {e}", exc_info=True)
            return False, f"خطا در اعمال کد تخفیف: {str(e)}", original_amount, None
            
    async def get_payment_instructions(self) -> str:
        """دریافت راهنمای پرداخت (kept for now, consider moving)"""
        instructions = (
            "📱 راهنمای شارژ کیف پول:\n\n"
            "۱. مبلغ مورد نظر را به شماره کارت زیر واریز کنید:\n"
            "𝟔𝟐𝟕𝟕-𝟔𝟎𝟔𝟏-𝟏𝟐𝟑𝟒-𝟓𝟔𝟓𝟖\n"
            "به نام «محمد محمدی»\n\n"
            "۲. پس از واریز، شماره پیگیری یا تصویر رسید پرداخت را به پشتیبانی ارسال کنید.\n\n"
            "۳. معمولاً شارژ کیف پول در کمتر از ۱۵ دقیقه انجام می‌شود.\n\n"
            "⚠️ لطفاً دقت کنید که شماره تراکنش را حتماً یادداشت کنید."
        )
        return instructions

    async def send_receipt_to_admin_channel(self, receipt_id: int) -> bool:
        """
        ارسال رسید به کانال ادمین برای بررسی
        
        Args:
            receipt_id: شناسه رسید
            
        Returns:
            bool: موفقیت عملیات
        """
        try:
            # Get receipt details
            receipt = await self.receipt_repo.get_by_id(receipt_id)
            if not receipt:
                logger.error(f"Receipt {receipt_id} not found")
                return False
                
            # Get user details
            user = await self.user_repo.get_by_id(receipt.user_id)
            if not user:
                logger.error(f"User {receipt.user_id} not found")
                return False
                
            # Get bank card details
            bank_card = await self.bank_card_repo.get_by_id(receipt.card_id)
            if not bank_card:
                logger.error(f"Bank card {receipt.card_id} not found")
                return False
                
            # Get order details if available
            order_text = ""
            if receipt.order_id:
                query = text("""
                    SELECT o.id, p.name, o.final_amount
                    FROM orders o
                    JOIN plans p ON o.plan_id = p.id
                    WHERE o.id = :order_id
                """)
                result = await self.session.execute(query, {"order_id": receipt.order_id})
                order_data = result.fetchone()
                if order_data:
                    order_id, plan_name, final_amount = order_data
                    order_text = f"📦 سفارش: {plan_name} (#{order_id})\n💰 مبلغ سفارش: {format_currency(float(final_amount))}\n\n"
            
            # Format the message for admin
            message = (
                f"🧾 <b>رسید جدید پرداخت کارت به کارت</b>\n\n"
                f"👤 کاربر: {user.full_name} (@{user.username or 'بدون یوزرنیم'})\n"
                f"🆔 شناسه کاربر: <code>{user.telegram_id}</code>\n\n"
                f"{order_text}"
                f"💳 کارت مقصد: <code>{bank_card.card_number}</code>\n"
                f"🏦 بانک: {bank_card.bank_name}\n"
                f"👤 به نام: {bank_card.holder_name}\n\n"
                f"💸 مبلغ: {format_currency(float(receipt.amount))}\n"
                f"🔢 کد پیگیری: <code>{receipt.tracking_code}</code>\n"
                f"⏱ زمان ثبت: {receipt.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            
            if receipt.text_reference:
                message += f"📝 توضیحات کاربر:\n<code>{receipt.text_reference}</code>\n\n"
                
            message += f"لطفا این رسید را بررسی و تایید یا رد کنید."
            
            # In a real implementation, this would send the message to Telegram
            # For now, we'll simulate this by updating the receipt record
            
            # Mock message and channel IDs for illustration
            mock_message_id = int(datetime.utcnow().timestamp())
            channel_id = bank_card.telegram_channel_id or -1001234567890  # Default channel if not specified
            
            # Update receipt with telegram message info
            await self.receipt_repo.update_telegram_info(
                receipt_id=receipt_id,
                message_id=mock_message_id,
                channel_id=channel_id
            )
            
            logger.info(f"Receipt {receipt_id} notification sent to admin channel with message ID {mock_message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending receipt {receipt_id} to admin channel: {e}", exc_info=True)
            return False

    async def refund_transaction(
        self,
        user_id: int,
        amount: Decimal,
        description: str,
        original_transaction_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """
        Processes a refund by creating a refund transaction and adjusting the user's wallet.
        Implements proper atomic operations and rollback handling.
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ بازگشتی (مثبت)
            description: توضیحات تراکنش
            original_transaction_id: شناسه تراکنش اصلی (اختیاری)
            
        Returns:
            Tuple[bool, str, Optional[Transaction]]:
            - موفقیت عملیات (bool)
            - پیام نتیجه (str)
            - تراکنش بازگشتی یا None در صورت خطا (Transaction)
        """
        logger.info(f"Processing refund for user {user_id}: amount={amount}, original_transaction_id={original_transaction_id}")
        
        if amount <= 0:
            logger.error(f"Invalid refund amount {amount} for user {user_id}")
            return False, "مبلغ بازگشتی باید مثبت باشد", None
            
        try:
            # 1. Create the refund transaction as pending first
            refund_transaction = await self.transaction_service.create_transaction(
                user_id=user_id,
                amount=float(amount), # Positive amount for refund
                type=TRANSACTION_TYPE_REFUND,
                status=TRANSACTION_STATUS_PENDING,
                description=description,
                related_entity_id=original_transaction_id,
                related_entity_type='transaction' if original_transaction_id else None
            )
            
            if not refund_transaction:
                logger.error(f"Failed to create refund transaction for user {user_id}, amount {amount}")
                return False, "خطا در ثبت تراکنش بازگشتی", None
                
            # 2. Adjust the wallet balance
            balance_adjusted = await self.wallet_service.adjust_balance(user_id, float(amount))
            if not balance_adjusted:
                logger.error(f"Failed to adjust wallet balance for refund to user {user_id}, amount {amount}")
                # Update transaction to failed
                await self.transaction_service.update_transaction_status(
                    transaction_id=refund_transaction.id,
                    status=TRANSACTION_STATUS_FAILED,
                    details={"error": "Failed to adjust wallet balance for refund"}
                )
                await self.session.flush()
                return False, "خطا در افزایش موجودی کیف پول برای بازگشت وجه", None
            
            # 3. Mark transaction as successful    
            await self.transaction_service.update_transaction_status(
                transaction_id=refund_transaction.id,
                status=TRANSACTION_STATUS_SUCCESS
            )
                
            # Flush to make changes visible in the current transaction
            await self.session.flush()
            
            logger.info(f"Refund processed successfully for user {user_id}: amount={amount}, transaction_id={refund_transaction.id}")
            return True, f"بازگشت وجه با موفقیت انجام شد. شناسه تراکنش: {refund_transaction.id}", refund_transaction
            
        except Exception as e:
            logger.error(f"Error in refund_transaction for user {user_id}: {e}", exc_info=True)
            return False, f"خطای سیستمی در بازگشت وجه: {str(e)}", None

    async def create_card_to_card_receipt(
        self,
        user_id: int,
        bank_card_id: int,
        amount: Decimal,
        order_id: Optional[int] = None,
        text_reference: Optional[str] = None,
        photo_file_id: Optional[str] = None,
        tracking_code: Optional[str] = None,
        auto_detected_amount: Optional[Decimal] = None
    ) -> Tuple[bool, str, Optional[ReceiptLog]]:
        """
        ثبت رسید پرداخت کارت به کارت
        
        Args:
            user_id: شناسه کاربر
            bank_card_id: شناسه کارت بانکی
            amount: مبلغ پرداختی
            order_id: شناسه سفارش (اختیاری)
            text_reference: متن رسید یا توضیحات (اختیاری)
            photo_file_id: شناسه فایل عکس رسید در تلگرام (اختیاری)
            tracking_code: کد پیگیری تراکنش (اختیاری، تولید خودکار)
            auto_detected_amount: مقدار تشخیص داده شده خودکار از رسید (اختیاری)
            
        Returns:
            Tuple[bool, str, Optional[ReceiptLog]]: 
            - موفقیت عملیات (bool)
            - پیام نتیجه (str)
            - رسید ثبت شده یا None در صورت خطا (ReceiptLog)
        """
        logger.info(f"Creating card-to-card receipt for user {user_id}: amount={amount}, order_id={order_id}")
        
        try:
            # 1. ایجاد کد پیگیری اگر ارسال نشده باشد
            if not tracking_code:
                random_part = uuid.uuid4().hex[:8]
                timestamp = int(datetime.utcnow().timestamp())
                tracking_code = f"CC-{timestamp}-{random_part}"
            
            # 2. ثبت رسید در دیتابیس
            receipt = await self.receipt_repo.create_receipt_log(
                user_id=user_id,
                card_id=bank_card_id,
                amount=float(amount),
                status="PENDING",  # از enum استفاده می‌شود اما اینجا به صورت string نشان داده شده
                text_reference=text_reference,
                photo_file_id=photo_file_id,
                order_id=order_id,
                tracking_code=tracking_code,
                submitted_at=datetime.utcnow()
            )
            
            if not receipt:
                logger.error(f"Failed to create receipt for user {user_id}")
                return False, "خطا در ثبت رسید پرداخت", None
            
            # 3. اگر سفارش مرتبط وجود دارد، وضعیت آن را به PENDING_RECEIPT تغییر دهید
            if order_id:
                from db.models.order import OrderStatus
                # Update order status to indicate it's waiting for receipt verification
                query = text("""
                    UPDATE orders 
                    SET status = :status, updated_at = :updated_at
                    WHERE id = :order_id
                """)
                await self.session.execute(query, {
                    "status": OrderStatus.PENDING_RECEIPT.value,
                    "updated_at": datetime.utcnow(),
                    "order_id": order_id
                })
            
            # 4. ارسال رسید به کانال ادمین
            await self.send_receipt_to_admin_channel(receipt.id)
            
            await self.session.commit()
            logger.info(f"Card-to-card receipt {receipt.id} created successfully, tracking code: {tracking_code}")
            
            return True, f"رسید پرداخت با موفقیت ثبت شد.\nکد پیگیری: {tracking_code}", receipt
            
        except Exception as e:
            logger.error(f"Error in create_card_to_card_receipt for user {user_id}: {e}", exc_info=True)
            # Transaction will be rolled back
            return False, f"خطای سیستمی: {str(e)}", None
            
    async def approve_card_to_card_receipt(
        self,
        receipt_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None,
        final_amount: Optional[Decimal] = None
    ) -> Tuple[bool, str, Optional[ReceiptLog]]:
        """
        تأیید رسید پرداخت کارت به کارت توسط ادمین
        
        Args:
            receipt_id: شناسه رسید
            admin_id: شناسه ادمین تأیید کننده
            admin_notes: یادداشت ادمین (اختیاری)
            final_amount: مبلغ نهایی تأیید شده (اختیاری، پیش‌فرض مقدار اصلی رسید)
            
        Returns:
            Tuple[bool, str, Optional[ReceiptLog]]: 
            - موفقیت عملیات (bool)
            - پیام نتیجه (str) 
            - رسید به‌روزرسانی شده یا None در صورت خطا (ReceiptLog)
        """
        logger.info(f"Approving receipt {receipt_id} by admin {admin_id}")
        
        try:
            # 1. دریافت جزئیات رسید
            receipt = await self.receipt_repo.get_by_id(receipt_id)
            if not receipt:
                logger.error(f"Receipt {receipt_id} not found")
                return False, "رسید مورد نظر یافت نشد", None
                
            # 2. بررسی وضعیت فعلی
            if receipt.status != "PENDING":
                logger.warning(f"Receipt {receipt_id} is not in PENDING status (current: {receipt.status})")
                return False, f"این رسید قبلاً {receipt.status} شده است", receipt
            
            # 3. مقدار نهایی تأیید شده
            approved_amount = final_amount if final_amount is not None else receipt.amount
            
            # 4. ایجاد تراکنش واریز به کیف پول
            user_id = receipt.user_id
            description = f"شارژ کیف پول از طریق کارت به کارت (کد پیگیری: {receipt.tracking_code})"
            
            success, message, transaction = await self.process_incoming_payment(
                user_id=user_id,
                amount=approved_amount,
                description=description
            )
            
            if not success:
                logger.error(f"Failed to process payment for receipt {receipt_id}: {message}")
                return False, f"خطا در پردازش پرداخت: {message}", None
            
            # 5. به‌روزرسانی اطلاعات رسید
            # 5.1 اگر نوت ادمین داریم، اضافه کنیم
            if admin_notes:
                receipt = await self.receipt_repo.add_note(receipt_id, admin_notes, admin_id)
                
            # 5.2 به‌روزرسانی وضعیت رسید
            receipt = await self.receipt_repo.update_status(receipt_id, "APPROVED", admin_id)
            if transaction:
                # ارتباط با تراکنش
                receipt.transaction_id = transaction.id
                await self.session.flush()
            
            # 6. اگر سفارش مرتبط وجود دارد، به‌روزرسانی وضعیت سفارش
            if receipt.order_id:
                from db.models.order import OrderStatus
                
                # Update order status to PAID
                query = text("""
                    UPDATE orders 
                    SET status = :status, updated_at = :updated_at
                    WHERE id = :order_id
                """)
                await self.session.execute(query, {
                    "status": OrderStatus.PAID.value, 
                    "updated_at": datetime.utcnow(),
                    "order_id": receipt.order_id
                })
                
                # Notify the user about successful payment
                order_id = receipt.order_id
                await self.notification_service.send_payment_confirmation(
                    user_id, 
                    order_id, 
                    float(approved_amount),
                    receipt.tracking_code
                )
            
            await self.session.commit()
            logger.info(f"Receipt {receipt_id} approved successfully by admin {admin_id}")
            
            return True, f"رسید با موفقیت تأیید شد. مبلغ {format_currency(float(approved_amount))} به کیف پول کاربر اضافه شد.", receipt
            
        except Exception as e:
            logger.error(f"Error in approve_card_to_card_receipt for receipt {receipt_id}: {e}", exc_info=True)
            # Transaction will be rolled back 
            return False, f"خطای سیستمی: {str(e)}", None
            
    async def reject_card_to_card_receipt(
        self,
        receipt_id: int,
        admin_id: int,
        rejection_reason: str
    ) -> Tuple[bool, str, Optional[ReceiptLog]]:
        """
        رد کردن رسید پرداخت کارت به کارت توسط ادمین
        
        Args:
            receipt_id: شناسه رسید
            admin_id: شناسه ادمین رد کننده
            rejection_reason: دلیل رد رسید
            
        Returns:
            Tuple[bool, str, Optional[ReceiptLog]]: 
            - موفقیت عملیات (bool) 
            - پیام نتیجه (str)
            - رسید به‌روزرسانی شده یا None در صورت خطا (ReceiptLog)
        """
        logger.info(f"Rejecting receipt {receipt_id} by admin {admin_id}")
        
        try:
            # 1. دریافت جزئیات رسید
            receipt = await self.receipt_repo.get_by_id(receipt_id)
            if not receipt:
                logger.error(f"Receipt {receipt_id} not found")
                return False, "رسید مورد نظر یافت نشد", None
                
            # 2. بررسی وضعیت فعلی
            if receipt.status != "PENDING":
                logger.warning(f"Receipt {receipt_id} is not in PENDING status (current: {receipt.status})")
                return False, f"این رسید قبلاً {receipt.status} شده است", receipt
            
            # 3. به‌روزرسانی اطلاعات رسید
            receipt.status = "REJECTED"
            receipt.admin_id = admin_id
            receipt.rejection_reason = rejection_reason
            receipt.responded_at = datetime.utcnow()
            
            # 4. اگر سفارش مرتبط وجود دارد، به‌روزرسانی وضعیت سفارش به PENDING
            if receipt.order_id:
                from db.models.order import OrderStatus
                
                # Return order to PENDING status
                query = text("""
                    UPDATE orders 
                    SET status = :status, updated_at = :updated_at
                    WHERE id = :order_id
                """)
                await self.session.execute(query, {
                    "status": OrderStatus.PENDING.value,
                    "updated_at": datetime.utcnow(),
                    "order_id": receipt.order_id
                })
                
                # Notify the user about rejected payment
                await self.notification_service.send_receipt_rejection(
                    receipt.user_id,
                    receipt.order_id,
                    receipt.tracking_code,
                    rejection_reason
                )
            
            await self.session.commit()
            logger.info(f"Receipt {receipt_id} rejected successfully by admin {admin_id}")
            
            return True, "رسید با موفقیت رد شد.", receipt
            
        except Exception as e:
            logger.error(f"Error in reject_card_to_card_receipt for receipt {receipt_id}: {e}", exc_info=True)
            # Transaction will be rolled back
            return False, f"خطای سیستمی: {str(e)}", None
            
    async def get_pending_receipts(self, limit: int = 10) -> list:
        """
        دریافت لیست رسیدهای در انتظار تأیید

        Args:
            limit: حداکثر تعداد نتایج

        Returns:
            list: لیست رسیدهای در انتظار تأیید
        """
        try:
            # Query pending receipts from repository
            pending_receipts = await self.receipt_repo.get_by_status('pending', limit=limit)
            return pending_receipts
        except Exception as e:
            logger.error(f"Error in get_pending_receipts: {e}", exc_info=True)
            return []
            
    async def get_receipt_details(self, receipt_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت جزئیات کامل یک رسید همراه با اطلاعات کاربر، سفارش و کارت بانکی

        Args:
            receipt_id: شناسه رسید

        Returns:
            Optional[Dict[str, Any]]: جزئیات رسید یا None در صورت خطا
        """
        try:
            # Get receipt with relationships loaded
            receipt = await self.receipt_repo.get_by_id(receipt_id)
            if not receipt:
                logger.error(f"Receipt not found: {receipt_id}")
                return None
                
            # Prepare detailed response
            receipt_details = {
                "id": receipt.id,
                "tracking_code": receipt.tracking_code,
                "amount": float(receipt.amount),
                "status": receipt.status,
                "submitted_at": receipt.submitted_at,
                "responded_at": receipt.responded_at,
                "text_reference": receipt.text_reference,
                "photo_file_id": receipt.photo_file_id,
                "notes": receipt.notes,
                "rejection_reason": receipt.rejection_reason,
                "order_id": receipt.order_id,
                "transaction_id": receipt.transaction_id,
                "user": {
                    "id": receipt.user_id,
                    "telegram_id": receipt.user.telegram_id if hasattr(receipt, 'user') and receipt.user else None,
                    "username": receipt.user.username if hasattr(receipt, 'user') and receipt.user else None,
                    "full_name": receipt.user.full_name if hasattr(receipt, 'user') and receipt.user else None,
                },
                "bank_card": {
                    "id": receipt.card_id,
                    "card_number": receipt.bank_card.card_number if hasattr(receipt, 'bank_card') and receipt.bank_card else None,
                    "bank_name": receipt.bank_card.bank_name if hasattr(receipt, 'bank_card') and receipt.bank_card else None,
                    "holder_name": receipt.bank_card.holder_name if hasattr(receipt, 'bank_card') and receipt.bank_card else None,
                },
            }
            
            return receipt_details
            
        except Exception as e:
            logger.error(f"Error in get_receipt_details: {e}", exc_info=True)
            return None
