#!/usr/bin/env python
"""
اسکریپت تست پرداخت کارت به کارت
این اسکریپت یک سفارش تست ایجاد می‌کند، پرداخت کارت به کارت را شبیه‌سازی کرده
و فرآیند تایید رسید را اجرا می‌کند
"""

import asyncio
import logging
import uuid
import sys
import os
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from db.models.receipt_log import ReceiptStatus
from db.models.order import OrderStatus

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("card_to_card_payment_test.log")
    ]
)
logger = logging.getLogger(__name__)

# اتصال به دیتابیس با استفاده از متغیرهای محیطی
from core.settings import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def test_card_to_card_payment():
    """تست پرداخت کارت به کارت با استفاده از عملیات مستقیم دیتابیس"""
    
    logger.info("شروع تست پرداخت کارت به کارت")
    
    async with async_session() as session:
        try:
            # مرحله 1: دریافت یک کاربر ادمین و یک کاربر عادی با استفاده از کوئری مستقیم
            # دریافت کاربر عادی
            result = await session.execute(
                text("SELECT id, telegram_id, username, full_name, balance FROM users WHERE role = 'USER' LIMIT 1")
            )
            normal_user_row = result.fetchone()
            if not normal_user_row:
                logger.error("هیچ کاربر عادی یافت نشد")
                return
                
            normal_user = {
                "id": normal_user_row[0],
                "telegram_id": normal_user_row[1],
                "username": normal_user_row[2],
                "full_name": normal_user_row[3],
                "balance": Decimal(str(normal_user_row[4] or 0))
            }
            
            # دریافت کاربر ادمین
            result = await session.execute(
                text("SELECT id, telegram_id, username, full_name FROM users WHERE role = 'ADMIN' LIMIT 1")
            )
            admin_user_row = result.fetchone()
            if not admin_user_row:
                logger.error("هیچ کاربر ادمین یافت نشد")
                return
                
            admin_user = {
                "id": admin_user_row[0],
                "telegram_id": admin_user_row[1],
                "username": admin_user_row[2],
                "full_name": admin_user_row[3]
            }
            
            logger.info(f"کاربر عادی: {normal_user['full_name']} (ID: {normal_user['id']})")
            logger.info(f"کاربر ادمین: {admin_user['full_name']} (ID: {admin_user['id']})")
            
            # مرحله 2: دریافت یک کارت بانکی فعال
            result = await session.execute(
                text("SELECT id, card_number, holder_name, bank_name FROM bank_cards WHERE is_active = 1 LIMIT 1")
            )
            card_row = result.fetchone()
            if not card_row:
                logger.error("هیچ کارت بانکی فعالی یافت نشد")
                return
                
            card = {
                "id": card_row[0],
                "card_number": card_row[1],
                "holder_name": card_row[2],
                "bank_name": card_row[3]
            }
            
            logger.info(f"کارت بانکی: {card['bank_name']} - {card['card_number']} به نام {card['holder_name']}")
            
            # مرحله 3: دریافت یک پلن فعال
            result = await session.execute(
                text("SELECT id, name, price FROM plans WHERE status = 'ACTIVE' LIMIT 1")
            )
            plan_row = result.fetchone()
            if not plan_row:
                logger.error("هیچ پلن فعالی یافت نشد")
                return
                
            plan = {
                "id": plan_row[0],
                "name": plan_row[1],
                "price": Decimal(str(plan_row[2]))
            }
            
            logger.info(f"پلن: {plan['name']} - قیمت: {plan['price']}")
            
            # مرحله 4: ایجاد یک سفارش جدید
            current_time = datetime.now(UTC)
            result = await session.execute(
                text("""
                    INSERT INTO orders 
                    (user_id, plan_id, location_name, amount, final_amount, status, receipt_required, created_at, updated_at)
                    VALUES 
                    (:user_id, :plan_id, 'tehran', :amount, :final_amount, 'PENDING', 1, :created_at, :updated_at)
                """),
                {
                    "user_id": normal_user["id"],
                    "plan_id": plan["id"],
                    "amount": float(plan["price"]),
                    "final_amount": float(plan["price"]),
                    "created_at": current_time,
                    "updated_at": current_time
                }
            )
            await session.flush()
            
            # Get the last inserted ID
            result = await session.execute(text("SELECT LAST_INSERT_ID()"))
            order_id = result.scalar()
            
            logger.info(f"سفارش تست با شناسه {order_id} ایجاد شد")
            
            # مرحله 5: ثبت رسید کارت به کارت
            amount = plan["price"]
            text_reference = f"پرداخت تست برای سفارش {order_id}"
            tracking_code = f"CC-{int(datetime.now(UTC).timestamp())}-{uuid.uuid4().hex[:6]}"
            
            result = await session.execute(
                text("""
                    INSERT INTO receipt_log 
                    (user_id, card_id, amount, status, text_reference, tracking_code, submitted_at, order_id, is_flagged, auto_validated)
                    VALUES 
                    (:user_id, :card_id, :amount, 'PENDING', :text_reference, :tracking_code, :submitted_at, :order_id, 0, 0)
                """),
                {
                    "user_id": normal_user["id"],
                    "card_id": card["id"],
                    "amount": float(amount),
                    "text_reference": text_reference,
                    "tracking_code": tracking_code,
                    "submitted_at": datetime.now(UTC),
                    "order_id": order_id
                }
            )
            await session.flush()
            
            # Get the last inserted ID
            result = await session.execute(text("SELECT LAST_INSERT_ID()"))
            receipt_id = result.scalar()
            
            logger.info(f"رسید با شناسه {receipt_id} و کد پیگیری {tracking_code} ایجاد شد")
            
            # مرحله 6: به‌روزرسانی وضعیت سفارش به PENDING_RECEIPT
            await session.execute(
                text("UPDATE orders SET status = 'PENDING_RECEIPT', updated_at = :updated_at WHERE id = :order_id"),
                {"order_id": order_id, "updated_at": datetime.now(UTC)}
            )
            await session.commit()
            logger.info(f"وضعیت سفارش به {OrderStatus.PENDING_RECEIPT} تغییر یافت")
            
            # مرحله 7: تأیید رسید (تغییر وضعیت به APPROVED)
            await session.execute(
                text("""
                    UPDATE receipt_log 
                    SET status = 'APPROVED', admin_id = :admin_id, responded_at = :responded_at, notes = :notes
                    WHERE id = :receipt_id
                """),
                {
                    "admin_id": admin_user["id"],
                    "responded_at": datetime.now(UTC),
                    "notes": "تست تأیید رسید",
                    "receipt_id": receipt_id
                }
            )
            await session.commit()
            logger.info(f"رسید با موفقیت تأیید شد")
            
            # مرحله 8: ایجاد تراکنش برای کاربر - با فیلدهای صحیح
            await session.execute(
                text("""
                    INSERT INTO transactions 
                    (user_id, related_order_id, amount, type, status, reference, tracking_code, created_at)
                    VALUES 
                    (:user_id, :related_order_id, :amount, 'DEPOSIT', 'SUCCESS', :reference, :tracking_code, :created_at)
                """),
                {
                    "user_id": normal_user["id"],
                    "related_order_id": order_id,
                    "amount": float(amount),
                    "reference": tracking_code,
                    "tracking_code": tracking_code,
                    "created_at": datetime.now(UTC)
                }
            )
            await session.flush()
            
            # Get the last inserted transaction ID
            result = await session.execute(text("SELECT LAST_INSERT_ID()"))
            transaction_id = result.scalar()
            logger.info(f"تراکنش با شناسه {transaction_id} ایجاد شد")
            
            # مرحله 9: اتصال تراکنش به رسید
            await session.execute(
                text("UPDATE receipt_log SET transaction_id = :transaction_id WHERE id = :receipt_id"),
                {"transaction_id": transaction_id, "receipt_id": receipt_id}
            )
            await session.commit()
            logger.info(f"تراکنش به رسید متصل شد")
            
            # مرحله 10: به‌روزرسانی موجودی کیف پول کاربر
            new_balance = normal_user["balance"] + amount
            await session.execute(
                text("UPDATE users SET balance = :balance WHERE id = :user_id"),
                {"balance": float(new_balance), "user_id": normal_user["id"]}
            )
            await session.commit()
            logger.info(f"موجودی کیف پول کاربر به‌روز شد: {new_balance}")
            
            # مرحله 11: تغییر وضعیت سفارش به PAID
            await session.execute(
                text("UPDATE orders SET status = 'PAID', updated_at = :updated_at WHERE id = :order_id"),
                {"order_id": order_id, "updated_at": datetime.now(UTC)}
            )
            await session.commit()
            logger.info(f"وضعیت سفارش به {OrderStatus.PAID} تغییر یافت")
            
            # مرحله 12: بررسی نهایی
            # بررسی وضعیت سفارش
            result = await session.execute(
                text("SELECT status FROM orders WHERE id = :order_id"),
                {"order_id": order_id}
            )
            order_status = result.scalar()
            
            if order_status == OrderStatus.PAID.value:
                logger.info(f"وضعیت سفارش به درستی به {order_status} تغییر کرده است")
            else:
                logger.warning(f"وضعیت سفارش به درستی تغییر نکرده است: {order_status}")
            
            # بررسی ارتباط رسید با تراکنش
            result = await session.execute(
                text("SELECT transaction_id FROM receipt_log WHERE id = :receipt_id"),
                {"receipt_id": receipt_id}
            )
            receipt_transaction_id = result.scalar()
            
            if receipt_transaction_id:
                logger.info(f"رسید به درستی به تراکنش با شناسه {receipt_transaction_id} متصل شده است")
            else:
                logger.warning("رسید به هیچ تراکنشی متصل نشده است")
            
            # بررسی موجودی کاربر بعد از تراکنش
            result = await session.execute(
                text("SELECT balance FROM users WHERE id = :user_id"),
                {"user_id": normal_user["id"]}
            )
            final_balance = Decimal(str(result.scalar() or 0))
            logger.info(f"موجودی کاربر پس از تراکنش: {final_balance}")
            
            logger.info("تست پرداخت کارت به کارت با موفقیت به پایان رسید")
            
        except Exception as e:
            logger.error(f"خطا در اجرای تست: {str(e)}", exc_info=True)
            await session.rollback()


async def main():
    """تابع اصلی برای اجرای تست"""
    try:
        await test_card_to_card_payment()
    except Exception as e:
        logger.error(f"خطا در اجرای برنامه: {str(e)}", exc_info=True)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main()) 