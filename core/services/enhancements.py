"""
Service classes for MoonVPN enhancement models.

This module contains service classes for managing system health, backups,
notifications, reporting, logging, configuration, and metrics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import json
import csv
from io import StringIO

from core.database.models.enhancements import (
    SystemHealth, SystemBackup, NotificationTemplate, Report,
    ReportSchedule, SystemLog, SystemConfiguration, SystemMetric
)
from core.schemas.enhancements import (
    SystemHealthCreate, SystemHealthUpdate,
    SystemBackupCreate, SystemBackupUpdate,
    NotificationTemplateCreate, NotificationTemplateUpdate,
    ReportCreate, ReportUpdate,
    ReportScheduleCreate, ReportScheduleUpdate,
    SystemLogCreate,
    SystemConfigurationCreate, SystemConfigurationUpdate,
    SystemMetricCreate, SystemMetricUpdate
)

class SystemHealthService:
    """Service for managing system health records."""

    @staticmethod
    def create_health_check(db: Session, health_check: SystemHealthCreate, user_id: int) -> SystemHealth:
        """Create a new system health check record."""
        db_health = SystemHealth(
            **health_check.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_health)
        db.commit()
        db.refresh(db_health)
        return db_health

    @staticmethod
    def update_health_check(db: Session, health_id: int, health_check: SystemHealthUpdate, user_id: int) -> Optional[SystemHealth]:
        """Update an existing system health check record."""
        db_health = db.query(SystemHealth).filter(SystemHealth.id == health_id).first()
        if not db_health:
            return None
        
        update_data = health_check.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_health, field, value)
        
        db_health.updated_by = user_id
        db.commit()
        db.refresh(db_health)
        return db_health

    @staticmethod
    def get_health_check(db: Session, health_id: int) -> Optional[SystemHealth]:
        """Get a system health check record by ID."""
        return db.query(SystemHealth).filter(SystemHealth.id == health_id).first()

    @staticmethod
    def get_component_health(db: Session, component: str) -> Optional[SystemHealth]:
        """Get the latest health check for a specific component."""
        return db.query(SystemHealth).filter(
            SystemHealth.component == component
        ).order_by(SystemHealth.last_check.desc()).first()

    @staticmethod
    def get_critical_health_checks(db: Session) -> List[SystemHealth]:
        """Get all critical health checks."""
        return db.query(SystemHealth).filter(
            SystemHealth.status == 'critical'
        ).all()

    @staticmethod
    def search_health_checks(db: Session, query: str) -> List[SystemHealth]:
        """Search health checks by component name or description."""
        return db.query(SystemHealth).filter(
            or_(
                SystemHealth.component.ilike(f"%{query}%"),
                SystemHealth.description.ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get health check statistics."""
        total_checks = db.query(func.count(SystemHealth.id)).scalar()
        critical_checks = db.query(func.count(SystemHealth.id)).filter(
            SystemHealth.status == 'critical'
        ).scalar()
        warning_checks = db.query(func.count(SystemHealth.id)).filter(
            SystemHealth.status == 'warning'
        ).scalar()
        healthy_checks = db.query(func.count(SystemHealth.id)).filter(
            SystemHealth.status == 'healthy'
        ).scalar()

        return {
            "total_checks": total_checks,
            "critical_checks": critical_checks,
            "warning_checks": warning_checks,
            "healthy_checks": healthy_checks,
            "critical_percentage": (critical_checks / total_checks * 100) if total_checks > 0 else 0,
            "warning_percentage": (warning_checks / total_checks * 100) if total_checks > 0 else 0,
            "healthy_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        }

    @staticmethod
    def export_health_checks(db: Session, format: str) -> Any:
        """Export health checks in specified format."""
        health_checks = db.query(SystemHealth).all()
        
        if format == "json":
            return [check.to_dict() for check in health_checks]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Component", "Status", "Last Check", "Description"])
            for check in health_checks:
                writer.writerow([
                    check.id,
                    check.component,
                    check.status,
                    check.last_check.isoformat(),
                    check.description
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for health checks."""
        try:
            # Process webhook payload
            component = payload.get("component")
            status = payload.get("status")
            description = payload.get("description")
            
            if not all([component, status]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create health check record
            health_check = SystemHealthCreate(
                component=component,
                status=status,
                description=description,
                last_check=datetime.utcnow()
            )
            
            db_health = SystemHealthService.create_health_check(db, health_check, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "health_check_id": db_health.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for health check operations."""
        query = db.query(SystemHealth)
        
        if start_date:
            query = query.filter(SystemHealth.created_at >= start_date)
        if end_date:
            query = query.filter(SystemHealth.created_at <= end_date)
        
        health_checks = query.order_by(SystemHealth.created_at.desc()).all()
        
        return [{
            "id": check.id,
            "component": check.component,
            "status": check.status,
            "created_at": check.created_at.isoformat(),
            "updated_at": check.updated_at.isoformat(),
            "created_by": check.created_by,
            "updated_by": check.updated_by
        } for check in health_checks]

class SystemBackupService:
    """Service for managing system backups."""

    @staticmethod
    def create_backup(db: Session, backup: SystemBackupCreate, user_id: int) -> SystemBackup:
        """Create a new system backup record."""
        db_backup = SystemBackup(
            **backup.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_backup)
        db.commit()
        db.refresh(db_backup)
        return db_backup

    @staticmethod
    def update_backup(db: Session, backup_id: int, backup: SystemBackupUpdate, user_id: int) -> Optional[SystemBackup]:
        """Update an existing system backup record."""
        db_backup = db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()
        if not db_backup:
            return None
        
        update_data = backup.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_backup, field, value)
        
        db_backup.updated_by = user_id
        db.commit()
        db.refresh(db_backup)
        return db_backup

    @staticmethod
    def get_backup(db: Session, backup_id: int) -> Optional[SystemBackup]:
        """Get a system backup record by ID."""
        return db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()

    @staticmethod
    def get_recent_backups(db: Session, limit: int = 10) -> List[SystemBackup]:
        """Get the most recent system backups."""
        return db.query(SystemBackup).order_by(
            SystemBackup.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_failed_backups(db: Session) -> List[SystemBackup]:
        """Get all failed system backups."""
        return db.query(SystemBackup).filter(
            SystemBackup.status == 'failed'
        ).all()

    @staticmethod
    def search_backups(db: Session, query: str) -> List[SystemBackup]:
        """Search backups by name or description."""
        return db.query(SystemBackup).filter(
            or_(
                SystemBackup.name.ilike(f"%{query}%"),
                SystemBackup.description.ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get backup statistics."""
        total_backups = db.query(func.count(SystemBackup.id)).scalar()
        successful_backups = db.query(func.count(SystemBackup.id)).filter(
            SystemBackup.status == 'success'
        ).scalar()
        failed_backups = db.query(func.count(SystemBackup.id)).filter(
            SystemBackup.status == 'failed'
        ).scalar()

        return {
            "total_backups": total_backups,
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "success_rate": (successful_backups / total_backups * 100) if total_backups > 0 else 0,
            "failure_rate": (failed_backups / total_backups * 100) if total_backups > 0 else 0
        }

    @staticmethod
    def export_backups(db: Session, format: str) -> Any:
        """Export backups in specified format."""
        backups = db.query(SystemBackup).all()
        
        if format == "json":
            return [backup.to_dict() for backup in backups]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Name", "Type", "Status", "Created At", "Size"])
            for backup in backups:
                writer.writerow([
                    backup.id,
                    backup.name,
                    backup.type,
                    backup.status,
                    backup.created_at.isoformat(),
                    backup.size
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for backups."""
        try:
            # Process webhook payload
            name = payload.get("name")
            type = payload.get("type")
            status = payload.get("status")
            
            if not all([name, type, status]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create backup record
            backup = SystemBackupCreate(
                name=name,
                type=type,
                status=status,
                size=payload.get("size"),
                path=payload.get("path")
            )
            
            db_backup = SystemBackupService.create_backup(db, backup, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "backup_id": db_backup.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for backup operations."""
        query = db.query(SystemBackup)
        
        if start_date:
            query = query.filter(SystemBackup.created_at >= start_date)
        if end_date:
            query = query.filter(SystemBackup.created_at <= end_date)
        
        backups = query.order_by(SystemBackup.created_at.desc()).all()
        
        return [{
            "id": backup.id,
            "name": backup.name,
            "type": backup.type,
            "status": backup.status,
            "created_at": backup.created_at.isoformat(),
            "updated_at": backup.updated_at.isoformat(),
            "created_by": backup.created_by,
            "updated_by": backup.updated_by
        } for backup in backups]

class NotificationTemplateService:
    """Service for managing notification templates."""

    @staticmethod
    def create_template(db: Session, template: NotificationTemplateCreate, user_id: int) -> NotificationTemplate:
        """Create a new notification template."""
        db_template = NotificationTemplate(
            **template.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def update_template(db: Session, template_id: int, template: NotificationTemplateUpdate, user_id: int) -> Optional[NotificationTemplate]:
        """Update an existing notification template."""
        db_template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
        if not db_template:
            return None
        
        update_data = template.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        db_template.updated_by = user_id
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[NotificationTemplate]:
        """Get a notification template by ID."""
        return db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()

    @staticmethod
    def get_active_templates(db: Session) -> List[NotificationTemplate]:
        """Get all active notification templates."""
        return db.query(NotificationTemplate).filter(
            NotificationTemplate.is_active == True
        ).all()

    @staticmethod
    def search_templates(db: Session, query: str) -> List[NotificationTemplate]:
        """Search templates by name or description."""
        return db.query(NotificationTemplate).filter(
            or_(
                NotificationTemplate.name.ilike(f"%{query}%"),
                NotificationTemplate.description.ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get template statistics."""
        total_templates = db.query(func.count(NotificationTemplate.id)).scalar()
        active_templates = db.query(func.count(NotificationTemplate.id)).filter(
            NotificationTemplate.is_active == True
        ).scalar()
        inactive_templates = db.query(func.count(NotificationTemplate.id)).filter(
            NotificationTemplate.is_active == False
        ).scalar()

        return {
            "total_templates": total_templates,
            "active_templates": active_templates,
            "inactive_templates": inactive_templates,
            "active_percentage": (active_templates / total_templates * 100) if total_templates > 0 else 0,
            "inactive_percentage": (inactive_templates / total_templates * 100) if total_templates > 0 else 0
        }

    @staticmethod
    def export_templates(db: Session, format: str) -> Any:
        """Export templates in specified format."""
        templates = db.query(NotificationTemplate).all()
        
        if format == "json":
            return [template.to_dict() for template in templates]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Name", "Type", "Channel", "Is Active", "Created At"])
            for template in templates:
                writer.writerow([
                    template.id,
                    template.name,
                    template.type,
                    template.channel,
                    template.is_active,
                    template.created_at.isoformat()
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for templates."""
        try:
            # Process webhook payload
            name = payload.get("name")
            type = payload.get("type")
            channel = payload.get("channel")
            
            if not all([name, type, channel]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create template record
            template = NotificationTemplateCreate(
                name=name,
                type=type,
                channel=channel,
                content=payload.get("content"),
                is_active=payload.get("is_active", True)
            )
            
            db_template = NotificationTemplateService.create_template(db, template, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "template_id": db_template.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for template operations."""
        query = db.query(NotificationTemplate)
        
        if start_date:
            query = query.filter(NotificationTemplate.created_at >= start_date)
        if end_date:
            query = query.filter(NotificationTemplate.created_at <= end_date)
        
        templates = query.order_by(NotificationTemplate.created_at.desc()).all()
        
        return [{
            "id": template.id,
            "name": template.name,
            "type": template.type,
            "channel": template.channel,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "created_by": template.created_by,
            "updated_by": template.updated_by
        } for template in templates]

class ReportService:
    """Service for managing system reports."""

    @staticmethod
    def create_report(db: Session, report: ReportCreate, user_id: int) -> Report:
        """Create a new report."""
        db_report = Report(
            **report.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report

    @staticmethod
    def update_report(db: Session, report_id: int, report: ReportUpdate, user_id: int) -> Optional[Report]:
        """Update an existing report."""
        db_report = db.query(Report).filter(Report.id == report_id).first()
        if not db_report:
            return None
        
        update_data = report.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_report, field, value)
        
        db_report.updated_by = user_id
        db.commit()
        db.refresh(db_report)
        return db_report

    @staticmethod
    def get_report(db: Session, report_id: int) -> Optional[Report]:
        """Get a report by ID."""
        return db.query(Report).filter(Report.id == report_id).first()

    @staticmethod
    def get_pending_reports(db: Session) -> List[Report]:
        """Get all pending reports."""
        return db.query(Report).filter(
            Report.status == 'pending'
        ).all()

    @staticmethod
    def search_reports(db: Session, query: str) -> List[Report]:
        """Search reports by name or description."""
        return db.query(Report).filter(
            or_(
                Report.name.ilike(f"%{query}%"),
                Report.description.ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get report statistics."""
        total_reports = db.query(func.count(Report.id)).scalar()
        pending_reports = db.query(func.count(Report.id)).filter(
            Report.status == 'pending'
        ).scalar()
        completed_reports = db.query(func.count(Report.id)).filter(
            Report.status == 'completed'
        ).scalar()
        failed_reports = db.query(func.count(Report.id)).filter(
            Report.status == 'failed'
        ).scalar()

        return {
            "total_reports": total_reports,
            "pending_reports": pending_reports,
            "completed_reports": completed_reports,
            "failed_reports": failed_reports,
            "pending_percentage": (pending_reports / total_reports * 100) if total_reports > 0 else 0,
            "completed_percentage": (completed_reports / total_reports * 100) if total_reports > 0 else 0,
            "failed_percentage": (failed_reports / total_reports * 100) if total_reports > 0 else 0
        }

    @staticmethod
    def export_reports(db: Session, format: str) -> Any:
        """Export reports in specified format."""
        reports = db.query(Report).all()
        
        if format == "json":
            return [report.to_dict() for report in reports]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Name", "Type", "Status", "Created At", "Updated At"])
            for report in reports:
                writer.writerow([
                    report.id,
                    report.name,
                    report.type,
                    report.status,
                    report.created_at.isoformat(),
                    report.updated_at.isoformat()
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for reports."""
        try:
            # Process webhook payload
            name = payload.get("name")
            type = payload.get("type")
            status = payload.get("status")
            
            if not all([name, type, status]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create report record
            report = ReportCreate(
                name=name,
                type=type,
                status=status,
                description=payload.get("description"),
                parameters=payload.get("parameters", {}),
                result=payload.get("result", {})
            )
            
            db_report = ReportService.create_report(db, report, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "report_id": db_report.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for report operations."""
        query = db.query(Report)
        
        if start_date:
            query = query.filter(Report.created_at >= start_date)
        if end_date:
            query = query.filter(Report.created_at <= end_date)
        
        reports = query.order_by(Report.created_at.desc()).all()
        
        return [{
            "id": report.id,
            "name": report.name,
            "type": report.type,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "created_by": report.created_by,
            "updated_by": report.updated_by
        } for report in reports]

class ReportScheduleService:
    """Service for managing report schedules."""

    @staticmethod
    def create_schedule(db: Session, schedule: ReportScheduleCreate, user_id: int) -> ReportSchedule:
        """Create a new report schedule."""
        db_schedule = ReportSchedule(
            **schedule.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule

    @staticmethod
    def update_schedule(db: Session, schedule_id: int, schedule: ReportScheduleUpdate, user_id: int) -> Optional[ReportSchedule]:
        """Update an existing report schedule."""
        db_schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
        if not db_schedule:
            return None
        
        update_data = schedule.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        
        db_schedule.updated_by = user_id
        db.commit()
        db.refresh(db_schedule)
        return db_schedule

    @staticmethod
    def get_schedule(db: Session, schedule_id: int) -> Optional[ReportSchedule]:
        """Get a report schedule by ID."""
        return db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()

    @staticmethod
    def get_active_schedules(db: Session) -> List[ReportSchedule]:
        """Get all active report schedules."""
        return db.query(ReportSchedule).filter(
            ReportSchedule.is_active == True
        ).all()

    @staticmethod
    def search_schedules(db: Session, query: str) -> List[ReportSchedule]:
        """Search schedules by name or description."""
        return db.query(ReportSchedule).filter(
            or_(
                ReportSchedule.name.ilike(f"%{query}%"),
                ReportSchedule.description.ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get schedule statistics."""
        total_schedules = db.query(func.count(ReportSchedule.id)).scalar()
        active_schedules = db.query(func.count(ReportSchedule.id)).filter(
            ReportSchedule.is_active == True
        ).scalar()
        inactive_schedules = db.query(func.count(ReportSchedule.id)).filter(
            ReportSchedule.is_active == False
        ).scalar()

        return {
            "total_schedules": total_schedules,
            "active_schedules": active_schedules,
            "inactive_schedules": inactive_schedules,
            "active_percentage": (active_schedules / total_schedules * 100) if total_schedules > 0 else 0,
            "inactive_percentage": (inactive_schedules / total_schedules * 100) if total_schedules > 0 else 0
        }

    @staticmethod
    def export_schedules(db: Session, format: str) -> Any:
        """Export schedules in specified format."""
        schedules = db.query(ReportSchedule).all()
        
        if format == "json":
            return [schedule.to_dict() for schedule in schedules]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Name", "Report Type", "Frequency", "Is Active", "Created At"])
            for schedule in schedules:
                writer.writerow([
                    schedule.id,
                    schedule.name,
                    schedule.report_type,
                    schedule.frequency,
                    schedule.is_active,
                    schedule.created_at.isoformat()
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for schedules."""
        try:
            # Process webhook payload
            name = payload.get("name")
            report_type = payload.get("report_type")
            frequency = payload.get("frequency")
            
            if not all([name, report_type, frequency]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create schedule record
            schedule = ReportScheduleCreate(
                name=name,
                report_type=report_type,
                frequency=frequency,
                description=payload.get("description"),
                parameters=payload.get("parameters", {}),
                is_active=payload.get("is_active", True)
            )
            
            db_schedule = ReportScheduleService.create_schedule(db, schedule, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "schedule_id": db_schedule.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for schedule operations."""
        query = db.query(ReportSchedule)
        
        if start_date:
            query = query.filter(ReportSchedule.created_at >= start_date)
        if end_date:
            query = query.filter(ReportSchedule.created_at <= end_date)
        
        schedules = query.order_by(ReportSchedule.created_at.desc()).all()
        
        return [{
            "id": schedule.id,
            "name": schedule.name,
            "report_type": schedule.report_type,
            "frequency": schedule.frequency,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
            "created_by": schedule.created_by,
            "updated_by": schedule.updated_by
        } for schedule in schedules]

class SystemLogService:
    """Service for managing system logs."""

    @staticmethod
    def create_log(db: Session, log: SystemLogCreate, user_id: int) -> SystemLog:
        """Create a new system log."""
        db_log = SystemLog(
            **log.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    @staticmethod
    def get_log(db: Session, log_id: int) -> Optional[SystemLog]:
        """Get a system log by ID."""
        return db.query(SystemLog).filter(SystemLog.id == log_id).first()

    @staticmethod
    def get_component_logs(db: Session, component: str, limit: int = 100) -> List[SystemLog]:
        """Get logs for a specific component."""
        return db.query(SystemLog).filter(
            SystemLog.component == component
        ).order_by(SystemLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_error_logs(db: Session, limit: int = 100) -> List[SystemLog]:
        """Get error logs."""
        return db.query(SystemLog).filter(
            SystemLog.level == 'error'
        ).order_by(SystemLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def search_logs(db: Session, query: str) -> List[SystemLog]:
        """Search logs by component, message, or metadata."""
        return db.query(SystemLog).filter(
            or_(
                SystemLog.component.ilike(f"%{query}%"),
                SystemLog.message.ilike(f"%{query}%"),
                SystemLog.metadata.cast(str).ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get log statistics."""
        total_logs = db.query(func.count(SystemLog.id)).scalar()
        error_logs = db.query(func.count(SystemLog.id)).filter(
            SystemLog.level == 'error'
        ).scalar()
        warning_logs = db.query(func.count(SystemLog.id)).filter(
            SystemLog.level == 'warning'
        ).scalar()
        info_logs = db.query(func.count(SystemLog.id)).filter(
            SystemLog.level == 'info'
        ).scalar()

        return {
            "total_logs": total_logs,
            "error_logs": error_logs,
            "warning_logs": warning_logs,
            "info_logs": info_logs,
            "error_percentage": (error_logs / total_logs * 100) if total_logs > 0 else 0,
            "warning_percentage": (warning_logs / total_logs * 100) if total_logs > 0 else 0,
            "info_percentage": (info_logs / total_logs * 100) if total_logs > 0 else 0
        }

    @staticmethod
    def export_logs(db: Session, format: str) -> Any:
        """Export logs in specified format."""
        logs = db.query(SystemLog).all()
        
        if format == "json":
            return [log.to_dict() for log in logs]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Component", "Level", "Message", "Created At"])
            for log in logs:
                writer.writerow([
                    log.id,
                    log.component,
                    log.level,
                    log.message,
                    log.created_at.isoformat()
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for logs."""
        try:
            # Process webhook payload
            component = payload.get("component")
            level = payload.get("level")
            message = payload.get("message")
            
            if not all([component, level, message]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create log record
            log = SystemLogCreate(
                component=component,
                level=level,
                message=message,
                metadata=payload.get("metadata", {})
            )
            
            db_log = SystemLogService.create_log(db, log, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "log_id": db_log.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for log operations."""
        query = db.query(SystemLog)
        
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        
        logs = query.order_by(SystemLog.created_at.desc()).all()
        
        return [{
            "id": log.id,
            "component": log.component,
            "level": log.level,
            "message": log.message,
            "created_at": log.created_at.isoformat(),
            "updated_at": log.updated_at.isoformat(),
            "created_by": log.created_by,
            "updated_by": log.updated_by
        } for log in logs]

class SystemConfigurationService:
    """Service for managing system configurations."""

    @staticmethod
    def create_config(db: Session, config: SystemConfigurationCreate, user_id: int) -> SystemConfiguration:
        """Create a new system configuration."""
        db_config = SystemConfiguration(
            **config.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    @staticmethod
    def update_config(db: Session, config_id: int, config: SystemConfigurationUpdate, user_id: int) -> Optional[SystemConfiguration]:
        """Update an existing system configuration."""
        db_config = db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
        if not db_config:
            return None
        
        update_data = config.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
        
        db_config.updated_by = user_id
        db.commit()
        db.refresh(db_config)
        return db_config

    @staticmethod
    def get_config(db: Session, config_id: int) -> Optional[SystemConfiguration]:
        """Get a system configuration by ID."""
        return db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()

    @staticmethod
    def get_config_by_key(db: Session, key: str) -> Optional[SystemConfiguration]:
        """Get a system configuration by key."""
        return db.query(SystemConfiguration).filter(SystemConfiguration.key == key).first()

    @staticmethod
    def search_configs(db: Session, query: str) -> List[SystemConfiguration]:
        """Search configurations by key, description, or value."""
        return db.query(SystemConfiguration).filter(
            or_(
                SystemConfiguration.key.ilike(f"%{query}%"),
                SystemConfiguration.description.ilike(f"%{query}%"),
                SystemConfiguration.value.cast(str).ilike(f"%{query}%")
            )
        ).all()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get configuration statistics."""
        total_configs = db.query(func.count(SystemConfiguration.id)).scalar()
        encrypted_configs = db.query(func.count(SystemConfiguration.id)).filter(
            SystemConfiguration.is_encrypted == True
        ).scalar()
        unencrypted_configs = db.query(func.count(SystemConfiguration.id)).filter(
            SystemConfiguration.is_encrypted == False
        ).scalar()

        return {
            "total_configs": total_configs,
            "encrypted_configs": encrypted_configs,
            "unencrypted_configs": unencrypted_configs,
            "encrypted_percentage": (encrypted_configs / total_configs * 100) if total_configs > 0 else 0,
            "unencrypted_percentage": (unencrypted_configs / total_configs * 100) if total_configs > 0 else 0
        }

    @staticmethod
    def export_configs(db: Session, format: str) -> Any:
        """Export configurations in specified format."""
        configs = db.query(SystemConfiguration).all()
        
        if format == "json":
            return [config.to_dict() for config in configs]
        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Key", "Value", "Is Encrypted", "Created At"])
            for config in configs:
                writer.writerow([
                    config.id,
                    config.key,
                    config.value if not config.is_encrypted else "[ENCRYPTED]",
                    config.is_encrypted,
                    config.created_at.isoformat()
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def handle_webhook(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook notifications for configurations."""
        try:
            # Process webhook payload
            key = payload.get("key")
            value = payload.get("value")
            is_encrypted = payload.get("is_encrypted", False)
            
            if not all([key, value]):
                raise ValueError("Missing required fields in webhook payload")
            
            # Create configuration record
            config = SystemConfigurationCreate(
                key=key,
                value=value,
                description=payload.get("description"),
                is_encrypted=is_encrypted,
                metadata=payload.get("metadata", {})
            )
            
            db_config = SystemConfigurationService.create_config(db, config, 0)  # System user
            
            return {
                "status": "success",
                "message": "Webhook processed successfully",
                "config_id": db_config.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    @staticmethod
    def get_audit_logs(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get audit logs for configuration operations."""
        query = db.query(SystemConfiguration)
        
        if start_date:
            query = query.filter(SystemConfiguration.created_at >= start_date)
        if end_date:
            query = query.filter(SystemConfiguration.created_at <= end_date)
        
        configs = query.order_by(SystemConfiguration.created_at.desc()).all()
        
        return [{
            "id": config.id,
            "key": config.key,
            "is_encrypted": config.is_encrypted,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "created_by": config.created_by,
            "updated_by": config.updated_by
        } for config in configs]

class SystemMetricService:
    """Service for managing system metrics."""

    @staticmethod
    def create_metric(db: Session, metric: SystemMetricCreate, user_id: int) -> SystemMetric:
        """Create a new system metric."""
        db_metric = SystemMetric(
            **metric.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        db.add(db_metric)
        db.commit()
        db.refresh(db_metric)
        return db_metric

    @staticmethod
    def update_metric(db: Session, metric_id: int, metric: SystemMetricUpdate, user_id: int) -> Optional[SystemMetric]:
        """Update an existing system metric."""
        db_metric = db.query(SystemMetric).filter(SystemMetric.id == metric_id).first()
        if not db_metric:
            return None
        
        update_data = metric.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_metric, field, value)
        
        db_metric.updated_by = user_id
        db.commit()
        db.refresh(db_metric)
        return db_metric

    @staticmethod
    def get_metric(db: Session, metric_id: int) -> Optional[SystemMetric]:
        """Get a system metric by ID."""
        return db.query(SystemMetric).filter(SystemMetric.id == metric_id).first()

    @staticmethod
    def get_metric_history(db: Session, metric_name: str, hours: int = 24) -> List[SystemMetric]:
        """Get metric history for a specific metric name."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return db.query(SystemMetric).filter(
            SystemMetric.metric_name == metric_name,
            SystemMetric.timestamp >= cutoff
        ).order_by(SystemMetric.timestamp.asc()).all() 