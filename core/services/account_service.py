"""
سرویس ایجاد، تمدید و حذف اکانت‌های VPN
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session

from core.integrations.xui_client import XUIClient
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
    
    def __init__(self, db_session: Session):
        """
        مقداردهی اولیه سرویس با دسترسی به دیتابیس
        
        Args:
            db_session: نشست دیتابیس
        """
        self.db_session = db_session
        self.panel_service = PanelService(db_session)
    
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
    
    def provision_account(self, user_id: int, plan_id: int, inbound_id: int) -> ClientAccount:
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
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            raise ValueError(f"User with ID {user_id} not found")
            
        plan = self.db_session.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            logger.error(f"Plan with ID {plan_id} not found")
            raise ValueError(f"Plan with ID {plan_id} not found")
            
        inbound = self.db_session.query(Inbound).filter(Inbound.id == inbound_id).first()
        if not inbound:
            logger.error(f"Inbound with ID {inbound_id} not found")
            raise ValueError(f"Inbound with ID {inbound_id} not found")
            
        panel = self.db_session.query(Panel).filter(Panel.id == inbound.panel_id).first()
        if not panel:
            logger.error(f"Panel for inbound {inbound_id} not found")
            raise ValueError(f"Panel for inbound {inbound_id} not found")
        
        logger.info(f"Creating account for user_id={user_id}, plan_id={plan_id}, inbound_id={inbound_id}")
        
        # محاسبه تاریخ انقضا و حجم ترافیک بر اساس پلن
        expires_at = datetime.now() + timedelta(days=plan.duration_days)
        traffic = plan.traffic  # حجم ترافیک به GB
        
        logger.info(f"Plan details: traffic={traffic}GB, duration={plan.duration_days} days, expires_at={expires_at}")
        
        # ایجاد نام اکانت با فرمت استاندارد
        # بر اساس الگوی: `FR-Moonvpn-012[-01]`
        transfer_id = self._generate_transfer_id(user_id)
        label = self._create_label(panel, user_id)
        
        # ایجاد UUID
        client_uuid = str(uuid.uuid4())
        
        logger.info(f"Generated account details: label={label}, uuid={client_uuid}")
        
        # ایجاد کلاینت در پنل با استفاده از XuiClient
        xui_client = XUIClient(panel.url, panel.username, panel.password)
        
        try:
            logger.info(f"Calling XUIClient.create_client with inbound_id={inbound.inbound_id}, email={label}, traffic={traffic}GB")
            
            client_data = xui_client.create_client(
                inbound_id=inbound.inbound_id,  # استفاده از inbound_id واقعی در پنل
                email=label,
                traffic=traffic,
                expires_at=expires_at,
                uuid=client_uuid
            )
            
            logger.info(f"Successfully created client in panel for user {user_id}, plan {plan_id}")
            
            # ساخت URL کانفیگ
            config_url = f"{panel.url}/api/config?uuid={client_uuid}&inbound_id={inbound.inbound_id}"
            
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
            self.db_session.add(client_account)
            self.db_session.commit()
            
            logger.info(f"Created new VPN account for user {user_id} with plan {plan_id}, expires at {expires_at}")
            logger.info(f"Config URL: {config_url}")
            
            return client_account
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to provision account for user {user_id}, plan {plan_id}: {e}")
            raise
    
    def delete_account(self, account_id: int) -> bool:
        """
        حذف اکانت VPN
        
        Args:
            account_id: شناسه اکانت
            
        Returns:
            موفقیت عملیات
        """
        # دریافت اطلاعات اکانت از دیتابیس
        account = self.db_session.query(ClientAccount).filter(ClientAccount.id == account_id).first()
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
            
        # دریافت اطلاعات پنل
        panel = self.db_session.query(Panel).filter(Panel.id == account.panel_id).first()
        if not panel:
            raise ValueError(f"Panel for account {account_id} not found")
        
        # اتصال به پنل و حذف کلاینت
        xui_client = XUIClient(panel.url, panel.username, panel.password)
        success = xui_client.delete_client(account.uuid)
        
        if success:
            # حذف از دیتابیس یا تغییر وضعیت
            account.status = AccountStatus.DISABLED
            self.db_session.commit()
            logger.info(f"Deleted VPN account {account_id} for user {account.user_id}")
            
        return success
    
    def get_active_accounts_by_user(self, user_id: int) -> list:
        """
        دریافت لیست اکانت‌های فعال یک کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            لیست اکانت‌های فعال
        """
        return self.db_session.query(ClientAccount).filter(
            ClientAccount.user_id == user_id,
            ClientAccount.status == AccountStatus.ACTIVE
        ).all()
