from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_superuser, get_current_active_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionResponse, 
    SubscriptionCreate, 
    SubscriptionFreeze, 
    SubscriptionUnfreeze,
    SubscriptionAddNote,
    SubscriptionToggleAutoRenew,
    SubscriptionChangeProtocolLocation
)
from app.schemas.panel import (
    PanelClientConfigResponse,
    PanelClientQRCodeResponse,
    PanelTrafficResponse
)
from app.services.subscription_service import (
    SubscriptionService, 
    SubscriptionException, 
    SubscriptionNotFoundError
)
from app.services.panel_service import (
    PanelService,
    PanelException,
    PanelClientNotFoundError,
    PanelConnectionError
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
    Toggle auto-renewal for a subscription.
    """
    try:
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Regular users can only modify their own subscriptions
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to modify this subscription"
            )
        
        return SubscriptionService.toggle_auto_renew(
            db=db,
            subscription_id=subscription_id,
            auto_renew=auto_renew_data.auto_renew,
            auto_renew_payment_method=auto_renew_data.auto_renew_payment_method
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

@router.get("/{subscription_id}/config", response_model=PanelClientConfigResponse)
def get_subscription_config(
    subscription_id: int,
    protocol: Optional[str] = Query(None, description="Protocol type to filter by (vmess, vless, trojan)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get connection configuration for a subscription.
    
    This endpoint returns the connection details needed to configure a VPN client,
    including the server address, port, protocol, and a connection link.
    """
    try:
        # Get the subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if user is allowed to access this subscription's config
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this subscription's configuration"
            )
        
        # Check if subscription is active
        if subscription.is_frozen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot get configuration for a frozen subscription"
            )
        
        # Get the client config using the panel service
        with PanelService() as panel_service:
            # Use the subscription's client email to fetch the configuration
            config = panel_service.get_client_config(
                email=subscription.client_email,
                protocol=protocol
            )
            
            # Add subscription-related information to the config
            config.update({
                "subscription_id": subscription.id,
                "plan_name": subscription.plan.name if subscription.plan else None,
                "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None
            })
            
            return config
            
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client configuration not found on the panel"
        )
    except PanelConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to VPN panel"
        )
    except (SubscriptionException, PanelException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{subscription_id}/qrcode", response_model=PanelClientQRCodeResponse)
def get_subscription_qrcode(
    subscription_id: int,
    protocol: Optional[str] = Query(None, description="Protocol type to filter by (vmess, vless, trojan)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get QR code for a subscription's connection configuration.
    
    Returns a base64-encoded image that can be displayed to users for
    easy configuration of mobile clients by scanning the QR code.
    """
    try:
        # Get the subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if user is allowed to access this subscription's QR code
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this subscription's QR code"
            )
        
        # Check if subscription is active
        if subscription.is_frozen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot get QR code for a frozen subscription"
            )
        
        # Get the client QR code using the panel service
        with PanelService() as panel_service:
            # First get the config to get protocol info
            config = panel_service.get_client_config(
                email=subscription.client_email,
                protocol=protocol
            )
            
            # Generate QR code
            qrcode_base64 = panel_service.get_client_qrcode(
                email=subscription.client_email,
                protocol=protocol
            )
            
            # Return response that matches PanelClientQRCodeResponse schema
            return {
                "email": subscription.client_email,
                "protocol": config["protocol"],
                "qrcode": qrcode_base64,
                "link": config["link"]
            }
            
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client configuration not found on the panel"
        )
    except PanelConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to VPN panel"
        )
    except (SubscriptionException, PanelException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{subscription_id}/traffic", response_model=PanelTrafficResponse)
def get_subscription_traffic(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get traffic usage statistics for a subscription.
    
    Returns information about data usage, including:
    - Total allocated traffic
    - Used traffic (download + upload)
    - Remaining traffic
    - Usage percentage
    """
    try:
        # Get the subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if user is allowed to access this subscription's traffic stats
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this subscription's traffic statistics"
            )
        
        # Get traffic statistics using the panel service
        with PanelService() as panel_service:
            traffic_stats = panel_service.get_client_traffic(
                email=subscription.client_email
            )
            
            # Return data in the format expected by PanelTrafficResponse
            # Convert bytes to fields needed by the response schema
            return {
                "up": traffic_stats.get("up", 0),
                "down": traffic_stats.get("down", 0),
                "total": traffic_stats.get("up", 0) + traffic_stats.get("down", 0),
                "enable": not subscription.is_frozen,
                "expiry_time": int(subscription.end_date.timestamp()) if subscription.end_date else None,
                "expiry_status": subscription.end_date < datetime.now() if subscription.end_date else False
            }
            
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found on the panel"
        )
    except PanelConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to VPN panel"
        )
    except (SubscriptionException, PanelException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{subscription_id}/protocol-location", response_model=SubscriptionResponse)
def change_subscription_protocol_location(
    subscription_id: int = Path(..., title="The ID of the subscription to modify"),
    change_data: SubscriptionChangeProtocolLocation = Body(..., title="Protocol or location change data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SubscriptionResponse:
    """
    Change the protocol (inbound) or location (panel) for a subscription.
    
    This endpoint allows changing a subscription's connection protocol or server location
    by specifying a new inbound ID, a new panel ID, or both.
    
    - Requires an active subscription
    - Cannot be performed on frozen or expired subscriptions
    - At least one of new_inbound_id or new_panel_id must be provided
    - Admin or staff role required, or the subscription must belong to the current user
    """
    try:
        # Get the subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if user is allowed to modify this subscription
        if current_user.role.name not in ["admin", "staff"] and subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to modify this subscription"
            )
        
        # Validate change_data
        if not change_data.new_inbound_id and not change_data.new_panel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of new_inbound_id or new_panel_id must be provided"
            )
        
        # Change protocol or location
        updated_subscription = SubscriptionService.change_protocol_or_location(
            db=db,
            subscription_id=subscription_id,
            new_inbound_id=change_data.new_inbound_id,
            new_panel_id=change_data.new_panel_id
        )
        
        return updated_subscription
        
    except SubscriptionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found on the panel"
        )
    except PanelConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to VPN panel"
        )
    except (SubscriptionException, PanelException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 