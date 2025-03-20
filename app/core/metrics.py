"""
Prometheus metrics configuration and collection.
"""
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.registry import CollectorRegistry

# Create a custom registry
registry = CollectorRegistry()

# System Resource Metrics
system_cpu_usage = Gauge(
    'system_cpu_usage',
    'System CPU usage percentage',
    registry=registry
)

system_memory_usage = Gauge(
    'system_memory_usage',
    'System memory usage percentage',
    registry=registry
)

system_disk_usage = Gauge(
    'system_disk_usage',
    'System disk usage percentage',
    registry=registry
)

# API Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

api_response_time = Histogram(
    'api_response_time_seconds',
    'API response time in seconds',
    ['endpoint'],
    registry=registry
)

# Database Metrics
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    registry=registry
)

db_active_connections = Gauge(
    'db_active_connections',
    'Number of active database connections',
    registry=registry
)

# VPN Service Metrics
vpn_active_users = Gauge(
    'vpn_active_users',
    'Number of active VPN users',
    registry=registry
)

vpn_traffic_bytes = Counter(
    'vpn_traffic_bytes_total',
    'Total VPN traffic in bytes',
    ['direction'],
    registry=registry
)

# Alert Metrics
active_alerts = Gauge(
    'active_alerts',
    'Number of active alerts',
    ['severity'],
    registry=registry
)

alert_created_total = Counter(
    'alert_created_total',
    'Total number of alerts created',
    ['severity', 'component'],
    registry=registry
)

# Bot Metrics
bot_active_users = Gauge(
    'bot_active_users',
    'Number of active bot users',
    registry=registry
)

bot_commands_total = Counter(
    'bot_commands_total',
    'Total number of bot commands processed',
    ['command'],
    registry=registry
)

# Cache Metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type'],
    registry=registry
)

# Background Task Metrics
background_tasks_total = Counter(
    'background_tasks_total',
    'Total number of background tasks processed',
    ['task_type', 'status'],
    registry=registry
)

task_execution_time = Summary(
    'task_execution_time_seconds',
    'Background task execution time in seconds',
    ['task_type'],
    registry=registry
)

def get_metrics() -> dict:
    """Get all registered metrics."""
    metrics = {}
    for metric in registry._collector_to_names.values():
        if isinstance(metric, MetricWrapperBase):
            metrics[metric._name] = metric._value.get()
    return metrics

def update_system_metrics(cpu_percent: float, memory_percent: float, disk_percent: float) -> None:
    """Update system resource metrics."""
    system_cpu_usage.set(cpu_percent)
    system_memory_usage.set(memory_percent)
    system_disk_usage.set(disk_percent)

def update_api_metrics(method: str, endpoint: str, status: int, response_time: float) -> None:
    """Update API metrics."""
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_response_time.labels(endpoint=endpoint).observe(response_time)

def update_db_metrics(pool_size: int, active_connections: int) -> None:
    """Update database metrics."""
    db_connection_pool_size.set(pool_size)
    db_active_connections.set(active_connections)

def update_vpn_metrics(active_users: int, upload_bytes: int, download_bytes: int) -> None:
    """Update VPN service metrics."""
    vpn_active_users.set(active_users)
    vpn_traffic_bytes.labels(direction='upload').inc(upload_bytes)
    vpn_traffic_bytes.labels(direction='download').inc(download_bytes)

def update_alert_metrics(active_alerts_by_severity: dict, new_alert_severity: str, new_alert_component: str) -> None:
    """Update alert metrics."""
    for severity, count in active_alerts_by_severity.items():
        active_alerts.labels(severity=severity).set(count)
    alert_created_total.labels(severity=new_alert_severity, component=new_alert_component).inc()

def update_bot_metrics(active_users: int, command: str) -> None:
    """Update bot metrics."""
    bot_active_users.set(active_users)
    bot_commands_total.labels(command=command).inc()

def update_cache_metrics(cache_type: str, hit: bool) -> None:
    """Update cache metrics."""
    if hit:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()

def update_background_task_metrics(task_type: str, status: str, execution_time: float) -> None:
    """Update background task metrics."""
    background_tasks_total.labels(task_type=task_type, status=status).inc()
    task_execution_time.labels(task_type=task_type).observe(execution_time)

"""
Metrics collector implementation for service integration.
"""
from typing import Any, Dict, Optional
import time
import logging
from datetime import datetime

from prometheus_client import Counter, Histogram, Gauge, start_http_server
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Prometheus metrics collector implementation."""
    
    def __init__(self):
        self._initialized = False
        
        # Operation metrics
        self.operation_duration = Histogram(
            "operation_duration_seconds",
            "Duration of operations in seconds",
            ["operation"]
        )
        self.operation_total = Counter(
            "operation_total",
            "Total number of operations",
            ["operation", "status"]
        )
        
        # Error metrics
        self.error_total = Counter(
            "error_total",
            "Total number of errors",
            ["operation", "type"]
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            "cache_hits_total",
            "Total number of cache hits",
            ["key"]
        )
        self.cache_misses = Counter(
            "cache_misses_total",
            "Total number of cache misses",
            ["key"]
        )
        self.cache_operations = Counter(
            "cache_operations_total",
            "Total number of cache operations",
            ["operation", "status"]
        )
        
        # Resource metrics
        self.resource_total = Gauge(
            "resource_total",
            "Total number of resources",
            ["resource_type"]
        )
        self.resource_operations = Counter(
            "resource_operations_total",
            "Total number of resource operations",
            ["resource_type", "operation", "status"]
        )
        
        # Service metrics
        self.service_health = Gauge(
            "service_health",
            "Health status of services",
            ["service"]
        )
        self.service_response_time = Histogram(
            "service_response_time_seconds",
            "Response time of services in seconds",
            ["service", "operation"]
        )
        
    async def initialize(self) -> None:
        """Initialize metrics server."""
        if self._initialized:
            return
            
        try:
            start_http_server(
                port=settings.METRICS_PORT,
                addr=settings.METRICS_HOST
            )
            self._initialized = True
            logger.info(
                f"Metrics server started on {settings.METRICS_HOST}:{settings.METRICS_PORT}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize metrics server: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Metrics initialization failed: {str(e)}"
            )
            
    async def cleanup(self) -> None:
        """Cleanup metrics collector."""
        self._initialized = False
        logger.info("Metrics collector cleaned up")
        
    def _check_initialized(self) -> None:
        """Check if metrics collector is initialized."""
        if not self._initialized:
            raise HTTPException(
                status_code=500,
                detail="Metrics collector not initialized"
            )
            
    async def record_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True
    ) -> None:
        """Record operation metrics."""
        self._check_initialized()
        
        try:
            # Record duration
            self.operation_duration.labels(operation=operation).observe(duration)
            
            # Record total operations
            status = "success" if success else "failure"
            self.operation_total.labels(
                operation=operation,
                status=status
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record operation metrics: {str(e)}")
            
    async def record_error(self, operation: str, error: str) -> None:
        """Record error metrics."""
        self._check_initialized()
        
        try:
            error_type = error.split(":")[0] if ":" in error else "unknown"
            self.error_total.labels(
                operation=operation,
                type=error_type
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {str(e)}")
            
    async def record_cache_hit(self, key: str) -> None:
        """Record cache hit."""
        self._check_initialized()
        
        try:
            self.cache_hits.labels(key=key).inc()
            self.cache_operations.labels(
                operation="get",
                status="hit"
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record cache hit metrics: {str(e)}")
            
    async def record_cache_miss(self, key: str) -> None:
        """Record cache miss."""
        self._check_initialized()
        
        try:
            self.cache_misses.labels(key=key).inc()
            self.cache_operations.labels(
                operation="get",
                status="miss"
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record cache miss metrics: {str(e)}")
            
    async def record_cache_operation(
        self,
        operation: str,
        success: bool = True
    ) -> None:
        """Record cache operation."""
        self._check_initialized()
        
        try:
            status = "success" if success else "failure"
            self.cache_operations.labels(
                operation=operation,
                status=status
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record cache operation metrics: {str(e)}")
            
    async def record_resource_count(
        self,
        resource_type: str,
        count: int
    ) -> None:
        """Record resource count."""
        self._check_initialized()
        
        try:
            self.resource_total.labels(
                resource_type=resource_type
            ).set(count)
            
        except Exception as e:
            logger.error(f"Failed to record resource count metrics: {str(e)}")
            
    async def record_resource_operation(
        self,
        resource_type: str,
        operation: str,
        success: bool = True
    ) -> None:
        """Record resource operation."""
        self._check_initialized()
        
        try:
            status = "success" if success else "failure"
            self.resource_operations.labels(
                resource_type=resource_type,
                operation=operation,
                status=status
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record resource operation metrics: {str(e)}")
            
    async def record_service_health(
        self,
        service: str,
        is_healthy: bool
    ) -> None:
        """Record service health."""
        self._check_initialized()
        
        try:
            self.service_health.labels(
                service=service
            ).set(1 if is_healthy else 0)
            
        except Exception as e:
            logger.error(f"Failed to record service health metrics: {str(e)}")
            
    async def record_service_response_time(
        self,
        service: str,
        operation: str,
        duration: float
    ) -> None:
        """Record service response time."""
        self._check_initialized()
        
        try:
            self.service_response_time.labels(
                service=service,
                operation=operation
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record service response time metrics: {str(e)}")
            
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics values."""
        self._check_initialized()
        
        try:
            return {
                "operations": {
                    "total": self.operation_total._value.sum(),
                    "duration": self.operation_duration._sum.sum()
                },
                "errors": self.error_total._value.sum(),
                "cache": {
                    "hits": self.cache_hits._value.sum(),
                    "misses": self.cache_misses._value.sum()
                },
                "resources": {
                    type: self.resource_total.labels(resource_type=type)._value
                    for type in self.resource_total._metrics
                },
                "services": {
                    service: self.service_health.labels(service=service)._value
                    for service in self.service_health._metrics
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            return {} 