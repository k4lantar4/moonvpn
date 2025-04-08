from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Text)
from sqlalchemy.sql import func

from api.models.base import Base

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    group = Column(String(50), nullable=True)  # For grouping related settings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Settings(id={self.id}, key={self.key})>"

class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # admin, payment, report, log, alert, backup
    channel_id = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    notification_types = Column(Text, nullable=True)  # JSON array of notification types
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationChannel(id={self.id}, name={self.name}, channel_id={self.channel_id})>"

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)  # info, warning, error, critical
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON details
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, module={self.module})>"

class Backup(Base):
    __tablename__ = "backups"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)  # Size in bytes
    type = Column(String(20), nullable=False)  # database, config, full
    status = Column(String(20), nullable=False)  # completed, failed
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Backup(id={self.id}, filename={self.filename}, type={self.type})>" 