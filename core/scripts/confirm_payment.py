#!/usr/bin/env python
"""
اسکریپت تأیید پرداخت‌ها برای استفاده از طریق خط فرمان

Usage:
    python -m core.scripts.confirm_payment --txn TRANSACTION_ID
"""

import argparse
import sys
from sqlalchemy.orm import Session
from sqlalchemy import select
from contextlib import contextmanager

from db import get_db
from db.models.transaction import Transaction
from core.services.payment_service import PaymentService


def parse_args():
    """آماده‌سازی آرگومان‌های خط فرمان"""
    parser = argparse.ArgumentParser(description="تأیید پرداخت و افزایش موجودی کاربر")
    
    # گروه‌بندی آرگومان‌ها برای مشخص کردن شناسه تراکنش
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--txn", type=int, help="شناسه تراکنش برای تأیید")
    group.add_argument("--order", type=int, help="شناسه سفارش برای تأیید تراکنش مرتبط")
    
    return parser.parse_args()


@contextmanager
def get_session():
    """ایجاد یک جلسه دیتابیس با استفاده از context manager"""
    session = next(get_db())
    try:
        yield session
    finally:
        session.close()


def confirm_payment(transaction_id=None, order_id=None):
    """پیاده‌سازی منطق تأیید پرداخت"""
    with get_session() as session:
        payment_service = PaymentService(session)
        
        if transaction_id:
            # تأیید پرداخت با شناسه تراکنش
            transaction = payment_service.confirm_payment(transaction_id)
            
            if transaction:
                print(f"✅ تراکنش {transaction_id} با موفقیت تأیید شد.")
                print(f"👤 کاربر {transaction.user.telegram_id}")
                print(f"💰 مبلغ: {transaction.amount} تومان")
                return True
            else:
                print(f"❌ تراکنش با شناسه {transaction_id} یافت نشد.")
                return False
        
        elif order_id:
            # پیدا کردن تراکنش مرتبط با شناسه سفارش
            query = select(Transaction).where(Transaction.order_id == order_id)
            result = session.execute(query)
            transaction = result.scalar_one_or_none()
            
            if transaction:
                # تأیید پرداخت تراکنش مرتبط با سفارش
                confirmed_transaction = payment_service.confirm_payment(transaction.id)
                if confirmed_transaction:
                    print(f"✅ تراکنش مرتبط با سفارش {order_id} با موفقیت تأیید شد.")
                    print(f"🔢 شناسه تراکنش: {confirmed_transaction.id}")
                    print(f"👤 کاربر: {confirmed_transaction.user.telegram_id}")
                    print(f"💰 مبلغ: {confirmed_transaction.amount} تومان")
                    return True
                else:
                    print(f"❌ خطا در تأیید تراکنش مرتبط با سفارش {order_id}.")
                    return False
            else:
                print(f"❌ تراکنشی برای سفارش با شناسه {order_id} یافت نشد.")
                return False


def main():
    """نقطه ورود اسکریپت"""
    args = parse_args()
    
    success = False
    if args.txn:
        success = confirm_payment(transaction_id=args.txn)
    elif args.order:
        success = confirm_payment(order_id=args.order)
    
    # خروج با کد مناسب
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 