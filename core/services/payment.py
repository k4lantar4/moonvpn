"""
Payment service for handling payment-related operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func

from core.database.models import Payment, Subscription, Plan, User
from core.schemas.payment import (
    PaymentCreate, PaymentUpdate, SubscriptionCreate,
    SubscriptionUpdate, PlanCreate, PlanUpdate,
    PaymentStats
)

class PaymentService:
    """Service for handling payment operations."""
    
    def __init__(self, db: Session):
        """Initialize the payment service."""
        self.db = db
    
    def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_user_payments(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Payment]:
        """Get list of user's payments with filtering."""
        query = self.db.query(Payment).filter(Payment.user_id == user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_user_payments_count(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> int:
        """Get total count of user's payments with filtering."""
        query = self.db.query(Payment).filter(Payment.user_id == user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.count()
    
    def create_payment(self, data: PaymentCreate) -> Payment:
        """Create a new payment."""
        # Check if user exists
        user = self.db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create new payment
        payment = Payment(**data.model_dump())
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def update_payment(self, payment_id: int, data: PaymentUpdate) -> Payment:
        """Update payment information."""
        payment = self.get_payment(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(payment, field, value)
        
        payment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID."""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    def get_user_subscriptions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Subscription]:
        """Get list of user's subscriptions with filtering."""
        query = self.db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if status:
            query = query.filter(Subscription.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_user_subscriptions_count(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> int:
        """Get total count of user's subscriptions with filtering."""
        query = self.db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if status:
            query = query.filter(Subscription.status == status)
        
        return query.count()
    
    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        """Create a new subscription."""
        # Check if user exists
        user = self.db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if plan exists
        plan = self.db.query(Plan).filter(Plan.id == data.plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Create new subscription
        subscription = Subscription(**data.model_dump())
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def update_subscription(self, subscription_id: int, data: SubscriptionUpdate) -> Subscription:
        """Update subscription information."""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(subscription, field, value)
        
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def get_plan(self, plan_id: int) -> Optional[Plan]:
        """Get plan by ID."""
        return self.db.query(Plan).filter(Plan.id == plan_id).first()
    
    def get_plans(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Plan]:
        """Get list of plans with filtering."""
        query = self.db.query(Plan)
        
        if is_active is not None:
            query = query.filter(Plan.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_plans_count(self, is_active: Optional[bool] = None) -> int:
        """Get total count of plans with filtering."""
        query = self.db.query(Plan)
        
        if is_active is not None:
            query = query.filter(Plan.is_active == is_active)
        
        return query.count()
    
    def create_plan(self, data: PlanCreate) -> Plan:
        """Create a new plan."""
        plan = Plan(**data.model_dump())
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def update_plan(self, plan_id: int, data: PlanUpdate) -> Plan:
        """Update plan information."""
        plan = self.get_plan(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        
        plan.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(plan)
        return plan
    
    def get_payment_stats(self) -> PaymentStats:
        """Get payment statistics."""
        now = datetime.utcnow()
        last_24h = now - timedelta(days=1)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Get total amount and transactions
        total_amount = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed"
        ).scalar() or Decimal("0")
        
        total_transactions = self.db.query(Payment).count()
        successful_transactions = self.db.query(Payment).filter(
            Payment.status == "completed"
        ).count()
        failed_transactions = self.db.query(Payment).filter(
            Payment.status == "failed"
        ).count()
        pending_transactions = self.db.query(Payment).filter(
            Payment.status == "pending"
        ).count()
        refunded_transactions = self.db.query(Payment).filter(
            Payment.status == "refunded"
        ).count()
        
        # Get last 24h stats
        last_24h_amount = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed",
            Payment.created_at >= last_24h
        ).scalar() or Decimal("0")
        
        last_24h_transactions = self.db.query(Payment).filter(
            Payment.created_at >= last_24h
        ).count()
        
        # Get last 7d stats
        last_7d_amount = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed",
            Payment.created_at >= last_7d
        ).scalar() or Decimal("0")
        
        last_7d_transactions = self.db.query(Payment).filter(
            Payment.created_at >= last_7d
        ).count()
        
        # Get last 30d stats
        last_30d_amount = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed",
            Payment.created_at >= last_30d
        ).scalar() or Decimal("0")
        
        last_30d_transactions = self.db.query(Payment).filter(
            Payment.created_at >= last_30d
        ).count()
        
        return PaymentStats(
            total_amount=total_amount,
            total_transactions=total_transactions,
            successful_transactions=successful_transactions,
            failed_transactions=failed_transactions,
            pending_transactions=pending_transactions,
            refunded_transactions=refunded_transactions,
            last_24h_amount=last_24h_amount,
            last_7d_amount=last_7d_amount,
            last_30d_amount=last_30d_amount,
            last_24h_transactions=last_24h_transactions,
            last_7d_transactions=last_7d_transactions,
            last_30d_transactions=last_30d_transactions
        ) 