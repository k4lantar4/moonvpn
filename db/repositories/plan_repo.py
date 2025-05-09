"""
ریپوزیتوری برای عملیات پایگاه داده مربوط به پلن‌ها
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.plan import Plan, PlanStatus
from .base_repository import BaseRepository

class PlanRepository(BaseRepository[Plan]):
    """کلاس ریپوزیتوری برای عملیات پایگاه داده پلن‌ها"""

    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با کلاس مدل Plan"""
        super().__init__(session, Plan)

    async def get_all_active(self) -> List[Plan]:
        """دریافت تمام پلن‌های فعال"""
        query = select(Plan).where(Plan.status == PlanStatus.ACTIVE).order_by(Plan.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """دریافت پلن با شناسه مشخص"""
        return await self.get_by_id(plan_id)

    async def create_plan(self, name: str, traffic: int, duration_days: int, price: int) -> Plan:
        """ایجاد پلن جدید"""
        return await self.create(
            name=name,
            traffic_gb=traffic,
            duration_days=duration_days,
            price=price,
            status=PlanStatus.ACTIVE
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
            plan.status = PlanStatus.INACTIVE
            await self.session.commit()
            return True
        return False 