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
        client = await self._get_xui_client(url, username, password)
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

    async def _get_xui_client(self, url: str, username: str, password: str) -> XuiClient:
        """
        ایجاد و لاگین کلاینت XUI
        Args:
            url: آدرس پنل
            username: نام کاربری
            password: رمز عبور
        Returns:
            XuiClient: کلاینت لاگین شده
        """
        client = XuiClient(url)
        await client.login(username, password)
        return client

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
            client = await self._get_xui_client(panel.url, panel.username, panel.password)
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
