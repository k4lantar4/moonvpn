from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from decimal import Decimal

from app import crud, models, schemas
from app.api import deps
from app.services.wallet_service import wallet_service, WalletException, InsufficientFundsException, InvalidAmountException

router = APIRouter()


@router.get("/balance", response_model=dict)
def get_balance(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's wallet balance.
    """
    try:
        balance = wallet_service.get_balance(db, user_id=current_user.id)
        return {"balance": balance}
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deposit", response_model=schemas.Transaction)
def deposit(
    *,
    db: Session = Depends(deps.get_db),
    deposit_in: schemas.DepositRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a deposit request.
    Regular users' deposits require admin approval.
    Admin deposits can be auto-approved.
    """
    try:
        # Check if user is admin
        is_admin = deps.check_user_permission(current_user, "admin:wallet:manage")
        auto_approve = is_admin
        
        # Create deposit
        transaction = wallet_service.deposit(
            db,
            user_id=current_user.id,
            amount=deposit_in.amount,
            payment_method=deposit_in.payment_method,
            payment_reference=deposit_in.payment_reference,
            description=deposit_in.description,
            admin_id=current_user.id if is_admin else None,
            auto_approve=auto_approve,
        )
        return transaction
    except InvalidAmountException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/withdraw", response_model=schemas.Transaction)
def withdraw(
    *,
    db: Session = Depends(deps.get_db),
    withdraw_in: schemas.WithdrawRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a withdrawal request from wallet.
    """
    try:
        transaction = wallet_service.withdraw(
            db,
            user_id=current_user.id,
            amount=withdraw_in.amount,
            description=withdraw_in.description,
        )
        return transaction
    except InsufficientFundsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidAmountException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pay-order/{order_id}", response_model=schemas.Order)
def pay_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to pay for"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Pay for an order using wallet balance.
    """
    try:
        transaction, order = wallet_service.pay_for_order(
            db,
            user_id=current_user.id,
            order_id=order_id,
        )
        return order
    except InsufficientFundsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=dict)
def get_transactions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get user's transaction history.
    """
    try:
        result = wallet_service.get_transaction_history(
            db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        return result
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Admin endpoints ---

@router.get("/admin/pending-deposits", response_model=List[schemas.Transaction])
def get_pending_deposits(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all pending deposits that need admin approval.
    Admin only.
    """
    # Check admin permissions
    if not deps.check_user_permission(current_user, "admin:wallet:manage"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access pending deposits"
        )
    
    try:
        deposits = crud.transaction.get_pending_deposits(db, skip=skip, limit=limit)
        return deposits
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/approve-deposit/{transaction_id}", response_model=schemas.Transaction)
def approve_deposit(
    *,
    db: Session = Depends(deps.get_db),
    transaction_id: int = Path(..., title="The ID of the deposit transaction to approve"),
    admin_note: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Approve a pending deposit.
    Admin only.
    """
    # Check admin permissions
    if not deps.check_user_permission(current_user, "admin:wallet:manage"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to approve deposits"
        )
    
    try:
        transaction = wallet_service.approve_deposit(
            db,
            transaction_id=transaction_id,
            admin_id=current_user.id,
            admin_note=admin_note,
        )
        return transaction
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/reject-deposit/{transaction_id}", response_model=schemas.Transaction)
def reject_deposit(
    *,
    db: Session = Depends(deps.get_db),
    transaction_id: int = Path(..., title="The ID of the deposit transaction to reject"),
    admin_note: str = Body(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Reject a pending deposit.
    Admin only.
    """
    # Check admin permissions
    if not deps.check_user_permission(current_user, "admin:wallet:manage"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to reject deposits"
        )
    
    try:
        transaction = wallet_service.reject_deposit(
            db,
            transaction_id=transaction_id,
            admin_id=current_user.id,
            admin_note=admin_note,
        )
        return transaction
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/adjustment", response_model=schemas.Transaction)
def admin_adjustment(
    *,
    db: Session = Depends(deps.get_db),
    adjustment: schemas.AdminAdjustment,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Make an admin adjustment to a user's wallet.
    Admin only.
    """
    # Check admin permissions
    if not deps.check_user_permission(current_user, "admin:wallet:manage"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to make wallet adjustments"
        )
    
    try:
        transaction = wallet_service.admin_adjustment(
            db,
            user_id=adjustment.user_id,
            amount=adjustment.amount,
            description=adjustment.description,
            admin_id=current_user.id,
            admin_note=adjustment.admin_note,
        )
        return transaction
    except InsufficientFundsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidAmountException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/user/{user_id}/transactions", response_model=dict)
def get_user_transactions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int = Path(..., title="The ID of the user to get transactions for"),
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a user's transaction history.
    Admin only.
    """
    # Check admin permissions
    if not deps.check_user_permission(current_user, "admin:wallet:manage"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view user transactions"
        )
    
    try:
        result = wallet_service.get_transaction_history(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
        return result
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/refund-order/{order_id}", response_model=schemas.Transaction)
def refund_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to refund"),
    amount: float = Body(None),
    admin_note: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Refund an order to the user's wallet.
    Admin only.
    """
    # Check admin permissions
    if not deps.check_user_permission(current_user, "admin:wallet:manage"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to refund orders"
        )
    
    try:
        amount_decimal = Decimal(str(amount)) if amount is not None else None
        transaction, order = wallet_service.refund_order(
            db,
            order_id=order_id,
            amount=amount_decimal,
            admin_id=current_user.id,
            admin_note=admin_note,
        )
        return transaction
    except InvalidAmountException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except WalletException as e:
        raise HTTPException(status_code=400, detail=str(e)) 