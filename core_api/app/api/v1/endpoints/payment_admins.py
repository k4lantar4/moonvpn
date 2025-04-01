from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db, get_current_active_user, get_current_active_superuser
from app.models.user import User
from app.services.payment_admin_service import PaymentAdminService
from app.schemas.payment_admin import (
    PaymentAdminAssignment,
    PaymentAdminAssignmentCreate,
    PaymentAdminAssignmentUpdate,
    PaymentAdminMetrics,
    PaymentAdminMetricsUpdate,
    PaymentAdminAssignmentWithMetrics,
    PaymentAdminStatistics,
    PaymentAdminAssignmentResponse
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/assignments/", response_model=List[PaymentAdminAssignment])
def get_payment_admin_assignments(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    bank_card_id: Optional[int] = Query(None, description="Filter by bank card ID"),
    telegram_group_id: Optional[str] = Query(None, description="Filter by Telegram group ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get all payment admin assignments with optional filtering.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    
    if user_id:
        return payment_admin_service.get_assignments_by_user(user_id)
    elif bank_card_id:
        return payment_admin_service.get_assignments_by_bank_card(bank_card_id)
    elif telegram_group_id:
        return payment_admin_service.get_assignments_by_telegram_group(telegram_group_id)
    else:
        # Get all assignments (filtered by active status if provided)
        assignments = db.query(PaymentAdminAssignment)
        if is_active is not None:
            assignments = assignments.filter(PaymentAdminAssignment.is_active == is_active)
        return assignments.all()


@router.post("/assignments/", response_model=PaymentAdminAssignment, status_code=status.HTTP_201_CREATED)
def create_payment_admin_assignment(
    assignment_in: PaymentAdminAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Create a new payment admin assignment.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    assignment = payment_admin_service.create_assignment(assignment_in)
    return assignment


@router.get("/assignments/{assignment_id}", response_model=PaymentAdminAssignmentWithMetrics)
def get_payment_admin_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get a specific payment admin assignment by ID, including metrics.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    assignment_with_metrics = payment_admin_service.get_assignment_with_metrics(assignment_id)
    
    if not assignment_with_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment admin assignment with ID {assignment_id} not found"
        )
    
    return assignment_with_metrics


@router.put("/assignments/{assignment_id}", response_model=PaymentAdminAssignment)
def update_payment_admin_assignment(
    assignment_id: int,
    assignment_in: PaymentAdminAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Update a payment admin assignment.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    assignment = payment_admin_service.update_assignment(assignment_id, assignment_in)
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment admin assignment with ID {assignment_id} not found"
        )
    
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_admin_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Delete a payment admin assignment.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    success = payment_admin_service.delete_assignment(assignment_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment admin assignment with ID {assignment_id} not found"
        )


@router.get("/metrics/{user_id}", response_model=PaymentAdminMetrics)
def get_payment_admin_metrics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get metrics for a specific payment admin.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    metrics = payment_admin_service.get_metrics(user_id)
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics for user with ID {user_id} not found"
        )
    
    return metrics


@router.put("/metrics/{user_id}", response_model=PaymentAdminMetrics)
def update_payment_admin_metrics(
    user_id: int,
    metrics_in: PaymentAdminMetricsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Update metrics for a payment admin.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    metrics = payment_admin_service.update_metrics(user_id, metrics_in)
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics for user with ID {user_id} not found"
        )
    
    return metrics


@router.post("/metrics/{user_id}/record-payment", response_model=PaymentAdminMetrics)
def record_payment_processed(
    user_id: int,
    approved: bool = Query(..., description="Whether the payment was approved"),
    response_time_seconds: float = Query(..., description="Response time in seconds"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Record a processed payment in the admin's metrics.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    metrics = payment_admin_service.record_payment_processed(
        user_id, approved, response_time_seconds
    )
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics for user with ID {user_id} not found"
        )
    
    return metrics


@router.get("/statistics/", response_model=PaymentAdminStatistics)
def get_payment_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get overall statistics for payment admins.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    statistics = payment_admin_service.get_admin_statistics()
    return statistics


@router.get("/select-for-payment/", response_model=Optional[PaymentAdminAssignment])
def select_admin_for_payment(
    bank_card_id: Optional[int] = Query(None, description="ID of the bank card used for payment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Select an appropriate payment admin for a new payment verification.
    
    This endpoint requires superuser privileges.
    """
    payment_admin_service = PaymentAdminService(db)
    assignment = payment_admin_service.select_admin_for_payment(bank_card_id)
    
    if not assignment:
        logger.warning("No suitable payment admin found")
    
    return assignment


@router.get("/assignments/card/{bank_card_id}", response_model=PaymentAdminAssignmentResponse)
async def get_payment_admin_for_card(
    bank_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the assigned payment admin for a specific bank card.
    Used by the Telegram bot to determine which admin/group should receive payment notifications.
    """
    try:
        # Create service instance
        payment_admin_service = PaymentAdminService(db)
        
        # Get assignment for this card using the load balancing algorithm
        assignment = await payment_admin_service.get_admin_for_card(bank_card_id)
        
        if assignment:
            # Include admin details in response
            admin = await db.get(User, assignment.admin_id)
            
            if admin:
                # Format response
                response_data = {
                    "id": assignment.id,
                    "admin_id": assignment.admin_id,
                    "bank_card_id": assignment.bank_card_id,
                    "telegram_group_id": assignment.telegram_group_id,
                    "active": assignment.active,
                    "admin": {
                        "id": admin.id,
                        "first_name": admin.first_name,
                        "last_name": admin.last_name,
                        "telegram_id": admin.telegram_id
                    }
                }
                
                return PaymentAdminAssignmentResponse(
                    success=True,
                    data=response_data
                )
        
        # No assignment found or admin not available
        return PaymentAdminAssignmentResponse(
            success=False,
            detail="No admin assigned for this bank card"
        )
    
    except Exception as e:
        logger.error(f"Error getting payment admin for card {bank_card_id}: {str(e)}")
        return PaymentAdminAssignmentResponse(
            success=False,
            detail=f"Error getting payment admin: {str(e)}"
        )


@router.get("/reports", response_model=schemas.PaymentAdminReportResponse)
async def generate_payment_admin_reports(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
):
    """
    Generate comprehensive reports on payment admin performance.
    
    This endpoint returns detailed metrics about payment admin performance,
    including average response times, approval rates, rejection reasons,
    and workload distribution. The data can be filtered by date range
    and specific admin.
    
    Admin users can only view their own reports, superusers can view all reports.
    
    Parameters:
    - start_date: Optional start date for filtering (YYYY-MM-DD format)
    - end_date: Optional end date for filtering (YYYY-MM-DD format)
    - admin_id: Optional admin ID to filter results for a specific admin
    
    Returns:
    - Detailed performance metrics for payment admins
    """
    try:
        # Parse dates if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid start_date format. Use YYYY-MM-DD format."
                )
        
        if end_date:
            try:
                # Set end date to end of day 
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid end_date format. Use YYYY-MM-DD format."
                )
        
        # Check permission if admin_id is specified and not superuser
        if admin_id and not current_user.is_superuser:
            if current_user.id != admin_id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only view your own reports"
                )
        
        # Create payment admin service
        payment_admin_service = PaymentAdminService(db)
        
        # Generate the reports
        reports = await payment_admin_service.generate_performance_reports(
            start_date=start_datetime,
            end_date=end_datetime,
            admin_id=admin_id
        )
        
        return {
            "success": True,
            "data": reports
        }
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Error generating payment admin reports: {str(e)}")
        return {
            "success": False,
            "detail": f"Error generating payment admin reports: {str(e)}"
        }
