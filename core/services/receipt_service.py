"""
core/services/receipt_service.py

سرویس مدیریت رسیدهای پرداخت کاربران
این سرویس برای مدیریت رسیدهای کارت به کارت و تایید آنها توسط ادمین استفاده می‌شود.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.receipt_log import ReceiptLog, ReceiptStatus
from db.repositories.receipt_log_repository import ReceiptLogRepository
from db.repositories.transaction_repo import TransactionRepository
from db.models.transaction import TransactionStatus
from core.services.wallet_service import WalletService
from core.services.notification_service import NotificationService


class ReceiptService:
    """سرویس مدیریت رسیدهای پرداخت"""

    def __init__(self, session: AsyncSession):
        """سازنده کلاس ReceiptService

        Args:
            session: نشست فعال دیتابیس
        """
        self._session = session
        self._receipt_repo = ReceiptLogRepository(session)
        self._transaction_repo = TransactionRepository(session)
        self._wallet_service = WalletService(session)
        self._notification_service = NotificationService(session)

    async def get_pending_receipts(self, limit: int = 10) -> List[ReceiptLog]:
        """دریافت لیست رسیدهای در انتظار تایید

        Args:
            limit: حداکثر تعداد رسیدهای برگشتی

        Returns:
            List[ReceiptLog]: لیست رسیدهای در انتظار تایید
        """
        return await self._receipt_repo.get_by_status(ReceiptStatus.PENDING.value, limit)

    async def approve_receipt(self, receipt_id: int, admin_id: int) -> Optional[ReceiptLog]:
        """تایید رسید توسط ادمین

        این متد رسید را تایید کرده، تراکنش مرتبط را به وضعیت SUCCESS تغییر می‌دهد و
        کیف پول کاربر را شارژ می‌کند.

        Args:
            receipt_id: شناسه رسید
            admin_id: شناسه ادمین تایید کننده

        Returns:
            Optional[ReceiptLog]: رسید به‌روزرسانی شده یا None در صورت خطا
        """
        async with self._session.begin():
            # رسید را دریافت می‌کنیم
            receipt = await self._receipt_repo.get_by_id(receipt_id)
            if not receipt:
                return None

            # بررسی وضعیت فعلی رسید
            if receipt.status != ReceiptStatus.PENDING:
                return receipt  # رسید قبلاً تایید یا رد شده است

            # تراکنش مرتبط را دریافت می‌کنیم
            if not receipt.transaction_id:
                # خطا: رسید به هیچ تراکنشی مرتبط نیست
                return None

            transaction = await self._transaction_repo.get_by_id(receipt.transaction_id)
            if not transaction:
                # خطا: تراکنش مرتبط یافت نشد
                return None

            # بررسی وضعیت تراکنش
            if transaction.status != TransactionStatus.PENDING:
                # تراکنش قبلاً پردازش شده است
                return receipt

            # وضعیت رسید را به APPROVED تغییر می‌دهیم
            updated_receipt = await self._receipt_repo.update_status(receipt_id, ReceiptStatus.APPROVED, admin_id)
            if not updated_receipt:
                return None

            # وضعیت تراکنش را به SUCCESS تغییر می‌دهیم
            updated_transaction = await self._transaction_repo.update_status(transaction.id, TransactionStatus.SUCCESS)
            if not updated_transaction:
                # اگر به‌روزرسانی تراکنش با مشکل مواجه شد، رسید هم باید به وضعیت قبلی برگردد
                # اما چون در یک transaction دیتابیس هستیم، rollback خودکار انجام می‌شود
                return None

            # کیف پول کاربر را شارژ می‌کنیم
            credit_amount = float(receipt.amount)
            success_credit = await self._wallet_service.credit(
                receipt.user_id, 
                credit_amount, 
                f"Deposit confirmation - Receipt ID: {receipt.id}"
            )
            if not success_credit:
                # شارژ کیف پول با خطا مواجه شد
                return None

            # به کاربر اطلاع‌رسانی می‌کنیم
            try:
                current_balance = await self._wallet_service.get_balance(receipt.user_id)
                user_message = (
                    f"✅ واریز شما با موفقیت تایید و به حساب شما اضافه شد.\n\n"
                    f"💰 مبلغ: {receipt.amount:,} تومان\n"
                    f"💸 موجودی جدید: {current_balance:,} تومان\n"
                    f"🔖 کد پیگیری رسید: {receipt.tracking_code}"
                )
                await self._notification_service.send_user_notification(
                    user_id=receipt.user_id,
                    content=user_message,
                    notification_type="RECEIPT"
                )
            except Exception:
                # خطا در اطلاع‌رسانی نباید روند تایید را متوقف کند
                pass

            return updated_receipt

    async def reject_receipt(
        self, 
        receipt_id: int, 
        admin_id: int, 
        rejection_reason: Optional[str] = None
    ) -> Optional[ReceiptLog]:
        """رد رسید توسط ادمین

        این متد رسید را رد کرده و تراکنش مرتبط را به وضعیت FAILED تغییر می‌دهد.

        Args:
            receipt_id: شناسه رسید
            admin_id: شناسه ادمین رد کننده
            rejection_reason: دلیل رد رسید (اختیاری)

        Returns:
            Optional[ReceiptLog]: رسید به‌روزرسانی شده یا None در صورت خطا
        """
        async with self._session.begin():
            # رسید را دریافت می‌کنیم
            receipt = await self._receipt_repo.get_by_id(receipt_id)
            if not receipt:
                return None

            # بررسی وضعیت فعلی رسید
            if receipt.status != ReceiptStatus.PENDING:
                return receipt  # رسید قبلاً تایید یا رد شده است

            # تراکنش مرتبط را دریافت می‌کنیم
            if not receipt.transaction_id:
                # خطا: رسید به هیچ تراکنشی مرتبط نیست
                return None

            transaction = await self._transaction_repo.get_by_id(receipt.transaction_id)
            if not transaction:
                # خطا: تراکنش مرتبط یافت نشد
                return None

            # بررسی وضعیت تراکنش
            if transaction.status != TransactionStatus.PENDING:
                # تراکنش قبلاً پردازش شده است
                return receipt

            # وضعیت رسید را به REJECTED تغییر می‌دهیم
            updated_receipt = await self._receipt_repo.update_status(receipt_id, ReceiptStatus.REJECTED, admin_id)
            if not updated_receipt:
                return None
            
            # اگر دلیل رد ارائه شده، آن را ذخیره می‌کنیم
            if rejection_reason:
                updated_receipt.rejection_reason = rejection_reason
                await self._session.commit()

            # وضعیت تراکنش را به FAILED تغییر می‌دهیم
            updated_transaction = await self._transaction_repo.update_status(transaction.id, TransactionStatus.FAILED)
            if not updated_transaction:
                # اگر به‌روزرسانی تراکنش با مشکل مواجه شد، رسید هم باید به وضعیت قبلی برگردد
                # اما چون در یک transaction دیتابیس هستیم، rollback خودکار انجام می‌شود
                return None

            # به کاربر اطلاع‌رسانی می‌کنیم
            try:
                reason_text = f"\n🔍 دلیل: {rejection_reason}" if rejection_reason else ""
                user_message = (
                    f"❌ متأسفانه رسید پرداخت شما تایید نشد.{reason_text}\n\n"
                    f"💰 مبلغ: {receipt.amount:,} تومان\n"
                    f"🔖 کد پیگیری: {receipt.tracking_code}\n\n"
                    f"📞 برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
                )
                await self._notification_service.send_user_notification(
                    user_id=receipt.user_id,
                    content=user_message,
                    notification_type="RECEIPT"
                )
            except Exception:
                # خطا در اطلاع‌رسانی نباید روند رد رسید را متوقف کند
                pass

            return updated_receipt 