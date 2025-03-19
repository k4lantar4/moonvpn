"""
Alert service for MoonVPN Telegram Bot.

This module provides functionality for managing system alerts and notifications.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from fastapi import HTTPException

from app.core.database.models import Server, Alert, AlertHistory, AlertRule
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class AlertService:
    """Service for managing system alerts and notifications."""
    
    def __init__(self):
        # Default thresholds
        self.default_thresholds = {
            "cpu": 80,  # CPU usage threshold (%)
            "memory": 80,  # Memory usage threshold (%)
            "disk": 80,  # Disk usage threshold (%)
            "uptime": 300,  # Minimum uptime (seconds)
            "traffic": 1000,  # Traffic threshold (MB/s)
            "connections": 1000,  # Maximum concurrent connections
            "error_rate": 5  # Error rate threshold (%)
        }
        
        # Alert severity levels
        self.severity_levels = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
    
    async def check_server_health(self, server: Server, db: Session) -> List[Dict[str, Any]]:
        """Check server health and generate alerts if needed."""
        try:
            alerts = []
            
            # Get custom thresholds for the server
            thresholds = await self._get_server_thresholds(server.id, db)
            
            # Check CPU usage
            if server.cpu_usage > thresholds["cpu"]:
                severity = self._calculate_severity(server.cpu_usage, thresholds["cpu"])
                alert = await self._create_alert(
                    db,
                    server.id,
                    "cpu_high",
                    f"CPU usage is high: {server.cpu_usage}%",
                    {
                        "threshold": thresholds["cpu"],
                        "current": server.cpu_usage,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            # Check memory usage
            if server.memory_usage > thresholds["memory"]:
                severity = self._calculate_severity(server.memory_usage, thresholds["memory"])
                alert = await self._create_alert(
                    db,
                    server.id,
                    "memory_high",
                    f"Memory usage is high: {server.memory_usage}%",
                    {
                        "threshold": thresholds["memory"],
                        "current": server.memory_usage,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            # Check disk usage
            if server.disk_usage > thresholds["disk"]:
                severity = self._calculate_severity(server.disk_usage, thresholds["disk"])
                alert = await self._create_alert(
                    db,
                    server.id,
                    "disk_high",
                    f"Disk usage is high: {server.disk_usage}%",
                    {
                        "threshold": thresholds["disk"],
                        "current": server.disk_usage,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            # Check uptime
            if server.uptime < thresholds["uptime"]:
                severity = "critical" if server.uptime < 60 else "high"
                alert = await self._create_alert(
                    db,
                    server.id,
                    "uptime_low",
                    f"Server uptime is low: {server.uptime} seconds",
                    {
                        "threshold": thresholds["uptime"],
                        "current": server.uptime,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            # Check traffic
            if server.traffic_rate > thresholds["traffic"]:
                severity = self._calculate_severity(server.traffic_rate, thresholds["traffic"])
                alert = await self._create_alert(
                    db,
                    server.id,
                    "traffic_high",
                    f"Traffic rate is high: {server.traffic_rate} MB/s",
                    {
                        "threshold": thresholds["traffic"],
                        "current": server.traffic_rate,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            # Check connections
            if server.active_connections > thresholds["connections"]:
                severity = self._calculate_severity(server.active_connections, thresholds["connections"])
                alert = await self._create_alert(
                    db,
                    server.id,
                    "connections_high",
                    f"Active connections are high: {server.active_connections}",
                    {
                        "threshold": thresholds["connections"],
                        "current": server.active_connections,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            # Check error rate
            if server.error_rate > thresholds["error_rate"]:
                severity = self._calculate_severity(server.error_rate, thresholds["error_rate"])
                alert = await self._create_alert(
                    db,
                    server.id,
                    "error_rate_high",
                    f"Error rate is high: {server.error_rate}%",
                    {
                        "threshold": thresholds["error_rate"],
                        "current": server.error_rate,
                        "severity": severity
                    }
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking server health: {str(e)}")
            raise
    
    async def _get_server_thresholds(self, server_id: int, db: Session) -> Dict[str, float]:
        """Get custom thresholds for a server or use defaults."""
        try:
            rules = db.query(AlertRule).filter(
                AlertRule.server_id == server_id
            ).all()
            
            thresholds = self.default_thresholds.copy()
            
            for rule in rules:
                if rule.metric in thresholds:
                    thresholds[rule.metric] = rule.threshold
            
            return thresholds
            
        except Exception as e:
            logger.error(f"Error getting server thresholds: {str(e)}")
            return self.default_thresholds
    
    def _calculate_severity(self, current: float, threshold: float) -> str:
        """Calculate alert severity based on threshold exceedance."""
        exceedance = (current - threshold) / threshold * 100
        
        if exceedance >= 50:
            return "critical"
        elif exceedance >= 25:
            return "high"
        elif exceedance >= 10:
            return "medium"
        else:
            return "low"
    
    async def _create_alert(
        self,
        db: Session,
        server_id: int,
        alert_type: str,
        message: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new alert and add it to history."""
        try:
            # Create alert
            alert = Alert(
                server_id=server_id,
                alert_type=alert_type,
                message=message,
                details=details,
                created_at=datetime.now(),
                status="active",
                severity=details.get("severity", "medium")
            )
            db.add(alert)
            
            # Add to history
            history = AlertHistory(
                server_id=server_id,
                alert_type=alert_type,
                message=message,
                details=details,
                created_at=datetime.now(),
                severity=details.get("severity", "medium")
            )
            db.add(history)
            
            db.commit()
            
            return {
                "id": alert.id,
                "server_id": server_id,
                "alert_type": alert_type,
                "message": message,
                "details": details,
                "created_at": alert.created_at,
                "status": alert.status,
                "severity": alert.severity
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
                    "created_at": alert.created_at,
                    "status": alert.status,
                    "severity": alert.severity,
                    "severity_emoji": self.severity_levels.get(alert.severity, "⚪")
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
        days: int = 7,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alert history with optional filters."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            query = db.query(AlertHistory).filter(
                AlertHistory.created_at >= start_date
            )
            
            if server_id:
                query = query.filter(AlertHistory.server_id == server_id)
            if severity:
                query = query.filter(AlertHistory.severity == severity)
            
            history = query.order_by(
                AlertHistory.created_at.desc()
            ).all()
            
            return [
                {
                    "id": record.id,
                    "server_id": record.server_id,
                    "alert_type": record.alert_type,
                    "message": record.message,
                    "details": record.details,
                    "created_at": record.created_at,
                    "severity": record.severity,
                    "severity_emoji": self.severity_levels.get(record.severity, "⚪")
                }
                for record in history
            ]
            
        except Exception as e:
            logger.error(f"Error getting alert history: {str(e)}")
            raise
    
    async def resolve_alert(self, alert_id: int, db: Session) -> Dict[str, Any]:
        """Mark an alert as resolved."""
        try:
            alert = db.query(Alert).filter(
                and_(
                    Alert.id == alert_id,
                    Alert.status == "active"
                )
            ).first()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            alert.status = "resolved"
            alert.resolved_at = datetime.now()
            
            db.commit()
            
            return {
                "id": alert.id,
                "server_id": alert.server_id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "details": alert.details,
                "created_at": alert.created_at,
                "resolved_at": alert.resolved_at,
                "status": alert.status,
                "severity": alert.severity,
                "severity_emoji": self.severity_levels.get(alert.severity, "⚪")
            }
            
        except Exception as e:
            logger.error(f"Error resolving alert: {str(e)}")
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
            
            # Get alerts by server
            alerts_by_server = db.query(
                AlertHistory.server_id,
                func.count(AlertHistory.id).label('count')
            ).filter(
                AlertHistory.created_at >= start_date
            ).group_by(
                AlertHistory.server_id
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
            
            # Get daily alert counts
            daily_counts = db.query(
                func.date(AlertHistory.created_at).label('date'),
                func.count(AlertHistory.id).label('count'),
                func.count(case((AlertHistory.severity == 'critical', 1), else_=None)).label('critical_count')
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
                "alerts_by_server": {
                    server_id: count
                    for server_id, count in alerts_by_server
                },
                "alerts_by_severity": {
                    severity: count
                    for severity, count in alerts_by_severity
                },
                "daily_counts": [
                    {
                        "date": count.date,
                        "total": count.count,
                        "critical": count.critical_count
                    }
                    for count in daily_counts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting alert stats: {str(e)}")
            raise 