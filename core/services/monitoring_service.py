"""Monitoring service for system metrics and health checks."""
import psutil
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Gauge, Histogram
from core.utils.logger import log_performance, log_error

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ERROR_COUNT = Counter('http_errors_total', 'Total HTTP errors', ['type'])
CPU_USAGE = Gauge('system_cpu_usage', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage', 'Memory usage percentage')
DISK_USAGE = Gauge('system_disk_usage', 'Disk usage percentage')

class MonitoringService:
    """Service for monitoring system metrics and health checks."""
    
    def __init__(self):
        """Initialize monitoring service."""
        self._last_metrics_update = 0
        self._metrics_update_interval = 60  # Update metrics every 60 seconds
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float) -> None:
        """Record HTTP request metrics."""
        try:
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            if status >= 400:
                ERROR_COUNT.labels(type=str(status)).inc()
                
        except Exception as e:
            log_error(e, context={
                "operation": "record_request",
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "duration": duration
            })
    
    def update_system_metrics(self) -> None:
        """Update system metrics."""
        try:
            current_time = time.time()
            if current_time - self._last_metrics_update < self._metrics_update_interval:
                return
                
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.percent)
            
            self._last_metrics_update = current_time
            
            # Log performance metrics
            log_performance(
                operation="system_metrics_update",
                duration=time.time() - current_time,
                resource_usage={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                }
            )
            
        except Exception as e:
            log_error(e, context={"operation": "update_system_metrics"})
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            return {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count(),
                    "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used,
                    "free": psutil.virtual_memory().free
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                    "packets_sent": psutil.net_io_counters().packets_sent,
                    "packets_recv": psutil.net_io_counters().packets_recv
                }
            }
        except Exception as e:
            log_error(e, context={"operation": "get_system_metrics"})
            return {}
    
    def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            metrics = self.get_system_metrics()
            
            # Define health thresholds
            cpu_threshold = 90  # 90% CPU usage
            memory_threshold = 90  # 90% memory usage
            disk_threshold = 90  # 90% disk usage
            
            # Check system health
            is_healthy = (
                metrics.get("cpu", {}).get("percent", 0) < cpu_threshold and
                metrics.get("memory", {}).get("percent", 0) < memory_threshold and
                metrics.get("disk", {}).get("percent", 0) < disk_threshold
            )
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": time.time(),
                "metrics": metrics,
                "thresholds": {
                    "cpu": cpu_threshold,
                    "memory": memory_threshold,
                    "disk": disk_threshold
                }
            }
            
        except Exception as e:
            log_error(e, context={"operation": "check_health"})
            return {
                "status": "error",
                "timestamp": time.time(),
                "error": str(e)
            }

# Create singleton instance
monitoring_service = MonitoringService() 