"""
سرویس مدیریت کیف پول و تراکنش‌ها
"""

import logging
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

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
        Formats and sends a receipt notification to the designated admin channel 
        for the associated bank card and updates the receipt log.
        """
        receipt: Optional[ReceiptLog] = await self.receipt_repo.get_by_id(receipt_id)
        if not receipt:
            logger.error(f"ReceiptLog not found for ID {receipt_id}")
            return False

        user: Optional[User] = await self.user_repo.get_by_id(receipt.user_id)
        card: Optional[BankCard] = await self.bank_card_repo.get_by_id(receipt.card_id)

        if not user or not card:
            logger.error(f"User or BankCard not found for ReceiptLog {receipt_id}")
            return False

        if not card.telegram_channel_id:
            logger.error(f"telegram_channel_id not set for BankCard {card.id}")
            # Maybe notify a default admin channel?
            return False

        target_channel_id = card.telegram_channel_id

        # Format the cover message
        user_link = f"<a href=\"tg://user?id={user.telegram_id}\">{user.username or user.telegram_id}</a>"
        card_masked = f"{card.card_number[:4]}******{card.card_number[-4:]}" if len(card.card_number) >= 8 else card.card_number
        amount_str = format_currency(receipt.amount) # Requires format_currency utility
        time_str = receipt.submitted_at.strftime("%Y/%m/%d - %H:%M")
        
        caption_parts = [
            f"📤 رسید جدید دریافت شد:",
            f"👤 کاربر: {user_link} ({user.telegram_id})",
            f"💳 کارت مقصد: {card_masked} ({card.bank_name} - {card.holder_name})",
            f"💰 مبلغ: {amount_str}",
            f"🕒 زمان: {time_str}",
        ]
        if receipt.tracking_code and not receipt.tracking_code.startswith("TEMP-"):
             caption_parts.append(f"🔖 کد پیگیری: {receipt.tracking_code}") # Only show if not placeholder
        if receipt.order_id:
            caption_parts.append(f"🆔 OrderID: #{receipt.order_id}")
        if receipt.text_reference:
            caption_parts.append(f"\n📝 متن کاربر: {receipt.text_reference}")

        caption = "\n".join(caption_parts)

        # Get the admin keyboard
        keyboard = get_receipt_admin_keyboard(receipt.id)

        # Send the notification
        try:
            if receipt.photo_file_id:
                sent_message = await self.notification_service.send_photo_to_channel(
                    channel_id=target_channel_id,
                    photo_file_id=receipt.photo_file_id,
                    caption=caption,
                    reply_markup=keyboard
                )
            else:
                sent_message = await self.notification_service.send_message_to_channel(
                    channel_id=target_channel_id,
                    text=caption,
                    reply_markup=keyboard
                )
            
            if sent_message:
                # Update receipt log with message details
                updated = await self.receipt_repo.update_receipt_telegram_info(
                    receipt_id=receipt.id,
                    message_id=sent_message.message_id,
                    channel_id=target_channel_id
                )
                if not updated:
                    logger.error(f"Failed to update ReceiptLog {receipt.id} with Telegram message details")
                    # Logged the error, but consider the main operation (sending) successful
                return True # Message sent successfully
            else:
                logger.error(f"NotificationService failed to send message for ReceiptLog {receipt_id} to channel {target_channel_id}")
                return False
        except Exception as e:
            logger.error(f"Error in send_receipt_to_admin_channel for receipt {receipt_id}: {e}", exc_info=True)
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
