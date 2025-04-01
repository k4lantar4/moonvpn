from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.bank_card_service import bank_card_service


router = APIRouter()


@router.get("/", response_model=schemas.BankCardList)
def read_bank_cards(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve bank cards.
    
    Regular users can only see their own bank cards.
    Users with admin permissions can see all bank cards and filter by user_id.
    """
    # Check if user is requesting their own bank cards or has admin permission
    is_admin = deps.check_user_permission(current_user, "admin:bank_card:read")
    
    if user_id is not None and user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access other users' bank cards"
        )
    
    # Set user_id filter based on permissions
    if not is_admin:
        user_id = current_user.id
    
    # Get bank cards based on filter
    if user_id is not None:
        bank_cards = crud.bank_card.get_multi_by_owner(
            db=db, user_id=user_id, skip=skip, limit=limit
        )
        total = crud.bank_card.count(db=db, user_id=user_id)
    else:
        bank_cards = crud.bank_card.get_multi(db=db, skip=skip, limit=limit)
        total = crud.bank_card.count(db=db)
    
    return {
        "items": bank_cards,
        "total": total
    }


@router.post("/", response_model=schemas.BankCard)
def create_bank_card(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_in: schemas.BankCardCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new bank card.
    
    Regular users can only create bank cards for themselves.
    Users with admin permissions can create bank cards for any user.
    """
    # Check if user is creating bank card for themselves or has admin permission
    is_admin = deps.check_user_permission(current_user, "admin:bank_card:create")
    
    if bank_card_in.user_id is not None and bank_card_in.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to create bank cards for other users"
        )
    
    # Set user_id if not provided
    if bank_card_in.user_id is None:
        bank_card_in.user_id = current_user.id
    
    # Create bank card
    bank_card = crud.bank_card.create_with_owner(
        db=db, obj_in=bank_card_in, created_by=current_user.id
    )
    
    return bank_card


@router.get("/for-payment", response_model=List[schemas.BankCard])
def read_bank_cards_for_payment(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 5,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve active bank cards for payment purposes, ordered by priority.
    
    This endpoint is accessible to all authenticated users to get cards
    that can be used for making payments.
    """
    return bank_card_service.get_bank_cards_for_payment(db=db, skip=skip, limit=limit)


@router.get("/active", response_model=List[schemas.BankCard])
def read_active_bank_cards(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve active bank cards ordered by priority.
    
    This endpoint is useful for getting cards that should be displayed to users
    for making payments.
    """
    # Check if user has admin permission
    if not deps.check_user_permission(current_user, "admin:bank_card:read"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access active bank cards"
        )
    
    bank_cards = crud.bank_card.get_active_cards(db=db, skip=skip, limit=limit)
    return bank_cards


@router.get("/{bank_card_id}", response_model=schemas.BankCard)
def read_bank_card(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_id: int = Path(..., title="The ID of the bank card to get"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get bank card by ID.
    
    Regular users can only see their own bank cards.
    Users with admin permissions can see any bank card.
    """
    bank_card = crud.bank_card.get(db=db, id=bank_card_id)
    
    if bank_card is None:
        raise HTTPException(
            status_code=404,
            detail="Bank card not found"
        )
    
    # Check if user is requesting their own bank card or has admin permission
    is_admin = deps.check_user_permission(current_user, "admin:bank_card:read")
    
    if bank_card.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this bank card"
        )
    
    return bank_card


@router.get("/{bank_card_id}/details", response_model=schemas.BankCardDetail)
def read_bank_card_details(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_id: int = Path(..., title="The ID of the bank card to get details for"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed bank card information.
    
    Regular users can only see their own bank card details.
    Users with admin permissions can see any bank card's details.
    """
    # First check if user has permission to access this bank card
    bank_card = crud.bank_card.get(db=db, id=bank_card_id)
    
    if bank_card is None:
        raise HTTPException(
            status_code=404,
            detail="Bank card not found"
        )
    
    is_admin = deps.check_user_permission(current_user, "admin:bank_card:read")
    
    if bank_card.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this bank card's details"
        )
    
    # Get detailed information
    return bank_card_service.get_bank_card_details(db=db, bank_card_id=bank_card_id)


@router.put("/{bank_card_id}", response_model=schemas.BankCard)
def update_bank_card(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_id: int = Path(..., title="The ID of the bank card to update"),
    bank_card_in: schemas.BankCardUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update bank card.
    
    Regular users can only update their own bank cards and cannot change the owner.
    Users with admin permissions can update any bank card and change the owner.
    """
    bank_card = crud.bank_card.get(db=db, id=bank_card_id)
    
    if bank_card is None:
        raise HTTPException(
            status_code=404,
            detail="Bank card not found"
        )
    
    # Check if user is updating their own bank card or has admin permission
    is_admin = deps.check_user_permission(current_user, "admin:bank_card:update")
    
    if bank_card.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update this bank card"
        )
    
    # Prevent user_id changes for non-admin users
    if bank_card_in.user_id is not None and bank_card_in.user_id != bank_card.user_id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to change bank card owner"
        )
    
    bank_card = crud.bank_card.update(db=db, db_obj=bank_card, obj_in=bank_card_in)
    return bank_card


@router.put("/{bank_card_id}/toggle-status", response_model=schemas.BankCard)
def toggle_bank_card_status(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_id: int = Path(..., title="The ID of the bank card to toggle status"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Toggle the active status of a bank card.
    
    Regular users can only toggle their own bank cards.
    Users with admin permissions can toggle any bank card.
    """
    return bank_card_service.toggle_card_status(
        db=db, bank_card_id=bank_card_id, current_user_id=current_user.id
    )


@router.put("/{bank_card_id}/priority", response_model=schemas.BankCard)
def update_bank_card_priority(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_id: int = Path(..., title="The ID of the bank card to update priority"),
    priority: int = Body(..., embed=True, ge=0),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update the priority of a bank card.
    
    Only users with admin permissions can update bank card priorities.
    Higher priority values will be shown first in the payment card selection.
    """
    return bank_card_service.update_card_priority(
        db=db, bank_card_id=bank_card_id, priority=priority, current_user_id=current_user.id
    )


@router.delete("/{bank_card_id}", response_model=schemas.BankCard)
def delete_bank_card(
    *,
    db: Session = Depends(deps.get_db),
    bank_card_id: int = Path(..., title="The ID of the bank card to delete"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete bank card.
    
    Regular users can only delete their own bank cards.
    Users with admin permissions can delete any bank card.
    """
    bank_card = crud.bank_card.get(db=db, id=bank_card_id)
    
    if bank_card is None:
        raise HTTPException(
            status_code=404,
            detail="Bank card not found"
        )
    
    # Check if user is deleting their own bank card or has admin permission
    is_admin = deps.check_user_permission(current_user, "admin:bank_card:delete")
    
    if bank_card.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to delete this bank card"
        )
    
    bank_card = crud.bank_card.remove(db=db, id=bank_card_id)
    return bank_card 