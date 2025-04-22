"""
سرویس ایجاد، تمدید و حذف اکانت‌های VPN
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession

from core.integrations.xui_client import XuiClient
from db.repositories.user_repo import UserRepository
from db.repositories.plan_repo import PlanRepository
from db.repositories.inbound_repo import InboundRepository
from db.repositories.panel_repo import PanelRepository
from db.repositories.client_account_repo import ClientAccountRepository
from db.models.client_account import AccountStatus
from db.schemas.client_account import ClientAccountCreate, ClientAccountUpdate
from db.models import Panel, Inbound, Plan, User, ClientAccount

logger = logging.getLogger(__name__)


class AccountService:
    """
    سرویس مدیریت اکانت‌های VPN کاربران
    """
    
    def __init__(self, session: AsyncSession):
        """
        مقداردهی اولیه سرویس با دسترسی به دیتابیس
        
        Args:
            session: نشست دیتابیس
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.plan_repo = PlanRepository(session)
        self.inbound_repo = InboundRepository(session)
        self.panel_repo = PanelRepository(session)
        self.account_repo = ClientAccountRepository(session)
    
    def _generate_transfer_id(self, user_id: int) -> str:
        """
        ایجاد شناسه انتقال (transfer_id) برای اکانت‌های کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            شناسه منحصر به فرد
        """
        return f"moonvpn-{user_id:03d}"
    
    def _create_label(self, panel_flag_emoji: str, panel_default_label: str, user_id: int) -> str:
        """
        ایجاد برچسب اکانت با فرمت استاندارد
        
        Args:
            panel_flag_emoji: اموجی کشویی پنل
            panel_default_label: برچسب پنل
            user_id: شناسه کاربر
            
        Returns:
            برچسب اکانت (label)
        """
        return f"{panel_flag_emoji}-{panel_default_label}-{user_id:03d}"
    
    async def provision_account(
        self,
        user_id: int,
        plan_id: int,
        inbound_id: int,
        order_id: Optional[int] = None
    ) -> Optional[ClientAccount]:
        """
        ایجاد اکانت VPN جدید برای کاربر بر اساس پلن انتخابی
        
        Args:
            user_id: شناسه کاربر
            plan_id: شناسه پلن انتخابی
            inbound_id: شناسه inbound (در دیتابیس ما)
            order_id: شناسه سفارش (اختیاری)
            
        Returns:
            اطلاعات اکانت ایجاد شده
        """
        # دریافت اطلاعات کاربر، پلن و inbound از دیتابیس
        user: Optional[User] = await self.user_repo.get_by_id(user_id)
        plan: Optional[Plan] = await self.plan_repo.get_by_id(plan_id)
        inbound: Optional[Inbound] = await self.inbound_repo.get_by_id(inbound_id)

        if not user or not plan or not inbound:
            logger.error(f"Missing data for provisioning: user={user_id}, plan={plan_id}, inbound={inbound_id}")
            raise ValueError("User, Plan, or Inbound not found")

        panel: Optional[Panel] = await self.panel_repo.get_by_id(inbound.panel_id)
        if not panel:
            logger.error(f"Panel {inbound.panel_id} for inbound {inbound_id} not found")
            raise ValueError(f"Panel for inbound {inbound_id} not found")
        
        logger.info(f"Creating account for user_id={user_id}, plan_id={plan_id}, inbound_id={inbound_id}")
        
        # محاسبه تاریخ انقضا و حجم ترافیک بر اساس پلن
        expires_at = datetime.now() + timedelta(days=plan.duration_days)
        traffic = plan.traffic_gb  # حجم ترافیک به GB
        
        logger.info(f"Plan details: traffic={traffic}GB, duration={plan.duration_days} days, expires_at={expires_at}")
        
        # ایجاد نام اکانت با فرمت استاندارد
        transfer_id = self._generate_transfer_id(user_id)
        label = self._create_label(panel.flag_emoji, panel.default_label, user_id)
        
        # ایجاد UUID
        client_uuid = str(uuid.uuid4())
        
        logger.info(f"Generated account details: label={label}, uuid={client_uuid}")
        
        # ایجاد کلاینت در پنل با استفاده از XuiClient
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        
        try:
            await xui_client.login()
            logger.info(f"Calling XuiClient.create_client with inbound_id={inbound.inbound_id}, email={label}, traffic={traffic}GB")
            
            # تبدیل تاریخ انقضا به میلی‌ثانیه
            expire_timestamp = int(datetime.timestamp(expires_at)) * 1000
            
            # ایجاد دیکشنری اطلاعات کلاینت
            client_data = {
                "email": label,
                "id": client_uuid,
                "enable": True,
                "total_gb": traffic * (1024**3),
                "expiry_time": expire_timestamp,
                "flow": plan.flow or "",
                "limit_ip": plan.ip_limit or 1,
                "sub_id": transfer_id
            }
            
            result = await xui_client.create_client(
                inbound_id=inbound.inbound_id,
                client_data=client_data
            )
            
            logger.info(f"Successfully created client in panel for user {user_id}, plan {plan_id}")
            
            # ساخت URL کانفیگ
            config_url = await xui_client.get_config(client_uuid)
            
            # ایجاد اکانت VPN در دیتابیس
            account_data = ClientAccountCreate(
                user_id=user_id,
                order_id=order_id,
                panel_id=panel.id,
                inbound_id=inbound.id,
                plan_id=plan_id,
                uuid=client_uuid,
                label=label,
                transfer_id=transfer_id,
                transfer_count=0,
                expires_at=expires_at,
                traffic_total_gb=traffic,
                traffic_used_gb=0,
                status=AccountStatus.ACTIVE,
                config_url=config_url,
                created_at=datetime.utcnow()
            )
            client_account = await self.account_repo.create(account_data)
            
            logger.info(f"Created new VPN account for user {user_id} with plan {plan_id}, expires at {expires_at}")
            logger.info(f"Config URL: {config_url}")
            
            return client_account
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to provision account for user {user_id}, plan {plan_id}: {e}")
            raise
    
    async def delete_account(self, account_id: int) -> bool:
        """
        حذف اکانت VPN
        
        Args:
            account_id: شناسه اکانت
            
        Returns:
            موفقیت عملیات
        """
        # دریافت اطلاعات اکانت از دیتابیس
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            logger.warning(f"Account with ID {account_id} not found for deletion.")
            return False
            
        # دریافت اطلاعات پنل
        panel = await self.panel_repo.get_by_id(account.panel_id)
        if not panel:
            logger.error(f"Panel {account.panel_id} for account {account_id} not found. Cannot delete from panel.")
            raise ValueError(f"Panel for account {account_id} not found")
        
        # اتصال به پنل و حذف کلاینت
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        panel_delete_success = False
        try:
            await xui_client.login()
            logger.info(f"Attempting to delete client UUID {account.uuid} from panel {panel.url}")
            panel_delete_success = await xui_client.delete_client(account.uuid)
            if panel_delete_success:
                logger.info(f"Successfully deleted client {account.uuid} from panel.")
            else:
                logger.warning(f"Failed to delete client {account.uuid} from panel (API returned false). Proceeding with DB deletion.")
        except Exception as e:
            logger.error(f"Error deleting client {account.uuid} from panel {panel.url}: {e}. Proceeding with DB deletion.", exc_info=True)
            # Continue to DB deletion even if panel deletion failed

        # حذف از دیتابیس
        try:
            delete_result = await self.account_repo.delete(account_id)
            if delete_result:
                logger.info(f"Successfully deleted ClientAccount record {account_id}")
                return True
            else:
                logger.warning(f"ClientAccount record {account_id} was not found for deletion in DB (possibly already deleted). Panel deletion status: {panel_delete_success}")
                return False
        except Exception as e:
            logger.error(f"Error deleting ClientAccount record {account_id} from DB: {e}", exc_info=True)
            return False
    
    async def get_active_accounts_by_user(self, user_id: int) -> List[ClientAccount]:
        """
        دریافت لیست اکانت‌های فعال کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            لیست اکانت‌های فعال
        """
        return await self.account_repo.get_active_by_user_id(user_id)
    
    async def renew_account(self, account_id: int, plan_id: int) -> Optional[ClientAccount]:
        """
        تمدید یک اکانت بر اساس پلن جدید
        
        Args:
            account_id: شناسه اکانت
            plan_id: شناسه پلن جدید
            
        Returns:
            موفقیت عملیات
        """
        # دریافت اطلاعات اکانت و پلن از دیتابیس
        account = await self.account_repo.get_by_id(account_id)
        new_plan = await self.plan_repo.get_by_id(plan_id)
        if not account or not new_plan:
            logger.error(f"Account {account_id} or Plan {plan_id} not found for renewal.")
            raise ValueError("Account or Plan not found")
            
        panel = await self.panel_repo.get_by_id(account.panel_id)
        if not panel:
            logger.error(f"Panel {account.panel_id} for account {account_id} not found.")
            raise ValueError(f"Panel for account {account_id} not found")
        
        # محاسبه تاریخ انقضای جدید و حجم ترافیک
        # اگر اکانت منقضی شده باشد، از تاریخ امروز محاسبه می‌شود
        # در غیر این صورت به تاریخ فعلی اضافه می‌شود
        now = datetime.now()
        if account.expires_at and account.expires_at > now:
            new_expires_at = account.expires_at + timedelta(days=new_plan.duration_days)
        else:
            new_expires_at = now + timedelta(days=new_plan.duration_days)
        
        # اتصال به پنل و به‌روزرسانی کلاینت
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        panel_update_successful = False
        try:
            await xui_client.login()
            new_expire_timestamp_ms = int(new_expires_at.timestamp() * 1000)
            new_total_bytes = (account.traffic_total_gb or 0) + new_plan.traffic_gb * (1024**3)

            update_data = {
                "enable": True,
                "total_gb": new_total_bytes,
                "expiry_time": new_expire_timestamp_ms,
                "limit_ip": new_plan.ip_limit or account.ip_limit or 1
            }
            logger.debug(f"Calling XuiClient.update_client for UUID {account.uuid} with data: {update_data}")

            panel_result = await xui_client.update_client(account.uuid, update_data)

            if panel_result and panel_result.get('success', False):
                panel_update_successful = True
                logger.info(f"Successfully updated client {account.uuid} in panel for renewal.")
            else:
                error_msg = panel_result.get('msg', 'Unknown error from panel')
                logger.error(f"Failed to update client {account.uuid} in panel for renewal: {error_msg}")
                raise RuntimeError(f"Panel API error during renewal: {error_msg}")

        except Exception as e:
            logger.error(f"Error interacting with XUI panel for renewing account {account_id}: {e}", exc_info=True)
            raise

        # به‌روزرسانی در دیتابیس
        try:
            update_db_data = ClientAccountUpdate(
                expires_at=new_expires_at,
                traffic_total_gb=(account.traffic_total_gb or 0) + new_plan.traffic_gb,
                status=AccountStatus.ACTIVE,
                plan_id=new_plan.id
            )
            updated_account = await self.account_repo.update(account_id, update_db_data)
            logger.info(f"Successfully updated ClientAccount record {account_id} for renewal.")
            return updated_account
        except Exception as e:
            logger.error(f"CRITICAL: Failed to update DB record for account {account_id} after successful panel renewal: {e}", exc_info=True)
            raise
    
    async def update_account_traffic(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        به‌روزرسانی اطلاعات ترافیک یک اکانت از پنل
        
        Args:
            account_id: شناسه اکانت
            
        Returns:
            اطلاعات به‌روزشده ترافیک
        """
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            logger.warning(f"Account {account_id} not found for traffic update.")
            return None

        panel = await self.panel_repo.get_by_id(account.panel_id)
        if not panel:
            logger.error(f"Panel {account.panel_id} for account {account_id} not found.")
            return None

        xui_client = XuiClient(panel.url, panel.username, panel.password)
        try:
            await xui_client.login()
            client_stats = await xui_client.get_client_stats(account.uuid)

            if client_stats:
                up_bytes = client_stats.get('up', 0)
                down_bytes = client_stats.get('down', 0)
                total_used_bytes = up_bytes + down_bytes
                total_used_gb = round(total_used_bytes / (1024**3), 3)

                logger.info(f"Fetched traffic for account {account_id} (UUID: {account.uuid}): Used {total_used_gb} GB")

                update_data = ClientAccountUpdate(traffic_used_gb=total_used_gb)
                await self.account_repo.update(account_id, update_data)

                return {
                    'up_gb': round(up_bytes / (1024**3), 3),
                    'down_gb': round(down_bytes / (1024**3), 3),
                    'total_used_gb': total_used_gb
                }
            else:
                logger.warning(f"Could not retrieve client stats for {account.uuid} from panel {panel.url}")
                return None
        except Exception as e:
            logger.error(f"Error updating traffic for account {account_id}: {e}", exc_info=True)
            return None
