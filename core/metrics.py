"""
Metrics System

This module provides metrics collection for monitoring application performance.
It includes Prometheus metrics for requests, API calls, database operations,
panel health, and cache efficiency.
"""

import time
import logging
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, Union

from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)

# Type definition for function returns
T = TypeVar('T')

# Define metrics
# Request metrics
REQUEST_COUNT = Counter(
    "moonvpn_request_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "moonvpn_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))
)

# API call metrics
API_CALL_COUNT = Counter(
    "moonvpn_api_call_total",
    "Total number of API calls",
    ["method", "endpoint", "status"]
)

API_CALL_LATENCY = Histogram(
    "moonvpn_api_call_latency_seconds",
    "API call latency in seconds",
    ["method", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, float("inf"))
)

# Database operation metrics
DB_OPERATION_COUNT = Counter(
    "moonvpn_db_operation_total",
    "Total number of database operations",
    ["operation", "model", "status"]
)

DB_OPERATION_LATENCY = Histogram(
    "moonvpn_db_operation_latency_seconds",
    "Database operation latency in seconds",
    ["operation", "model"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float("inf"))
)

# Cache metrics
CACHE_HIT_COUNT = Counter(
    "moonvpn_cache_hit_total",
    "Total number of cache hits",
    ["cache_type"]
)

CACHE_MISS_COUNT = Counter(
    "moonvpn_cache_miss_total",
    "Total number of cache misses",
    ["cache_type"]
)

CACHE_OPERATION_LATENCY = Histogram(
    "moonvpn_cache_operation_latency_seconds",
    "Cache operation latency in seconds",
    ["operation", "cache_type"],
    buckets=(0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, float("inf"))
)

# Panel metrics
PANEL_HEALTH_GAUGE = Gauge(
    "moonvpn_panel_health",
    "Panel health status (1=healthy, 0=unhealthy)",
    ["panel_id", "panel_name", "location"]
)

PANEL_RESPONSE_TIME = Gauge(
    "moonvpn_panel_response_time_seconds",
    "Panel response time in seconds",
    ["panel_id", "panel_name", "location"]
)

PANEL_CLIENT_COUNT = Gauge(
    "moonvpn_panel_client_count",
    "Number of clients on a panel",
    ["panel_id", "panel_name", "location"]
)

PANEL_INBOUND_COUNT = Gauge(
    "moonvpn_panel_inbound_count",
    "Number of inbounds on a panel",
    ["panel_id", "panel_name", "location"]
)

PANEL_ONLINE_CLIENT_COUNT = Gauge(
    "moonvpn_panel_online_client_count",
    "Number of online clients on a panel",
    ["panel_id", "panel_name", "location"]
)

# Business metrics
ACTIVE_USER_COUNT = Gauge(
    "moonvpn_active_user_count",
    "Number of active users in the system"
)

ACTIVE_CLIENT_COUNT = Gauge(
    "moonvpn_active_client_count",
    "Number of active clients in the system",
    ["location"]
)

ORDER_COUNT = Counter(
    "moonvpn_order_total",
    "Total number of orders",
    ["status"]
)

PAYMENT_COUNT = Counter(
    "moonvpn_payment_total",
    "Total number of payments",
    ["method", "status"]
)

PAYMENT_AMOUNT = Counter(
    "moonvpn_payment_amount_total",
    "Total payment amount",
    ["method", "status"]
)


@contextmanager
def measure_latency(histogram: Histogram, labels: Dict[str, str] = None) -> Generator[None, None, None]:
    """
    Measure and record latency using a context manager.
    
    Args:
        histogram: Histogram to record latency
        labels: Labels for the histogram
    """
    start_time = time.time()
    try:
        yield
    finally:
        latency = time.time() - start_time
        if labels:
            histogram.labels(**labels).observe(latency)
        else:
            histogram.observe(latency)


def measure_request(method: str, endpoint: str) -> Callable:
    """
    Decorator to measure request latency and count.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                latency = time.time() - start_time
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        
        return wrapper
    
    return decorator


def measure_api_call(method: str, endpoint: str) -> Callable:
    """
    Decorator to measure API call latency and count.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                latency = time.time() - start_time
                API_CALL_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                API_CALL_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        
        return wrapper
    
    return decorator


def measure_db_operation(operation: str, model: str) -> Callable:
    """
    Decorator to measure database operation latency and count.
    
    Args:
        operation: Operation type (create, read, update, delete)
        model: Model name
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                latency = time.time() - start_time
                DB_OPERATION_COUNT.labels(operation=operation, model=model, status=status).inc()
                DB_OPERATION_LATENCY.labels(operation=operation, model=model).observe(latency)
        
        return wrapper
    
    return decorator


def track_cache_operation(operation: str, cache_type: str) -> Callable:
    """
    Decorator to track cache operations.
    
    Args:
        operation: Operation type (get, set, delete)
        cache_type: Cache type (redis, memory)
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start_time
                CACHE_OPERATION_LATENCY.labels(operation=operation, cache_type=cache_type).observe(latency)
                
                # Track cache hits/misses for get operations
                if operation == "get":
                    if result is not None:
                        CACHE_HIT_COUNT.labels(cache_type=cache_type).inc()
                    else:
                        CACHE_MISS_COUNT.labels(cache_type=cache_type).inc()
                
                return result
            except Exception:
                raise
        
        return wrapper
    
    return decorator


def update_panel_metrics(
    panel_id: int,
    panel_name: str,
    location: str,
    health_status: bool,
    response_time: float,
    client_count: int = None,
    inbound_count: int = None,
    online_client_count: int = None
) -> None:
    """
    Update panel metrics.
    
    Args:
        panel_id: Panel ID
        panel_name: Panel name
        location: Panel location
        health_status: Panel health status (True=healthy, False=unhealthy)
        response_time: Panel response time in seconds
        client_count: Number of clients on the panel
        inbound_count: Number of inbounds on the panel
        online_client_count: Number of online clients on the panel
    """
    PANEL_HEALTH_GAUGE.labels(
        panel_id=str(panel_id),
        panel_name=panel_name,
        location=location
    ).set(1 if health_status else 0)
    
    PANEL_RESPONSE_TIME.labels(
        panel_id=str(panel_id),
        panel_name=panel_name,
        location=location
    ).set(response_time)
    
    if client_count is not None:
        PANEL_CLIENT_COUNT.labels(
            panel_id=str(panel_id),
            panel_name=panel_name,
            location=location
        ).set(client_count)
    
    if inbound_count is not None:
        PANEL_INBOUND_COUNT.labels(
            panel_id=str(panel_id),
            panel_name=panel_name,
            location=location
        ).set(inbound_count)
    
    if online_client_count is not None:
        PANEL_ONLINE_CLIENT_COUNT.labels(
            panel_id=str(panel_id),
            panel_name=panel_name,
            location=location
        ).set(online_client_count)


def update_business_metrics(
    active_user_count: int = None,
    active_client_counts: Dict[str, int] = None,
    new_order: Optional[Dict[str, str]] = None,
    new_payment: Optional[Dict[str, Union[str, float]]] = None
) -> None:
    """
    Update business metrics.
    
    Args:
        active_user_count: Number of active users
        active_client_counts: Number of active clients by location
        new_order: Order details (status)
        new_payment: Payment details (method, status, amount)
    """
    if active_user_count is not None:
        ACTIVE_USER_COUNT.set(active_user_count)
    
    if active_client_counts:
        for location, count in active_client_counts.items():
            ACTIVE_CLIENT_COUNT.labels(location=location).set(count)
    
    if new_order:
        ORDER_COUNT.labels(status=new_order["status"]).inc()
    
    if new_payment:
        PAYMENT_COUNT.labels(
            method=new_payment["method"],
            status=new_payment["status"]
        ).inc()
        
        PAYMENT_AMOUNT.labels(
            method=new_payment["method"],
            status=new_payment["status"]
        ).inc(float(new_payment["amount"]))
