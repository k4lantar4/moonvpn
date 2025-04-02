from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
import logging
import urllib.parse
from typing import List

from app import crud, models, schemas
from app.api import deps
from app.services.zarinpal_service import zarinpal_service, ZarinpalAPIError
from app.models.order import OrderStatus, PaymentMethod
from app.services.order_service import order_service, OrderProcessingError
from app.core.config import settings
from app.schemas.payment import PaymentRequestResponse, PaymentMethodResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_available_payment_methods(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get a list of available payment methods. 
    Returns only payment methods that are currently active.
    """
    # Define all possible payment methods
    all_methods = [
        {"method": PaymentMethod.CARD_TO_CARD.value, "active": True},  # Card to Card is always active
        {"method": PaymentMethod.WALLET.value, "active": True},  # Wallet is always active
        {"method": PaymentMethod.ZARINPAL.value, "active": zarinpal_service.enabled},  # Zarinpal depends on service config
        {"method": PaymentMethod.CRYPTO.value, "active": False},  # Crypto not implemented yet
        {"method": PaymentMethod.MANUAL.value, "active": False},  # Manual only for admins
    ]
    
    # For admins, enable all payment methods
    if deps.check_user_permission(current_user, "admin:payment:manage"):
        all_methods = [{"method": method.value, "active": True} for method in PaymentMethod]
    
    # Filter only active methods
    active_methods = [method for method in all_methods if method["active"]]
    
    return active_methods


@router.post("/zarinpal/request/{order_id}", response_model=PaymentRequestResponse)
async def request_zarinpal_payment(
    *, 
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., title="The ID of the order to pay for"),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Initiates a payment request with Zarinpal for a specific order.
    
    Returns the payment URL for the user to be redirected to.
    """
    order = crud.order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.user_id != current_user.id and not deps.check_user_permission(current_user, "admin:order:read"):
        raise HTTPException(status_code=403, detail="Not allowed to access this order")

    if order.status != OrderStatus.PENDING:
         raise HTTPException(
            status_code=400, 
            detail=f"Cannot start payment for order with status {order.status.value}. Expected PENDING."
         )

    if not order.final_amount or order.final_amount <= 0:
         raise HTTPException(status_code=400, detail="Order amount is invalid or zero.")

    try:
        payment_url, authority = zarinpal_service.request_payment(
            amount=order.final_amount,
            description=f"Payment for MoonVPN Order #{order.order_id}",
            order_id=order.id,
            user_email=current_user.email,
            # user_mobile=current_user.phone_number # Add if phone number is available
        )
        
        # Store the authority token in the order
        crud.order.update(db, db_obj=order, obj_in={"payment_authority": authority})
        
        return {"payment_url": payment_url}
        
    except ZarinpalAPIError as e:
        logger.error(f"Zarinpal request failed for order {order_id}: {e}", exc_info=True)
        # Optionally mark order as failed here?
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error requesting Zarinpal payment for order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during payment request.")


@router.get("/zarinpal/callback/{order_id}", summary="Zarinpal Payment Callback")
async def handle_zarinpal_callback(
    request: Request,
    order_id: int = Path(..., title="The ID of the order being processed"),
    Status: str = Query(..., description="Payment status from Zarinpal (OK or NOK)"),
    Authority: str = Query(..., description="Authority token from Zarinpal"),
    db: Session = Depends(deps.get_db)
):
    """
    Handles the callback from Zarinpal after a payment attempt.
    Verifies the payment and updates the order status.
    Redirects the user to a frontend status page.
    """
    order = crud.order.get(db, id=order_id)
    frontend_redirect_url = settings.FRONTEND_PAYMENT_RESULT_URL # Needs to be added to settings
    params = {"order_id": order_id}

    if not order:
        logger.error(f"Zarinpal callback received for non-existent order ID: {order_id}")
        params["status"] = "error"
        params["message"] = "Order not found"
        return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")

    # Verify authority matches the one stored (security check)
    if not order.payment_authority or order.payment_authority != Authority:
         logger.warning(f"Zarinpal callback authority mismatch for order {order_id}. Expected: {order.payment_authority}, Received: {Authority}")
         params["status"] = "error"
         params["message"] = "Invalid payment authority"
         # Optionally update order status to FAILED here?
         return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")

    # Check if already processed
    if order.status == OrderStatus.PAID:
        logger.info(f"Zarinpal callback received for already paid order {order_id}. Redirecting.")
        params["status"] = "success"
        return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")
        
    # If payment was not successful according to Zarinpal status
    if Status != 'OK':
        logger.warning(f"Zarinpal callback indicates failed payment for order {order_id}. Status: {Status}, Authority: {Authority}")
        crud.order.update(db, db_obj=order, obj_in={
            "status": OrderStatus.FAILED,
            "admin_note": f"Zarinpal payment failed by user or gateway. Status: {Status}"
        })
        params["status"] = "failed"
        params["message"] = "Payment was not successful"
        return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")

    # If Status is OK, verify the transaction with Zarinpal API
    try:
        verification_data = zarinpal_service.verify_payment(
            amount=order.final_amount,
            authority=Authority
        )
        
        ref_id = verification_data.get('ref_id')
        card_pan = verification_data.get('card_pan', 'N/A')
        
        # Payment verified successfully, process the order
        logger.info(f"Zarinpal payment verified for order {order_id}. Ref ID: {ref_id}, Card: {card_pan}")
        order_service.process_payment(
            db=db,
            order_id=order.id,
            payment_method=PaymentMethod.ZARINPAL.value,
            payment_reference=f"Zarinpal Ref ID: {ref_id}",
            # admin_id=None # System processed
            admin_note=f"Paid via Zarinpal. Card: {card_pan}"
        )
        
        # TODO: Potentially trigger client creation here if auto-provisioning is desired
        # Commenting out the auto-creation part for now, can be added later
        # try:
        #     order_service.create_client_on_panel(db, order_id=order.id, admin_note="Auto-created after Zarinpal payment")
        # except OrderProcessingError as client_error:
        #     logger.error(f"Failed to auto-create client for order {order_id} after Zarinpal payment: {client_error}")
        #     # Order is paid, but client creation failed. Needs manual intervention.
        
        params["status"] = "success"
        return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")

    except ZarinpalAPIError as e:
        logger.error(f"Zarinpal verification failed for order {order_id}, Authority: {Authority}. Error: {e}", exc_info=True)
        crud.order.update(db, db_obj=order, obj_in={
            "status": OrderStatus.FAILED,
            "admin_note": f"Zarinpal verification failed. Error code: {e.code}, Message: {e.message}"
        })
        params["status"] = "error"
        params["message"] = f"Payment verification failed: {e.message}"
        return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")
        
    except OrderProcessingError as e:
         logger.error(f"Failed to process order {order_id} after Zarinpal verification. Error: {e}", exc_info=True)
         # Order might be paid in Zarinpal but failed locally. Needs investigation.
         params["status"] = "error"
         params["message"] = "Failed to update order status after successful payment verification."
         return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")
         
    except Exception as e:
        logger.error(f"Unexpected error during Zarinpal callback for order {order_id}: {e}", exc_info=True)
        params["status"] = "error"
        params["message"] = "An unexpected server error occurred."
        return RedirectResponse(f"{frontend_redirect_url}?{urllib.parse.urlencode(params)}")

# TODO: Add a schema for PaymentRequestResponse { "payment_url": str }
# TODO: Add FRONTEND_PAYMENT_RESULT_URL to config
# TODO: Import urllib.parse 