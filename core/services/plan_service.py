"""
سرویس مدیریت پلن‌های سیستم MoonVPN
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models.plan import Plan


class PlanService:
    """سرویس مدیریت پلن‌ها و دسترسی به اطلاعات آنها"""
    
    def __init__(self, db_session: Session):
        """مقداردهی اولیه سرویس"""
        self.db_session = db_session
    
    def get_all_active_plans(self) -> List[Plan]:
        """دریافت لیست تمام پلن‌های فعال"""
        query = select(Plan).where(Plan.is_trial == False).order_by(Plan.price)
        return list(self.db_session.execute(query).scalars().all())
    
    def get_plan_by_id(self, plan_id: int) -> Plan:
        """دریافت اطلاعات یک پلن با شناسه آن"""
        return self.db_session.query(Plan).filter(Plan.id == plan_id).first()
    
    def get_trial_plans(self) -> List[Plan]:
        """دریافت پلن‌های تستی"""
        query = select(Plan).where(Plan.is_trial == True)
        return list(self.db_session.execute(query).scalars().all())
    
    def get_plans_by_location(self, location_code: str) -> List[Plan]:
        """دریافت پلن‌های مناسب برای یک لوکیشن خاص"""
        # نکته: این روش نیاز به بررسی دارد - available_locations در ستون JSON
        query = select(Plan).where(Plan.is_trial == False)
        plans = list(self.db_session.execute(query).scalars().all())
        
        # فیلتر پلن‌هایی که لوکیشن موردنظر را پشتیبانی می‌کنند
        compatible_plans = []
        for plan in plans:
            if plan.available_locations is None:
                compatible_plans.append(plan)  # اگر محدودیتی نباشد، همه لوکیشن‌ها مجاز هستند
            elif location_code in plan.available_locations:
                compatible_plans.append(plan)
        
        return compatible_plans 