"""
ماژول Plan - مدل مدیریت پلن‌های سرویس MoonVPN
"""

from sqlalchemy import Boolean, Column, Integer, String, DECIMAL, JSON
from sqlalchemy.orm import relationship

from db.models import Base

class Plan(Base):
    """مدل پلن‌های سرویس VPN"""
    
    __tablename__ = "plans"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True, comment="شناسه پلن")
    name = Column(String(100), nullable=False, index=True, comment="نام پلن")
    traffic = Column(Integer, nullable=False, comment="حجم ترافیک به گیگابایت")
    duration_days = Column(Integer, nullable=False, comment="مدت اعتبار به روز")
    price = Column(DECIMAL(10, 2), nullable=False, comment="قیمت")
    available_locations = Column(JSON, nullable=True, comment="لیست لوکیشن‌های مجاز")
    is_trial = Column(Boolean, default=False, nullable=False, comment="آیا پلن تستی است؟")
    is_active = Column(Boolean, default=True, nullable=False, comment="آیا پلن فعال است؟")
    
    # تعریف روابط با سایر مدل‌ها
    orders = relationship("Order", back_populates="plan")
    test_account_logs = relationship("TestAccountLog", back_populates="plan")
    
    def __repr__(self) -> str:
        """نمایش متنی مدل"""
        return f"<Plan(id={self.id}, name='{self.name}', traffic={self.traffic}GB, days={self.duration_days})>"
