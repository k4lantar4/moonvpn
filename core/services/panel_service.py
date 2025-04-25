"""
سرویس مدیریت پنل‌ها و تنظیمات inbound
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from db.models.panel import Panel, PanelStatus
from db.models.inbound import Inbound, InboundStatus
from core.integrations.xui_client import XuiClient
from core.services.notification_service import NotificationService
from db.repositories.panel_repo import PanelRepository
from db import get_async_db

logger = logging.getLogger(__name__)


class PanelService:
    """سرویس مدیریت پنل‌ها و تنظیمات inbound"""

    def __init__(self, session: AsyncSession):
        """
        ایجاد نمونه سرویس
        Args:
            session: نشست پایگاه داده
        """
        self.session = session
        self.panel_repo = PanelRepository(session)
        self.notification_service = NotificationService(session)
        self._xui_clients: Dict[int, XuiClient] = {}  # Cache for XuiClient instances

    async def add_panel(self, name: str, location: str, flag_emoji: str,
                     url: str, username: str, password: str) -> Panel:
        """
        افزودن پنل جدید
        Args:
            name: نام پنل
            location: موقعیت پنل
            flag_emoji: ایموجی پرچم
            url: آدرس پنل
            username: نام کاربری
            password: رمز عبور
        Returns:
            Panel: پنل ایجاد شده
        """
        # تست اتصال به پنل
        client = await self._get_xui_client(Panel(
            name=name,
            location=location,
            flag_emoji=flag_emoji,
            url=url,
            username=username,
            password=password,
            status=PanelStatus.ACTIVE
        ))
        if not await client.test_connection():
            raise ValueError("خطا در اتصال به پنل")

        # ایجاد پنل
        panel = Panel(
            name=name,
            location=location,
            flag_emoji=flag_emoji,
            url=url,
            username=username,
            password=password,
            status=PanelStatus.ACTIVE
        )
        
        await self.panel_repo.add(panel)
        await self.session.flush()
        
        # همگام‌سازی inbound‌ها
        try:
            await self.sync_panel_inbounds(panel.id)
        except Exception as e:
            logger.error(f"خطا در همگام‌سازی inbound‌های پنل {panel.id}: {str(e)}", exc_info=True)
            
        return panel

    async def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """
        دریافت پنل با شناسه
        Args:
            panel_id: شناسه پنل
        Returns:
            Panel: پنل یافت شده یا None
        """
        return await self.panel_repo.get_by_id(panel_id)

    async def get_active_panels(self) -> List[Panel]:
        """
        دریافت لیست پنل‌های فعال
        Returns:
            List[Panel]: لیست پنل‌های فعال
        """
        return await self.panel_repo.get_active_panels()

    async def get_all_panels(self) -> List[Panel]:
        """
        دریافت لیست تمامی پنل‌ها
        Returns:
            List[Panel]: لیست تمامی پنل‌ها
        """
        return await self.panel_repo.get_all_panels()

    async def _get_xui_client(self, panel: Panel) -> XuiClient:
        """
        دریافت یا ایجاد یک نمونه XuiClient برای پنل
        
        Args:
            panel: مدل پنل
            
        Returns:
            نمونه XuiClient
        """
        if panel.id not in self._xui_clients:
            client = XuiClient(
                host=panel.url,
                username=panel.username,
                password=panel.password
            )
            await client.login()  # Login to the panel
            self._xui_clients[panel.id] = client
            
        return self._xui_clients[panel.id]

    async def sync_panel_inbounds(self, panel_id: int) -> None:
        """
        همگام‌سازی inbound‌های پنل با پایگاه داده
        Args:
            panel_id: شناسه پنل
        """
        # دریافت پنل
        panel = await self.panel_repo.get_by_id(panel_id, [selectinload(Panel.inbounds)])
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")

        # دریافت inbound‌های فعلی
        current_inbounds = {inb.remote_id: inb for inb in panel.inbounds 
                          if inb.status != InboundStatus.DELETED}

        try:
            # دریافت inbound‌ها از پنل
            client = await self._get_xui_client(panel)
            panel_inbounds = await client.get_inbounds()

            # به‌روزرسانی یا ایجاد inbound‌ها
            for inb_data in panel_inbounds:
                remote_id = inb_data["id"]
                
                if remote_id in current_inbounds:
                    # به‌روزرسانی inbound موجود
                    inbound = current_inbounds[remote_id]
                    inbound.protocol = inb_data["protocol"]
                    inbound.tag = inb_data.get("remark", "")
                    inbound.port = inb_data["port"]
                    inbound.settings_json = inb_data.get("settings", {})
                    inbound.sniffing = inb_data.get("sniffing", {})
                    inbound.status = (InboundStatus.ACTIVE 
                                    if inb_data.get("enable", True) 
                                    else InboundStatus.DISABLED)
                    inbound.last_synced = datetime.utcnow()
                else:
                    # ایجاد inbound جدید
                    new_inbound = Inbound(
                        panel_id=panel.id,
                        remote_id=remote_id,
                        protocol=inb_data["protocol"],
                        tag=inb_data.get("remark", ""),
                        port=inb_data["port"],
                        settings_json=inb_data.get("settings", {}),
                        sniffing=inb_data.get("sniffing", {}),
                        status=(InboundStatus.ACTIVE 
                               if inb_data.get("enable", True) 
                               else InboundStatus.DISABLED),
                        max_clients=inb_data.get("max_clients", 0),
                        last_synced=datetime.utcnow()
                    )
                    panel.inbounds.append(new_inbound)

            # علامت‌گذاری inbound‌های حذف شده
            panel_inbound_ids = {inb["id"] for inb in panel_inbounds}
            for inbound in current_inbounds.values():
                if inbound.remote_id not in panel_inbound_ids:
                    inbound.status = InboundStatus.DELETED
                    inbound.last_synced = datetime.utcnow()

            await self.session.commit()
            logger.info(f"همگام‌سازی موفق inbound‌های پنل {panel_id}")

        except Exception as e:
            await self.session.rollback()
            logger.error(f"خطا در همگام‌سازی inbound‌های پنل {panel_id}: {str(e)}", exc_info=True)
            raise

    async def sync_all_panels_inbounds(self) -> Dict[int, List[Inbound]]:
        """
        همگام‌سازی inbound‌های تمام پنل‌های فعال با دیتابیس
        
        Returns:
            دیکشنری از شناسه پنل به لیست inbound‌های همگام‌سازی شده
        """
        panels = await self.get_active_panels()
        results = {}
        
        for panel in panels:
            try:
                await self.sync_panel_inbounds(panel.id)
                results[panel.id] = panel.inbounds
                logger.info(f"Successfully synced {len(panel.inbounds)} inbounds for panel {panel.name}")
            except Exception as e:
                logger.error(f"Failed to sync inbounds for panel {panel.name} (ID: {panel.id}): {str(e)}")
                # ارسال نوتیفیکیشن به ادمین‌ها
                await self.notification_service.notify_admins(
                    f"⚠️ خطا در همگام‌سازی inbound‌های پنل {panel.name}:\n{str(e)}"
                )
                # ادامه دادن با پنل بعدی بدون توقف پروسه
                results[panel.id] = []
        
        return results

    async def get_panel_by_location(self, location: str) -> Optional[Panel]:
        """
        دریافت پنل با لوکیشن مشخص
        
        Args:
            location: نام لوکیشن
            
        Returns:
            پنل یافت شده یا None
        """
        return await self.panel_repo.get_by_location(location)

    async def get_panel_by_address(self, address: str) -> Optional[Panel]:
        """
        دریافت پنل با آدرس مشخص
        
        Args:
            address: آدرس پنل
            
        Returns:
            پنل یافت شده یا None
        """
        return await self.panel_repo.get_by_address(address)

    # اضافه کردن متد برای دریافت لیست اینباندها به صورت real-time
    async def get_inbounds_by_panel_id(self, panel_id: int) -> List[Dict[str, Any]]:
        """
        دریافت لیست inbound‌های یک پنل خاص
        Args:
            panel_id: شناسه پنل
        Returns:
            لیست inbound‌ها
        """
        panel = await self.panel_repo.get_by_id(panel_id, [selectinload(Panel.inbounds)])
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")

        # Filter out deleted inbounds
        active_inbounds = [
            {
                "id": inb.remote_id,
                "protocol": inb.protocol,
                "remark": inb.tag,
                "port": inb.port,
                "enable": inb.status == InboundStatus.ACTIVE
            }
            for inb in panel.inbounds if inb.status != InboundStatus.DELETED
        ]
        return active_inbounds

    async def get_clients_by_inbound(self, panel_id: int, inbound_id: int) -> List[Dict[str, Any]]:
        """
        دریافت لیست کلاینت‌های یک inbound خاص از پنل
        Args:
            panel_id: شناسه پنل
            inbound_id: شناسه inbound در پنل
        Returns:
            لیست دیکشنری شامل اطلاعات کلاینت‌ها
        """
        panel = await self.panel_repo.get_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")

        client = await self._get_xui_client(panel)
        inbound_data = await client.get_inbound(inbound_id)

        if not inbound_data:
            return [] # Inbound not found or no data

        # Determine if clientStats is enabled and available
        use_client_stats = inbound_data.get("clientStats", False) and "clientStats" in inbound_data

        clients_list = []
        if use_client_stats and isinstance(inbound_data.get("clientStats"), list):
             # Use clientStats if enabled and available
             for client_stat in inbound_data["clientStats"]:
                clients_list.append({
                    "uuid": client_stat.get("id"), # Use id for UUID
                    "email": client_stat.get("email"),
                    "enable": client_stat.get("enable", False),
                    "totalGB": client_stat.get("totalGB", 0),
                    "up": client_stat.get("up", 0),
                    "down": client_stat.get("down", 0),
                    "expiryTime": client_stat.get("expiryTime", 0),
                    # Add other relevant fields from clientStats if needed
                })
        elif isinstance(inbound_data.get("settings", {}).get("clients"), list):
            # Otherwise, use clients from settings
            for client_setting in inbound_data["settings"]["clients"]:
                clients_list.append({
                    "uuid": client_setting.get("id"), # Use id for UUID
                    "email": client_setting.get("email"),
                    "enable": client_setting.get("enable", False), # Assuming enable is in settings
                    "totalGB": client_setting.get("totalGB", 0), # Assuming totalGB is in settings
                    "up": client_setting.get("up", 0), # Assuming these are not in settings and will be 0 if clientStats is off
                    "down": client_setting.get("down", 0),
                    "expiryTime": client_setting.get("expiryTime", 0), # Assuming expiryTime is in settings
                    # Add other relevant fields from settings if needed
                })
        else:
            # No client data found
            return []


        return clients_list

    async def get_client_config(self, panel_id: int, inbound_id: int, uuid: str) -> str:
        """
        دریافت لینک کانفیگ یک کلاینت
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")
        client = await self._get_xui_client(panel)
        try:
            config_url = await client.get_config(uuid)
            logger.info(f"Generated config URL for client {uuid} on panel {panel_id}")
            return config_url
        except Exception as e:
            logger.error(f"Error getting config for client {uuid} on panel {panel_id}: {str(e)}", exc_info=True)
            raise

    async def reset_client_traffic(self, panel_id: int, uuid: str) -> bool:
        """
        ریست کردن ترافیک یک کلاینت
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")
        client = await self._get_xui_client(panel)
        try:
            result = await client.reset_client_traffic(uuid)
            logger.info(f"Successfully reset traffic for client {uuid} on panel {panel_id}")
            return result
        except Exception as e:
            logger.error(f"Error resetting traffic for client {uuid} on panel {panel_id}: {str(e)}", exc_info=True)
            raise

    async def delete_client(self, panel_id: int, inbound_id: int, uuid: str) -> bool:
        """
        حذف یک کلاینت از inbound و دیتابیس
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")
        client = await self._get_xui_client(panel)
        try:
            result = await client.delete_client(uuid)
            if result:
                from db.models.client_account import ClientAccount
                # حذف رکورد از دیتابیس
                stmt = select(ClientAccount).where(
                    ClientAccount.panel_id == panel_id,
                    ClientAccount.inbound_id == inbound_id,
                    ClientAccount.remote_uuid == uuid
                )
                res = await self.session.execute(stmt)
                account = res.scalar_one_or_none()
                if account:
                    await self.session.delete(account)
                    await self.session.commit()
                logger.info(f"Deleted client {uuid} from panel {panel_id} and DB")
            return result
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting client {uuid} on panel {panel_id}: {str(e)}", exc_info=True)
            raise

    async def register_panel(self, url: str, username: str, password: str, location_name: str) -> Panel:
        """
        ثبت یک پنل جدید
        Args:
            url: آدرس پنل
            username: نام کاربری
            password: رمز عبور
            location_name: نام موقعیت
        Returns:
            Panel: پنل ثبت شده
        """
        # Check for duplicate panel by URL
        existing_panel = await self.panel_repo.get_panel_by_url(url)
        if existing_panel:
            raise Exception("پنل با این آدرس قبلاً ثبت شده است.")
        panel_data = {
            "url": url,
            "username": username,
            "password": password,
            "location_name": location_name,
            "status": PanelStatus.ACTIVE
        }
        panel = await self.panel_repo.create_panel(panel_data)
        return panel
