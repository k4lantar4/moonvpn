"""
Payment routes for MoonVPN.

This module contains FastAPI routes for handling payment-related
operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database.session import get_db
from app.core.schemas.payment import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    Wallet,
    WalletCreate,
    WalletUpdate,
    Order,
    OrderCreate,
    OrderUpdate,
    PaymentRequest,
    PaymentResponse,
    PaymentVerification
)
from app.core.services.payment_service import PaymentService
from app.core.auth import get_current_user
from app.core.schemas.user import User

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate a new payment."""
    payment_service = PaymentService(db)
    return await payment_service.process_payment(
        user_id=current_user.id,
        order_id=payment_request.order_id,
        amount=payment_request.amount,
        payment_method=payment_request.payment_method,
        callback_url=payment_request.callback_url
    )

@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    verification: PaymentVerification,
    db: Session = Depends(get_db)
):
    """Verify a payment with the payment gateway."""
    payment_service = PaymentService(db)
    return await payment_service.verify_payment(
        authority=verification.authority,
        status=verification.status,
        ref_id=verification.ref_id
    )

@router.get("/transactions", response_model=List[Transaction])
async def get_user_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions for the current user."""
    payment_service = PaymentService(db)
    return await payment_service.get_user_transactions(current_user.id)

@router.get("/wallet", response_model=Wallet)
async def get_user_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's wallet."""
    payment_service = PaymentService(db)
    return await payment_service.get_user_wallet(current_user.id)

@router.post("/wallet/deposit", response_model=PaymentResponse)
async def deposit_to_wallet(
    amount: float,
    payment_method: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deposit money to the user's wallet."""
    payment_service = PaymentService(db)
    return await payment_service.deposit_to_wallet(
        user_id=current_user.id,
        amount=amount,
        payment_method=payment_method
    )

@router.get("/orders", response_model=List[Order])
async def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all orders for the current user."""
    payment_service = PaymentService(db)
    return await payment_service.get_user_orders(current_user.id)

@router.post("/orders", response_model=Order)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order."""
    payment_service = PaymentService(db)
    return await payment_service.create_order(
        user_id=current_user.id,
        plan_id=order.plan_id,
        amount=order.amount
    ) 