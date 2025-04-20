"""
سرویس مدیریت پنل‌ها، دریافت inbound‌ها و تنظیمات پیش‌فرض
"""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models.panel import Panel
from db.models.inbound import Inbound
from core.integrations.xui_client import XuiClient

logger = logging.getLogger(__name__)


class PanelService:
    """سرویس مدیریت پنل‌ها با منطق کسب و کار مرتبط"""
    
    def __init__(self, db_session: Session):
        """مقداردهی اولیه سرویس"""
        self.db_session = db_session
    
    async def add_panel(self, name: str, location: str, flag_emoji: str,
                 url: str, username: str, password: str, default_label: str) -> Panel:
        """
        اضافه کردن پنل جدید به سیستم
        
        Args:
            name: نام پنل
            location: موقعیت (کشور)
            flag_emoji: ایموجی پرچم
            url: آدرس پنل
            username: نام کاربری
            password: رمز عبور
            default_label: پیشوند نام اکانت پیش‌فرض
        
        Returns:
            مدل Panel ایجاد شده
        """
        # ایجاد آبجکت پنل جدید
        new_panel = Panel(
            name=name,
            location=location,
            flag_emoji=flag_emoji,
            url=url,
            username=username,
            password=password,
            default_label=default_label,
            status=True
        )
        
        try:
            # تست اتصال به پنل
            await self._test_panel_connection(url, username, password)
            
            # افزودن به دیتابیس
            self.db_session.add(new_panel)
            self.db_session.commit()
            self.db_session.refresh(new_panel)
            
            logger.info(f"Panel {name} added successfully with ID {new_panel.id}")
            return new_panel
        
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to add panel {name}: {str(e)}")
            raise
    
    async def _test_panel_connection(self, url: str, username: str, password: str) -> bool:
        """
        تست اتصال به پنل قبل از ذخیره‌سازی
        
        Args:
            url: آدرس پنل
            username: نام کاربری
            password: رمز عبور
        
        Returns:
            True اگر اتصال موفقیت‌آمیز باشد
        """
        try:
            # تلاش برای ایجاد کلاینت و اتصال به پنل
            client = XuiClient(url, username, password)
            await client.login()
            # تست دریافت inbounds
            await client.get_inbounds()
            return True
        except Exception as e:
            logger.error(f"Panel connection test failed: {str(e)}")
            raise ValueError(f"پنل با آدرس {url} قابل دسترسی نیست: {str(e)}")
    
    def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """
        دریافت پنل با شناسه
        
        Args:
            panel_id: شناسه پنل
        
        Returns:
            مدل Panel یا None اگر یافت نشود
        """
        return self.db_session.query(Panel).filter(Panel.id == panel_id).first()
    
    def get_all_panels(self, active_only: bool = True) -> List[Panel]:
        """
        دریافت تمام پنل‌ها
        
        Args:
            active_only: فقط پنل‌های فعال برگردانده شوند
        
        Returns:
            لیست پنل‌ها
        """
        query = self.db_session.query(Panel)
        if active_only:
            query = query.filter(Panel.status == True)
        return query.all()
    
    def update_panel_status(self, panel_id: int, status: bool) -> Optional[Panel]:
        """
        بروزرسانی وضعیت پنل
        
        Args:
            panel_id: شناسه پنل
            status: وضعیت جدید
        
        Returns:
            مدل Panel بروزرسانی شده یا None اگر یافت نشود
        """
        panel = self.get_panel_by_id(panel_id)
        if not panel:
            return None
        
        try:
            panel.status = status
            self.db_session.commit()
            self.db_session.refresh(panel)
            logger.info(f"Panel {panel.name} status updated to {status}")
            return panel
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Failed to update panel status: {e}")
            raise
    
    def _get_xui_client(self, panel: Panel) -> XuiClient:
        """
        ایجاد کلاینت XUI برای پنل
        
        Args:
            panel: مدل Panel
        
        Returns:
            کلاینت XUI
        """
        return XuiClient(panel.url, panel.username, panel.password)
    
    async def sync_panel_inbounds(self, panel_id: int) -> List[Inbound]:
        """
        همگام‌سازی inbound‌های پنل با دیتابیس
        
        Args:
            panel_id: شناسه پنل
        
        Returns:
            لیست inbound‌های همگام‌سازی شده
        """
        panel = self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"Panel with ID {panel_id} not found")
        
        # دریافت تمام inbound‌های فعلی پنل از دیتابیس
        existing_inbounds = self.db_session.query(Inbound).filter(Inbound.panel_id == panel_id).all()
        existing_inbound_ids = {inbound.inbound_id: inbound for inbound in existing_inbounds}
        
        # ایجاد کلاینت و دریافت inbound‌ها از پنل
        client = self._get_xui_client(panel)
        await client.login()
        inbounds_from_panel = await client.get_inbounds()
        
        # لیست inbound‌های به‌روزشده یا جدید
        updated_inbounds = []
        
        try:
            for inbound_data in inbounds_from_panel:
                inbound_id = inbound_data["id"]
                protocol = inbound_data["protocol"]
                tag = inbound_data["remark"] or f"Inbound-{inbound_id}"
                
                # استخراج اطلاعات مهم از تنظیمات inbound
                settings = inbound_data.get("settings", {})
                clients = settings.get("clients", [])
                client_limit = len(clients) if clients else 0
                
                # ترافیک محدودیت (اگر وجود دارد)
                traffic_limit = None
                if inbound_data.get("totalGB", 0) > 0:
                    traffic_limit = inbound_data["totalGB"]
                
                # اگر inbound در دیتابیس وجود دارد، به‌روزرسانی می‌شود
                if inbound_id in existing_inbound_ids:
                    inbound = existing_inbound_ids[inbound_id]
                    inbound.protocol = protocol
                    inbound.tag = tag
                    inbound.client_limit = client_limit
                    inbound.traffic_limit = traffic_limit
                    logger.info(f"Updated inbound {inbound_id} ({tag}) for panel {panel.name}")
                else:
                    # ایجاد inbound جدید
                    inbound = Inbound(
                        panel_id=panel_id,
                        inbound_id=inbound_id,
                        protocol=protocol,
                        tag=tag,
                        client_limit=client_limit,
                        traffic_limit=traffic_limit
                    )
                    self.db_session.add(inbound)
                    logger.info(f"Added new inbound {inbound_id} ({tag}) for panel {panel.name}")
                
                updated_inbounds.append(inbound)
            
            # حذف inbound‌هایی که دیگر در پنل وجود ندارند
            panel_inbound_ids = {inbound["id"] for inbound in inbounds_from_panel}
            for db_inbound_id, inbound in existing_inbound_ids.items():
                if db_inbound_id not in panel_inbound_ids:
                    self.db_session.delete(inbound)
                    logger.info(f"Removed inbound {db_inbound_id} as it no longer exists in panel {panel.name}")
            
            # ذخیره تغییرات
            self.db_session.commit()
            
            # تازه‌سازی inbound‌ها
            for inbound in updated_inbounds:
                self.db_session.refresh(inbound)
            
            logger.info(f"Synchronized {len(updated_inbounds)} inbounds for panel {panel.name}")
            return updated_inbounds
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to sync inbounds for panel {panel.name}: {str(e)}")
            raise

    async def sync_all_panels_inbounds(self) -> Dict[int, List[Inbound]]:
        """
        همگام‌سازی inbound‌های تمام پنل‌های فعال با دیتابیس
        
        Returns:
            دیکشنری از شناسه پنل به لیست inbound‌های همگام‌سازی شده
        """
        panels = self.get_all_panels(active_only=True)
        results = {}
        
        for panel in panels:
            try:
                inbounds = await self.sync_panel_inbounds(panel.id)
                results[panel.id] = inbounds
                logger.info(f"Successfully synced {len(inbounds)} inbounds for panel {panel.name}")
            except Exception as e:
                logger.error(f"Failed to sync inbounds for panel {panel.name} (ID: {panel.id}): {str(e)}")
                # ادامه دادن با پنل بعدی بدون توقف پروسه
                results[panel.id] = []
        
        return results
