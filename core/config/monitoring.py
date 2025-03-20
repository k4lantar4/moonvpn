from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.services.monitoring import MonitoringService
from app.models.monitoring import (
    MonitoringMetric,
    Alert,
    SystemStatus,
    Log,
    Notification,
    Report,
    ReportSchedule
)
from app.schemas.monitoring import (
    MetricCreate,
    MetricResponse,
    AlertCreate,
    AlertResponse,
    SystemStatusResponse,
    LogResponse,
    NotificationResponse,
    ReportResponse,
    ReportScheduleCreate,
    ReportScheduleResponse
)

router = APIRouter()

@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    name: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    interval: str = "1h",
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get monitoring metrics."""
    monitoring_service = MonitoringService()
    return await monitoring_service.aggregate_metrics(
        name=name,
        interval=interval
    )

@router.post("/metrics", response_model=MetricResponse)
async def create_metric(
    metric: MetricCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Create monitoring metric."""
    monitoring_service = MonitoringService()
    return await monitoring_service.collect_custom_metric(
        name=metric.name,
        value=metric.value,
        tags=metric.tags
    )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get system alerts."""
    monitoring_service = MonitoringService()
    alerts = await monitoring_service.get_active_alerts()
    
    if status:
        alerts = [a for a in alerts if a.status == status]
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    return alerts

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Create system alert."""
    monitoring_service = MonitoringService()
    return await monitoring_service.create_alert(
        name=alert.name,
        description=alert.description,
        severity=alert.severity
    )

@router.put("/alerts/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: int,
    status: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Update alert status."""
    monitoring_service = MonitoringService()
    return await monitoring_service.update_alert_status(
        alert_id=alert_id,
        status=status
    )

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get system status."""
    monitoring_service = MonitoringService()
    return await monitoring_service.check_system_status()

@router.get("/logs", response_model=List[LogResponse])
async def get_logs(
    level: Optional[str] = None,
    source: Optional[str] = None,
    query: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get system logs."""
    monitoring_service = MonitoringService()
    if query:
        return await monitoring_service.search_logs(
            query=query,
            level=level
        )
    return await monitoring_service.collect_logs()

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get notification history."""
    monitoring_service = MonitoringService()
    return await monitoring_service.get_notification_history()

@router.post("/notifications/alert/{alert_id}", response_model=NotificationResponse)
async def send_alert_notification(
    alert_id: int,
    channel: str = "email",
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Send alert notification."""
    monitoring_service = MonitoringService()
    return await monitoring_service.send_alert_notification(
        alert_id=alert_id,
        channel=channel
    )

@router.post("/notifications/status", response_model=NotificationResponse)
async def send_status_notification(
    status: str,
    channel: str = "slack",
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Send status notification."""
    monitoring_service = MonitoringService()
    return await monitoring_service.send_status_notification(
        status=status,
        channel=channel
    )

@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get report history."""
    monitoring_service = MonitoringService()
    return await monitoring_service.get_report_history()

@router.post("/reports", response_model=ReportResponse)
async def generate_report(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Generate monitoring report."""
    monitoring_service = MonitoringService()
    return await monitoring_service.generate_report()

@router.post("/reports/schedules", response_model=ReportScheduleResponse)
async def schedule_report(
    schedule: ReportScheduleCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Schedule monitoring report."""
    monitoring_service = MonitoringService()
    return await monitoring_service.schedule_report(
        report_type=schedule.report_type,
        recipients=schedule.recipients
    )

@router.get("/dashboard", response_model=dict)
async def get_dashboard_metrics(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get dashboard metrics."""
    monitoring_service = MonitoringService()
    return await monitoring_service.get_dashboard_metrics()

@router.get("/visualization/{metric_name}", response_model=dict)
async def get_metric_visualization(
    metric_name: str,
    time_range: str = "1h",
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get metric visualization."""
    monitoring_service = MonitoringService()
    return await monitoring_service.generate_visualization(
        metric_name=metric_name,
        time_range=time_range
    )

@router.get("/compare/{metric_name}", response_model=List[dict])
async def compare_metrics(
    metric_name: str,
    time_ranges: List[str] = Query(["1h", "24h"]),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Compare metrics across time ranges."""
    monitoring_service = MonitoringService()
    return await monitoring_service.compare_metrics(
        metric_name=metric_name,
        time_ranges=time_ranges
    )

@router.post("/recover", response_model=dict)
async def recover_from_failure(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Handle monitoring system failure."""
    monitoring_service = MonitoringService()
    return await monitoring_service.handle_monitoring_failure() 