"""
سرویس مدیریت پلن‌های VPN
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.plan import Plan
from db.repositories.plan_repository import PlanRepository

class PlanService:
    """کلاس سرویس برای مدیریت پلن‌ها"""
    
    def __init__(self, session: AsyncSession):
        """
        مقداردهی اولیه سرویس
        
        Args:
            session: نشست پایگاه داده
        """
        self.repository = PlanRepository(session)
    
    async def get_all_active_plans(self) -> List[Plan]:
        """
        دریافت لیست پلن‌های فعال (برای حفظ سازگاری با کد قبلی)
        
        Returns:
            لیست پلن‌های فعال
        """
        return await self.repository.get_all_active_plans()
    
    async def get_all_plans(self, active_only: bool = True) -> List[Plan]:
        """
        دریافت لیست پلن‌ها
        
        Args:
            active_only: فقط پلن‌های فعال برگردانده شوند
            
        Returns:
            لیست پلن‌ها
        """
        if active_only:
            return await self.repository.get_all_active_plans()
        return await self.repository.get_all()
    
    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """
        دریافت پلن با شناسه مشخص
        
        Args:
            plan_id: شناسه پلن
            
        Returns:
            پلن یافت شده یا None
        """
        return await self.repository.get_plan_by_id(plan_id)
    
    async def create_plan(self, name: str, traffic: int, duration_days: int, price: int) -> Plan:
        """
        ایجاد پلن جدید
        
        Args:
            name: نام پلن
            traffic: حجم ترافیک به گیگابایت
            duration_days: مدت اعتبار به روز
            price: قیمت به تومان
            
        Returns:
            پلن ایجاد شده
        """
        return await self.repository.create_plan(
            name=name,
            traffic=traffic,
            duration_days=duration_days,
            price=price
        )
    
    async def update_plan(self, plan_id: int, **kwargs) -> Optional[Plan]:
        """
        به‌روزرسانی پلن
        
        Args:
            plan_id: شناسه پلن
            **kwargs: فیلدهای جدید
            
        Returns:
            پلن به‌روزرسانی شده یا None
        """
        return await self.repository.update_plan(plan_id, **kwargs)
    
    async def delete_plan(self, plan_id: int) -> bool:
        """
        حذف نرم پلن (غیرفعال کردن)
        
        Args:
            plan_id: شناسه پلن
            
        Returns:
            True اگر حذف موفق باشد
        """
        return await self.repository.delete_plan(plan_id) 