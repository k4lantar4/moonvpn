from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, 
                        BigInteger, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    client_uuid = Column(String(36), nullable=False)
    email = Column(String(255), nullable=False)
    remark = Column(String(255), nullable=False)  # Display name identifier
    expire_date = Column(DateTime, nullable=False)
    traffic = Column(BigInteger, nullable=False)  # in GB
    used_traffic = Column(BigInteger, default=0)  # in GB
    status = Column(String(20), nullable=False)  # active, expired, disabled, frozen
    protocol = Column(String(20), nullable=False)  # vmess, vless
    config_json = Column(Text, nullable=True)  # JSON configuration
    subscription_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    freeze_start = Column(DateTime, nullable=True)
    freeze_end = Column(DateTime, nullable=True)
    is_trial = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=False)
    last_notified = Column(DateTime, nullable=True)
    
    # New fields for client migration and remark management
    original_client_uuid = Column(String(36), nullable=True)
    original_remark = Column(String(255), nullable=True)
    custom_name = Column(String(100), nullable=True)
    migration_count = Column(Integer, default=0)
    previous_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=True)
    migration_history = Column(Text, nullable=True)  # JSON array of migration history
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="clients")
    panel = relationship("Panel", foreign_keys=[panel_id], back_populates="clients")
    previous_panel = relationship("Panel", foreign_keys=[previous_panel_id])
    location = relationship("Location", back_populates="clients")
    plan = relationship("Plan", back_populates="clients")
    order = relationship("Order", back_populates="clients")
    migrations = relationship("ClientMigration", back_populates="client")
    
    def __repr__(self):
        return f"<Client(id={self.id}, user_id={self.user_id}, remark={self.remark}, status={self.status})>"

class ClientMigration(Base):
    __tablename__ = "client_migrations"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    from_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    to_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    old_uuid = Column(String(36), nullable=False)
    new_uuid = Column(String(36), nullable=False)
    old_remark = Column(String(255), nullable=False)
    new_remark = Column(String(255), nullable=False)
    traffic_carried_over = Column(BigInteger, nullable=False)  # Traffic amount carried over
    time_carried_over = Column(Integer, nullable=False)  # Days carried over
    reason = Column(Text, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="migrations")
    from_panel = relationship("Panel", foreign_keys=[from_panel_id])
    to_panel = relationship("Panel", foreign_keys=[to_panel_id])
    performed_by_user = relationship("User")
    
    def __repr__(self):
        return f"<ClientMigration(id={self.id}, client_id={self.client_id}, from_panel={self.from_panel_id}, to_panel={self.to_panel_id})>" 