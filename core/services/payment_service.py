"""
سرویس مدیریت کیف پول و تراکنش‌ها
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.wallet_service import WalletService
from core.services.transaction_service import TransactionService
from core.services.notification_service import NotificationService
from db.repositories.user_repo import UserRepository
from db.repositories.receipt_log_repository import ReceiptLogRepository
from db.repositories.bank_card_repository import BankCardRepository
from db.models.transaction import Transaction
from db.models.receipt_log import ReceiptLog
from db.models.user import User
from db.models.bank_card import BankCard
from bot.keyboards.receipt_keyboards import get_receipt_admin_keyboard
from bot.utils import format_currency

# Define constants for transaction types/status if not already central
TRANSACTION_TYPE_DEPOSIT = 'deposit'
TRANSACTION_TYPE_PURCHASE = 'purchase'
TRANSACTION_STATUS_PENDING = 'pending'
TRANSACTION_STATUS_SUCCESS = 'completed' # Assuming 'completed' is the success status
TRANSACTION_STATUS_FAILED = 'failed'

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
    ) -> Optional[Transaction]:
        """
        Processes a successful incoming payment (e.g., from a gateway or manual confirmation).
        Creates a transaction, adjusts wallet balance, and notifies.
        """
        # 1. Create a transaction record
        transaction = await self.transaction_service.create_transaction(
            user_id=user_id,
            amount=float(amount), # Transaction service might expect float
            type=TRANSACTION_TYPE_DEPOSIT,
            status=TRANSACTION_STATUS_SUCCESS, # Assuming payment is confirmed
            description=description,
            # Add gateway details if available
            # related_entity_id=...,
            # related_entity_type=...
        )
        if not transaction:
            # Log error: Failed to create transaction record
            return None

        # 2. Adjust user's wallet balance
        balance_adjusted = await self.wallet_service.adjust_balance(user_id, float(amount))
        if not balance_adjusted:
            # Log error: Failed to adjust balance, potentially inconsistency
            # Consider updating transaction status to failed/review needed
            await self.transaction_service.update_transaction_status(
                transaction_id=transaction.id,
                status=TRANSACTION_STATUS_FAILED,
                details={"error": "Failed to adjust wallet balance after payment confirmation"}
            )
            return None # Or return the failed transaction

        # 3. Notify user and admin (optional, depends on flow)
        user = await self.user_repo.get_by_id(user_id)
        current_balance = await self.wallet_service.get_balance(user_id)
        if user and current_balance is not None:
            # Send user notification
            user_message = (
                f"🎉 پرداخت شما با موفقیت تأیید شد!\n\n"
                f"💰 مبلغ: {amount} تومان\n"
                f"💼 موجودی فعلی: {Decimal(current_balance):.2f} تومان\n\n"
                f"🔢 شناسه تراکنش: #{transaction.id}"
            )
            await self.notification_service.notify_user(user.telegram_id, user_message)

            # Send admin notification
            admin_message = (
                f"✅ تراکنش شارژ تأیید شد:\n\n"
                f"👤 کاربر: {user.telegram_id} (ID: {user_id})\n"
                f"💰 مبلغ: {amount} تومان\n"
                f"🔢 شناسه تراکنش: #{transaction.id}"
            )
            await self.notification_service.notify_admin(admin_message)

        # Note: Commit should happen outside this service, likely by the calling handler/task runner
        return transaction

    async def pay_from_wallet(
        self,
        user_id: int,
        amount: Decimal,
        description: str,
        order_id: Optional[int] = None # Link transaction to an order if applicable
    ) -> Optional[Transaction]:
        """
        Attempts to pay a specific amount from the user's wallet.
        Checks balance, adjusts balance, creates transaction.
        """
        # 1. Check balance
        current_balance = await self.wallet_service.get_balance(user_id)
        if current_balance is None or Decimal(current_balance) < amount:
            # Not enough funds or user not found
            return None # Indicate failure

        # 2. Adjust balance (negative amount for withdrawal)
        balance_adjusted = await self.wallet_service.adjust_balance(user_id, -float(amount))
        if not balance_adjusted:
            # Log error: Failed to withdraw funds, possibly concurrent modification?
            return None

        # 3. Create transaction record for the purchase/payment
        transaction = await self.transaction_service.create_transaction(
            user_id=user_id,
            amount=-float(amount), # Record the withdrawal
            type=TRANSACTION_TYPE_PURCHASE,
            status=TRANSACTION_STATUS_SUCCESS,
            description=description,
            related_entity_id=order_id,
            related_entity_type='order' if order_id else None
        )
        if not transaction:
            # CRITICAL: Balance was adjusted, but transaction failed!
            # Need robust error handling here - maybe try to revert balance?
            # Log this critical error for manual review.
            # For now, return None to indicate failure.
            # TODO: Implement compensation logic (e.g., attempt refund transaction)
            return None

        # Commit should happen outside
        return transaction

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
            print(f"Error: ReceiptLog not found for ID {receipt_id}")
            return False

        user: Optional[User] = await self.user_repo.get_by_id(receipt.user_id)
        card: Optional[BankCard] = await self.bank_card_repo.get_by_id(receipt.card_id)

        if not user or not card:
            print(f"Error: User or BankCard not found for ReceiptLog {receipt_id}")
            return False

        if not card.telegram_channel_id:
            print(f"Error: telegram_channel_id not set for BankCard {card.id}")
            # Maybe notify a default admin channel?
            return False

        target_channel_id = card.telegram_channel_id

        # Format the cover message
        user_link = f"<a href=\"tg://user?id={user.telegram_id}\">{user.username or user.telegram_id}</a>"
        card_masked = f"{card.card_number[:4]}******{card.card_number[-4:]}"
        amount_str = format_currency(receipt.amount) # Requires format_currency utility
        time_str = receipt.submitted_at.strftime("%Y/%m/%d - %H:%M")
        
        caption_parts = [
            f"📤 رسید جدید دریافت شد:",
            f"👤 کاربر: {user_link} ({user.telegram_id})",
            f"💳 کارت مقصد: {card_masked} ({card.bank_name} - {card.holder_name})",
            f"💰 مبلغ: {amount_str}",
            f"🕒 زمان: {time_str}",
        ]
        if receipt.tracking_code and receipt.tracking_code.startswith("TEMP-") is False:
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
                    print(f"Error: Failed to update ReceiptLog {receipt.id} with message info.")
                    # Consider deleting the sent message or logging for manual review
                return updated is not None
            else:
                print(f"Error: Failed to send message to channel {target_channel_id} for receipt {receipt.id}")
                return False

        except Exception as e:
            print(f"Exception sending receipt {receipt.id} to channel {target_channel_id}: {e}")
            # Log the exception properly
            return False
