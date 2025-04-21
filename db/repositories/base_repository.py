"""
کلاس پایه برای ریپوزیتوری‌های پایگاه داده
"""

from typing import Optional, TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Base

# تعریف نوع مدل برای استفاده در Generic
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """کلاس پایه برای ریپوزیتوری‌ها با عملیات مشترک"""
    
    def __init__(self, model_class: Type[ModelType], session: AsyncSession):
        """
        مقداردهی اولیه ریپوزیتوری
        
        Args:
            model_class: کلاس مدل SQLAlchemy
            session: نشست پایگاه داده
        """
        self.model_class = model_class
        self.session = session
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        دریافت رکورد با شناسه مشخص
        
        Args:
            id: شناسه رکورد
            
        Returns:
            مدل یافت شده یا None
        """
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self) -> list[ModelType]:
        """
        دریافت تمام رکوردها
        
        Returns:
            لیست تمام رکوردها
        """
        query = select(self.model_class)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelType:
        """
        ایجاد رکورد جدید
        
        Args:
            **kwargs: فیلدهای مدل
            
        Returns:
            مدل ایجاد شده
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        به‌روزرسانی رکورد
        
        Args:
            id: شناسه رکورد
            **kwargs: فیلدهای جدید
            
        Returns:
            مدل به‌روزرسانی شده یا None
        """
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.commit()
            await self.session.refresh(instance)
        return instance
    
    async def delete(self, id: int) -> bool:
        """
        حذف رکورد
        
        Args:
            id: شناسه رکورد
            
        Returns:
            True اگر حذف موفق باشد
        """
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.commit()
            return True
        return False 