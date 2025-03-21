"""
Payment endpoints for handling payment-related operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import User
from core.schemas.payment import (
    Payment, PaymentCreate, PaymentUpdate,
    Subscription, SubscriptionCreate, SubscriptionUpdate,
    Plan, PlanCreate, PlanUpdate,
    PaymentList, SubscriptionList, PlanList,
    PaymentStats
)
from core.services.payment import PaymentService
from core.services.auth import get_current_user

router = APIRouter()

# Payment endpoints
@router.get("/payments", response_model=PaymentList)
async def get_user_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's payments."""
    payment_service = PaymentService(db)
    payments = payment_service.get_user_payments(
        current_user.id, skip, limit, status
    )
    total = payment_service.get_user_payments_count(
        current_user.id, status
    )
    
    return PaymentList(
        total=total,
        payments=payments,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/payments", response_model=Payment)
async def create_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new payment."""
    payment_service = PaymentService(db)
    return payment_service.create_payment(data)

@router.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment by ID."""
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if user has access to this payment
    if not current_user.is_superuser and payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return payment

@router.put("/payments/{payment_id}", response_model=Payment)
async def update_payment(
    payment_id: int,
    data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update payment information (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    payment_service = PaymentService(db)
    return payment_service.update_payment(payment_id, data)

# Subscription endpoints
@router.get("/subscriptions", response_model=SubscriptionList)
async def get_user_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's subscriptions."""
    payment_service = PaymentService(db)
    subscriptions = payment_service.get_user_subscriptions(
        current_user.id, skip, limit, status
    )
    total = payment_service.get_user_subscriptions_count(
        current_user.id, status
    )
    
    return SubscriptionList(
        total=total,
        subscriptions=subscriptions,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/subscriptions", response_model=Subscription)
async def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new subscription."""
    payment_service = PaymentService(db)
    return payment_service.create_subscription(data)

@router.get("/subscriptions/{subscription_id}", response_model=Subscription)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription by ID."""
    payment_service = PaymentService(db)
    subscription = payment_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check if user has access to this subscription
    if not current_user.is_superuser and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return subscription

@router.put("/subscriptions/{subscription_id}", response_model=Subscription)
async def update_subscription(
    subscription_id: int,
    data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update subscription information."""
    payment_service = PaymentService(db)
    subscription = payment_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check if user has access to this subscription
    if not current_user.is_superuser and subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return payment_service.update_subscription(subscription_id, data)

# Plan endpoints
@router.get("/plans", response_model=PlanList)
async def get_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of plans."""
    payment_service = PaymentService(db)
    plans = payment_service.get_plans(skip, limit, is_active)
    total = payment_service.get_plans_count(is_active)
    
    return PlanList(
        total=total,
        plans=plans,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/plans", response_model=Plan)
async def create_plan(
    data: PlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new plan (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    payment_service = PaymentService(db)
    return payment_service.create_plan(data)

@router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get plan by ID."""
    payment_service = PaymentService(db)
    plan = payment_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return plan

@router.put("/plans/{plan_id}", response_model=Plan)
async def update_plan(
    plan_id: int,
    data: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update plan information (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    payment_service = PaymentService(db)
    return payment_service.update_plan(plan_id, data)

# Statistics endpoints
@router.get("/stats", response_model=PaymentStats)
async def get_payment_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment statistics (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    payment_service = PaymentService(db)
    return payment_service.get_payment_stats() 