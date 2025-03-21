"""
Security monitoring service for real-time security monitoring and alerts.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.models.security import SecurityEvent
from ..core.config import settings
from ..core.exceptions import SecurityError

class SecurityMonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.alert_thresholds = {
            "failed_login": 5,  # 5 failed attempts
            "api_errors": 10,  # 10 errors per minute
            "suspicious_ip": 3,  # 3 suspicious events
            "critical_events": 1  # 1 critical event
        }
        self.monitoring_tasks = []

    async def start_monitoring(self):
        """Start security monitoring tasks."""
        try:
            # Start monitoring tasks
            self.monitoring_tasks = [
                asyncio.create_task(self._monitor_failed_logins()),
                asyncio.create_task(self._monitor_api_errors()),
                asyncio.create_task(self._monitor_suspicious_ips()),
                asyncio.create_task(self._monitor_critical_events())
            ]
            
            # Start alert processing
            self.monitoring_tasks.append(
                asyncio.create_task(self._process_alerts())
            )
            
        except Exception as e:
            raise SecurityError(f"Failed to start security monitoring: {str(e)}")

    async def stop_monitoring(self):
        """Stop security monitoring tasks."""
        try:
            # Cancel all monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            self.monitoring_tasks = []
            
        except Exception as e:
            raise SecurityError(f"Failed to stop security monitoring: {str(e)}")

    async def _monitor_failed_logins(self):
        """Monitor failed login attempts."""
        while True:
            try:
                # Get failed login attempts in the last 5 minutes
                start_time = datetime.utcnow() - timedelta(minutes=5)
                failed_logins = self.db.query(SecurityEvent)\
                    .filter(
                        SecurityEvent.event_type == "login_failure",
                        SecurityEvent.created_at >= start_time
                    )\
                    .count()
                
                # Check threshold
                if failed_logins >= self.alert_thresholds["failed_login"]:
                    await self._create_alert(
                        "high",
                        "Multiple failed login attempts detected",
                        {
                            "event_type": "failed_login",
                            "count": failed_logins,
                            "threshold": self.alert_thresholds["failed_login"]
                        }
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error monitoring failed logins: {str(e)}")
                await asyncio.sleep(60)

    async def _monitor_api_errors(self):
        """Monitor API error rates."""
        while True:
            try:
                # Get API errors in the last minute
                start_time = datetime.utcnow() - timedelta(minutes=1)
                api_errors = self.db.query(SecurityEvent)\
                    .filter(
                        SecurityEvent.event_type == "api_error",
                        SecurityEvent.created_at >= start_time
                    )\
                    .count()
                
                # Check threshold
                if api_errors >= self.alert_thresholds["api_errors"]:
                    await self._create_alert(
                        "medium",
                        "High API error rate detected",
                        {
                            "event_type": "api_errors",
                            "count": api_errors,
                            "threshold": self.alert_thresholds["api_errors"]
                        }
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error monitoring API errors: {str(e)}")
                await asyncio.sleep(60)

    async def _monitor_suspicious_ips(self):
        """Monitor suspicious IP addresses."""
        while True:
            try:
                # Get suspicious events in the last hour
                start_time = datetime.utcnow() - timedelta(hours=1)
                suspicious_events = self.db.query(
                    SecurityEvent.ip_address,
                    func.count(SecurityEvent.id)
                ).filter(
                    SecurityEvent.severity == "warning",
                    SecurityEvent.created_at >= start_time
                ).group_by(
                    SecurityEvent.ip_address
                ).all()
                
                # Check each IP
                for ip, count in suspicious_events:
                    if count >= self.alert_thresholds["suspicious_ip"]:
                        await self._create_alert(
                            "medium",
                            f"Suspicious activity from IP: {ip}",
                            {
                                "event_type": "suspicious_ip",
                                "ip_address": ip,
                                "event_count": count,
                                "threshold": self.alert_thresholds["suspicious_ip"]
                            }
                        )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Error monitoring suspicious IPs: {str(e)}")
                await asyncio.sleep(300)

    async def _monitor_critical_events(self):
        """Monitor critical security events."""
        while True:
            try:
                # Get critical events in the last minute
                start_time = datetime.utcnow() - timedelta(minutes=1)
                critical_events = self.db.query(SecurityEvent)\
                    .filter(
                        SecurityEvent.severity == "critical",
                        SecurityEvent.created_at >= start_time
                    )\
                    .all()
                
                # Check for critical events
                if critical_events:
                    for event in critical_events:
                        await self._create_alert(
                            "critical",
                            f"Critical security event: {event.description}",
                            {
                                "event_type": "critical_event",
                                "event_id": event.id,
                                "description": event.description,
                                "ip_address": event.ip_address,
                                "user_id": event.user_id
                            }
                        )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error monitoring critical events: {str(e)}")
                await asyncio.sleep(60)

    async def _create_alert(self, severity: str, message: str, details: Dict[str, Any]):
        """Create a security alert."""
        try:
            # Create alert event
            event = SecurityEvent(
                event_type="security_alert",
                severity=severity,
                description=message,
                metadata=details
            )
            
            self.db.add(event)
            self.db.commit()
            
            # Send alert notification
            await self._send_alert_notification(severity, message, details)
            
        except Exception as e:
            self.db.rollback()
            print(f"Error creating alert: {str(e)}")

    async def _send_alert_notification(self, severity: str, message: str, details: Dict[str, Any]):
        """Send alert notification through configured channels."""
        try:
            # TODO: Implement notification sending through configured channels
            # (email, SMS, webhook, etc.)
            print(f"Security Alert [{severity.upper()}]: {message}")
            print(f"Details: {details}")
            
        except Exception as e:
            print(f"Error sending alert notification: {str(e)}")

    async def _process_alerts(self):
        """Process and manage security alerts."""
        while True:
            try:
                # Get unprocessed alerts
                alerts = self.db.query(SecurityEvent)\
                    .filter(
                        SecurityEvent.event_type == "security_alert",
                        SecurityEvent.processed == False
                    )\
                    .all()
                
                # Process each alert
                for alert in alerts:
                    # Mark alert as processed
                    alert.processed = True
                    alert.processed_at = datetime.utcnow()
                
                self.db.commit()
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                print(f"Error processing alerts: {str(e)}")
                await asyncio.sleep(60)

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current security monitoring status."""
        try:
            # Get monitoring metrics
            metrics = {
                "active_monitors": len(self.monitoring_tasks),
                "alert_thresholds": self.alert_thresholds,
                "recent_alerts": await self._get_recent_alerts(),
                "monitoring_stats": await self._get_monitoring_stats()
            }
            
            return metrics
            
        except Exception as e:
            raise SecurityError(f"Failed to get monitoring status: {str(e)}")

    async def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent security alerts."""
        try:
            alerts = self.db.query(SecurityEvent)\
                .filter(SecurityEvent.event_type == "security_alert")\
                .order_by(desc(SecurityEvent.created_at))\
                .limit(limit)\
                .all()
            
            return [
                {
                    "id": alert.id,
                    "severity": alert.severity,
                    "message": alert.description,
                    "details": json.loads(alert.metadata) if alert.metadata else None,
                    "created_at": alert.created_at.isoformat(),
                    "processed": alert.processed,
                    "processed_at": alert.processed_at.isoformat() if alert.processed_at else None
                }
                for alert in alerts
            ]
            
        except Exception as e:
            raise SecurityError(f"Failed to get recent alerts: {str(e)}")

    async def _get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        try:
            # Get stats for the last 24 hours
            start_time = datetime.utcnow() - timedelta(hours=24)
            
            stats = {
                "total_alerts": self.db.query(SecurityEvent)\
                    .filter(
                        SecurityEvent.event_type == "security_alert",
                        SecurityEvent.created_at >= start_time
                    )\
                    .count(),
                "alerts_by_severity": dict(
                    self.db.query(
                        SecurityEvent.severity,
                        func.count(SecurityEvent.id)
                    ).filter(
                        SecurityEvent.event_type == "security_alert",
                        SecurityEvent.created_at >= start_time
                    ).group_by(
                        SecurityEvent.severity
                    ).all()
                ),
                "processed_alerts": self.db.query(SecurityEvent)\
                    .filter(
                        SecurityEvent.event_type == "security_alert",
                        SecurityEvent.processed == True,
                        SecurityEvent.created_at >= start_time
                    )\
                    .count()
            }
            
            return stats
            
        except Exception as e:
            raise SecurityError(f"Failed to get monitoring stats: {str(e)}") 