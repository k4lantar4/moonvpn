"""
مدل AdminPermission برای مدیریت مجوزهای ادمین
"""
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from . import Base

class AdminPermission(Base):
    """مدل مجوزهای ادمین (قابل توسعه برای مجوزهای بیشتر)"""
    __tablename__ = "admin_permissions"
    __table_args__ = (UniqueConstraint("user_id", name="uq_admin_permissions_user_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    can_approve_receipt = Column(Boolean, default=False, nullable=False)
    can_support = Column(Boolean, default=False, nullable=False)
    can_view_users = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # رابطه با مدل User
    user: Mapped["User"] = relationship("User", back_populates="admin_permission")

    def __repr__(self) -> str:
        return f"<AdminPermission(user_id={self.user_id}, approve={self.can_approve_receipt}, support={self.can_support}, view_users={self.can_view_users})>" 