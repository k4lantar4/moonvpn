"""
سرویس مدیریت اینباندها و پروتکل‌های VPN
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.inbound import Inbound
from db.repositories.inbound_repo import InboundRepository

logger = logging.getLogger(__name__)

class InboundService:
    """سرویس مدیریت اینباندها"""

    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با سشن دیتابیس"""
        self.session = session
        self.repository = InboundRepository(session)

    async def get_active_inbounds(self) -> List[Inbound]:
        """
        دریافت لیست اینباندهای فعال
        
        Returns:
            List[Inbound]: لیست اینباندهای فعال
        """
        try:
            inbounds = await self.repository.get_active_inbounds()
            logger.info(f"Retrieved {len(inbounds)} active inbounds")
            return inbounds
        except Exception as e:
            logger.error(f"Failed to get active inbounds: {e}")
            return []

    async def get_inbound(self, inbound_id: int) -> Optional[Inbound]:
        """
        دریافت اطلاعات یک اینباند با شناسه آن
        
        Args:
            inbound_id: شناسه اینباند
            
        Returns:
            Optional[Inbound]: اطلاعات اینباند یا None در صورت عدم وجود
        """
        try:
            inbound = await self.repository.get_by_id(inbound_id)
            if inbound:
                logger.info(f"Retrieved inbound with ID {inbound_id}")
            else:
                logger.warning(f"Inbound with ID {inbound_id} not found")
            return inbound
        except Exception as e:
            logger.error(f"Failed to get inbound with ID {inbound_id}: {e}")
            return None

    async def get_inbounds_by_panel_id(self, panel_id: int) -> List[Inbound]:
        """دریافت اینباندهای یک پنل خاص"""
        try:
            return await self.repository.get_by_panel_id(panel_id)
        except Exception as e:
            logger.error(f"Failed to get inbounds for panel {panel_id}: {e}")
            return []

    async def get_suitable_inbound(self, panel_id: int) -> Optional[Inbound]:
        """
        یافتن اینباند مناسب برای یک پنل خاص.
        
        Args:
            panel_id: شناسه پنل.
            
        Returns:
            شیء Inbound مناسب یا None در صورت عدم وجود.
        """
        logger.debug(f"جستجوی اینباند مناسب برای پنل: {panel_id}")
        inbounds = await self.repository.get_active_inbounds_by_panel_id(panel_id)
        
        if not inbounds:
            logger.warning(f"هیچ اینباند فعالی برای پنل {panel_id} یافت نشد.")
            return None
            
        # فعلاً اولین اینباند فعال را انتخاب می‌کنیم
        # در آینده می‌توان الگوریتم‌های پیچیده‌تری برای انتخاب اینباند اضافه کرد
        return inbounds[0] 