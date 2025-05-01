"""
مدل Panel برای مدیریت پنل‌های VPN
"""

from typing import List, Optional
from enum import Enum as PythonEnum # Alias standard Enum to avoid conflict

from sqlalchemy import Integer, String, Text, Column, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, column_property
from sqlalchemy.ext.hybrid import hybrid_property

# Import PanelStatus from the central enums file
from .enums import PanelStatus, PanelType 
from . import Base


# Remove the duplicate PanelStatus definition here
# class PanelStatus(str, Enum):
#    \"\"\"وضعیت‌های ممکن برای پنل\"\"\"
#    ACTIVE = "active"
#    DISABLED = "disabled"
#    DELETED = "deleted"

# Remove the duplicate PanelType definition here (assuming it's also in enums.py)
# class PanelType(str, Enum):
#    \"\"\"نوع پنل\"\"\"
#    XUI = "xui"


class Panel(Base):
    """مدل پنل‌های 3x-ui در سیستم MoonVPN"""
    
    __tablename__ = "panels"
    
    # فیلدهای اصلی
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False) # Added name field based on previous service usage
    location_name = Column(String(100), nullable=False)
    flag_emoji = Column(String(10), nullable=True) # Changed to match the documentation
    url = Column(Text, nullable=False) # Use Text type as per documentation
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False) # Store securely later
    type = Column(SQLEnum(PanelType), 
                  default=PanelType.XUI, nullable=False)
    _status = Column('status', SQLEnum(PanelStatus), 
                    default=PanelStatus.ACTIVE, 
                    nullable=False)
    notes = Column(Text, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    inbounds: Mapped[List["Inbound"]] = relationship("Inbound", back_populates="panel", cascade="all, delete-orphan")
    client_accounts: Mapped[List["ClientAccount"]] = relationship("ClientAccount", back_populates="panel")
    
    @hybrid_property
    def status(self) -> PanelStatus:
        """Get the panel status with proper enum conversion."""
        if isinstance(self._status, str):
            try:
                return PanelStatus[self._status.upper()]
            except KeyError:
                # Default to ACTIVE if invalid status
                return PanelStatus.ACTIVE
        return self._status
    
    @status.setter
    def status(self, value):
        """Set the panel status with proper enum conversion."""
        if isinstance(value, str):
            try:
                self._status = PanelStatus[value.upper()]
            except KeyError:
                # Default to ACTIVE if invalid status
                self._status = PanelStatus.ACTIVE
        else:
            self._status = value
    
    def __repr__(self) -> str:
        return f"<Panel(id={self.id}, name={self.name}, location={self.location_name})>"
