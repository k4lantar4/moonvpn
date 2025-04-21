"""
ریپوزیتوری برای عملیات پایگاه داده مربوط به پلن‌ها
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.plan import Plan
from .base_repository import BaseRepository

class PlanRepository(BaseRepository[Plan]):
    """کلاس ریپوزیتوری برای عملیات پایگاه داده پلن‌ها"""

    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با کلاس مدل Plan"""
        super().__init__(Plan, session)

    async def get_all_active_plans(self) -> List[Plan]:
        """دریافت تمام پلن‌های فعال"""
        query = select(Plan).where(Plan.is_active == True).order_by(Plan.price)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """دریافت پلن با شناسه مشخص"""
        return await self.get_by_id(plan_id)

    async def create_plan(self, name: str, traffic: int, duration_days: int, price: int) -> Plan:
        """ایجاد پلن جدید"""
        return await self.create(
            name=name,
            traffic=traffic,
            duration_days=duration_days,
            price=price,
            is_active=True
        )

    async def update_plan(self, plan_id: int, **kwargs) -> Optional[Plan]:
        """به‌روزرسانی پلن"""
        return await self.update(plan_id, **kwargs)

    async def delete_plan(self, plan_id: int) -> bool:
        """
        حذف نرم پلن (غیرفعال کردن)
        
        به جای حذف فیزیکی، پلن را غیرفعال می‌کند
        """
        plan = await self.get_by_id(plan_id)
        if plan:
            plan.is_active = False
            await self.session.commit()
            return True
        return False 