from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_superuser, get_current_active_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionResponse, 
    SubscriptionCreate, 
    SubscriptionFreeze, 
    SubscriptionUnfreeze,
    SubscriptionAddNote,
    SubscriptionToggleAutoRenew
)
from app.services.subscription_service import (
    SubscriptionService, 
    SubscriptionException, 
    SubscriptionNotFoundError
)

router = APIRouter()

@router.get("/", response_model=List[SubscriptionResponse])
def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status: Optional[str] = Query(None, description="Filter by subscription status"),
    is_frozen: Optional[bool] = Query(None, description="Filter by frozen status"),
    skip: int = 0,
    limit: int = 100
) -> List[SubscriptionResponse]:
    """
    Get current user's subscriptions.
    """
    # Admin or staff members can get all subscriptions
    if current_user.role.name in ["admin", "staff"]:
        subscriptions = db.query(current_user.subscriptions)
        
        # Apply filters if provided
        if status:
            subscriptions = subscriptions.filter(current_user.subscriptions.status == status)
        if is_frozen is not None:
            subscriptions = subscriptions.filter(current_user.subscriptions.is_frozen == is_frozen)
            
        subscriptions = subscriptions.offset(skip).limit(limit).all()
    else:
        # Regular users can only see their own subscriptions
        subscriptions = SubscriptionService.get_user_subscriptions(db, current_user.id)
        
        # Apply filters
        if status:
            subscriptions = [s for s in subscriptions if s.status == status]
        if is_frozen is not None:
            subscriptions = [s for s in subscriptions if s.is_frozen == is_frozen]
            
        # Apply pagination
        subscriptions = subscriptions[skip:skip+limit]
    
    return subscriptions

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SubscriptionResponse:
    """
    Get a specific subscription.
    """
    try:
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Regular users can only access their own subscriptions
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this subscription"
            )
            
        return subscription
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )

@router.post("/", response_model=SubscriptionResponse)
def create_subscription(
    subscription_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> SubscriptionResponse:
    """
    Create a new subscription (admin only).
    """
    try:
        # Only admins can create subscriptions for other users
        # For regular users, subscriptions would typically be created
        # as part of an order/payment flow
        subscription = SubscriptionService.create_subscription(
            db=db,
            user_id=subscription_in.user_id,
            plan_id=subscription_in.plan_id,
            start_date=subscription_in.start_date,
            end_date=subscription_in.end_date,
            auto_renew=subscription_in.auto_renew
        )
        return subscription
    except SubscriptionException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{subscription_id}/freeze", response_model=SubscriptionResponse)
def freeze_subscription(
    subscription_id: int,
    freeze_data: SubscriptionFreeze,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SubscriptionResponse:
    """
    Freeze a subscription.
    """
    try:
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Regular users can only freeze their own subscriptions
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to freeze this subscription"
            )
        
        return SubscriptionService.freeze_subscription(
            db=db,
            subscription_id=subscription_id,
            freeze_end_date=freeze_data.freeze_end_date,
            freeze_reason=freeze_data.freeze_reason,
            sync_with_panel=True
        )
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    except SubscriptionException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{subscription_id}/unfreeze", response_model=SubscriptionResponse)
def unfreeze_subscription(
    subscription_id: int,
    unfreeze_data: SubscriptionUnfreeze,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SubscriptionResponse:
    """
    Unfreeze a subscription.
    """
    try:
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Regular users can only unfreeze their own subscriptions
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to unfreeze this subscription"
            )
        
        return SubscriptionService.unfreeze_subscription(
            db=db,
            subscription_id=subscription_id,
            sync_with_panel=True
        )
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    except SubscriptionException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{subscription_id}/notes", response_model=SubscriptionResponse)
def add_note(
    subscription_id: int,
    note_data: SubscriptionAddNote,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SubscriptionResponse:
    """
    Add a note to a subscription.
    """
    try:
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Only admins/staff can add notes to any subscription
        # Regular users can only add notes to their own subscriptions
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to add notes to this subscription"
            )
        
        return SubscriptionService.add_note(
            db=db,
            subscription_id=subscription_id,
            note=note_data.note
        )
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )

@router.post("/{subscription_id}/auto-renew", response_model=SubscriptionResponse)
def toggle_auto_renew(
    subscription_id: int,
    auto_renew_data: SubscriptionToggleAutoRenew,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SubscriptionResponse:
    """
    Toggle auto-renew settings for a subscription.
    """
    try:
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Regular users can only change auto-renew for their own subscriptions
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to modify this subscription"
            )
        
        return SubscriptionService.toggle_auto_renew(
            db=db,
            subscription_id=subscription_id,
            enabled=auto_renew_data.enabled,
            payment_method=auto_renew_data.payment_method
        )
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        ) 