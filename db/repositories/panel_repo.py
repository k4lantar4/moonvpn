"""
ریپوزیتوری برای مدیریت پنل‌ها در پایگاه داده
"""

from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models.panel import Panel, PanelStatus
from db.repositories.base_repository import BaseRepository


class PanelRepository(BaseRepository[Panel]):
    """ریپوزیتوری برای عملیات CRUD روی مدل Panel"""

    async def get_active_panels(self) -> List[Panel]:
        """
        دریافت لیست پنل‌های فعال
        Returns:
            List[Panel]: لیست پنل‌های فعال
        """
        query = select(Panel).where(Panel.status == PanelStatus.ACTIVE)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, panel_id: int, options: Optional[Sequence] = None) -> Optional[Panel]:
        """
        دریافت پنل با شناسه
        Args:
            panel_id: شناسه پنل
            options: گزینه‌های اضافی برای بارگذاری روابط
        Returns:
            Panel: پنل یافت شده یا None
        """
        query = select(Panel).where(Panel.id == panel_id)
        if options:
            for option in options:
                query = query.options(option)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add(self, panel: Panel) -> None:
        """
        افزودن پنل جدید
        Args:
            panel: پنل جدید
        """
        self.session.add(panel)
        await self.session.flush() 