"""
سرویس مدیریت کیف پول و تراکنش‌ها
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models.user import User
from db.models.transaction import Transaction, TransactionType, TransactionStatus
from db.repositories.user_repo import UserRepository
from core.services.notification_service import NotificationService

class PaymentService:
    """سرویس مدیریت پرداخت و تراکنش‌ها با منطق کسب و کار مرتبط"""
    
    def __init__(self, db_session: Session):
        """مقداردهی اولیه سرویس"""
        self.db_session = db_session
        self.user_repo = UserRepository(db_session)
        self.notification_service = NotificationService(db_session)
    
    def get_user_balance(self, telegram_id: int) -> Decimal:
        """دریافت موجودی کیف پول کاربر"""
        user = self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return Decimal('0.0')
        return user.balance
    
    def create_transaction(
        self, 
        user_id: int, 
        amount: Decimal,
        transaction_type: TransactionType = TransactionType.PAYMENT,
        order_id: Optional[int] = None,
        status: TransactionStatus = TransactionStatus.PENDING
    ) -> Transaction:
        """ایجاد تراکنش جدید"""
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=transaction_type,
            order_id=order_id,
            status=status,
            created_at=datetime.now()  # تنظیم صریح زمان ایجاد
        )
        self.db_session.add(transaction)
        self.db_session.commit()
        return transaction
    
    def get_user_transactions(self, user_id: int) -> List[Transaction]:
        """دریافت تمام تراکنش‌های یک کاربر"""
        query = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.created_at.desc())
        result = self.db_session.execute(query)
        return list(result.scalars().all())
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """دریافت یک تراکنش با شناسه"""
        query = select(Transaction).where(Transaction.id == transaction_id)
        result = self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    def update_transaction_status(self, transaction_id: int, new_status: TransactionStatus) -> Optional[Transaction]:
        """به‌روزرسانی وضعیت تراکنش"""
        transaction = self.get_transaction_by_id(transaction_id)
        if not transaction:
            return None
            
        transaction.status = new_status
        
        # اگر تراکنش تکمیل شد و از نوع شارژ بود، موجودی کاربر را افزایش دهیم
        if new_status == TransactionStatus.SUCCESS and (transaction.type == TransactionType.PAYMENT or transaction.type == TransactionType.DEPOSIT):
            user = self.user_repo.get_by_id(transaction.user_id)
            if user:
                user.balance += transaction.amount
        
        self.db_session.commit()
        return transaction
    
    def confirm_payment(self, transaction_id: int) -> Optional[Transaction]:
        """
        تأیید پرداخت، افزایش موجودی کاربر و ارسال نوتیفیکیشن
        
        Args:
            transaction_id (int): شناسه تراکنش
            
        Returns:
            Optional[Transaction]: تراکنش تأیید شده یا None در صورت عدم وجود
        """
        transaction = self.get_transaction_by_id(transaction_id)
        if not transaction:
            return None
            
        # تغییر وضعیت تراکنش
        transaction.status = TransactionStatus.SUCCESS
        
        # افزایش موجودی کاربر اگر تراکنش از نوع پرداخت یا شارژ است
        if transaction.type == TransactionType.PAYMENT or transaction.type == TransactionType.DEPOSIT:
            user = self.user_repo.get_by_id(transaction.user_id)
            if user:
                user.balance += transaction.amount
                
                # ارسال نوتیفیکیشن به کاربر
                message = (
                    f"🎉 پرداخت شما با موفقیت تأیید شد!\n\n"
                    f"💰 مبلغ: {transaction.amount} تومان\n"
                    f"💼 موجودی فعلی: {user.balance} تومان\n\n"
                    f"🔢 شناسه تراکنش: #{transaction.id}"
                )
                self.notification_service.notify_user(user.telegram_id, message)
                
                # ارسال نوتیفیکیشن به ادمین
                admin_message = (
                    f"✅ تراکنش تأیید شد:\n\n"
                    f"👤 کاربر: {user.telegram_id}\n"
                    f"💰 مبلغ: {transaction.amount} تومان\n"
                    f"🔢 شناسه تراکنش: #{transaction.id}"
                )
                self.notification_service.notify_admin(admin_message)
        
        self.db_session.commit()
        return transaction
    
    def get_payment_instructions(self) -> str:
        """دریافت راهنمای پرداخت"""
        instructions = (
            "📱 راهنمای شارژ کیف پول:\n\n"
            "۱. مبلغ مورد نظر را به شماره کارت زیر واریز کنید:\n"
            "𝟔𝟐𝟕𝟕-𝟔𝟎𝟔𝟏-𝟏𝟐𝟑𝟒-𝟓𝟔𝟕𝟖\n"
            "به نام «محمد محمدی»\n\n"
            "۲. پس از واریز، شماره پیگیری یا تصویر رسید پرداخت را به پشتیبانی ارسال کنید.\n\n"
            "۳. معمولاً شارژ کیف پول در کمتر از ۱۵ دقیقه انجام می‌شود.\n\n"
            "⚠️ لطفاً دقت کنید که شماره تراکنش را حتماً یادداشت کنید."
        )
        return instructions
