"""
Payment API endpoints for MoonVPN.

This module contains the FastAPI router for payment-related endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db.repositories.factory import RepositoryFactory
from app.services.payment import PaymentService
from app.models.payment import Payment, PaymentCreate, PaymentUpdate, PaymentResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=List[PaymentResponse])
async def get_current_user_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[PaymentResponse]:
    """Get current user's payments."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payments = await service.get_by_telegram_id(current_user.telegram_id)
    
    return [PaymentResponse.from_orm(payment) for payment in payments]

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Get payment by ID."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.get_by_id(payment_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if not current_user.is_admin and payment.telegram_id != current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return PaymentResponse.from_orm(payment)

@router.get("/authority/{authority}", response_model=PaymentResponse)
async def get_payment_by_authority(
    authority: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Get payment by authority token."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.get_by_authority(authority)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if not current_user.is_admin and payment.telegram_id != current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return PaymentResponse.from_orm(payment)

@router.get("/transaction/{transaction_id}", response_model=PaymentResponse)
async def get_payment_by_transaction_id(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Get payment by transaction ID."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.get_by_transaction_id(transaction_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if not current_user.is_admin and payment.telegram_id != current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return PaymentResponse.from_orm(payment)

@router.get("/pending", response_model=List[PaymentResponse])
async def get_pending_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[PaymentResponse]:
    """Get all pending payments (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payments = await service.get_pending_payments()
    
    return [PaymentResponse.from_orm(payment) for payment in payments]

@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Create a new payment."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.create(payment_data)
    
    return PaymentResponse.from_orm(payment)

@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Update a payment (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.update(payment_id, payment_data)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentResponse.from_orm(payment)

@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a payment (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    success = await service.delete(payment_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return {"message": "Payment deleted successfully"}

@router.post("/{payment_id}/verify")
async def verify_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Verify a payment (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.get_by_id(payment_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    is_valid = await service.verify_payment(payment.authority)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment"
        )
    
    return {"message": "Payment verified successfully"}

@router.post("/callback/{authority}")
async def process_payment_callback(
    authority: str,
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Process a payment callback from the payment gateway."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.process_payment_callback(authority, transaction_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentResponse.from_orm(payment)

@router.get("/{payment_id}/stats")
async def get_payment_stats(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get payment statistics."""
    factory = RepositoryFactory(db)
    service = PaymentService(factory.payment_repository, factory.user_repository)
    payment = await service.get_by_id(payment_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if not current_user.is_admin and payment.telegram_id != current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await service.get_payment_stats(payment.telegram_id) 