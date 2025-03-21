"""
Alert service for MoonVPN Telegram Bot.

This module provides functionality for managing system alerts and notifications.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from fastapi import HTTPException

from app.core.database.models import (
    Server, Alert, AlertHistory, AlertRule,
    AlertSeverity, AlertStatus, AlertType
)
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class AlertService:
    """Service for managing system alerts and notifications."""
    
    def __init__(self):
        # Default thresholds for different metrics
        self.default_thresholds = {
            "cpu": {
                "warning": 70,  # CPU usage percentage
                "critical": 90
            },
            "memory": {
                "warning": 80,  # Memory usage percentage
                "critical": 95
            },
            "disk": {
                "warning": 85,  # Disk usage percentage
                "critical": 95
            },
            "uptime": {
                "warning": 7,  # Days
                "critical": 30
            },
            "traffic": {
                "warning": 1000,  # MB/s
                "critical": 5000
            },
            "connections": {
                "warning": 1000,  # Active connections
                "critical": 5000
            },
            "error_rate": {
                "warning": 5,  # Errors per minute
                "critical": 20
            }
        }
        
        # Alert severity levels with emojis
        self.severity_levels = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚡",
            "low": "ℹ️"
        }
        
        # Alert type emojis
        self.type_emojis = {
            "system": "⚙️",
            "security": "🔒",
            "performance": "⚡",
            "network": "🌐",
            "database": "🗄️",
            "backup": "💾",
            "user": "👤",
            "payment": "💳",
            "other": "📝"
        }
        
        # Alert status emojis
        self.status_emojis = {
            "active": "🔴",
            "resolved": "✅",
            "acknowledged": "👁️",
            "ignored": "⏭️"
        }
        
        # Alert severity colors for UI
        self.severity_colors = {
            "critical": "#FF0000",
            "high": "#FFA500",
            "medium": "#FFFF00",
            "low": "#00FF00"
        }
    
    async def check_server_health(self, server_id: int, db: Session) -> Dict[str, Any]:
        """Check server health and generate alerts if needed."""
        try:
            # Get server info
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            # Get server-specific thresholds
            thresholds = await self._get_server_thresholds(server_id, db)
            
            # Get server metrics from panel
            metrics = await self._get_server_metrics(server)
            
            alerts = []
            
            # Check CPU usage
            if metrics["cpu_usage"] >= thresholds["cpu"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="performance",
                    message=f"Critical CPU usage: {metrics['cpu_usage']}%",
                    details={"metric": "cpu", "value": metrics["cpu_usage"]},
                    severity="critical"
                ))
            elif metrics["cpu_usage"] >= thresholds["cpu"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="performance",
                    message=f"High CPU usage: {metrics['cpu_usage']}%",
                    details={"metric": "cpu", "value": metrics["cpu_usage"]},
                    severity="high"
                ))
            
            # Check memory usage
            if metrics["memory_usage"] >= thresholds["memory"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="performance",
                    message=f"Critical memory usage: {metrics['memory_usage']}%",
                    details={"metric": "memory", "value": metrics["memory_usage"]},
                    severity="critical"
                ))
            elif metrics["memory_usage"] >= thresholds["memory"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="performance",
                    message=f"High memory usage: {metrics['memory_usage']}%",
                    details={"metric": "memory", "value": metrics["memory_usage"]},
                    severity="high"
                ))
            
            # Check disk usage
            if metrics["disk_usage"] >= thresholds["disk"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="performance",
                    message=f"Critical disk usage: {metrics['disk_usage']}%",
                    details={"metric": "disk", "value": metrics["disk_usage"]},
                    severity="critical"
                ))
            elif metrics["disk_usage"] >= thresholds["disk"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="performance",
                    message=f"High disk usage: {metrics['disk_usage']}%",
                    details={"metric": "disk", "value": metrics["disk_usage"]},
                    severity="high"
                ))
            
            # Check uptime
            uptime_days = (datetime.now() - server.last_restart).days
            if uptime_days >= thresholds["uptime"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="system",
                    message=f"Server uptime critical: {uptime_days} days",
                    details={"metric": "uptime", "value": uptime_days},
                    severity="critical"
                ))
            elif uptime_days >= thresholds["uptime"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="system",
                    message=f"Server uptime warning: {uptime_days} days",
                    details={"metric": "uptime", "value": uptime_days},
                    severity="high"
                ))
            
            # Check traffic rate
            if metrics["traffic_rate"] >= thresholds["traffic"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="network",
                    message=f"Critical traffic rate: {metrics['traffic_rate']} MB/s",
                    details={"metric": "traffic", "value": metrics["traffic_rate"]},
                    severity="critical"
                ))
            elif metrics["traffic_rate"] >= thresholds["traffic"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="network",
                    message=f"High traffic rate: {metrics['traffic_rate']} MB/s",
                    details={"metric": "traffic", "value": metrics["traffic_rate"]},
                    severity="high"
                ))
            
            # Check active connections
            if metrics["active_connections"] >= thresholds["connections"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="network",
                    message=f"Critical number of active connections: {metrics['active_connections']}",
                    details={"metric": "connections", "value": metrics["active_connections"]},
                    severity="critical"
                ))
            elif metrics["active_connections"] >= thresholds["connections"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="network",
                    message=f"High number of active connections: {metrics['active_connections']}",
                    details={"metric": "connections", "value": metrics["active_connections"]},
                    severity="high"
                ))
            
            # Check error rate
            if metrics["error_rate"] >= thresholds["error_rate"]["critical"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="system",
                    message=f"Critical error rate: {metrics['error_rate']} errors/min",
                    details={"metric": "error_rate", "value": metrics["error_rate"]},
                    severity="critical"
                ))
            elif metrics["error_rate"] >= thresholds["error_rate"]["warning"]:
                alerts.append(await self._create_alert(
                    db=db,
                    server_id=server_id,
                    alert_type="system",
                    message=f"High error rate: {metrics['error_rate']} errors/min",
                    details={"metric": "error_rate", "value": metrics["error_rate"]},
                    severity="high"
                ))
            
            return {
                "server_id": server_id,
                "server_name": server.name,
                "timestamp": datetime.now(),
                "metrics": metrics,
                "thresholds": thresholds,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Error checking server health for server {server_id}: {str(e)}")
            raise
    
    async def _get_server_thresholds(self, server_id: int, db: Session) -> Dict[str, Any]:
        """Get server-specific thresholds or use defaults."""
        try:
            # Get server-specific thresholds
            rules = db.query(AlertRule).filter(
                AlertRule.server_id == server_id
            ).all()
            
            if rules:
                # Convert rules to threshold format
                thresholds = {}
                for rule in rules:
                    if rule.metric not in thresholds:
                        thresholds[rule.metric] = {}
                    thresholds[rule.metric][rule.severity] = rule.threshold
                return thresholds
            
            return self.default_thresholds
            
        except Exception as e:
            logger.error(f"Error getting server thresholds for server {server_id}: {str(e)}")
            return self.default_thresholds
    
    async def _get_server_metrics(self, server: Server) -> Dict[str, Any]:
        """Get server metrics from panel."""
        try:
            # TODO: Implement panel API call to get server metrics
            # This is a placeholder that should be replaced with actual panel API integration
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "traffic_rate": 0,
                "active_connections": 0,
                "error_rate": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting server metrics for server {server.id}: {str(e)}")
            raise
    
    async def _create_alert(
        self,
        db: Session,
        server_id: int,
        alert_type: str,
        message: str,
        details: Dict[str, Any],
        severity: str
    ) -> Dict[str, Any]:
        """Create a new alert and add to history."""
        try:
            # Validate alert type and severity
            if alert_type not in self.type_emojis:
                raise ValueError(f"Invalid alert type: {alert_type}")
            if severity not in self.severity_levels:
                raise ValueError(f"Invalid severity level: {severity}")
            
            # Create alert
            alert = Alert(
                server_id=server_id,
                alert_type=alert_type,
                message=message,
                details=details,
                severity=severity,
                status="active",
                created_at=datetime.now()
            )
            db.add(alert)
            
            # Create history record
            history = AlertHistory(
                alert_id=alert.id,
                server_id=server_id,
                alert_type=alert_type,
                message=message,
                details=details,
                severity=severity,
                status="active",
                created_at=datetime.now()
            )
            db.add(history)
            
            db.commit()
            
            return {
                "id": alert.id,
                "server_id": server_id,
                "alert_type": alert_type,
                "message": message,
                "details": details,
                "severity": severity,
                "status": "active",
                "created_at": alert.created_at,
                "type_emoji": self.type_emojis.get(alert_type, "📝"),
                "severity_emoji": self.severity_levels.get(severity, "⚪"),
                "status_emoji": self.status_emojis.get("active", "⚪"),
                "severity_color": self.severity_colors.get(severity, "#000000")
            }
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise
    
    async def get_active_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        try:
            alerts = db.query(Alert).filter(
                Alert.status == "active"
            ).order_by(
                Alert.created_at.desc()
            ).all()
            
            return [
                {
                    "id": alert.id,
                    "server_id": alert.server_id,
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "details": alert.details,
                    "severity": alert.severity,
                    "status": alert.status,
                    "created_at": alert.created_at,
                    "type_emoji": self.type_emojis.get(alert.alert_type, "📝"),
                    "severity_emoji": self.severity_levels.get(alert.severity, "⚪"),
                    "status_emoji": self.status_emojis.get(alert.status, "⚪"),
                    "severity_color": self.severity_colors.get(alert.severity, "#000000")
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            raise
    
    async def get_alert_history(
        self,
        db: Session,
        server_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get alert history with optional filters."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            query = db.query(AlertHistory).filter(
                AlertHistory.created_at >= start_date
            )
            
            if server_id:
                query = query.filter(AlertHistory.server_id == server_id)
            if alert_type:
                query = query.filter(AlertHistory.alert_type == alert_type)
            if severity:
                query = query.filter(AlertHistory.severity == severity)
            
            history = query.order_by(
                AlertHistory.created_at.desc()
            ).all()
            
            return [
                {
                    "id": record.id,
                    "alert_id": record.alert_id,
                    "server_id": record.server_id,
                    "alert_type": record.alert_type,
                    "message": record.message,
                    "details": record.details,
                    "severity": record.severity,
                    "status": record.status,
                    "created_at": record.created_at,
                    "type_emoji": self.type_emojis.get(record.alert_type, "📝"),
                    "severity_emoji": self.severity_levels.get(record.severity, "⚪"),
                    "status_emoji": self.status_emojis.get(record.status, "⚪"),
                    "severity_color": self.severity_colors.get(record.severity, "#000000")
                }
                for record in history
            ]
            
        except Exception as e:
            logger.error(f"Error getting alert history: {str(e)}")
            raise
    
    async def resolve_alert(self, alert_id: int, db: Session) -> Dict[str, Any]:
        """Resolve an alert and update history."""
        try:
            # Get alert
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            # Update alert status
            alert.status = "resolved"
            alert.resolved_at = datetime.now()
            
            # Create history record
            history = AlertHistory(
                alert_id=alert.id,
                server_id=alert.server_id,
                alert_type=alert.alert_type,
                message=alert.message,
                details=alert.details,
                severity=alert.severity,
                status="resolved",
                created_at=datetime.now()
            )
            db.add(history)
            
            db.commit()
            
            return {
                "id": alert.id,
                "server_id": alert.server_id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "details": alert.details,
                "severity": alert.severity,
                "status": alert.status,
                "created_at": alert.created_at,
                "resolved_at": alert.resolved_at,
                "type_emoji": self.type_emojis.get(alert.alert_type, "📝"),
                "severity_emoji": self.severity_levels.get(alert.severity, "⚪"),
                "status_emoji": self.status_emojis.get(alert.status, "⚪"),
                "severity_color": self.severity_colors.get(alert.severity, "#000000")
            }
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {str(e)}")
            raise
    
    async def get_alert_stats(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Get alert statistics for the specified period."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get total alerts
            total_alerts = db.query(AlertHistory).filter(
                AlertHistory.created_at >= start_date
            ).count()
            
            # Get alerts by type
            alerts_by_type = db.query(
                AlertHistory.alert_type,
                func.count(AlertHistory.id).label('count')
            ).filter(
                AlertHistory.created_at >= start_date
            ).group_by(
                AlertHistory.alert_type
            ).all()
            
            # Get alerts by severity
            alerts_by_severity = db.query(
                AlertHistory.severity,
                func.count(AlertHistory.id).label('count')
            ).filter(
                AlertHistory.created_at >= start_date
            ).group_by(
                AlertHistory.severity
            ).all()
            
            # Get alerts by server
            alerts_by_server = db.query(
                AlertHistory.server_id,
                func.count(AlertHistory.id).label('count')
            ).filter(
                and_(
                    AlertHistory.created_at >= start_date,
                    AlertHistory.server_id.isnot(None)
                )
            ).group_by(
                AlertHistory.server_id
            ).all()
            
            # Get daily alert counts
            daily_counts = db.query(
                func.date(AlertHistory.created_at).label('date'),
                func.count(AlertHistory.id).label('count'),
                func.count(case((AlertHistory.severity == 'critical', 1), else_=None)).label('critical_count'),
                func.count(case((AlertHistory.severity == 'high', 1), else_=None)).label('high_count')
            ).filter(
                AlertHistory.created_at >= start_date
            ).group_by(
                func.date(AlertHistory.created_at)
            ).all()
            
            return {
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_alerts": total_alerts,
                "alerts_by_type": {
                    alert_type: count
                    for alert_type, count in alerts_by_type
                },
                "alerts_by_severity": {
                    severity: count
                    for severity, count in alerts_by_severity
                },
                "alerts_by_server": {
                    server_id: count
                    for server_id, count in alerts_by_server
                },
                "daily_counts": [
                    {
                        "date": count.date,
                        "total": count.count,
                        "critical": count.critical_count,
                        "high": count.high_count
                    }
                    for count in daily_counts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting alert stats: {str(e)}")
            raise 