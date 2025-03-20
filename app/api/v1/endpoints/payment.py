"""
Payment endpoints for MoonVPN.

This module handles all payment-related API endpoints including
payment processing, verification, and wallet management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.services.payment_service import PaymentService
from app.core.schemas.payment import (
    PaymentRequest,
    PaymentResponse,
    Transaction,
    Wallet,
    Order,
    PaymentMethod
)
from app.core.exceptions import (
    PaymentError,
    InsufficientBalanceError,
    TransactionNotFoundError,
    PaymentVerificationError,
    PaymentGatewayError,
    InvalidPaymentMethodError,
    PaymentAmountError,
    WalletLimitError
)

router = APIRouter()

@router.post("/process", response_model=PaymentResponse)
async def process_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db)
):
    """Process a payment request."""
    try:
        payment_service = PaymentService(db)
        return await payment_service.process_payment(
            user_id=payment_request.user_id,
            order_id=payment_request.order_id,
            amount=payment_request.amount,
            payment_method=payment_request.payment_method,
            callback_url=payment_request.callback_url
        )
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidPaymentMethodError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PaymentAmountError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PaymentGatewayError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    authority: str,
    status: str,
    ref_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Verify a payment with the payment gateway."""
    try:
        payment_service = PaymentService(db)
        return await payment_service.verify_payment(
            authority=authority,
            status=status,
            ref_id=ref_id
        )
    except TransactionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PaymentVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/transactions/{user_id}", response_model=List[Transaction])
async def get_user_transactions(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all transactions for a user."""
    try:
        payment_service = PaymentService(db)
        return await payment_service.get_user_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/wallet/{user_id}", response_model=Wallet)
async def get_user_wallet(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's wallet."""
    try:
        payment_service = PaymentService(db)
        return await payment_service.get_user_wallet(user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/wallet/deposit", response_model=PaymentResponse)
async def deposit_to_wallet(
    user_id: int,
    amount: float,
    payment_method: PaymentMethod,
    db: Session = Depends(get_db)
):
    """Deposit money to user's wallet."""
    try:
        payment_service = PaymentService(db)
        return await payment_service.deposit_to_wallet(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method
        )
    except PaymentAmountError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WalletLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidPaymentMethodError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/orders/{user_id}", response_model=List[Order])
async def get_user_orders(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all orders for a user."""
    try:
        payment_service = PaymentService(db)
        return await payment_service.get_user_orders(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        ) 