"""
تست‌های سرویس مدیریت اکانت‌های VPN
"""

import logging
import time
import uuid as uuid_lib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.services.account_service import AccountService
from db.models.base import Base
from db.models.client_account import ClientAccount, AccountStatus
from db.models.inbound import Inbound
from db.models.panel import Panel
from db.models.plan import Plan
from db.models.user import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def setup_test_db():
    """راه‌اندازی دیتابیس تست"""
    # استفاده از دیتابیس تست (با تنظیمات اولیه پروژه)
    DATABASE_URL = "mysql+aiomysql://moonvpn:moonvpn@localhost:3306/moonvpn"
    engine = create_async_engine(DATABASE_URL)
    SessionLocal = async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)
    return SessionLocal()


async def test_manually_create_client_account():
    """تست ساخت دستی اکانت کلاینت با استفاده از XuiClient"""
    try:
        # ساخت نشست دیتابیس
        db = setup_test_db()
        
        # خواندن اطلاعات موجود برای تست
        user = db.query(User).first()
        if not user:
            logger.error("No users found in database for testing")
            return False
            
        plan = db.query(Plan).first()
        if not plan:
            logger.error("No plans found in database for testing")
            return False
            
        inbound = db.query(Inbound).first()
        if not inbound:
            logger.error("No inbounds found in database for testing")
            return False
            
        panel = db.query(Panel).filter(Panel.id == inbound.panel_id).first()
        if not panel:
            logger.error(f"Panel for inbound {inbound.id} not found")
            return False
            
        # محاسبه تاریخ انقضا و حجم ترافیک
        expires_at = datetime.now() + timedelta(days=plan.duration_days)
        traffic = plan.traffic  # حجم ترافیک به GB
        
        logger.info(f"Plan details: traffic={traffic}GB, duration={plan.duration_days} days, expires_at={expires_at}")
        
        # ایجاد یک timestamp منحصر به فرد برای تست
        timestamp = int(time.time())
        transfer_id = f"moonvpn-{user.id:03d}-test-{timestamp}"
        
        # ایجاد نام اکانت با فرمت استاندارد که منحصر به فرد باشد
        label = f"{panel.flag_emoji}-{panel.default_label}-{user.id:03d}-test-{timestamp}"
        
        # ایجاد UUID
        client_uuid = str(uuid_lib.uuid4())
        
        logger.info(f"Generated test account details: label={label}, uuid={client_uuid}, transfer_id={transfer_id}")
        
        # ایجاد کلاینت در پنل
        from core.integrations.xui_client import XuiClient
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        
        try:
            await xui_client.login()
            logger.info(f"Creating client in panel: inbound_id={inbound.inbound_id}, email={label}")
            
            # تبدیل تاریخ انقضا به میلی‌ثانیه
            expire_timestamp = int(datetime.timestamp(expires_at)) * 1000
            
            # ایجاد دیکشنری اطلاعات کلاینت
            client_data = {
                "email": label,
                "id": client_uuid,
                "enable": True,
                "total_gb": traffic,
                "expiry_time": expire_timestamp,
                "flow": None
            }
            
            result = await xui_client.create_client(
                inbound_id=inbound.inbound_id,
                client_data=client_data
            )
            
            logger.info(f"Successfully created client in panel for user {user.id}, plan {plan.id}")
            
            # دریافت لینک کانفیگ
            config_url = await xui_client.get_config(client_uuid)
            
            # ایجاد اکانت VPN در دیتابیس
            client_account = ClientAccount(
                user_id=user.id,
                panel_id=panel.id,
                inbound_id=inbound.id,
                uuid=client_uuid,
                label=label,
                transfer_id=transfer_id,
                transfer_count=0,
                expires_at=expires_at,
                traffic_total=traffic,
                traffic_used=0,
                status=AccountStatus.ACTIVE,
                config_url=config_url
            )
            
            # ذخیره در دیتابیس
            db.add(client_account)
            db.commit()
            db.refresh(client_account)
            
            logger.info(f"Created new VPN account in DB with ID: {client_account.id}")
            logger.info(f"Config URL: {config_url}")
            
            # بررسی ایجاد اکانت در دیتابیس
            saved_account = db.query(ClientAccount).filter(
                ClientAccount.uuid == client_uuid
            ).first()
            
            if saved_account:
                logger.info("✅ Test passed: Account saved to database successfully")
                logger.info(f"Account Details:\n"
                          f"- ID: {saved_account.id}\n"
                          f"- User ID: {saved_account.user_id}\n"
                          f"- Label: {saved_account.label}\n"
                          f"- Traffic: {saved_account.traffic_total} GB\n"
                          f"- Expires: {saved_account.expires_at}\n"
                          f"- Config URL: {saved_account.config_url}")
                return True
            else:
                logger.error("❌ Test failed: Account not found in database")
                return False
                
        except Exception as e:
            db.rollback()
            logger.error(f"Test failed with error: {e}")
            
            # پاکسازی - حذف کلاینت از پنل در صورت خطا
            try:
                logger.info(f"Cleaning up by deleting client from panel: {client_uuid}")
                await xui_client.delete_client(client_uuid)
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
                
            return False
            
    except Exception as e:
        logger.error(f"Test setup failed with error: {e}")
        return False
    finally:
        # بستن نشست دیتابیس
        if 'db' in locals():
            db.close()


async def test_account_service_provision_account():
    """تست متد provision_account سرویس AccountService"""
    try:
        # ساخت نشست دیتابیس
        db = setup_test_db()
        
        # خواندن اطلاعات موجود برای تست
        user = db.query(User).first()
        if not user:
            logger.error("No users found in database for testing")
            return False
            
        plan = db.query(Plan).first()
        if not plan:
            logger.error("No plans found in database for testing")
            return False
            
        inbound = db.query(Inbound).first()
        if not inbound:
            logger.error("No inbounds found in database for testing")
            return False
            
        panel = db.query(Panel).filter(Panel.id == inbound.panel_id).first()
        if not panel:
            logger.error(f"Panel for inbound {inbound.id} not found")
            return False
            
        # ایجاد یک timestamp منحصر به فرد برای تست
        # استفاده از مقدار زمان با تأخیر 1 ثانیه برای تضمین متفاوت بودن
        time.sleep(1)
        timestamp = int(time.time())
        transfer_id = f"moonvpn-{user.id:03d}-service-test-{timestamp}"
        unique_label = f"{panel.flag_emoji}-{panel.default_label}-{user.id:03d}-service-{timestamp}"
            
        # پچ کردن توابع ساخت transfer_id و label برای جلوگیری از خطای تکراری بودن
        with patch('core.services.account_service.AccountService._generate_transfer_id', 
                  return_value=transfer_id):
                  
            # پچ کردن تابع _create_label
            original_init = AccountService.__init__
            
            def patched_init(self, db_session):
                original_init(self, db_session)
                # تعریف متدی که متد اصلی را جایگزین می‌کند
                self._create_label = MagicMock(return_value=unique_label)
                
            with patch('core.services.account_service.AccountService.__init__', patched_init):
                # تست ساخت اکانت
                account_service = AccountService(db)
                
                logger.info(f"Testing provision_account with user_id={user.id}, plan_id={plan.id}, inbound_id={inbound.id}")
                
                # پچ کردن متد _create_label برای ارسال برچسب منحصر به فرد
                account_service._create_label = MagicMock(return_value=unique_label)
                
                # ایجاد اکانت جدید
                client_account = await account_service.provision_account(
                    user_id=user.id,
                    plan_id=plan.id,
                    inbound_id=inbound.id
                )
                
                logger.info(f"Account created successfully with UUID: {client_account.uuid}")
                logger.info(f"Config URL: {client_account.config_url}")
                
                # بررسی ایجاد اکانت در دیتابیس
                saved_account = db.query(ClientAccount).filter(
                    ClientAccount.uuid == client_account.uuid
                ).first()
                
                if saved_account:
                    logger.info("✅ Test passed: Account created successfully with provision_account method")
                    logger.info(f"Account Details:\n"
                              f"- ID: {saved_account.id}\n"
                              f"- User ID: {saved_account.user_id}\n"
                              f"- Label: {saved_account.label}\n"
                              f"- Transfer ID: {saved_account.transfer_id}\n"
                              f"- Traffic: {saved_account.traffic_total} GB\n"
                              f"- Expires: {saved_account.expires_at}\n"
                              f"- Config URL: {saved_account.config_url}")
                    return True
                else:
                    logger.error("❌ Test failed: Account not found in database")
                    return False
                
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False
    finally:
        # بستن نشست دیتابیس
        if 'db' in locals():
            db.close()


async def run_tests():
    """اجرای تست‌ها به صورت آسنکرون"""
    logger.info("Starting account service tests...")
    
    logger.info("=== Test 1: Manual client creation ===")
    result1 = await test_manually_create_client_account()
    
    logger.info("\n=== Test 2: Account service provision_account method ===")
    result2 = await test_account_service_provision_account()
    
    if result1 and result2:
        logger.info("All tests passed successfully! 🎉")


if __name__ == "__main__":
    asyncio.run(run_tests()) 