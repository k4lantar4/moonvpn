from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app import crud, models, schemas
from app.api import deps
from app.models.order import OrderStatus, PaymentMethod
from app.services.order_service import order_service, OrderProcessingError

router = APIRouter()


@router.get("/", response_model=List[schemas.Order])
def read_orders(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
    status_filter: Optional[List[OrderStatus]] = Query(None),
) -> Any:
    """
    Retrieve orders.
    
    For regular users, returns only their own orders.
    For admins, returns all orders (can be filtered by status).
    """
    # Check if user is an admin with sufficient permissions
    is_admin = deps.check_user_permission(current_user, "admin:order:read")
    
    if is_admin:
        # Admin can see all orders, optionally filtered by status
        if status_filter:
            orders = crud.order.get_by_statuses(db, statuses=status_filter, skip=skip, limit=limit)
        else:
            orders = crud.order.get_multi(db, skip=skip, limit=limit)
    else:
        # Regular users can only see their own orders
        orders = crud.order.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    
    return orders


@router.post("/", response_model=schemas.Order)
def create_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: schemas.OrderCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new order.
    
    Users can create orders for themselves.
    Admins can create orders for any user.
    """
    # Check if the user is creating an order for themselves
    is_self_order = order_in.user_id == current_user.id
    # Check if user has admin permissions to create orders for others
    is_admin = deps.check_user_permission(current_user, "admin:order:create")
    
    if not (is_self_order or is_admin):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create orders for other users"
        )
    
    # Verify the plan exists
    plan = crud.plan.get(db, id=order_in.plan_id)
    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )
    
    # If panel_id is provided, verify it exists
    if order_in.panel_id:
        panel = crud.panel.get(db, id=order_in.panel_id)
        if not panel:
            raise HTTPException(
                status_code=404,
                detail="Panel not found"
            )
    
    # Use the OrderService to create the order
    try:
        order = order_service.create_order(
            db=db,
            user_id=order_in.user_id,
            plan_id=order_in.plan_id,
            amount=float(order_in.amount),
            discount_amount=float(order_in.discount_amount),
            discount_code=order_in.discount_code,
            panel_id=order_in.panel_id,
            config_protocol=order_in.config_protocol,
            config_days=order_in.config_days,
            config_traffic_gb=order_in.config_traffic_gb,
            config_details=order_in.config_details,
            admin_note=order_in.admin_note
        )
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=schemas.OrderDetail)
def read_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to get"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get order by ID.
    
    Users can only access their own orders.
    Admins can access any order.
    """
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=404, 
            detail="Order not found"
        )
    
    # Check if user is allowed to access this order
    is_owner = order.user_id == current_user.id
    is_admin = deps.check_user_permission(current_user, "admin:order:read")
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this order"
        )
    
    return order


@router.put("/{order_id}", response_model=schemas.Order)
def update_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to update"),
    order_in: schemas.OrderUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an order.
    
    Full update is admin-only.
    Users can only update certain fields (e.g., payment proof).
    """
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Check permissions
    is_owner = order.user_id == current_user.id
    is_admin = deps.check_user_permission(current_user, "admin:order:update")
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update this order"
        )
    
    # If user is not admin, restrict what fields they can update
    if not is_admin:
        # Create a new OrderUpdate with only the fields regular users can change
        allowed_update = schemas.OrderUpdate(
            payment_proof=order_in.payment_proof,
            payment_reference=order_in.payment_reference
        )
        order_in = allowed_update
    
    # If changing to CONFIRMED status, ensure client details are provided
    if order_in.status == OrderStatus.CONFIRMED:
        if not all([order_in.client_uuid, order_in.client_email]):
            raise HTTPException(
                status_code=400,
                detail="Client UUID and email must be provided when confirming an order"
            )
    
    # If marking as paid, record payment time
    if order_in.status == OrderStatus.PAID and order.status != OrderStatus.PAID:
        order_in.paid_at = datetime.utcnow()
        
    # If confirming, record confirmation time
    if order_in.status == OrderStatus.CONFIRMED and order.status != OrderStatus.CONFIRMED:
        order_in.confirmed_at = datetime.utcnow()
        
        # Set expiry date if not explicitly provided
        if not order_in.expires_at and order.config_days:
            order_in.expires_at = datetime.utcnow() + timedelta(days=order.config_days)
    
    # Update the order
    order = crud.order.update(db, db_obj=order, obj_in=order_in)
    return order


@router.delete("/{order_id}", response_model=schemas.Order)
def cancel_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to cancel"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel an order.
    
    Users can cancel their own pending orders.
    Admins can cancel any order.
    """
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Check permissions
    is_owner = order.user_id == current_user.id
    is_admin = deps.check_user_permission(current_user, "admin:order:delete")
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to cancel this order"
        )
    
    # Regular users can only cancel PENDING orders
    if is_owner and not is_admin and order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be canceled by users"
        )
    
    # Cancel the order
    order = crud.order.cancel_order(
        db, 
        order_id=order_id,
        admin_id=current_user.id if is_admin else None,
        admin_note="Canceled by user" if not is_admin else None
    )
    
    return order


@router.post("/{order_id}/process-payment", response_model=schemas.Order)
def process_payment(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to process"),
    payment_method: PaymentMethod = Body(...),
    payment_reference: str = Body(...),
    admin_note: Optional[str] = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Process payment for an order (admin only).
    
    Marks an order as paid and records payment details.
    """
    # Verify admin permissions
    if not deps.check_user_permission(current_user, "admin:order:update"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to process payments"
        )
    
    try:
        # Process the payment using the service
        order = order_service.process_payment(
            db,
            order_id=order_id,
            payment_method=payment_method.value,
            payment_reference=payment_reference,
            admin_id=current_user.id,
            admin_note=admin_note
        )
        return order
    except OrderProcessingError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{order_id}/confirm", response_model=schemas.Order)
def confirm_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to confirm"),
    panel_id: int = Body(...),
    inbound_id: int = Body(...),
    client_uuid: str = Body(default_factory=lambda: str(uuid.uuid4())),
    client_email: str = Body(...),
    expires_at: Optional[datetime] = Body(None),
    admin_note: Optional[str] = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Confirm an order after account creation (admin only).
    
    Marks an order as confirmed and records the client details.
    """
    # Verify admin permissions
    if not deps.check_user_permission(current_user, "admin:order:update"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to confirm orders"
        )
    
    # Get the order
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Check if the panel exists
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(
            status_code=404,
            detail="Panel not found"
        )
    
    # Check if order can be confirmed
    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail=f"Only paid orders can be confirmed, current status: {order.status.value}"
        )
    
    # Set expiry date if not explicitly provided
    if not expires_at and order.config_days:
        expires_at = datetime.utcnow() + timedelta(days=order.config_days)
    elif not expires_at:
        # If no config_days and no explicit expires_at, default to 30 days
        expires_at = datetime.utcnow() + timedelta(days=30)
    
    # Confirm the order
    order = crud.order.confirm_order(
        db,
        order_id=order_id,
        panel_id=panel_id,
        inbound_id=inbound_id,
        client_uuid=client_uuid,
        client_email=client_email,
        expires_at=expires_at,
        admin_id=current_user.id,
        admin_note=admin_note
    )
    
    return order


@router.post("/{order_id}/reject", response_model=schemas.Order)
def reject_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to reject"),
    admin_note: str = Body(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Reject an order (admin only).
    
    Marks an order as rejected and records the reason.
    """
    # Verify admin permissions
    if not deps.check_user_permission(current_user, "admin:order:update"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to reject orders"
        )
    
    # Get the order
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Reject the order
    order = crud.order.reject_order(
        db,
        order_id=order_id,
        admin_id=current_user.id,
        admin_note=admin_note
    )
    
    return order


@router.post("/{order_id}/create-client", response_model=schemas.Order)
def create_client(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to create client for"),
    panel_id: Optional[int] = Body(None),
    client_uuid: Optional[str] = Body(None),
    admin_note: Optional[str] = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Automatically create a client on the panel for a paid order (admin only).
    
    This is a convenience endpoint that handles both client creation on the panel
    and order confirmation in one step.
    """
    # Verify admin permissions
    if not deps.check_user_permission(current_user, "admin:order:update"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create clients"
        )
    
    try:
        # Create client and confirm the order using the service
        order, client_info = order_service.create_client_on_panel(
            db,
            order_id=order_id,
            admin_id=current_user.id,
            admin_note=admin_note,
            client_uuid=client_uuid,
            panel_id=panel_id
        )
        return order
    except OrderProcessingError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/{order_id}/client-config")
def get_client_config(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to get configuration for"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get client configuration for a confirmed order.
    
    Users can get configuration for their own orders.
    Admins can get configuration for any order.
    """
    # Get the order
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Check if user is allowed to access this order's config
    is_owner = order.user_id == current_user.id
    is_admin = deps.check_user_permission(current_user, "admin:order:read")
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this order's configuration"
        )
    
    # Check if order is confirmed
    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot get configuration for order with status {order.status.value}"
        )
    
    try:
        # Get the configuration using the service
        config = order_service.get_client_config(db, order_id=order_id)
        return config
    except OrderProcessingError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) 