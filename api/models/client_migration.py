from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship
from api.models.base import Base

class ClientMigration(Base):
    __tablename__ = "client_migrations"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    old_location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    new_location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    old_panel_id = Column(Integer, ForeignKey('panels.id'), nullable=False)
    new_panel_id = Column(Integer, ForeignKey('panels.id'), nullable=False)
    old_remark = Column(String(255), nullable=False)
    new_remark = Column(String(255), nullable=False)
    old_uuid = Column(String(36), nullable=True)
    new_uuid = Column(String(36), nullable=True)
    reason = Column(String(255), nullable=True)
    transferred_traffic = Column(BigInteger, default=0)
    transferred_expiry = Column(Boolean, default=True)
    performed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    client = relationship("Client", back_populates="migrations")
    user = relationship("User", foreign_keys=[user_id])
    old_location = relationship("Location", foreign_keys=[old_location_id])
    new_location = relationship("Location", foreign_keys=[new_location_id])
    old_panel = relationship("Panel", foreign_keys=[old_panel_id])
    new_panel = relationship("Panel", foreign_keys=[new_panel_id])
    admin = relationship("User", foreign_keys=[performed_by])
    
    def __repr__(self):
        return f"<ClientMigration {self.id}: {self.old_location.name} -> {self.new_location.name}, Client: {self.client_id}>" 