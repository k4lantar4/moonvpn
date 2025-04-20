"""
تست سرویس اکانت‌ها - MoonVPN
"""

import logging
from datetime import datetime, timedelta
import os
import uuid as uuid_lib
import time
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.services.account_service import AccountService
from db.models import Base
from db.models.user import User
from db.models.plan import Plan
from db.models.panel import Panel
from db.models.inbound import Inbound
from db.models.client_account import ClientAccount, AccountStatus

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# مشخصات اتصال به دیتابیس تستی (از محیط Docker)
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://moonvpn_user:strong_password_here@db:3306/moonvpn")
logger.info(f"Using database URL: {DATABASE_URL}")


def setup_test_db():
    """آماده‌سازی دیتابیس تست"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    return db


def test_manually_create_client_account():
    """
    تست ساخت دستی اکانت کلاینت با استفاده از XuiClient
    این تست مستقیماً کلاینت را در پنل ایجاد می‌کند و سپس رکورد آن را در دیتابیس ذخیره می‌کند
    """
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
        
        # دریافت سرویس و پارامترهای لازم برای ایجاد اکانت
        account_service = AccountService(db)
        
        # محاسبه تاریخ انقضا و حجم ترافیک بر اساس پلن
        expires_at = datetime.now() + timedelta(days=plan.duration_days)
        traffic = plan.traffic  # حجم ترافیک به GB
        
        # ایجاد یک transfer_id منحصر به فرد
        timestamp = int(time.time())
        transfer_id = f"moonvpn-{user.id:03d}-test-{timestamp}"
        
        # ایجاد نام اکانت با فرمت استاندارد که منحصر به فرد باشد
        label = f"{panel.flag_emoji}-{panel.default_label}-{user.id:03d}-test-{timestamp}"
        
        # ایجاد UUID
        client_uuid = str(uuid_lib.uuid4())
        
        logger.info(f"Generated test account details: label={label}, uuid={client_uuid}, transfer_id={transfer_id}")
        
        # ایجاد کلاینت در پنل
        from core.integrations.xui_client import XUIClient
        xui_client = XUIClient(panel.url, panel.username, panel.password)
        
        try:
            logger.info(f"Creating client in panel: inbound_id={inbound.inbound_id}, email={label}")
            
            client_data = xui_client.create_client(
                inbound_id=inbound.inbound_id,  # استفاده از inbound_id واقعی در پنل
                email=label,
                traffic=traffic,
                expires_at=expires_at,
                uuid=client_uuid
            )
            
            logger.info(f"Successfully created client in panel for user {user.id}, plan {plan.id}")
            
            # ساخت URL کانفیگ
            config_url = f"{panel.url}/api/config?uuid={client_uuid}&inbound_id={inbound.inbound_id}"
            
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
                xui_client.delete_client(client_uuid)
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


def test_account_service_provision_account():
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
                client_account = account_service.provision_account(
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


if __name__ == "__main__":
    logger.info("Starting account service tests...")
    
    logger.info("=== Test 1: Manual client creation ===")
    result1 = test_manually_create_client_account()
    
    logger.info("\n=== Test 2: Account service provision_account method ===")
    result2 = test_account_service_provision_account()
    
    if result1 and result2:
        logger.info("All tests passed successfully! 🎉")
    else:
        logger.error("Some tests failed! ❌") 