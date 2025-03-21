"""
API endpoints for MoonVPN enhancement features.

This module contains FastAPI endpoints for managing system health, backups,
notifications, reporting, logging, configuration, and metrics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from core.api.deps import get_current_user, get_db, rate_limit
from core.database.models.user import User
from core.services.enhancements import (
    SystemHealthService, SystemBackupService, NotificationTemplateService,
    ReportService, ReportScheduleService, SystemLogService,
    SystemConfigurationService, SystemMetricService
)
from core.schemas.enhancements import (
    SystemHealth, SystemHealthCreate, SystemHealthUpdate,
    SystemBackup, SystemBackupCreate, SystemBackupUpdate,
    NotificationTemplate, NotificationTemplateCreate, NotificationTemplateUpdate,
    Report, ReportCreate, ReportUpdate,
    ReportSchedule, ReportScheduleCreate, ReportScheduleUpdate,
    SystemLog, SystemLogCreate,
    SystemConfiguration, SystemConfigurationCreate, SystemConfigurationUpdate,
    SystemMetric, SystemMetricCreate, SystemMetricUpdate
)
from core.schemas.common import PaginatedResponse, FilterParams, SortParams

router = APIRouter()

# Common query parameters
async def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    filters: Dict[str, Any] = Body(None, description="Filter parameters")
):
    return {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "filters": filters or {}
    }

# System Health endpoints
@router.post("/health", response_model=SystemHealth)
@rate_limit(max_requests=10, window_seconds=60)
async def create_health_check(
    health_check: SystemHealthCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new system health check."""
    try:
        return SystemHealthService.create_health_check(db, health_check, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", response_model=PaginatedResponse[SystemHealth])
@rate_limit(max_requests=30, window_seconds=60)
async def list_health_checks(
    pagination: dict = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all health checks with pagination, filtering, and sorting."""
    try:
        query = db.query(SystemHealth)
        
        # Apply filters
        if pagination["filters"]:
            for key, value in pagination["filters"].items():
                if hasattr(SystemHealth, key):
                    query = query.filter(getattr(SystemHealth, key) == value)
        
        # Apply sorting
        if pagination["sort_by"] and hasattr(SystemHealth, pagination["sort_by"]):
            sort_column = getattr(SystemHealth, pagination["sort_by"])
            query = query.order_by(
                desc(sort_column) if pagination["sort_order"] == "desc" else asc(sort_column)
            )
        
        # Calculate pagination
        total = query.count()
        total_pages = (total + pagination["page_size"] - 1) // pagination["page_size"]
        items = query.offset((pagination["page"] - 1) * pagination["page_size"]).limit(pagination["page_size"]).all()
        
        return {
            "items": items,
            "total": total,
            "page": pagination["page"],
            "page_size": pagination["page_size"],
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/health/{health_id}", response_model=SystemHealth)
def update_health_check(
    health_id: int,
    health_check: SystemHealthUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing system health check."""
    db_health = SystemHealthService.update_health_check(db, health_id, health_check, current_user.id)
    if not db_health:
        raise HTTPException(status_code=404, detail="Health check not found")
    return db_health

@router.get("/health/{health_id}", response_model=SystemHealth)
def get_health_check(
    health_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a system health check by ID."""
    db_health = SystemHealthService.get_health_check(db, health_id)
    if not db_health:
        raise HTTPException(status_code=404, detail="Health check not found")
    return db_health

@router.get("/health/component/{component}", response_model=SystemHealth)
def get_component_health(
    component: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest health check for a specific component."""
    db_health = SystemHealthService.get_component_health(db, component)
    if not db_health:
        raise HTTPException(status_code=404, detail="Component health check not found")
    return db_health

@router.get("/health/critical", response_model=List[SystemHealth])
def get_critical_health_checks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all critical health checks."""
    return SystemHealthService.get_critical_health_checks(db)

# System Backup endpoints
@router.post("/backups", response_model=SystemBackup)
def create_backup(
    backup: SystemBackupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new system backup."""
    return SystemBackupService.create_backup(db, backup, current_user.id)

@router.put("/backups/{backup_id}", response_model=SystemBackup)
def update_backup(
    backup_id: int,
    backup: SystemBackupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing system backup."""
    db_backup = SystemBackupService.update_backup(db, backup_id, backup, current_user.id)
    if not db_backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return db_backup

@router.get("/backups/{backup_id}", response_model=SystemBackup)
def get_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a system backup by ID."""
    db_backup = SystemBackupService.get_backup(db, backup_id)
    if not db_backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return db_backup

@router.get("/backups/recent", response_model=List[SystemBackup])
def get_recent_backups(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the most recent system backups."""
    return SystemBackupService.get_recent_backups(db, limit)

@router.get("/backups/failed", response_model=List[SystemBackup])
def get_failed_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all failed system backups."""
    return SystemBackupService.get_failed_backups(db)

# Add bulk operations endpoints for backups
@router.post("/backups/bulk", response_model=List[SystemBackup])
@rate_limit(max_requests=5, window_seconds=60)
async def create_bulk_backups(
    backups: List[SystemBackupCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple backups in a single request."""
    try:
        results = []
        for backup in backups:
            result = SystemBackupService.create_backup(db, backup, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add search endpoint for backups
@router.get("/backups/search", response_model=List[SystemBackup])
@rate_limit(max_requests=20, window_seconds=60)
async def search_backups(
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search backups by name or description."""
    try:
        return SystemBackupService.search_backups(db, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add statistics endpoint for backups
@router.get("/backups/stats", response_model=Dict[str, Any])
@rate_limit(max_requests=30, window_seconds=60)
async def get_backup_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get backup statistics."""
    try:
        return SystemBackupService.get_statistics(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add export endpoint for backups
@router.get("/backups/export")
@rate_limit(max_requests=5, window_seconds=60)
async def export_backups(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export backups in specified format."""
    try:
        data = SystemBackupService.export_backups(db, format)
        return JSONResponse(
            content=data,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add webhook notification endpoint for backups
@router.post("/webhooks/backups", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=60)
async def backup_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle webhook notifications for backups."""
    try:
        return SystemBackupService.handle_webhook(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add audit log endpoint for backups
@router.get("/audit/backups", response_model=List[Dict[str, Any]])
@rate_limit(max_requests=20, window_seconds=60)
async def get_backup_audit_logs(
    start_date: datetime = Query(None, description="Start date for audit logs"),
    end_date: datetime = Query(None, description="End date for audit logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs for backup operations."""
    try:
        return SystemBackupService.get_audit_logs(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Notification Template endpoints
@router.post("/templates", response_model=NotificationTemplate)
def create_template(
    template: NotificationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification template."""
    return NotificationTemplateService.create_template(db, template, current_user.id)

@router.put("/templates/{template_id}", response_model=NotificationTemplate)
def update_template(
    template_id: int,
    template: NotificationTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing notification template."""
    db_template = NotificationTemplateService.update_template(db, template_id, template, current_user.id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.get("/templates/{template_id}", response_model=NotificationTemplate)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a notification template by ID."""
    db_template = NotificationTemplateService.get_template(db, template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.get("/templates/active", response_model=List[NotificationTemplate])
def get_active_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active notification templates."""
    return NotificationTemplateService.get_active_templates(db)

# Add bulk operations endpoints for notification templates
@router.post("/templates/bulk", response_model=List[NotificationTemplate])
@rate_limit(max_requests=5, window_seconds=60)
async def create_bulk_templates(
    templates: List[NotificationTemplateCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple notification templates in a single request."""
    try:
        results = []
        for template in templates:
            result = NotificationTemplateService.create_template(db, template, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add search endpoint for notification templates
@router.get("/templates/search", response_model=List[NotificationTemplate])
@rate_limit(max_requests=20, window_seconds=60)
async def search_templates(
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search notification templates by name or description."""
    try:
        return NotificationTemplateService.search_templates(db, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add statistics endpoint for notification templates
@router.get("/templates/stats", response_model=Dict[str, Any])
@rate_limit(max_requests=30, window_seconds=60)
async def get_template_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification template statistics."""
    try:
        return NotificationTemplateService.get_statistics(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add export endpoint for notification templates
@router.get("/templates/export")
@rate_limit(max_requests=5, window_seconds=60)
async def export_templates(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export notification templates in specified format."""
    try:
        data = NotificationTemplateService.export_templates(db, format)
        return JSONResponse(
            content=data,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add webhook notification endpoint for templates
@router.post("/webhooks/templates", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=60)
async def template_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle webhook notifications for notification templates."""
    try:
        return NotificationTemplateService.handle_webhook(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add audit log endpoint for templates
@router.get("/audit/templates", response_model=List[Dict[str, Any]])
@rate_limit(max_requests=20, window_seconds=60)
async def get_template_audit_logs(
    start_date: datetime = Query(None, description="Start date for audit logs"),
    end_date: datetime = Query(None, description="End date for audit logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs for notification template operations."""
    try:
        return NotificationTemplateService.get_audit_logs(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Report endpoints
@router.post("/reports", response_model=Report)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report."""
    return ReportService.create_report(db, report, current_user.id)

@router.put("/reports/{report_id}", response_model=Report)
def update_report(
    report_id: int,
    report: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing report."""
    db_report = ReportService.update_report(db, report_id, report, current_user.id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.get("/reports/{report_id}", response_model=Report)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a report by ID."""
    db_report = ReportService.get_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.get("/reports/pending", response_model=List[Report])
def get_pending_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pending reports."""
    return ReportService.get_pending_reports(db)

# Report Schedule endpoints
@router.post("/schedules", response_model=ReportSchedule)
def create_schedule(
    schedule: ReportScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new report schedule."""
    return ReportScheduleService.create_schedule(db, schedule, current_user.id)

@router.put("/schedules/{schedule_id}", response_model=ReportSchedule)
def update_schedule(
    schedule_id: int,
    schedule: ReportScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing report schedule."""
    db_schedule = ReportScheduleService.update_schedule(db, schedule_id, schedule, current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule

@router.get("/schedules/{schedule_id}", response_model=ReportSchedule)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a report schedule by ID."""
    db_schedule = ReportScheduleService.get_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule

@router.get("/schedules/active", response_model=List[ReportSchedule])
def get_active_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active report schedules."""
    return ReportScheduleService.get_active_schedules(db)

# Add bulk operations endpoints for report schedules
@router.post("/schedules/bulk", response_model=List[ReportSchedule])
@rate_limit(max_requests=5, window_seconds=60)
async def create_bulk_schedules(
    schedules: List[ReportScheduleCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple report schedules in a single request."""
    try:
        results = []
        for schedule in schedules:
            result = ReportScheduleService.create_schedule(db, schedule, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add search endpoint for report schedules
@router.get("/schedules/search", response_model=List[ReportSchedule])
@rate_limit(max_requests=20, window_seconds=60)
async def search_schedules(
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search report schedules by name or description."""
    try:
        return ReportScheduleService.search_schedules(db, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add statistics endpoint for report schedules
@router.get("/schedules/stats", response_model=Dict[str, Any])
@rate_limit(max_requests=30, window_seconds=60)
async def get_schedule_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report schedule statistics."""
    try:
        return ReportScheduleService.get_statistics(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add export endpoint for report schedules
@router.get("/schedules/export")
@rate_limit(max_requests=5, window_seconds=60)
async def export_schedules(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export report schedules in specified format."""
    try:
        data = ReportScheduleService.export_schedules(db, format)
        return JSONResponse(
            content=data,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=schedules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add webhook notification endpoint for report schedules
@router.post("/webhooks/schedules", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=60)
async def schedule_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle webhook notifications for report schedules."""
    try:
        return ReportScheduleService.handle_webhook(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add audit log endpoint for report schedules
@router.get("/audit/schedules", response_model=List[Dict[str, Any]])
@rate_limit(max_requests=20, window_seconds=60)
async def get_schedule_audit_logs(
    start_date: datetime = Query(None, description="Start date for audit logs"),
    end_date: datetime = Query(None, description="End date for audit logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs for report schedule operations."""
    try:
        return ReportScheduleService.get_audit_logs(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# System Log endpoints
@router.post("/logs", response_model=SystemLog)
def create_log(
    log: SystemLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new system log."""
    return SystemLogService.create_log(db, log, current_user.id)

@router.get("/logs/{log_id}", response_model=SystemLog)
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a system log by ID."""
    db_log = SystemLogService.get_log(db, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    return db_log

@router.get("/logs/component/{component}", response_model=List[SystemLog])
def get_component_logs(
    component: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get logs for a specific component."""
    return SystemLogService.get_component_logs(db, component, limit)

@router.get("/logs/error", response_model=List[SystemLog])
def get_error_logs(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get error logs."""
    return SystemLogService.get_error_logs(db, limit)

# Add bulk operations endpoints for system logs
@router.post("/logs/bulk", response_model=List[SystemLog])
@rate_limit(max_requests=5, window_seconds=60)
async def create_bulk_logs(
    logs: List[SystemLogCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple system logs in a single request."""
    try:
        results = []
        for log in logs:
            result = SystemLogService.create_log(db, log, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add search endpoint for system logs
@router.get("/logs/search", response_model=List[SystemLog])
@rate_limit(max_requests=20, window_seconds=60)
async def search_logs(
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search system logs by component, message, or metadata."""
    try:
        return SystemLogService.search_logs(db, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add statistics endpoint for system logs
@router.get("/logs/stats", response_model=Dict[str, Any])
@rate_limit(max_requests=30, window_seconds=60)
async def get_log_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system log statistics."""
    try:
        return SystemLogService.get_statistics(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add export endpoint for system logs
@router.get("/logs/export")
@rate_limit(max_requests=5, window_seconds=60)
async def export_logs(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export system logs in specified format."""
    try:
        data = SystemLogService.export_logs(db, format)
        return JSONResponse(
            content=data,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add webhook notification endpoint for system logs
@router.post("/webhooks/logs", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=60)
async def log_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle webhook notifications for system logs."""
    try:
        return SystemLogService.handle_webhook(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add audit log endpoint for system logs
@router.get("/audit/logs", response_model=List[Dict[str, Any]])
@rate_limit(max_requests=20, window_seconds=60)
async def get_log_audit_logs(
    start_date: datetime = Query(None, description="Start date for audit logs"),
    end_date: datetime = Query(None, description="End date for audit logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs for system log operations."""
    try:
        return SystemLogService.get_audit_logs(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# System Configuration endpoints
@router.post("/configs", response_model=SystemConfiguration)
def create_config(
    config: SystemConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new system configuration."""
    return SystemConfigurationService.create_config(db, config, current_user.id)

@router.put("/configs/{config_id}", response_model=SystemConfiguration)
def update_config(
    config_id: int,
    config: SystemConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing system configuration."""
    db_config = SystemConfigurationService.update_config(db, config_id, config, current_user.id)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return db_config

@router.get("/configs/{config_id}", response_model=SystemConfiguration)
def get_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a system configuration by ID."""
    db_config = SystemConfigurationService.get_config(db, config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return db_config

@router.get("/configs/key/{key}", response_model=SystemConfiguration)
def get_config_by_key(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a system configuration by key."""
    db_config = SystemConfigurationService.get_config_by_key(db, key)
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return db_config

# System Metric endpoints
@router.post("/metrics", response_model=SystemMetric)
def create_metric(
    metric: SystemMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new system metric."""
    return SystemMetricService.create_metric(db, metric, current_user.id)

@router.put("/metrics/{metric_id}", response_model=SystemMetric)
def update_metric(
    metric_id: int,
    metric: SystemMetricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing system metric."""
    db_metric = SystemMetricService.update_metric(db, metric_id, metric, current_user.id)
    if not db_metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return db_metric

@router.get("/metrics/{metric_id}", response_model=SystemMetric)
def get_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a system metric by ID."""
    db_metric = SystemMetricService.get_metric(db, metric_id)
    if not db_metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return db_metric

@router.get("/metrics/history/{metric_name}", response_model=List[SystemMetric])
def get_metric_history(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get metric history for a specific metric name."""
    return SystemMetricService.get_metric_history(db, metric_name, hours)

# Add bulk operations endpoints
@router.post("/health/bulk", response_model=List[SystemHealth])
@rate_limit(max_requests=5, window_seconds=60)
async def create_bulk_health_checks(
    health_checks: List[SystemHealthCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple health checks in a single request."""
    try:
        results = []
        for health_check in health_checks:
            result = SystemHealthService.create_health_check(db, health_check, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add search endpoint
@router.get("/health/search", response_model=List[SystemHealth])
@rate_limit(max_requests=20, window_seconds=60)
async def search_health_checks(
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search health checks by component name or description."""
    try:
        return SystemHealthService.search_health_checks(db, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add statistics endpoint
@router.get("/health/stats", response_model=Dict[str, Any])
@rate_limit(max_requests=30, window_seconds=60)
async def get_health_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get health check statistics."""
    try:
        return SystemHealthService.get_statistics(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add export endpoint
@router.get("/health/export")
@rate_limit(max_requests=5, window_seconds=60)
async def export_health_checks(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export health checks in specified format."""
    try:
        data = SystemHealthService.export_health_checks(db, format)
        return JSONResponse(
            content=data,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=health_checks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add webhook notification endpoint
@router.post("/webhooks/health", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=60)
async def health_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle webhook notifications for health checks."""
    try:
        return SystemHealthService.handle_webhook(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add audit log endpoint
@router.get("/audit/health", response_model=List[Dict[str, Any]])
@rate_limit(max_requests=20, window_seconds=60)
async def get_health_audit_logs(
    start_date: datetime = Query(None, description="Start date for audit logs"),
    end_date: datetime = Query(None, description="End date for audit logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs for health check operations."""
    try:
        return SystemHealthService.get_audit_logs(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add bulk operations endpoints for reports
@router.post("/reports/bulk", response_model=List[Report])
@rate_limit(max_requests=5, window_seconds=60)
async def create_bulk_reports(
    reports: List[ReportCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple reports in a single request."""
    try:
        results = []
        for report in reports:
            result = ReportService.create_report(db, report, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add search endpoint for reports
@router.get("/reports/search", response_model=List[Report])
@rate_limit(max_requests=20, window_seconds=60)
async def search_reports(
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search reports by name or description."""
    try:
        return ReportService.search_reports(db, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add statistics endpoint for reports
@router.get("/reports/stats", response_model=Dict[str, Any])
@rate_limit(max_requests=30, window_seconds=60)
async def get_report_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report statistics."""
    try:
        return ReportService.get_statistics(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add export endpoint for reports
@router.get("/reports/export")
@rate_limit(max_requests=5, window_seconds=60)
async def export_reports(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export reports in specified format."""
    try:
        data = ReportService.export_reports(db, format)
        return JSONResponse(
            content=data,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add webhook notification endpoint for reports
@router.post("/webhooks/reports", response_model=Dict[str, Any])
@rate_limit(max_requests=10, window_seconds=60)
async def report_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle webhook notifications for reports."""
    try:
        return ReportService.handle_webhook(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add audit log endpoint for reports
@router.get("/audit/reports", response_model=List[Dict[str, Any]])
@rate_limit(max_requests=20, window_seconds=60)
async def get_report_audit_logs(
    start_date: datetime = Query(None, description="Start date for audit logs"),
    end_date: datetime = Query(None, description="End date for audit logs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs for report operations."""
    try:
        return ReportService.get_audit_logs(db, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 