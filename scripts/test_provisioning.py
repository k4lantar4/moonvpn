import asyncio
import logging
import sys
import os
from typing import Optional

# اضافه کردن مسیر ریشه پروژه به sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# وارد کردن موارد لازم از db.config و core.settings
from db.config import async_session_maker, engine
# از آنجایی که db.config خودش DATABASE_URL را از core.settings وارد می‌کند، نیازی به وارد کردن مجدد نیست
# اما اگر در جای دیگری از اسکریپت نیاز بود، می‌توان core.settings را وارد کرد
# from core.settings import DATABASE_URL 

from db.models import User, Plan, Panel, Inbound, ClientAccount
# وارد کردن همه ریپازیتوری‌های مورد نیاز
from db.repositories.user_repo import UserRepository
from db.repositories.plan_repo import PlanRepository
from db.repositories.panel_repo import PanelRepository
from db.repositories.inbound_repo import InboundRepository
from db.repositories.account_repo import AccountRepository
from db.repositories.client_repo import ClientRepository
from db.repositories.order_repo import OrderRepository
from db.repositories.client_renewal_log_repo import ClientRenewalLogRepository

from core.services.panel_service import PanelService
from core.services.client_service import ClientService
from core.services.account_service import AccountService

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- مقادیر تست ---
TEST_USER_ID = 1
TEST_PLAN_ID = 1
TEST_PANEL_ID = 1
TEST_INBOUND_ID = 22 # شناسه دیتابیس اینباند
# -------------------

async def main():
    """تابع اصلی برای اجرای تست"""
    logger.info("Starting test script for provision_account...")
    
    async with async_session_maker() as session:
        logger.info("Database session created.")
        try:
            # 2. ایجاد ریپازیتوری‌ها (PanelService خودش ریپازیتوری‌هاش رو می‌سازه)
            user_repo = UserRepository(session)
            plan_repo = PlanRepository(session)
            panel_repo = PanelRepository(session) # برای ClientService لازم است
            inbound_repo = InboundRepository(session) # برای ClientService لازم است
            account_repo = AccountRepository(session)
            client_repo = ClientRepository(session)
            order_repo = OrderRepository(session)
            renewal_log_repo = ClientRenewalLogRepository(session)
            
            # 3. ایجاد سرویس‌ها
            panel_service = PanelService(session) # فقط session نیاز دارد
            client_service = ClientService(
                session=session,
                client_repo=client_repo,
                order_repo=order_repo,
                panel_repo=panel_repo, # پاس دادن panel_repo ایجاد شده
                inbound_repo=inbound_repo, # پاس دادن inbound_repo ایجاد شده
                user_repo=user_repo,
                plan_repo=plan_repo,
                renewal_log_repo=renewal_log_repo,
                panel_service=panel_service
            )
            account_service = AccountService(session, client_service, panel_service)
            logger.info("Services initialized correctly.")

            # 4. دریافت اشیاء مورد نیاز از دیتابیس
            user: Optional[User] = await user_repo.get_by_id(TEST_USER_ID)
            plan: Optional[Plan] = await plan_repo.get_by_id(TEST_PLAN_ID)
            # از panel_repo برای دریافت panel استفاده می‌کنیم
            panel: Optional[Panel] = await panel_repo.get_panel_by_id(TEST_PANEL_ID) 
            # از inbound_repo برای دریافت inbound استفاده می‌کنیم
            inbound: Optional[Inbound] = await inbound_repo.get_by_id(TEST_INBOUND_ID) 

            # بررسی وجود تمام اشیاء قبل از ادامه
            if not user:
                logger.error(f"Test User ID {TEST_USER_ID} not found. Aborting.")
                return
            if not plan:
                logger.error(f"Test Plan ID {TEST_PLAN_ID} not found. Aborting.")
                return
            if not panel:
                logger.error(f"Test Panel ID {TEST_PANEL_ID} not found. Aborting.")
                return
            if not inbound:
                logger.error(f"Test Inbound ID {TEST_INBOUND_ID} not found. Aborting.")
                return

            logger.info(f"Fetched entities: User={user.id}, Plan={plan.id}, Panel={panel.id}, Inbound={inbound.id}")

            # 5. فراخوانی provision_account
            logger.info("Calling account_service.provision_account...")
            created_account: Optional[ClientAccount] = await account_service.provision_account(
                user_id=user.id,
                plan=plan,
                inbound=inbound,
                panel=panel,
                order_id=None # بدون سفارش فعلاً
            )
            
            if created_account:
                logger.info(f"SUCCESS! Account provisioned successfully.")
                # Refresh needed to load relationships like panel
                await session.refresh(created_account, attribute_names=['panel']) 
                logger.info(f"  Account ID: {created_account.id}")
                logger.info(f"  Remote UUID: {created_account.remote_uuid}")
                logger.info(f"  Client Name: {created_account.client_name}")
                logger.info(f"  Panel Name (via relationship): {created_account.panel.name if created_account.panel else 'N/A'}")
                logger.info(f"  Config URL: {created_account.config_url}")
                # Commit کردن تغییرات
                await session.commit()
                logger.info("Transaction committed.")
            else:
                logger.error("FAILURE! provision_account returned None.")
                await session.rollback()
                logger.info("Transaction rolled back.")

        except Exception as e:
            logger.error(f"An error occurred during provisioning: {e}", exc_info=True)
            await session.rollback()
            logger.info("Transaction rolled back due to error.")
        finally:
            pass # Context manager handles session closing

async def shutdown():
    logger.info("Disposing database engine.")
    await engine.dispose()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(shutdown())
        logger.info("Script finished.") 