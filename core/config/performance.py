from typing import Any, Dict, List, Optional
from prometheus_client import Counter, Gauge, Histogram, Summary
from app.core.cache import cache
import psutil
import time
from datetime import datetime

class PerformanceMonitor:
    """Performance monitoring system with metrics collection and alerting."""
    
    def __init__(self):
        """Initialize performance monitor with Prometheus metrics."""
        # Request metrics
        self.request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )
        self.request_latency = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"]
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            "cache_hits_total",
            "Total cache hits"
        )
        self.cache_misses = Counter(
            "cache_misses_total",
            "Total cache misses"
        )
        
        # Database metrics
        self.db_query_count = Counter(
            "db_queries_total",
            "Total database queries",
            ["operation"]
        )
        self.db_query_latency = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"]
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            "system_cpu_usage_percent",
            "CPU usage percentage"
        )
        self.memory_usage = Gauge(
            "system_memory_usage_bytes",
            "Memory usage in bytes"
        )
        self.disk_usage = Gauge(
            "system_disk_usage_bytes",
            "Disk usage in bytes"
        )
        
        # Error metrics
        self.error_count = Counter(
            "errors_total",
            "Total errors",
            ["type"]
        )
        
        # Alert thresholds
        self.alert_thresholds = {
            "cpu": 80.0,  # 80% CPU usage
            "memory": 85.0,  # 85% memory usage
            "disk": 90.0,  # 90% disk usage
            "latency": 1.0,  # 1 second request latency
            "errors": 10  # 10 errors per minute
        }
        
    async def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ) -> None:
        """Record HTTP request metrics."""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.request_latency.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Check for latency alerts
        if duration > self.alert_thresholds["latency"]:
            await self.send_alert(
                "high_latency",
                f"High latency detected: {duration:.2f}s for {method} {endpoint}"
            )
            
    async def record_cache_metrics(
        self,
        hits: int,
        misses: int
    ) -> None:
        """Record cache performance metrics."""
        self.cache_hits.inc(hits)
        self.cache_misses.inc(misses)
        
    async def record_db_metrics(
        self,
        operation: str,
        duration: float
    ) -> None:
        """Record database performance metrics."""
        self.db_query_count.labels(operation=operation).inc()
        self.db_query_latency.labels(operation=operation).observe(duration)
        
    async def record_system_metrics(self) -> None:
        """Record system resource usage metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.used)
        
        # Disk usage
        disk = psutil.disk_usage("/")
        self.disk_usage.set(disk.used)
        
        # Check for resource alerts
        if cpu_percent > self.alert_thresholds["cpu"]:
            await self.send_alert(
                "high_cpu",
                f"High CPU usage detected: {cpu_percent}%"
            )
            
        if memory.percent > self.alert_thresholds["memory"]:
            await self.send_alert(
                "high_memory",
                f"High memory usage detected: {memory.percent}%"
            )
            
        if disk.percent > self.alert_thresholds["disk"]:
            await self.send_alert(
                "high_disk",
                f"High disk usage detected: {disk.percent}%"
            )
            
    async def record_error(self, error_type: str) -> None:
        """Record error metrics."""
        self.error_count.labels(type=error_type).inc()
        
        # Check for error rate alerts
        error_count = self.error_count.labels(type=error_type)._value.get()
        if error_count > self.alert_thresholds["errors"]:
            await self.send_alert(
                "high_errors",
                f"High error rate detected: {error_count} errors for {error_type}"
            )
            
    async def send_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning"
    ) -> None:
        """Send alert to monitoring system."""
        try:
            alert = {
                "type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store alert in cache for persistence
            await cache.set(
                f"alert:{alert_type}:{datetime.now().timestamp()}",
                alert,
                expire=3600  # 1 hour
            )
            
            # TODO: Send alert to notification system
            # This will be implemented in the notification service
            
        except Exception as e:
            # Log error but don't raise to prevent cascading failures
            pass
            
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            "requests": {
                "total": self.request_count._value.get(),
                "latency": self.request_latency._sum.get() / self.request_latency._count.get()
                if self.request_latency._count.get() > 0
                else 0
            },
            "cache": {
                "hits": self.cache_hits._value.get(),
                "misses": self.cache_misses._value.get()
            },
            "database": {
                "queries": self.db_query_count._value.get(),
                "latency": self.db_query_latency._sum.get() / self.db_query_latency._count.get()
                if self.db_query_latency._count.get() > 0
                else 0
            },
            "system": {
                "cpu": self.cpu_usage._value.get(),
                "memory": self.memory_usage._value.get(),
                "disk": self.disk_usage._value.get()
            },
            "errors": self.error_count._value.get()
        }
        
    async def get_alerts(
        self,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active alerts."""
        try:
            # Get all alert keys
            alert_keys = await cache.keys("alert:*")
            
            alerts = []
            for key in alert_keys:
                alert = await cache.get(key)
                if alert:
                    if alert_type and alert["type"] != alert_type:
                        continue
                    if severity and alert["severity"] != severity:
                        continue
                    alerts.append(alert)
                    
            return sorted(
                alerts,
                key=lambda x: x["timestamp"],
                reverse=True
            )
        except Exception as e:
            return []
            
    async def clear_alerts(self) -> None:
        """Clear all active alerts."""
        try:
            alert_keys = await cache.keys("alert:*")
            for key in alert_keys:
                await cache.delete(key)
        except Exception as e:
            pass 