"""
مدل Panel برای مدیریت پنل‌های VPN
"""

from typing import List, Optional
from enum import Enum as PythonEnum # Alias standard Enum to avoid conflict

from sqlalchemy import Integer, String, Text, Column, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

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
    flag_emoji = Column(String(10), nullable=False) # Changed nullable to False
    url = Column(String(1024), unique=True, nullable=False) # Change url type to String(1024) to allow unique constraint in MySQL
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False) # Store securely later
    type = Column(SQLEnum(PanelType, name="paneltype", native_enum=False), 
                  default=PanelType.XUI, nullable=False)
    status = Column(SQLEnum(PanelStatus, name="panelstatus", native_enum=False), # Use imported enum, specify name, native_enum=False
                    default=PanelStatus.ACTIVE, 
                    nullable=False)
    notes = Column(Text, nullable=True)
    
    # ارتباط با سایر مدل‌ها
    inbounds: Mapped[List["Inbound"]] = relationship("Inbound", back_populates="panel", cascade="all, delete-orphan")
    client_accounts: Mapped[List["ClientAccount"]] = relationship("ClientAccount", back_populates="panel")
    
    def __repr__(self) -> str:
        return f"<Panel(id={self.id}, name={self.name}, location={self.location_name})>"
