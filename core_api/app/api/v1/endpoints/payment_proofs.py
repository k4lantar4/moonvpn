from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud, models, schemas
from app.api import deps
from app.models.order import OrderStatus, PaymentMethod
from app.services.order_service import order_service, OrderProcessingError
from app.services.payment_admin_service import PaymentAdminService
from app.services.file_storage_service import file_storage_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/{order_id}/submit", status_code=status.HTTP_200_OK)
async def submit_payment_proof(
    *,
    order_id: int = Path(..., title="The ID of the order to submit proof for"),
    payment_reference: str = Form(..., min_length=4, max_length=100, description="Payment reference or transaction ID"),
    payment_method: PaymentMethod = Form(PaymentMethod.CARD_TO_CARD, description="Payment method used"),
    notes: Optional[str] = Form(None, description="Additional notes from the user"),
    proof_image: UploadFile = File(..., description="Payment receipt image"),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Submit payment proof for an order.
    
    Users can only submit proof for their own orders.
    Requires an image file upload (JPG, PNG, GIF, WEBP) of payment receipt.
    """
    # Get the order
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if user owns this order
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this order"
        )
    
    try:
        # Save the uploaded file
        img_url = await file_storage_service.save_payment_proof(
            order_id=order_id,
            user_id=current_user.id,
            file=proof_image
        )
        
        # Update order with payment proof details
        updated_order = order_service.submit_payment_proof(
            db=db,
            order_id=order_id,
            payment_proof_img_url=img_url,
            payment_reference=payment_reference,
            payment_method=payment_method,
            notes=notes
        )
        
        # TODO: Notify admins about new payment proof submission
        # This would be implemented based on the notification system
        
        return {
            "success": True,
            "order_id": order_id,
            "message": "Payment proof submitted successfully and is awaiting verification",
            "status": updated_order.status.value
        }
        
    except (HTTPException, OrderProcessingError) as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            logger.error(f"Error submitting payment proof: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post("/{order_id}/verify", response_model=schemas.OrderResponse)
def verify_payment_proof(
    order_id: int,
    verification: schemas.PaymentVerification,
    order_service: OrderService = Depends(get_order_service),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Verify a payment proof for an order.
    
    This endpoint allows admins to approve or reject a payment proof that has been submitted.
    If approved, the order status will be updated to CONFIRMED. If rejected, it will be updated
    to REJECTED with the provided rejection reason.
    
    - **order_id**: The ID of the order to verify
    - **is_approved**: Whether the payment is approved or rejected
    - **rejection_reason**: Required reason if the payment is rejected
    - **admin_note**: Optional note from the admin
    
    Returns the updated order information.
    """
    # Check if user is authorized to verify payments
    if not crud.user.is_superuser(current_user) and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=403, 
            detail="Only admins can verify payment proofs"
        )
    
    try:
        # Call the service to verify the payment
        order = order_service.verify_payment_proof(
            order_id=order_id,
            admin_id=current_user.id,
            is_approved=verification.is_approved,
            rejection_reason=verification.rejection_reason,
            admin_note=verification.admin_note
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying payment proof: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while verifying the payment")


@router.get("/pending", response_model=List[schemas.Order])
async def get_pending_payment_proofs(
    *,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get orders with pending payment proofs for verification.
    
    This endpoint requires superuser privileges.
    """
    # Get orders with status VERIFICATION_PENDING
    orders = crud.order.get_by_statuses(
        db, 
        statuses=[OrderStatus.VERIFICATION_PENDING],
        skip=skip,
        limit=limit
    )
    
    return orders


@router.get("/admin/{admin_id}", response_model=List[schemas.Order])
async def get_admin_verified_orders(
    *,
    admin_id: int = Path(..., title="The ID of the admin"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get orders verified by a specific admin.
    
    This endpoint requires superuser privileges.
    """
    # Verify the admin exists
    admin = crud.user.get(db, id=admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Get orders verified by this admin
    orders = db.query(models.Order).filter(
        models.Order.payment_verification_admin_id == admin_id
    ).order_by(
        models.Order.payment_verified_at.desc()
    ).offset(skip).limit(limit).all()
    
    return orders


@router.patch("/{order_id}/telegram-message", response_model=schemas.OrderResponse)
def update_telegram_message_id(
    order_id: int,
    telegram_data: schemas.TelegramMessageUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update the Telegram message ID associated with a payment proof.
    
    This endpoint allows updating the telegram_msg_id and telegram_group_id for
    tracking and management purposes.
    
    - **order_id**: The ID of the order to update
    - **telegram_msg_id**: The Telegram message ID
    - **telegram_group_id**: The Telegram group ID
    
    Returns the updated order information.
    """
    try:
        # Call the service to update the telegram message details
        order = order_service.update_telegram_message_info(
            order_id=order_id,
            telegram_msg_id=telegram_data.telegram_msg_id,
            telegram_group_id=telegram_data.telegram_group_id
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating telegram message info: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while updating telegram message info") 