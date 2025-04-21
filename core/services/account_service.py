"""
سرویس ایجاد، تمدید و حذف اکانت‌های VPN
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.integrations.xui_client import XuiClient
from core.services.panel_service import PanelService
from db.models.client_account import ClientAccount, AccountStatus
from db.models.inbound import Inbound
from db.models.panel import Panel
from db.models.plan import Plan
from db.models.user import User

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
        self.panel_service = PanelService(session)
    
    def _generate_transfer_id(self, user_id: int) -> str:
        """
        ایجاد شناسه انتقال (transfer_id) برای اکانت‌های کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            شناسه منحصر به فرد
        """
        return f"moonvpn-{user_id:03d}"
    
    def _create_label(self, panel: Panel, user_id: int) -> str:
        """
        ایجاد برچسب اکانت با فرمت استاندارد
        
        Args:
            panel: اطلاعات پنل
            user_id: شناسه کاربر
            
        Returns:
            برچسب اکانت (label)
        """
        return f"{panel.flag_emoji}-{panel.default_label}-{user_id:03d}"
    
    async def provision_account(self, user_id: int, plan_id: int, inbound_id: int) -> ClientAccount:
        """
        ایجاد اکانت VPN جدید برای کاربر بر اساس پلن انتخابی
        
        Args:
            user_id: شناسه کاربر
            plan_id: شناسه پلن انتخابی
            inbound_id: شناسه inbound (در دیتابیس ما)
            
        Returns:
            اطلاعات اکانت ایجاد شده
        """
        # دریافت اطلاعات کاربر، پلن و inbound از دیتابیس
        user_result = await self.session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            raise ValueError(f"User with ID {user_id} not found")
            
        plan_result = await self.session.execute(select(Plan).where(Plan.id == plan_id))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            logger.error(f"Plan with ID {plan_id} not found")
            raise ValueError(f"Plan with ID {plan_id} not found")
            
        inbound_result = await self.session.execute(select(Inbound).where(Inbound.id == inbound_id))
        inbound = inbound_result.scalar_one_or_none()
        if not inbound:
            logger.error(f"Inbound with ID {inbound_id} not found")
            raise ValueError(f"Inbound with ID {inbound_id} not found")
            
        panel_result = await self.session.execute(select(Panel).where(Panel.id == inbound.panel_id))
        panel = panel_result.scalar_one_or_none()
        if not panel:
            logger.error(f"Panel for inbound {inbound_id} not found")
            raise ValueError(f"Panel for inbound {inbound_id} not found")
        
        logger.info(f"Creating account for user_id={user_id}, plan_id={plan_id}, inbound_id={inbound_id}")
        
        # محاسبه تاریخ انقضا و حجم ترافیک بر اساس پلن
        expires_at = datetime.now() + timedelta(days=plan.duration_days)
        traffic = plan.traffic  # حجم ترافیک به GB
        
        logger.info(f"Plan details: traffic={traffic}GB, duration={plan.duration_days} days, expires_at={expires_at}")
        
        # ایجاد نام اکانت با فرمت استاندارد
        transfer_id = self._generate_transfer_id(user_id)
        label = self._create_label(panel, user_id)
        
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
                "total_gb": traffic,
                "expiry_time": expire_timestamp,
                "flow": None
            }
            
            result = await xui_client.create_client(
                inbound_id=inbound.inbound_id,
                client_data=client_data
            )
            
            logger.info(f"Successfully created client in panel for user {user_id}, plan {plan_id}")
            
            # ساخت URL کانفیگ
            config_url = await xui_client.get_config(client_uuid)
            
            # ایجاد اکانت VPN در دیتابیس
            client_account = ClientAccount(
                user_id=user_id,
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
            self.session.add(client_account)
            await self.session.commit()
            await self.session.refresh(client_account)
            
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
        account_result = await self.session.execute(
            select(ClientAccount).where(ClientAccount.id == account_id)
        )
        account = account_result.scalar_one_or_none()
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
            
        # دریافت اطلاعات پنل
        panel_result = await self.session.execute(
            select(Panel).where(Panel.id == account.panel_id)
        )
        panel = panel_result.scalar_one_or_none()
        if not panel:
            raise ValueError(f"Panel for account {account_id} not found")
        
        # اتصال به پنل و حذف کلاینت
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        await xui_client.login()
        success = await xui_client.delete_client(account.uuid)
        
        if success:
            # حذف از دیتابیس
            await self.session.delete(account)
            await self.session.commit()
            logger.info(f"Successfully deleted account {account_id}")
            return True
        return False
    
    async def get_active_accounts_by_user(self, user_id: int) -> List[ClientAccount]:
        """
        دریافت لیست اکانت‌های فعال کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            لیست اکانت‌های فعال
        """
        result = await self.session.execute(
            select(ClientAccount)
            .where(ClientAccount.user_id == user_id)
            .where(ClientAccount.status == AccountStatus.ACTIVE)
        )
        return list(result.scalars().all())
    
    async def reset_account_traffic(self, account_id: int) -> bool:
        """
        ریست کردن ترافیک یک اکانت
        
        Args:
            account_id: شناسه اکانت
            
        Returns:
            موفقیت عملیات
        """
        # دریافت اطلاعات اکانت از دیتابیس
        account = await self.session.get(ClientAccount, account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
            
        # دریافت اطلاعات پنل
        panel = await self.session.get(Panel, account.panel_id)
        if not panel:
            raise ValueError(f"Panel for account {account_id} not found")
        
        # اتصال به پنل و ریست ترافیک
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        await xui_client.login()
        success = await xui_client.reset_client_traffic(account.uuid)
        
        if success:
            # به‌روزرسانی در دیتابیس
            account.traffic_used = 0
            await self.session.commit()
            logger.info(f"Reset traffic for account {account_id} of user {account.user_id}")
            
        return success
    
    async def renew_account(self, account_id: int, plan_id: int) -> bool:
        """
        تمدید یک اکانت بر اساس پلن جدید
        
        Args:
            account_id: شناسه اکانت
            plan_id: شناسه پلن جدید
            
        Returns:
            موفقیت عملیات
        """
        # دریافت اطلاعات اکانت و پلن از دیتابیس
        account = await self.session.get(ClientAccount, account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
            
        plan = await self.session.get(Plan, plan_id)
        if not plan:
            raise ValueError(f"Plan with ID {plan_id} not found")
            
        panel = await self.session.get(Panel, account.panel_id)
        if not panel:
            raise ValueError(f"Panel for account {account_id} not found")
        
        # محاسبه تاریخ انقضای جدید و حجم ترافیک
        # اگر اکانت منقضی شده باشد، از تاریخ امروز محاسبه می‌شود
        # در غیر این صورت به تاریخ فعلی اضافه می‌شود
        now = datetime.now()
        if account.expires_at and account.expires_at > now:
            new_expires_at = account.expires_at + timedelta(days=plan.duration_days)
        else:
            new_expires_at = now + timedelta(days=plan.duration_days)
        
        # اتصال به پنل و به‌روزرسانی کلاینت
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        await xui_client.login()
        
        # تبدیل تاریخ انقضا به میلی‌ثانیه
        expire_timestamp = int(datetime.timestamp(new_expires_at)) * 1000
        
        # داده‌های به‌روزرسانی کلاینت
        client_data = {
            "email": account.label,
            "id": account.uuid,
            "enable": True,
            "total_gb": plan.traffic,
            "expiry_time": expire_timestamp,
        }
        
        try:
            result = await xui_client.update_client(account.uuid, client_data)
            
            # ریست ترافیک درصورت درخواست
            if plan.reset_traffic_on_renew:
                await xui_client.reset_client_traffic(account.uuid)
                account.traffic_used = 0
            
            # به‌روزرسانی در دیتابیس
            account.expires_at = new_expires_at
            account.traffic_total = plan.traffic
            account.status = AccountStatus.ACTIVE
            
            await self.session.commit()
            logger.info(f"Renewed account {account_id} with plan {plan_id}, new expiry: {new_expires_at}")
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to renew account {account_id} with plan {plan_id}: {e}")
            raise
    
    async def update_account_traffic(self, account_id: int) -> Dict[str, Any]:
        """
        به‌روزرسانی اطلاعات ترافیک یک اکانت از پنل
        
        Args:
            account_id: شناسه اکانت
            
        Returns:
            اطلاعات به‌روزشده ترافیک
        """
        # دریافت اطلاعات اکانت از دیتابیس
        account = await self.session.get(ClientAccount, account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
            
        panel = await self.session.get(Panel, account.panel_id)
        if not panel:
            raise ValueError(f"Panel for account {account_id} not found")
        
        # اتصال به پنل و دریافت اطلاعات ترافیک
        xui_client = XuiClient(panel.url, panel.username, panel.password)
        await xui_client.login()
        
        try:
            traffic_info = await xui_client.get_client_traffic(account.uuid)
            
            if traffic_info:
                # به‌روزرسانی اطلاعات در دیتابیس
                account.traffic_used = traffic_info.get("up", 0) + traffic_info.get("down", 0)
                await self.session.commit()
                
                logger.info(f"Updated traffic for account {account_id}: {account.traffic_used / (1024*1024*1024):.2f} GB used")
                
                return {
                    "account_id": account.id,
                    "uuid": account.uuid,
                    "traffic_used": account.traffic_used,
                    "traffic_total": account.traffic_total,
                    "traffic_percent": (account.traffic_used / account.traffic_total) * 100 if account.traffic_total > 0 else 0
                }
            
            logger.warning(f"No traffic information found for account {account_id}")
            return {
                "account_id": account.id,
                "uuid": account.uuid,
                "traffic_used": account.traffic_used,
                "traffic_total": account.traffic_total,
                "traffic_percent": (account.traffic_used / account.traffic_total) * 100 if account.traffic_total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to update traffic for account {account_id}: {e}")
            raise
