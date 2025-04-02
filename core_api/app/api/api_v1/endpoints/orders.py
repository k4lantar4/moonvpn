from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.affiliate_handler import AffiliateHandler

router = APIRouter()


@router.get("/", response_model=List[schemas.Order])
def read_orders(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Retrieve orders.
    """
    orders = crud.order.get_multi(db, skip=skip, limit=limit, status=status)
    return orders


@router.post("/", response_model=schemas.Order)
def create_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: schemas.OrderCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new order.
    """
    # Create the order
    order = crud.order.create_with_owner(db=db, obj_in=order_in, user_id=current_user.id)
    
    # Process affiliate commission if applicable
    AffiliateHandler.process_order_commission(db, order)
    
    return order


@router.post("/telegram", response_model=schemas.Order)
def create_order_telegram(
    *,
    db: Session = Depends(deps.get_db),
    order_in: schemas.OrderCreateTelegram,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new order from Telegram.
    """
    # Create the order
    order = crud.order.create_with_owner_telegram(db=db, obj_in=order_in, user_id=current_user.id)
    
    # Process affiliate commission if applicable
    AffiliateHandler.process_order_commission(db, order)
    
    return order


@router.put("/{id}", response_model=schemas.Order)
def update_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the order to update"),
    order_in: schemas.OrderUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update an order.
    """
    order = crud.order.get(db=db, id=id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = crud.order.update(db=db, db_obj=order, obj_in=order_in)
    return order


@router.get("/{id}", response_model=schemas.OrderDetail)
def read_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the order to get"),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get order by ID.
    """
    order = crud.order.get(db=db, id=id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not crud.user.is_superuser(current_user) and (order.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return order


@router.delete("/{id}", response_model=schemas.Order)
def delete_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the order to delete"),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Delete an order.
    """
    order = crud.order.get(db=db, id=id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = crud.order.remove(db=db, id=id)
    return order


@router.get("/user/{user_id}", response_model=List[schemas.Order])
def read_user_orders(
    user_id: int = Path(..., title="The ID of the user to get orders for"),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get orders for a specific user.
    """
    if user_id != current_user.id and not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    orders = crud.order.get_multi_by_user(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    return orders 