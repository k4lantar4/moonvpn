from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repo import BaseRepository
from core.database.models.plan import Plan
from core.database.models.plan_category import PlanCategory
from core.schemas.plan import PlanCreate, PlanUpdate, PlanCategoryCreate, PlanCategoryUpdate # Assuming schemas

class PlanRepository(BaseRepository[Plan, PlanCreate, PlanUpdate]):
    def __init__(self):
        super().__init__(Plan)

    async def get_active_plans(self, db: AsyncSession) -> List[Plan]:
        statement = (
            select(self.model)
            .join(PlanCategory)
            .where(self.model.is_active == True, PlanCategory.is_active == True)
            .order_by(PlanCategory.sorting_order, self.model.sorting_order)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_active_plans_by_category(self, db: AsyncSession, category_id: int) -> List[Plan]:
        statement = (
            select(self.model)
            .where(self.model.category_id == category_id, self.model.is_active == True)
            .order_by(self.model.sorting_order)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_featured_plans(self, db: AsyncSession) -> List[Plan]:
        statement = (
            select(self.model)
            .join(PlanCategory)
            .where(self.model.is_featured == True, self.model.is_active == True, PlanCategory.is_active == True)
            .order_by(PlanCategory.sorting_order, self.model.sorting_order)
        )
        result = await db.execute(statement)
        return result.scalars().all()

class PlanCategoryRepository(BaseRepository[PlanCategory, PlanCategoryCreate, PlanCategoryUpdate]):
    def __init__(self):
        super().__init__(PlanCategory)

    async def get_active_categories(self, db: AsyncSession) -> List[PlanCategory]:
        statement = select(self.model).where(self.model.is_active == True).order_by(self.model.sorting_order)
        result = await db.execute(statement)
        return result.scalars().all() 