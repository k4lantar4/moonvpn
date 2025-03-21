"""
Payment endpoints.

This module provides API endpoints for payment management, including transactions
and payment methods.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import get_current_user, get_current_active_superuser
from core.database import get_db
from core.database.models import Transaction, User
from core.schemas.payment import TransactionCreate, TransactionResponse, TransactionUpdate

router = APIRouter()


@router.get("/transactions/me", response_model=List[TransactionResponse])
def read_user_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    """
    Get current user transactions.
    
    Retrieve all transactions belonging to the current user.
    """
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    return [TransactionResponse.from_orm(transaction) for transaction in transactions]


@router.post("/transactions", response_model=TransactionResponse)
def create_transaction(
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Create transaction.
    
    Create a new payment transaction for the current user.
    """
    # Create transaction in database
    db_transaction = Transaction(
        user_id=current_user.id,
        amount=transaction_in.amount,
        currency=transaction_in.currency,
        payment_method=transaction_in.payment_method,
        status="pending",
        description=transaction_in.description or "Payment transaction",
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # In a real scenario, you would now redirect to payment gateway
    # and create a callback URL for payment verification
    
    return TransactionResponse.from_orm(db_transaction)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def read_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Get transaction.
    
    Retrieve a specific transaction by ID.
    """
    # Regular users can only see their own transactions
    if not current_user.is_superuser:
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        ).first()
    else:
        # Superusers can see any transaction
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    return TransactionResponse.from_orm(transaction)


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_in: TransactionUpdate,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> TransactionResponse:
    """
    Update transaction.
    
    Update a specific transaction by ID (admin only).
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    # Update transaction attributes
    for key, value in transaction_in.dict(exclude_unset=True).items():
        if hasattr(transaction, key):
            setattr(transaction, key, value)
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse.from_orm(transaction)


@router.get("/transactions", response_model=List[TransactionResponse])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    _: Any = Depends(get_current_active_superuser),
) -> List[TransactionResponse]:
    """
    List transactions.
    
    Retrieve a list of all transactions (admin only).
    """
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
    return [TransactionResponse.from_orm(transaction) for transaction in transactions]


@router.post("/verify-payment/{transaction_id}", response_model=TransactionResponse)
def verify_payment(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Verify payment.
    
    Endpoint for payment gateway callbacks to verify payment status.
    This would typically be called by the payment gateway and would
    include additional verification steps.
    """
    # Find transaction by ID
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    # In a real implementation, you would verify the payment
    # with the payment gateway here
    
    # For demo purposes, we'll just update the status
    transaction.status = "completed"
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse.from_orm(transaction) 