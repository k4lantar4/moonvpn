"""
کلاس پایه برای تمام ریپازیتوری‌ها
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    کلاس پایه برای تمام ریپازیتوری‌ها که عملیات CRUD پایه را فراهم می‌کند
    """
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        مقداردهی اولیه با جلسه دیتابیس و مدل
        
        Args:
            session: جلسه دیتابیس
            model: کلاس مدل SQLAlchemy
        """
        self.session = session
        self.model = model
    
    async def create(self, data: Dict[str, Any]) -> T:
        """ایجاد یک رکورد جدید"""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """دریافت رکورد با شناسه"""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[T]:
        """دریافت تمام رکوردها"""
        query = select(self.model)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """به‌روزرسانی رکورد با شناسه"""
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def delete(self, id: int) -> bool:
        """حذف رکورد با شناسه"""
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def exists(self, id: int) -> bool:
        """بررسی وجود رکورد با شناسه"""
        query = select(self.model.id).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None 