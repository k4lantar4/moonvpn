from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_superuser
from app.models.order import OrderStatus, PaymentMethod
from app.models.transaction import TransactionType, TransactionStatus
from app.models.affiliate import CommissionStatus
from app.models.user import User
from app.services.financial_reporting_service import (
    FinancialReportingService, 
    ReportType, 
    ReportFormat, 
    TimeFrame
)


router = APIRouter()


@router.get("/summary", response_model=Dict[str, Any])
def get_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Get financial summary data for the dashboard.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    return reporting_service.get_summary_dashboard_data()


@router.get("/export/{report_type}")
def export_financial_report(
    report_type: ReportType,
    format: ReportFormat = ReportFormat.EXCEL,
    time_frame: TimeFrame = TimeFrame.THIS_MONTH,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_method: Optional[PaymentMethod] = None,
    order_status: Optional[OrderStatus] = None,
    transaction_type: Optional[TransactionType] = None,
    transaction_status: Optional[TransactionStatus] = None,
    commission_status: Optional[CommissionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> StreamingResponse:
    """
    Generate and export a financial report in the specified format.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    
    # Prepare kwargs based on report type
    kwargs = {}
    if report_type == ReportType.ORDERS:
        kwargs = {
            "payment_method": payment_method,
            "status": order_status
        }
    elif report_type == ReportType.TRANSACTIONS:
        kwargs = {
            "transaction_type": transaction_type,
            "status": transaction_status
        }
    elif report_type == ReportType.COMMISSIONS:
        kwargs = {
            "status": commission_status
        }
    
    # Generate the report
    try:
        file_content, filename = reporting_service.export_report(
            report_type=report_type,
            report_format=format,
            time_frame=time_frame,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
    
    # Set appropriate content type based on format
    if format == ReportFormat.EXCEL:
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif format == ReportFormat.CSV:
        media_type = "text/csv"
    else:  # JSON
        media_type = "application/json"
    
    # Create a streaming response with the file content
    return StreamingResponse(
        iter([file_content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/orders", response_model=List[Dict[str, Any]])
def get_orders_report(
    time_frame: TimeFrame = TimeFrame.THIS_MONTH,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_method: Optional[PaymentMethod] = None,
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Get orders report data for display in the dashboard.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    df = reporting_service.generate_orders_report(
        time_frame=time_frame,
        start_date=start_date,
        end_date=end_date,
        payment_method=payment_method,
        status=status
    )
    
    # Convert DataFrame to JSON records
    return df.to_dict(orient="records")


@router.get("/transactions", response_model=List[Dict[str, Any]])
def get_transactions_report(
    time_frame: TimeFrame = TimeFrame.THIS_MONTH,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Get transactions report data for display in the dashboard.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    df = reporting_service.generate_transactions_report(
        time_frame=time_frame,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        status=status
    )
    
    # Convert DataFrame to JSON records
    return df.to_dict(orient="records")


@router.get("/commissions", response_model=List[Dict[str, Any]])
def get_commissions_report(
    time_frame: TimeFrame = TimeFrame.THIS_MONTH,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[CommissionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Get affiliate commissions report data for display in the dashboard.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    df = reporting_service.generate_commissions_report(
        time_frame=time_frame,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    
    # Convert DataFrame to JSON records
    return df.to_dict(orient="records")


@router.get("/revenue", response_model=List[Dict[str, Any]])
def get_revenue_report(
    time_frame: TimeFrame = TimeFrame.THIS_MONTH,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Get revenue report data for display in the dashboard.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    df = reporting_service.generate_revenue_report(
        time_frame=time_frame,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Convert DataFrame to JSON records
    return df.to_dict(orient="records")


@router.get("/subscriptions", response_model=List[Dict[str, Any]])
def get_subscription_report(
    time_frame: TimeFrame = TimeFrame.THIS_MONTH,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Get subscription report data for display in the dashboard.
    Only accessible to superusers.
    """
    reporting_service = FinancialReportingService(db)
    df = reporting_service.generate_subscription_report(
        time_frame=time_frame,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Convert DataFrame to JSON records
    return df.to_dict(orient="records") 