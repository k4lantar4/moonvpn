"""
MoonVPN API Client

This module provides a robust API client for interacting with the MoonVPN backend API and 3x-UI Panel.
It includes caching, error handling, session management, rate limiting, retry mechanisms, monitoring, metrics,
circuit breaker pattern, and comprehensive diagnostics.
"""

import os
import requests
import logging
import json
import base64
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic, Callable, NamedTuple, Set
from urllib.parse import urlparse, parse_qs
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import redis
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import statistics
import psutil
import socket
import traceback
import asyncio
import aiohttp
import warnings

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')

class Metric(NamedTuple):
    """Metric data structure."""
    timestamp: float
    value: float
    labels: Dict[str, str]

class MetricsManager:
    """Manages API metrics collection and monitoring."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.lock = threading.Lock()
        
        # Start background cleanup
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_old_metrics,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def record(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric."""
        with self.lock:
            metric = Metric(time.time(), value, labels or {})
            self.metrics[name].append(metric)
    
    def get_stats(self, name: str, window: int = 300) -> Dict[str, float]:
        """Get statistics for a metric over the last window seconds."""
        now = time.time()
        with self.lock:
            recent = [
                m.value for m in self.metrics[name]
                if now - m.timestamp <= window
            ]
        
        if not recent:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "p95": 0
            }
        
        sorted_values = sorted(recent)
        p95_idx = int(len(sorted_values) * 0.95)
        
        return {
            "count": len(recent),
            "min": min(recent),
            "max": max(recent),
            "mean": statistics.mean(recent),
            "median": statistics.median(recent),
            "p95": sorted_values[p95_idx]
        }
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics periodically."""
        while True:
            time.sleep(300)  # Run every 5 minutes
            now = time.time()
            with self.lock:
                for name in self.metrics:
                    self.metrics[name] = [
                        m for m in self.metrics[name]
                        if now - m.timestamp <= 3600  # Keep last hour
                    ]

class ConnectionPool:
    """Manages a pool of reusable connections."""
    
    def __init__(self, max_size: int = 10, timeout: int = 30):
        self.max_size = max_size
        self.timeout = timeout
        self.pool = queue.Queue(maxsize=max_size)
        self.active = 0
        self.lock = threading.Lock()
        
        # Fill pool with initial connections
        for _ in range(max_size):
            self.pool.put(self._create_connection())
    
    def _create_connection(self) -> requests.Session:
        """Create a new connection."""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MoonVPN-Bot/1.0"
        })
        return session
    
    def get(self) -> requests.Session:
        """Get a connection from the pool."""
        try:
            return self.pool.get(timeout=self.timeout)
        except queue.Empty:
            with self.lock:
                if self.active < self.max_size:
                    self.active += 1
                    return self._create_connection()
                raise ConnectionError("Connection pool exhausted")
    
    def put(self, session: requests.Session):
        """Return a connection to the pool."""
        try:
            self.pool.put(session, block=False)
        except queue.Full:
            session.close()
            with self.lock:
                self.active -= 1

class HealthCheck:
    """Health check implementation."""
    
    def __init__(self):
        self.last_check = {}
        self.status = {}
        self.lock = threading.Lock()
    
    def check(self, service: str) -> bool:
        """Check service health."""
        now = time.time()
        
        with self.lock:
            last = self.last_check.get(service, 0)
            if now - last < 60:  # Cache health status for 1 minute
                return self.status.get(service, False)
            
            # Perform health check
            try:
                if service == "redis":
                    redis.Redis().ping()
                elif service == "panel":
                    socket.create_connection(
                        (os.getenv("X_UI_PANEL_URL", ""), 80),
                        timeout=5
                    )
                elif service == "backend":
                    socket.create_connection(
                        (os.getenv("API_BASE_URL", "").split("://")[1].split(":")[0], 8000),
                        timeout=5
                    )
                
                self.status[service] = True
                self.last_check[service] = now
                return True
                
            except Exception as e:
                logger.error(f"Health check failed for {service}: {e}")
                self.status[service] = False
                self.last_check[service] = now
                return False

class SystemMonitor:
    """System resource monitoring."""
    
    @staticmethod
    def get_metrics() -> Dict[str, float]:
        """Get system metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "network_bytes_sent": psutil.net_io_counters().bytes_sent,
            "network_bytes_recv": psutil.net_io_counters().bytes_recv,
            "open_files": len(psutil.Process().open_files()),
            "threads": len(psutil.Process().threads()),
            "connections": len(psutil.Process().connections())
        }

class APIErrorCode(Enum):
    """Error codes for API errors."""
    UNKNOWN = "unknown_error"
    NETWORK = "network_error"
    TIMEOUT = "timeout_error"
    AUTH = "authentication_error"
    RATE_LIMIT = "rate_limit_error"
    SERVER = "server_error"
    CLIENT = "client_error"
    VALIDATION = "validation_error"
    NOT_FOUND = "not_found_error"
    CACHE = "cache_error"

class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, 
                 message: str, 
                 error_code: APIErrorCode = APIErrorCode.UNKNOWN,
                 status_code: Optional[int] = None, 
                 response: Optional[Dict] = None,
                 retry_after: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.response = response
        self.retry_after = retry_after
        super().__init__(self.message)

class AuthenticationError(APIError):
    """Raised when authentication fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message, APIErrorCode.AUTH, status_code, response)

class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None, retry_after: Optional[int] = None):
        super().__init__(message, APIErrorCode.RATE_LIMIT, status_code, response, retry_after)

class ServerError(APIError):
    """Raised when server returns 5xx error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message, APIErrorCode.SERVER, status_code, response)

class ClientError(APIError):
    """Raised when client makes an invalid request."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message, APIErrorCode.CLIENT, status_code, response)

class ValidationError(APIError):
    """Raised when request validation fails."""
    def __init__(self, message: str, errors: Dict[str, List[str]], status_code: Optional[int] = None):
        super().__init__(message, APIErrorCode.VALIDATION, status_code, {"errors": errors})

class NotFoundError(APIError):
    """Raised when resource is not found."""
    def __init__(self, message: str, resource_type: str, resource_id: Union[str, int]):
        super().__init__(
            message,
            APIErrorCode.NOT_FOUND,
            404,
            {"resource_type": resource_type, "resource_id": resource_id}
        )

@dataclass
class APIResponse(Generic[T]):
    """Wrapper for API responses with type hints."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    cached: bool = False
    timestamp: float = time.time()

class RateLimiter:
    """Rate limiter implementation."""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str) -> tuple[bool, Optional[int]]:
        """Check if request is allowed."""
        with self.lock:
            now = time.time()
            
            # Clean old requests
            self.requests = {k: v for k, v in self.requests.items() 
                           if now - v[-1] < self.time_window}
            
            if key not in self.requests:
                self.requests[key] = []
            
            requests = self.requests[key]
            
            # Remove old timestamps
            while requests and now - requests[0] >= self.time_window:
                requests.pop(0)
            
            if len(requests) >= self.max_requests:
                retry_after = int(requests[0] + self.time_window - now) + 1
                return False, retry_after
            
            requests.append(now)
            return True, None

class CacheManager:
    """Manages caching of API responses."""
    
    def __init__(self, redis_config: Optional[Dict[str, Any]] = None):
        config = redis_config or {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "db": int(os.getenv("REDIS_DB", 0)),
            "decode_responses": True
        }
        
        self.redis = redis.Redis(**config)
        self.local_cache = {}
        self.local_cache_ttl = {}
        self.lock = threading.Lock()
    
    def _get_local(self, key: str) -> Optional[str]:
        """Get value from local cache."""
        with self.lock:
            if key in self.local_cache:
                if time.time() < self.local_cache_ttl.get(key, 0):
                    return self.local_cache[key]
                else:
                    del self.local_cache[key]
                    del self.local_cache_ttl[key]
        return None
    
    def _set_local(self, key: str, value: str, expire: int) -> None:
        """Set value in local cache."""
        with self.lock:
            self.local_cache[key] = value
            self.local_cache_ttl[key] = time.time() + expire
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        # Try local cache first
        value = self._get_local(key)
        if value is not None:
            return value
        
        # Try Redis
        try:
            value = self.redis.get(key)
            if value:
                self._set_local(key, value, 60)  # Cache locally for 1 minute
            return value
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None
    
    def set(self, key: str, value: str, expire: int = 300) -> bool:
        """Set value in cache with expiration."""
        try:
            # Set in Redis
            success = bool(self.redis.setex(key, expire, value))
            
            # Set in local cache
            if success:
                self._set_local(key, value, min(expire, 60))
            
            return success
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            # Delete from Redis
            success = bool(self.redis.delete(key))
            
            # Delete from local cache
            with self.lock:
                self.local_cache.pop(key, None)
                self.local_cache_ttl.pop(key, None)
            
            return success
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate all keys matching pattern."""
        try:
            # Get all matching keys
            keys = self.redis.keys(pattern)
            
            # Delete from Redis
            if keys:
                self.redis.delete(*keys)
            
            # Delete from local cache
            with self.lock:
                for key in list(self.local_cache.keys()):
                    if any(key.startswith(p) for p in keys):
                        del self.local_cache[key]
                        del self.local_cache_ttl[key]
            
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return False

def cached(expire: int = 300, invalidate_on_methods: List[str] = None):
    """Decorator for caching API responses."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check if this is a write operation that should invalidate cache
            if invalidate_on_methods and func.__name__ in invalidate_on_methods:
                pattern = f"{func.__name__.split('_')[0]}*"
                self.cache.invalidate_pattern(pattern)
            
            # Try to get from cache
            cached_value = self.cache.get(cache_key)
            if cached_value:
                try:
                    data = json.loads(cached_value)
                    return APIResponse(success=True, data=data, cached=True)
                except json.JSONDecodeError:
                    pass
            
            # Call original function
            result = func(self, *args, **kwargs)
            
            # Cache successful responses
            if result and result.success:
                try:
                    self.cache.set(cache_key, json.dumps(result.data), expire)
                except (TypeError, json.JSONDecodeError):
                    pass
            
            return result
        return wrapper
    return decorator

def retry_on_error(max_retries: int = 3, 
                  retry_delay: int = 1,
                  retry_on: tuple = (ServerError, RateLimitError)):
    """Decorator for retrying failed API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except retry_on as e:
                    last_error = e
                    
                    # Handle rate limiting
                    if isinstance(e, RateLimitError) and e.retry_after:
                        time.sleep(e.retry_after)
                    else:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            
            raise last_error
        return wrapper
    return decorator

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_limit: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_limit = half_open_limit
        
        self.state = CircuitBreakerState.CLOSED
        self.failures = 0
        self.last_failure_time = 0
        self.half_open_successes = 0
        self.lock = threading.Lock()
        
        # Metrics
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = []
    
    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        with self.lock:
            self.failures += 1
            self.total_failures += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.CLOSED and self.failures >= self.failure_threshold:
                self._change_state(CircuitBreakerState.OPEN)
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self._change_state(CircuitBreakerState.OPEN)
    
    def record_success(self):
        """Record a success and potentially close the circuit."""
        with self.lock:
            self.total_successes += 1
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_successes += 1
                if self.half_open_successes >= self.half_open_limit:
                    self._change_state(CircuitBreakerState.CLOSED)
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        with self.lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self._change_state(CircuitBreakerState.HALF_OPEN)
                    return True
                return False
            
            # HALF_OPEN state
            return True
    
    def _change_state(self, new_state: CircuitBreakerState):
        """Change the circuit breaker state."""
        old_state = self.state
        self.state = new_state
        self.failures = 0
        self.half_open_successes = 0
        
        # Record state change
        self.state_changes.append({
            "timestamp": time.time(),
            "from": old_state.value,
            "to": new_state.value
        })
        
        logger.warning(f"Circuit breaker state changed from {old_state.value} to {new_state.value}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        with self.lock:
            return {
                "state": self.state.value,
                "failures": self.failures,
                "total_failures": self.total_failures,
                "total_successes": self.total_successes,
                "failure_rate": (self.total_failures / (self.total_failures + self.total_successes)) 
                               if (self.total_failures + self.total_successes) > 0 else 0,
                "last_state_change": self.state_changes[-1] if self.state_changes else None,
                "state_changes_24h": len([
                    c for c in self.state_changes
                    if time.time() - c["timestamp"] <= 86400
                ])
            }

class Diagnostics:
    """System diagnostics and troubleshooting."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.error_patterns = defaultdict(int)
        self.slow_endpoints = defaultdict(list)
        self.connection_issues = defaultdict(list)
        self.lock = threading.Lock()
        
        # Keep last 1000 issues
        self.issue_history = deque(maxlen=1000)
        
        # Start diagnostic thread
        self._diagnostic_thread = threading.Thread(
            target=self._run_diagnostics,
            daemon=True
        )
        self._diagnostic_thread.start()
    
    def record_issue(self, 
                    category: str,
                    severity: str,
                    message: str,
                    context: Dict[str, Any] = None):
        """Record a system issue."""
        with self.lock:
            issue = {
                "timestamp": time.time(),
                "category": category,
                "severity": severity,
                "message": message,
                "context": context or {},
                "stack_trace": traceback.format_stack()
            }
            
            self.issue_history.append(issue)
            
            if severity == "error":
                self.issues.append(issue)
            elif severity == "warning":
                self.warnings.append(issue)
            
            # Track error patterns
            if "error_type" in (context or {}):
                self.error_patterns[context["error_type"]] += 1
    
    def record_slow_request(self, endpoint: str, duration: float, context: Dict[str, Any] = None):
        """Record a slow API request."""
        with self.lock:
            self.slow_endpoints[endpoint].append({
                "timestamp": time.time(),
                "duration": duration,
                "context": context or {}
            })
            
            # Keep only last hour
            self.slow_endpoints[endpoint] = [
                r for r in self.slow_endpoints[endpoint]
                if time.time() - r["timestamp"] <= 3600
            ]
    
    def record_connection_issue(self, host: str, error: Exception, context: Dict[str, Any] = None):
        """Record a connection issue."""
        with self.lock:
            self.connection_issues[host].append({
                "timestamp": time.time(),
                "error": str(error),
                "error_type": type(error).__name__,
                "context": context or {}
            })
            
            # Keep only last hour
            self.connection_issues[host] = [
                i for i in self.connection_issues[host]
                if time.time() - i["timestamp"] <= 3600
            ]
    
    def _run_diagnostics(self):
        """Run periodic system diagnostics."""
        while True:
            try:
                self._check_system_health()
                self._analyze_error_patterns()
                self._check_performance()
                self._cleanup_old_data()
                
                time.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Diagnostic error: {e}")
    
    def _check_system_health(self):
        """Check overall system health."""
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent
        
        if cpu_percent > 80:
            self.record_issue(
                "system",
                "warning",
                f"High CPU usage: {cpu_percent}%",
                {"cpu_percent": cpu_percent}
            )
        
        if memory_percent > 80:
            self.record_issue(
                "system",
                "warning",
                f"High memory usage: {memory_percent}%",
                {"memory_percent": memory_percent}
            )
        
        if disk_percent > 80:
            self.record_issue(
                "system",
                "warning",
                f"High disk usage: {disk_percent}%",
                {"disk_percent": disk_percent}
            )
    
    def _analyze_error_patterns(self):
        """Analyze error patterns for potential issues."""
        with self.lock:
            for error_type, count in self.error_patterns.items():
                if count >= 10:  # More than 10 occurrences
                    self.record_issue(
                        "errors",
                        "warning",
                        f"Frequent error pattern detected: {error_type}",
                        {
                            "error_type": error_type,
                            "count": count
                        }
                    )
    
    def _check_performance(self):
        """Check for performance issues."""
        with self.lock:
            for endpoint, requests in self.slow_endpoints.items():
                if len(requests) >= 5:  # At least 5 slow requests
                    avg_duration = statistics.mean(r["duration"] for r in requests)
                    self.record_issue(
                        "performance",
                        "warning",
                        f"Slow endpoint detected: {endpoint}",
                        {
                            "endpoint": endpoint,
                            "avg_duration": avg_duration,
                            "request_count": len(requests)
                        }
                    )
    
    def _cleanup_old_data(self):
        """Clean up old diagnostic data."""
        now = time.time()
        with self.lock:
            # Keep only last 24 hours of issues
            self.issues = [
                i for i in self.issues
                if now - i["timestamp"] <= 86400
            ]
            self.warnings = [
                w for w in self.warnings
                if now - w["timestamp"] <= 86400
            ]
            
            # Reset error patterns
            self.error_patterns.clear()
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        with self.lock:
            return {
                "issues": {
                    "current": len(self.issues),
                    "total": len(self.issue_history),
                    "by_severity": {
                        "error": len([i for i in self.issues if i["severity"] == "error"]),
                        "warning": len([i for i in self.issues if i["severity"] == "warning"])
                    },
                    "by_category": defaultdict(int, {
                        i["category"]: sum(1 for x in self.issues if x["category"] == i["category"])
                        for i in self.issues
                    })
                },
                "performance": {
                    "slow_endpoints": {
                        endpoint: {
                            "count": len(requests),
                            "avg_duration": statistics.mean(r["duration"] for r in requests)
                        }
                        for endpoint, requests in self.slow_endpoints.items()
                    }
                },
                "connections": {
                    "issues": {
                        host: {
                            "count": len(issues),
                            "last_error": issues[-1]["error"] if issues else None
                        }
                        for host, issues in self.connection_issues.items()
                    }
                },
                "error_patterns": dict(self.error_patterns)
            }

class BaseAPIClient:
    """Base class for API clients with common functionality."""
    
    def __init__(self, 
                 base_url: str, 
                 auth_token: Optional[str] = None,
                 max_retries: int = 3,
                 timeout: int = 30,
                 rate_limit: tuple[int, int] = (100, 60)):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize components
        self.connection_pool = ConnectionPool()
        self.cache = CacheManager()
        self.rate_limiter = RateLimiter(*rate_limit)
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.metrics = MetricsManager()
        self.health = HealthCheck()
        self.monitor = SystemMonitor()
        self.diagnostics = Diagnostics()
        
        # Circuit breakers for different services
        self.circuit_breakers = {
            "api": CircuitBreaker(),
            "redis": CircuitBreaker(),
            "panel": CircuitBreaker()
        }
        
        # Start monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background monitoring."""
        def monitor():
            while True:
                try:
                    # Record system metrics
                    metrics = self.monitor.get_metrics()
                    for name, value in metrics.items():
                        self.metrics.record(f"system_{name}", value)
                    
                    # Check service health
                    for service in ["redis", "panel", "backend"]:
                        self.health.check(service)
                    
                    time.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get all recorded metrics."""
        metrics = {}
        
        # API metrics
        metrics["api_latency"] = self.metrics.get_stats("api_latency")
        metrics["api_errors"] = self.metrics.get_stats("api_errors")
        metrics["cache_hits"] = self.metrics.get_stats("cache_hits")
        metrics["rate_limits"] = self.metrics.get_stats("rate_limits")
        
        # System metrics
        for name in [
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "network_bytes_sent",
            "network_bytes_recv",
            "open_files",
            "threads",
            "connections"
        ]:
            metrics[f"system_{name}"] = self.metrics.get_stats(f"system_{name}")
        
        return metrics
    
    def get_health(self) -> Dict[str, bool]:
        """Get health status of all services."""
        return {
            service: self.health.check(service)
            for service in ["redis", "panel", "backend"]
        }
    
    def _handle_response(self, response: requests.Response) -> APIResponse:
        """Handle API response and convert to APIResponse object."""
        try:
            response.raise_for_status()
            
            if not response.content:
                return APIResponse(success=True)
            
            data = response.json()
            return APIResponse(
                success=True,
                data=data,
                status_code=response.status_code
            )
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_data = None
            
            try:
                error_data = e.response.json()
            except:
                error_data = {"message": e.response.text}
            
            if status_code == 401:
                raise AuthenticationError(
                    "Authentication failed",
                    status_code,
                    error_data
                )
            elif status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code,
                    error_data,
                    retry_after
                )
            elif status_code >= 500:
                raise ServerError(
                    "Server error occurred",
                    status_code,
                    error_data
                )
            elif status_code == 404:
                resource_info = error_data.get("resource", {})
                raise NotFoundError(
                    error_data.get("message", "Resource not found"),
                    resource_info.get("type", "unknown"),
                    resource_info.get("id")
                )
            elif status_code == 422:
                raise ValidationError(
                    error_data.get("message", "Validation failed"),
                    error_data.get("errors", {}),
                    status_code
                )
            else:
                raise ClientError(
                    error_data.get("message", "Request failed"),
                    status_code,
                    error_data
                )
                
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.Timeout):
                raise APIError(
                    f"Request timed out: {str(e)}",
                    APIErrorCode.TIMEOUT
                )
            elif isinstance(e, requests.exceptions.ConnectionError):
                raise APIError(
                    f"Network error: {str(e)}",
                    APIErrorCode.NETWORK
                )
            else:
                raise APIError(
                    f"Request failed: {str(e)}",
                    APIErrorCode.UNKNOWN
                )
        
        except json.JSONDecodeError:
            raise APIError(
                "Invalid JSON response",
                APIErrorCode.CLIENT
            )
    
    def _check_circuit_breaker(self, service: str) -> bool:
        """Check if service circuit breaker allows request."""
        breaker = self.circuit_breakers.get(service)
        if breaker and not breaker.allow_request():
            raise APIError(
                f"Circuit breaker open for {service}",
                APIErrorCode.SERVER,
                503,
                {"service": service}
            )
        return True
    
    @retry_on_error()
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """Make an API request with circuit breaker and diagnostics."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        # Check circuit breaker
        self._check_circuit_breaker("api")
        
        # Check rate limit
        allowed, retry_after = self.rate_limiter.is_allowed(endpoint)
        if not allowed:
            self.metrics.record("rate_limits", 1)
            self.diagnostics.record_issue(
                "rate_limit",
                "warning",
                f"Rate limit exceeded for {endpoint}",
                {"retry_after": retry_after}
            )
            raise RateLimitError(
                "Rate limit exceeded",
                429,
                {"message": "Too many requests"},
                retry_after
            )
        
        # Get connection from pool
        session = self.connection_pool.get()
        try:
            if self.auth_token:
                session.headers["Authorization"] = f"Bearer {self.auth_token}"
            
            response = session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=timeout or self.timeout
            )
            
            duration = time.time() - start_time
            
            # Record metrics
            self.metrics.record(
                "api_latency",
                duration,
                {
                    "method": method,
                    "endpoint": endpoint,
                    "status": str(response.status_code)
                }
            )
            
            # Check for slow requests
            if duration > 1.0:  # More than 1 second
                self.diagnostics.record_slow_request(
                    endpoint,
                    duration,
                    {
                        "method": method,
                        "status": response.status_code,
                        "size": len(response.content)
                    }
                )
            
            result = self._handle_response(response)
            
            if not result.success:
                self.metrics.record("api_errors", 1)
                self.circuit_breakers["api"].record_failure()
                self.diagnostics.record_issue(
                    "api",
                    "error",
                    f"API request failed: {result.error}",
                    {
                        "endpoint": endpoint,
                        "status_code": result.status_code,
                        "error": result.error
                    }
                )
            else:
                self.circuit_breakers["api"].record_success()
            
            return result
            
        except Exception as e:
            self.metrics.record("api_errors", 1)
            self.circuit_breakers["api"].record_failure()
            
            self.diagnostics.record_issue(
                "api",
                "error",
                f"API request error: {str(e)}",
                {
                    "endpoint": endpoint,
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )
            
            if isinstance(e, requests.exceptions.ConnectionError):
                self.diagnostics.record_connection_issue(
                    self.base_url,
                    e,
                    {"endpoint": endpoint}
                )
            
            raise
        
        finally:
            # Return connection to pool
            self.connection_pool.put(session)

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the system."""
        return {
            "health": self.get_health(),
            "metrics": self.get_metrics(),
            "diagnostics": self.diagnostics.get_diagnostics(),
            "circuit_breakers": {
                name: breaker.get_metrics()
                for name, breaker in self.circuit_breakers.items()
            },
            "panel": self.panel.get_panel_info(),
            "cache": {
                "size": len(self.cache.local_cache),
                "ttl": self.cache.local_cache_ttl
            },
            "rate_limiter": {
                "requests": self.rate_limiter.requests
            },
            "connections": {
                "active": self.connection_pool.active,
                "available": self.connection_pool.pool.qsize()
            }
        }

class XUIPanel:
    """3x-UI Panel API client."""
    
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.cache = CacheManager()
        self._cookie = None
        self._last_login = None
    
    @property
    def is_logged_in(self) -> bool:
        """Check if currently logged in."""
        return bool(self._cookie and self._last_login and
                   (datetime.now() - self._last_login) < timedelta(hours=1))
    
    def login(self) -> bool:
        """Log in to the panel."""
        try:
            response = self.session.post(
                f"{self.url}/login",
                data={
                    "username": self.username,
                    "password": self.password
                },
                allow_redirects=False
            )
            
            if response.status_code == 302 or "Location" in response.headers:
                self._cookie = self.session.cookies.get_dict()
                self._last_login = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry: bool = True
    ) -> APIResponse:
        """Make a request to the panel."""
        if not self.is_logged_in and not self.login():
            raise AuthenticationError("Failed to log in to panel")
        
        try:
            response = self.session.request(
                method=method.upper(),
                url=f"{self.url}/{endpoint.lstrip('/')}",
                json=data,
                params=params
            )
            
            # Check if session expired
            if response.status_code == 302 and retry:
                self._cookie = None
                self._last_login = None
                return self.request(method, endpoint, data, params, False)
            
            return APIResponse(
                success=True,
                data=response.json() if response.content else None,
                status_code=response.status_code
            )
            
        except Exception as e:
            raise APIError(f"Panel request failed: {str(e)}")

class MoonVPNAPI(BaseAPIClient):
    """MoonVPN API client."""
    
    def __init__(self):
        super().__init__(
            base_url=os.getenv("API_BASE_URL", "http://backend:8000/api/v1"),
            auth_token=os.getenv("API_AUTH_TOKEN", "")
        )
        
        # Initialize 3x-UI Panel client
        self.panel = XUIPanel(
            url=os.getenv("X_UI_PANEL_URL", ""),
            username=os.getenv("X_UI_PANEL_USERNAME", ""),
            password=os.getenv("X_UI_PANEL_PASSWORD", "")
        )

    # Location methods
    @cached(expire=300)
    def get_locations(self) -> List[Dict[str, Any]]:
        """Get all available locations."""
        response = self.get("locations/")
        return response.data or []
    
    def create_location(self, name: str, flag: str, is_active: bool = True) -> Optional[Dict[str, Any]]:
        """Create a new location."""
        response = self.post("locations/", data={
            "name": name,
            "flag": flag,
            "is_active": is_active
        })
        return response.data
    
    def update_location(self, location_id: int, **kwargs) -> bool:
        """Update a location."""
        response = self.put(f"locations/{location_id}/", data=kwargs)
        return response.success
    
    def delete_location(self, location_id: int) -> bool:
        """Delete a location."""
        response = self.delete(f"locations/{location_id}/")
        return response.success

    # Server methods
    @cached(expire=60)
    def get_servers(self) -> List[Dict[str, Any]]:
        """Get all available servers."""
        response = self.get("servers/")
        return response.data or []
    
    @cached(expire=60)
    def get_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """Get a server by ID."""
        response = self.get(f"servers/{server_id}/")
        return response.data
    
    def create_server(self, server_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new server."""
        response = self.post("servers/", data=server_data)
        return response.data
    
    def update_server(self, server_id: int, server_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a server."""
        response = self.put(f"servers/{server_id}/", data=server_data)
        return response.data
    
    def delete_server(self, server_id: int) -> bool:
        """Delete a server."""
        response = self.delete(f"servers/{server_id}/")
        return response.success
    
    def test_server_connection(self, server_id: int) -> Dict[str, Any]:
        """Test connection to a server."""
        response = self.get(f"servers/{server_id}/test/")
        if response.success:
            return response.data
        return {"success": False, "ping": None, "error": "Connection failed"}
    
    @cached(expire=30)
    def get_server_metrics(self, server_id: int) -> Dict[str, Any]:
        """Get server metrics."""
        response = self.get(f"servers/{server_id}/metrics/")
        return response.data or {}
    
    @cached(expire=30)
    def get_server_load(self) -> Dict[int, float]:
        """Get the load of all servers."""
        response = self.get("servers/load/")
        if not response.data:
            return {}
        
        loads = {}
        for server in response.data:
            server_id = server.get("id")
            load = server.get("load")
            if server_id is not None and load is not None:
                loads[server_id] = load
        
        return loads

    # User management methods
    @cached(expire=60)
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        response = self.get("users/")
        return response.data or []

    @cached(expire=30)
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        response = self.get(f"users/{user_id}/")
        return response.data

    @cached(expire=30)
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by Telegram ID."""
        response = self.get("users/", params={"telegram_id": telegram_id})
        if response.success and response.data:
            return response.data[0]
        return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        response = self.post("users/", data=user_data)
        return response.data

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user."""
        response = self.put(f"users/{user_id}/", data=user_data)
        return response.data

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        response = self.delete(f"users/{user_id}/")
        return response.success

    def block_user(self, user_id: int) -> bool:
        """Block a user."""
        response = self.post(f"users/{user_id}/block/")
        return response.success

    def unblock_user(self, user_id: int) -> bool:
        """Unblock a user."""
        response = self.post(f"users/{user_id}/unblock/")
        return response.success

    # User profile methods
    @cached(expire=30)
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user's profile."""
        response = self.get(f"users/{user_id}/profile/")
        return response.data

    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's profile."""
        response = self.put(f"users/{user_id}/profile/", data=profile_data)
        return response.data

    def update_user_wallet(self, user_id: int, amount: float, note: str = None) -> bool:
        """Update a user's wallet balance."""
        response = self.post(f"users/{user_id}/wallet/", data={
            "amount": amount,
            "note": note
        })
        return response.success

    def change_user_role(self, user_id: int, role: str) -> bool:
        """Change a user's role."""
        response = self.post(f"users/{user_id}/role/", data={"role": role})
        return response.success

    # Payment methods
    @cached(expire=60)
    def get_payments(self) -> List[Dict[str, Any]]:
        """Get all payments."""
        response = self.get("payments/")
        return response.data or []

    @cached(expire=30)
    def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Get a payment by ID."""
        response = self.get(f"payments/{payment_id}/")
        return response.data

    @cached(expire=30)
    def get_user_payments(self, user_id: int) -> List[Dict[str, Any]]:
        """Get payments for a user."""
        response = self.get("payments/", params={"user_id": user_id})
        return response.data or []

    def create_payment(self, payment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new payment."""
        response = self.post("payments/", data=payment_data)
        return response.data

    def verify_payment(self, payment_id: int, transaction_id: str = None) -> bool:
        """Verify a payment."""
        data = {}
        if transaction_id:
            data["transaction_id"] = transaction_id
        response = self.post(f"payments/{payment_id}/verify/", data=data)
        return response.success

    def cancel_payment(self, payment_id: int, reason: str = None) -> bool:
        """Cancel a payment."""
        data = {}
        if reason:
            data["reason"] = reason
        response = self.post(f"payments/{payment_id}/cancel/", data=data)
        return response.success

    # Subscription methods
    @cached(expire=60)
    def get_plans(self) -> List[Dict[str, Any]]:
        """Get all subscription plans."""
        response = self.get("plans/")
        return response.data or []

    @cached(expire=30)
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan by ID."""
        response = self.get(f"plans/{plan_id}/")
        return response.data

    def create_plan(self, plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new plan."""
        response = self.post("plans/", data=plan_data)
        return response.data

    def update_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a plan."""
        response = self.put(f"plans/{plan_id}/", data=plan_data)
        return response.data

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan."""
        response = self.delete(f"plans/{plan_id}/")
        return response.success

    # Account methods
    @cached(expire=60)
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts."""
        response = self.get("accounts/")
        return response.data or []

    @cached(expire=30)
    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get an account by ID."""
        response = self.get(f"accounts/{account_id}/")
        return response.data

    @cached(expire=30)
    def get_user_accounts(self, user_id: int) -> List[Dict[str, Any]]:
        """Get accounts for a user."""
        response = self.get("accounts/", params={"user_id": user_id})
        return response.data or []

    def create_account(self, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new account."""
        response = self.post("accounts/", data=account_data)
        return response.data

    def update_account(self, account_id: int, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an account."""
        response = self.put(f"accounts/{account_id}/", data=account_data)
        return response.data

    def delete_account(self, account_id: int) -> bool:
        """Delete an account."""
        response = self.delete(f"accounts/{account_id}/")
        return response.success

    def get_account_config(self, account_id: int, protocol: str = None) -> Dict[str, Any]:
        """Get the configuration for an account."""
        params = {}
        if protocol:
            params["protocol"] = protocol
        response = self.get(f"accounts/{account_id}/config/", params=params)
        return response.data or {}

    def reset_account_traffic(self, account_id: int) -> bool:
        """Reset the traffic for an account."""
        response = self.post(f"accounts/{account_id}/reset-traffic/")
        return response.success

    def change_account_server(self, account_id: int, server_id: int) -> bool:
        """Change the server for an account."""
        response = self.post(f"accounts/{account_id}/change-server/", data={
            "server_id": server_id
        })
        return response.success

    def renew_account(self, account_id: int) -> bool:
        """Renew an account."""
        response = self.post(f"accounts/{account_id}/renew/")
        return response.success

    # Discount methods
    @cached(expire=300)
    def get_discounts(self) -> List[Dict[str, Any]]:
        """Get all discount codes."""
        response = self.get("discounts/")
        return response.data or []

    def create_discount(self, discount_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new discount code."""
        response = self.post("discounts/", data=discount_data)
        return response.data

    def update_discount(self, discount_id: int, discount_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a discount code."""
        response = self.put(f"discounts/{discount_id}/", data=discount_data)
        return response.data

    def delete_discount(self, discount_id: int) -> bool:
        """Delete a discount code."""
        response = self.delete(f"discounts/{discount_id}/")
        return response.success

    def verify_discount(self, code: str) -> Optional[Dict[str, Any]]:
        """Verify a discount code."""
        response = self.get(f"discounts/verify/{code}/")
        return response.data

    # System statistics methods
    @cached(expire=60)
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        response = self.get("stats/system/")
        return response.data or {}

    @cached(expire=300)
    def get_revenue_stats(self) -> Dict[str, Any]:
        """Get revenue statistics."""
        response = self.get("stats/revenue/")
        return response.data or {}

    @cached(expire=60)
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        response = self.get("stats/users/")
        return response.data or {}

    @cached(expire=30)
    def get_server_stats(self, server_id: int = None) -> Dict[str, Any]:
        """Get server statistics."""
        if server_id:
            response = self.get(f"stats/servers/{server_id}/")
        else:
            response = self.get("stats/servers/")
        return response.data or {}

    def get_financial_stats(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get financial statistics."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        response = self.get("stats/financial/", params=params)
        return response.data or {}

    # Backup methods
    @cached(expire=300)
    def get_backups(self) -> List[Dict[str, Any]]:
        """Get all backups."""
        response = self.get("backups/")
        return response.data or []

    def create_backup(self) -> bool:
        """Create a new backup."""
        response = self.post("backups/")
        return response.success

    def restore_backup(self, backup_id: int) -> bool:
        """Restore a backup."""
        response = self.post(f"backups/{backup_id}/restore/")
        return response.success

    def delete_backup(self, backup_id: int) -> bool:
        """Delete a backup."""
        response = self.delete(f"backups/{backup_id}/")
        return response.success

    def download_backup(self, backup_id: int) -> Optional[bytes]:
        """Download a backup."""
        try:
            response = self.get(f"backups/{backup_id}/download/")
            if response.success and response.data:
                return base64.b64decode(response.data)
            return None
        except Exception as e:
            logger.error(f"Error downloading backup: {e}")
            return None

    # Messaging methods
    def send_broadcast(self, message: str, user_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a broadcast message to users."""
        data = {"message": message}
        if user_filter:
            data["filter"] = user_filter
        response = self.post("notifications/broadcast/", data=data)
        return response.data or {"success": False, "sent": 0, "failed": 0}

    # Utility methods
    def generate_qrcode(self, data: str) -> str:
        """Generate a QR code."""
        response = self.post("utils/qrcode/", data={"data": data})
        return response.data.get("qrcode", "") if response.success else ""

    # Panel methods
    def get_inbounds(self) -> List[Dict[str, Any]]:
        """Get all inbounds from the panel."""
        response = self.panel.request("GET", "panel/inbounds")
        return response.data.get("obj", []) if response.success else []

    def create_inbound(self, inbound_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new inbound in the panel."""
        response = self.panel.request("POST", "panel/inbound", data=inbound_data)
        if response.success:
            inbounds = self.get_inbounds()
            return inbounds[-1] if inbounds else None
        return None

    def update_inbound(self, inbound_id: int, inbound_data: Dict[str, Any]) -> bool:
        """Update an inbound in the panel."""
        response = self.panel.request(
            "POST",
            f"panel/inbound/update/{inbound_id}",
            data=inbound_data
        )
        return response.success

    def delete_inbound(self, inbound_id: int) -> bool:
        """Delete an inbound from the panel."""
        response = self.panel.request("POST", f"panel/inbound/del/{inbound_id}")
        return response.success

    @cached(expire=30)
    def get_clients(self, inbound_id: int) -> List[Dict[str, Any]]:
        """Get all clients for an inbound."""
        response = self.panel.request(
            "GET",
            f"panel/inbound/{inbound_id}/getClientTraffics"
        )
        return response.data.get("obj", []) if response.success else []

    def add_client(self, inbound_id: int, client_data: Dict[str, Any]) -> bool:
        """Add a client to an inbound."""
        response = self.panel.request(
            "POST",
            f"panel/inbound/addClient/{inbound_id}",
            data=client_data
        )
        return response.success

    def update_client(self, inbound_id: int, email: str, client_data: Dict[str, Any]) -> bool:
        """Update a client in the panel."""
        response = self.panel.request(
            "POST",
            "panel/inbound/updateClient",
            data={
                "id": inbound_id,
                "email": email,
                "clientData": client_data
            }
        )
        return response.success

    def delete_client(self, inbound_id: int, email: str) -> bool:
        """Delete a client from the panel."""
        response = self.panel.request(
            "POST",
            "panel/inbound/delClient",
            data={
                "id": inbound_id,
                "email": email
            }
        )
        return response.success

    def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """Reset a client's traffic in the panel."""
        response = self.panel.request(
            "POST",
            "panel/inbound/resetClientTraffic",
            data={
                "id": inbound_id,
                "email": email
            }
        )
        return response.success

    @cached(expire=30)
    def get_client_traffic(self, inbound_id: int, email: str) -> Dict[str, Any]:
        """Get a client's traffic from the panel."""
        clients = self.get_clients(inbound_id)
        for client in clients:
            if client.get("email") == email:
                return {
                    "up": client.get("up", 0),
                    "down": client.get("down", 0),
                    "total": client.get("total", 0),
                    "expiry_time": client.get("expiryTime", 0)
                }
        return {"up": 0, "down": 0, "total": 0, "expiry_time": 0}

    @cached(expire=300)
    def get_panel_info(self) -> Dict[str, Any]:
        """Get information about the panel."""
        response = self.panel.request("GET", "panel/status")
        if not response.success:
            return {
                "status": "error",
                "message": "Could not get panel status",
                "version": "",
                "uptime": "",
                "cpu": 0,
                "memory": 0,
                "disk": 0,
                "xray_running": False,
                "xray_version": ""
            }
        
        data = response.data.get("obj", {})
        return {
            "status": "ok",
            "version": data.get("version", ""),
            "uptime": data.get("uptime", ""),
            "cpu": data.get("cpu", 0),
            "memory": data.get("mem", 0),
            "disk": data.get("disk", 0),
            "xray_running": data.get("xray_running", False),
            "xray_version": data.get("xray_version", "")
        }

# Initialize global API client
api_client = MoonVPNAPI()

# Export for backward compatibility
def get_api_client() -> MoonVPNAPI:
    """Get the global API client instance."""
    return api_client 