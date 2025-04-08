from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, 
                        DECIMAL, BigInteger, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class PlanCategory(Base):
    __tablename__ = "plan_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sorting_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with plans
    plans = relationship("Plan", back_populates="category")
    
    def __repr__(self):
        return f"<PlanCategory(id={self.id}, name={self.name})>"

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    traffic = Column(BigInteger, nullable=False)  # in GB
    days = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # JSON array of additional features
    
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    max_clients = Column(Integer, nullable=True)
    protocols = Column(String(255), nullable=True)  # comma-separated protocols (vmess, vless)
    
    category_id = Column(Integer, ForeignKey("plan_categories.id"), nullable=True)
    sorting_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    category = relationship("PlanCategory", back_populates="plans")
    clients = relationship("Client", back_populates="plan")
    orders = relationship("Order", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name}, price={self.price})>" 