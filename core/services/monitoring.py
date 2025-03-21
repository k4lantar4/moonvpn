import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.monitoring import MonitoringMetric, Alert, SystemStatus
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import get_db

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self):
        self.db = next(get_db())
        self.metrics_cache = {}
        self.alert_thresholds = {
            "cpu_usage": 80,
            "memory_usage": 85,
            "disk_usage": 90,
            "error_rate": 5
        }

    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system metrics."""
        try:
            # Collect CPU usage
            cpu_usage = self._get_cpu_usage()
            
            # Collect memory usage
            memory_usage = self._get_memory_usage()
            
            # Collect disk usage
            disk_usage = self._get_disk_usage()
            
            metrics = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "timestamp": time.time()
            }
            
            # Store metrics
            await self.store_metric(MonitoringMetric(
                name="system_metrics",
                value=metrics,
                unit="percentage",
                timestamp=time.time(),
                tags={"type": "system"}
            ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            raise

    async def collect_application_metrics(self) -> Dict[str, float]:
        """Collect application metrics."""
        try:
            # Collect request count
            request_count = self._get_request_count()
            
            # Collect response time
            response_time = self._get_response_time()
            
            # Collect error rate
            error_rate = self._get_error_rate()
            
            metrics = {
                "request_count": request_count,
                "response_time": response_time,
                "error_rate": error_rate,
                "timestamp": time.time()
            }
            
            # Store metrics
            await self.store_metric(MonitoringMetric(
                name="application_metrics",
                value=metrics,
                unit="count",
                timestamp=time.time(),
                tags={"type": "application"}
            ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {str(e)}")
            raise

    async def collect_custom_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> MonitoringMetric:
        """Collect custom metric."""
        try:
            metric = MonitoringMetric(
                name=name,
                value=value,
                unit="custom",
                timestamp=time.time(),
                tags=tags or {}
            )
            
            return await self.store_metric(metric)
            
        except Exception as e:
            logger.error(f"Error collecting custom metric: {str(e)}")
            raise

    async def store_metric(self, metric: MonitoringMetric) -> MonitoringMetric:
        """Store metric in database."""
        try:
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            return metric
            
        except Exception as e:
            logger.error(f"Error storing metric: {str(e)}")
            self.db.rollback()
            raise

    async def get_metric(self, metric_id: int) -> Optional[MonitoringMetric]:
        """Get metric by ID."""
        try:
            return self.db.query(MonitoringMetric).filter(
                MonitoringMetric.id == metric_id
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting metric: {str(e)}")
            raise

    async def aggregate_metrics(
        self,
        name: str,
        interval: str = "1h"
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by time interval."""
        try:
            # Calculate time range
            end_time = time.time()
            if interval == "1h":
                start_time = end_time - 3600
            elif interval == "24h":
                start_time = end_time - 86400
            else:
                start_time = end_time - 3600  # Default to 1h
            
            # Query metrics
            metrics = self.db.query(MonitoringMetric).filter(
                MonitoringMetric.name == name,
                MonitoringMetric.timestamp >= start_time,
                MonitoringMetric.timestamp <= end_time
            ).all()
            
            # Aggregate metrics
            aggregated = []
            current_interval = start_time
            while current_interval < end_time:
                interval_metrics = [
                    m for m in metrics
                    if current_interval <= m.timestamp < current_interval + 300  # 5-minute intervals
                ]
                
                if interval_metrics:
                    aggregated.append({
                        "timestamp": current_interval,
                        "value": sum(m.value for m in interval_metrics) / len(interval_metrics),
                        "count": len(interval_metrics)
                    })
                
                current_interval += 300
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating metrics: {str(e)}")
            raise

    async def create_alert(
        self,
        name: str,
        description: str,
        severity: str = "medium"
    ) -> Alert:
        """Create new alert."""
        try:
            alert = Alert(
                name=name,
                description=description,
                severity=severity,
                status="active",
                created_at=time.time()
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            # Send notification
            await self.send_alert_notification(alert.id)
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            self.db.rollback()
            raise

    async def update_alert_status(
        self,
        alert_id: int,
        status: str
    ) -> Alert:
        """Update alert status."""
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            alert.status = status
            if status == "resolved":
                alert.resolved_at = time.time()
            
            self.db.commit()
            self.db.refresh(alert)
            
            return alert
            
        except Exception as e:
            logger.error(f"Error updating alert status: {str(e)}")
            self.db.rollback()
            raise

    async def get_alert(self, alert_id: int) -> Optional[Alert]:
        """Get alert by ID."""
        try:
            return self.db.query(Alert).filter(
                Alert.id == alert_id
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting alert: {str(e)}")
            raise

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        try:
            return self.db.query(Alert).filter(
                Alert.status == "active"
            ).all()
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            raise

    async def check_system_status(self) -> Dict[str, Any]:
        """Check system status."""
        try:
            # Get latest metrics
            system_metrics = await self.collect_system_metrics()
            app_metrics = await self.collect_application_metrics()
            
            # Check thresholds
            alerts = []
            for metric, value in system_metrics.items():
                if metric in self.alert_thresholds:
                    if value > self.alert_thresholds[metric]:
                        alerts.append({
                            "name": f"High {metric}",
                            "description": f"{metric} is at {value}%",
                            "severity": "high"
                        })
            
            # Get component status
            components = await self.get_component_status()
            
            return {
                "health": "healthy" if not alerts else "warning",
                "metrics": {
                    "system": system_metrics,
                    "application": app_metrics
                },
                "alerts": alerts,
                "components": components,
                "last_check": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error checking system status: {str(e)}")
            raise

    async def get_component_status(self) -> List[Dict[str, Any]]:
        """Get status of system components."""
        try:
            components = [
                {
                    "name": "database",
                    "status": self._check_database_status(),
                    "last_check": time.time()
                },
                {
                    "name": "cache",
                    "status": self._check_cache_status(),
                    "last_check": time.time()
                },
                {
                    "name": "api",
                    "status": self._check_api_status(),
                    "last_check": time.time()
                }
            ]
            
            return components
            
        except Exception as e:
            logger.error(f"Error getting component status: {str(e)}")
            raise

    async def get_status_history(self) -> List[Dict[str, Any]]:
        """Get system status history."""
        try:
            # Get last 24 hours of status checks
            end_time = time.time()
            start_time = end_time - 86400
            
            history = self.db.query(SystemStatus).filter(
                SystemStatus.timestamp >= start_time,
                SystemStatus.timestamp <= end_time
            ).order_by(
                SystemStatus.timestamp.desc()
            ).all()
            
            return [
                {
                    "timestamp": status.timestamp,
                    "health": status.health,
                    "metrics": status.metrics,
                    "alerts": status.alerts
                }
                for status in history
            ]
            
        except Exception as e:
            logger.error(f"Error getting status history: {str(e)}")
            raise

    async def monitor_response_time(self) -> Dict[str, float]:
        """Monitor API response time."""
        try:
            # Get response time metrics
            metrics = await self.aggregate_metrics(
                name="response_time",
                interval="1h"
            )
            
            if not metrics:
                return {
                    "average": 0,
                    "p95": 0,
                    "p99": 0
                }
            
            # Calculate statistics
            values = [m["value"] for m in metrics]
            values.sort()
            
            return {
                "average": sum(values) / len(values),
                "p95": values[int(len(values) * 0.95)],
                "p99": values[int(len(values) * 0.99)]
            }
            
        except Exception as e:
            logger.error(f"Error monitoring response time: {str(e)}")
            raise

    async def monitor_throughput(self) -> Dict[str, float]:
        """Monitor system throughput."""
        try:
            # Get request metrics
            metrics = await self.aggregate_metrics(
                name="request_count",
                interval="1h"
            )
            
            if not metrics:
                return {
                    "requests_per_second": 0,
                    "bytes_per_second": 0
                }
            
            # Calculate throughput
            total_requests = sum(m["value"] for m in metrics)
            total_bytes = sum(m.get("bytes", 0) for m in metrics)
            
            return {
                "requests_per_second": total_requests / 3600,
                "bytes_per_second": total_bytes / 3600
            }
            
        except Exception as e:
            logger.error(f"Error monitoring throughput: {str(e)}")
            raise

    async def monitor_resources(self) -> Dict[str, float]:
        """Monitor system resources."""
        try:
            return {
                "cpu": self._get_cpu_usage(),
                "memory": self._get_memory_usage(),
                "disk": self._get_disk_usage()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring resources: {str(e)}")
            raise

    async def collect_logs(self) -> List[Dict[str, Any]]:
        """Collect system logs."""
        try:
            # Get logs from database
            logs = self.db.query(Log).order_by(
                Log.timestamp.desc()
            ).limit(1000).all()
            
            return [
                {
                    "timestamp": log.timestamp,
                    "level": log.level,
                    "message": log.message,
                    "source": log.source
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error collecting logs: {str(e)}")
            raise

    async def analyze_logs(self) -> Dict[str, int]:
        """Analyze system logs."""
        try:
            logs = await self.collect_logs()
            
            return {
                "error_count": len([l for l in logs if l["level"] == "ERROR"]),
                "warning_count": len([l for l in logs if l["level"] == "WARNING"]),
                "info_count": len([l for l in logs if l["level"] == "INFO"])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {str(e)}")
            raise

    async def search_logs(
        self,
        query: str,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search system logs."""
        try:
            logs = await self.collect_logs()
            
            # Filter by level if specified
            if level:
                logs = [l for l in logs if l["level"] == level]
            
            # Search by query
            return [
                l for l in logs
                if query.lower() in l["message"].lower()
            ]
            
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            raise

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for dashboard."""
        try:
            # Get system health
            status = await self.check_system_status()
            
            # Get performance metrics
            performance = {
                "response_time": await self.monitor_response_time(),
                "throughput": await self.monitor_throughput()
            }
            
            # Get active alerts
            alerts = await self.get_active_alerts()
            
            return {
                "system_health": status["health"],
                "performance": performance,
                "alerts": [
                    {
                        "id": alert.id,
                        "name": alert.name,
                        "severity": alert.severity,
                        "created_at": alert.created_at
                    }
                    for alert in alerts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            raise

    async def generate_visualization(
        self,
        metric_name: str,
        time_range: str = "1h"
    ) -> Dict[str, Any]:
        """Generate metric visualization."""
        try:
            # Get metric data
            data = await self.aggregate_metrics(
                name=metric_name,
                interval=time_range
            )
            
            return {
                "data": data,
                "chart_type": "line",
                "metric_name": metric_name,
                "time_range": time_range
            }
            
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            raise

    async def compare_metrics(
        self,
        metric_name: str,
        time_ranges: List[str]
    ) -> List[Dict[str, Any]]:
        """Compare metrics across time ranges."""
        try:
            comparisons = []
            for time_range in time_ranges:
                data = await self.aggregate_metrics(
                    name=metric_name,
                    interval=time_range
                )
                comparisons.append({
                    "time_range": time_range,
                    "data": data
                })
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing metrics: {str(e)}")
            raise

    async def send_alert_notification(
        self,
        alert_id: int,
        channel: str = "email"
    ) -> Dict[str, Any]:
        """Send alert notification."""
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            # Prepare notification
            notification = {
                "alert_id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "severity": alert.severity,
                "channel": channel,
                "timestamp": time.time()
            }
            
            # Send notification based on channel
            if channel == "email":
                await self._send_email_notification(notification)
            elif channel == "slack":
                await self._send_slack_notification(notification)
            
            return {
                "status": "sent",
                "notification": notification
            }
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")
            raise

    async def send_status_notification(
        self,
        status: str,
        channel: str = "slack"
    ) -> Dict[str, Any]:
        """Send status notification."""
        try:
            # Get system status
            system_status = await self.check_system_status()
            
            # Prepare notification
            notification = {
                "status": status,
                "health": system_status["health"],
                "alerts": system_status["alerts"],
                "channel": channel,
                "timestamp": time.time()
            }
            
            # Send notification based on channel
            if channel == "email":
                await self._send_email_notification(notification)
            elif channel == "slack":
                await self._send_slack_notification(notification)
            
            return {
                "status": "sent",
                "notification": notification
            }
            
        except Exception as e:
            logger.error(f"Error sending status notification: {str(e)}")
            raise

    async def get_notification_history(self) -> List[Dict[str, Any]]:
        """Get notification history."""
        try:
            # Get last 24 hours of notifications
            end_time = time.time()
            start_time = end_time - 86400
            
            notifications = self.db.query(Notification).filter(
                Notification.timestamp >= start_time,
                Notification.timestamp <= end_time
            ).order_by(
                Notification.timestamp.desc()
            ).all()
            
            return [
                {
                    "id": n.id,
                    "type": n.type,
                    "channel": n.channel,
                    "status": n.status,
                    "timestamp": n.timestamp
                }
                for n in notifications
            ]
            
        except Exception as e:
            logger.error(f"Error getting notification history: {str(e)}")
            raise

    async def generate_report(self) -> Dict[str, Any]:
        """Generate monitoring report."""
        try:
            # Get system status
            status = await self.check_system_status()
            
            # Get performance metrics
            performance = {
                "response_time": await self.monitor_response_time(),
                "throughput": await self.monitor_throughput(),
                "resources": await self.monitor_resources()
            }
            
            # Get active alerts
            alerts = await self.get_active_alerts()
            
            # Get log analysis
            log_analysis = await self.analyze_logs()
            
            return {
                "summary": {
                    "health": status["health"],
                    "alerts_count": len(alerts),
                    "timestamp": time.time()
                },
                "metrics": performance,
                "alerts": [
                    {
                        "id": alert.id,
                        "name": alert.name,
                        "severity": alert.severity,
                        "created_at": alert.created_at
                    }
                    for alert in alerts
                ],
                "logs": log_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    async def schedule_report(
        self,
        report_type: str,
        recipients: List[str]
    ) -> Dict[str, Any]:
        """Schedule monitoring report."""
        try:
            schedule = ReportSchedule(
                report_type=report_type,
                recipients=recipients,
                next_run=self._calculate_next_run(report_type),
                created_at=time.time()
            )
            
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)
            
            return {
                "schedule_id": schedule.id,
                "report_type": schedule.report_type,
                "recipients": schedule.recipients,
                "next_run": schedule.next_run
            }
            
        except Exception as e:
            logger.error(f"Error scheduling report: {str(e)}")
            self.db.rollback()
            raise

    async def get_report_history(self) -> List[Dict[str, Any]]:
        """Get report history."""
        try:
            # Get last 30 days of reports
            end_time = time.time()
            start_time = end_time - 2592000  # 30 days
            
            reports = self.db.query(Report).filter(
                Report.timestamp >= start_time,
                Report.timestamp <= end_time
            ).order_by(
                Report.timestamp.desc()
            ).all()
            
            return [
                {
                    "id": r.id,
                    "type": r.type,
                    "timestamp": r.timestamp,
                    "status": r.status
                }
                for r in reports
            ]
            
        except Exception as e:
            logger.error(f"Error getting report history: {str(e)}")
            raise

    async def handle_monitoring_failure(self) -> Dict[str, Any]:
        """Handle monitoring system failure."""
        try:
            start_time = time.time()
            
            # Attempt recovery
            success = await self.recover_from_failure()
            
            return {
                "status": "success" if success else "failed",
                "recovery_time": time.time() - start_time,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error handling monitoring failure: {str(e)}")
            raise

    async def recover_from_failure(self) -> bool:
        """Recover from monitoring system failure."""
        try:
            # Check database connection
            if not self._check_database_status():
                return False
            
            # Check cache connection
            if not self._check_cache_status():
                return False
            
            # Check API endpoints
            if not self._check_api_status():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error recovering from failure: {str(e)}")
            return False

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        # Implementation depends on system
        return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage."""
        # Implementation depends on system
        return 0.0

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage."""
        # Implementation depends on system
        return 0.0

    def _get_request_count(self) -> int:
        """Get total request count."""
        # Implementation depends on system
        return 0

    def _get_response_time(self) -> float:
        """Get average response time."""
        # Implementation depends on system
        return 0.0

    def _get_error_rate(self) -> float:
        """Get error rate percentage."""
        # Implementation depends on system
        return 0.0

    def _check_database_status(self) -> bool:
        """Check database connection status."""
        try:
            self.db.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _check_cache_status(self) -> bool:
        """Check cache connection status."""
        # Implementation depends on cache system
        return True

    def _check_api_status(self) -> bool:
        """Check API endpoints status."""
        # Implementation depends on API endpoints
        return True

    def _calculate_next_run(self, report_type: str) -> float:
        """Calculate next report run time."""
        now = time.time()
        if report_type == "daily":
            return now + 86400
        elif report_type == "weekly":
            return now + 604800
        elif report_type == "monthly":
            return now + 2592000
        else:
            return now + 86400  # Default to daily

    async def _send_email_notification(self, notification: Dict[str, Any]) -> None:
        """Send email notification."""
        # Implementation depends on email service
        pass

    async def _send_slack_notification(self, notification: Dict[str, Any]) -> None:
        """Send Slack notification."""
        # Implementation depends on Slack integration
        pass 