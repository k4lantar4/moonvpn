"""
سرویس مدیریت لوکیشن‌های VPN
"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.panel import Panel
from db.repositories.panel_repo import PanelRepository
from core.services.panel_service import PanelService

logger = logging.getLogger(__name__)

class LocationService:
    """سرویس مدیریت لوکیشن‌ها"""

    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با سشن دیتابیس"""
        self.session = session
        self.repository = PanelRepository(session)

    async def get_active_locations(self) -> List[Panel]:
        """
        دریافت لیست لوکیشن‌های فعال
        
        Returns:
            List[Panel]: لیست پنل‌های فعال به عنوان لوکیشن
        """
        try:
            # دریافت پنل‌های فعال
            panels = await self.repository.get_active_panels()
            logger.info(f"Retrieved {len(panels)} active locations")
            return panels
        except Exception as e:
            logger.error(f"Failed to get active locations: {e}")
            return []

    async def get_location(self, location_id: int) -> Optional[Panel]:
        """
        دریافت اطلاعات یک لوکیشن با شناسه آن
        
        Args:
            location_id: شناسه لوکیشن (پنل)
            
        Returns:
            Optional[Panel]: اطلاعات پنل یا None در صورت عدم وجود
        """
        try:
            # دریافت پنل با شناسه مشخص
            panel = await self.repository.get_by_id(location_id)
            if panel:
                logger.info(f"Retrieved location with ID {location_id}")
            else:
                logger.warning(f"Location with ID {location_id} not found")
            return panel
        except Exception as e:
            logger.error(f"Failed to get location with ID {location_id}: {e}")
            return None

    async def get_location_by_name(self, name: str) -> Optional[Panel]:
        """
        دریافت اطلاعات یک لوکیشن با نام آن
        
        Args:
            name: نام لوکیشن (مثلا Germany 🇩🇪)
            
        Returns:
            Optional[Panel]: اطلاعات پنل یا None در صورت عدم وجود
        """
        try:
            panels = await self.repository.filter_by(name=name, is_active=True)
            if panels:
                logger.info(f"Retrieved location with name {name}")
                return panels[0]
            else:
                logger.warning(f"Location with name {name} not found")
                return None
        except Exception as e:
            logger.error(f"Failed to get location with name {name}: {e}")
            return None

    async def get_locations_by_status(self, is_active: bool = True) -> List[Panel]:
        """
        دریافت لیست لوکیشن‌ها بر اساس وضعیت
        
        Args:
            is_active: وضعیت فعال/غیرفعال
            
        Returns:
            List[Panel]: لیست پنل‌ها
        """
        try:
            panels = await self.repository.filter_by(is_active=is_active)
            status = "active" if is_active else "inactive"
            logger.info(f"Retrieved {len(panels)} {status} locations")
            return panels
        except Exception as e:
            logger.error(f"Failed to get {status} locations: {e}")
            return []

    async def get_available_locations(self) -> List[Panel]:
        """
        دریافت لیست لوکیشن‌های قابل دسترس براساس پنل‌های فعال

        Returns:
            List[Panel]: لیست پنل‌های فعال به عنوان لوکیشن
        """
        try:
            # استفاده از سرویس پنل‌ها برای دریافت پنل‌های فعال
            panel_service = PanelService(self.session)
            panels = await panel_service.get_active_panels()
            logger.info(f"Retrieved {len(panels)} available locations from PanelService")
            return panels
        except Exception as e:
            logger.error(f"Failed to get available locations: {e}")
            return []