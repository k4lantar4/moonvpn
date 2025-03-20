"""Logging utility module."""
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

# Get loggers
logger = logging.getLogger("app")
access_logger = logging.getLogger("app.access")
performance_logger = logging.getLogger("app.performance")
error_logger = logging.getLogger("app.error")

def log_access(
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    response_time: Optional[float] = None,
) -> None:
    """Log access information."""
    access_logger.info(
        "Access log",
        extra={
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
        }
    )

def log_performance(
    operation: str,
    duration: float,
    resource_usage: Optional[dict] = None,
    additional_info: Optional[dict] = None,
) -> None:
    """Log performance metrics."""
    log_data = {
        "operation": operation,
        "duration": duration,
        "resource_usage": resource_usage or {},
        "additional_info": additional_info or {},
    }
    performance_logger.info("Performance log", extra=log_data)

def log_error(
    error: Exception,
    context: Optional[dict] = None,
    user_id: Optional[int] = None,
    severity: str = "ERROR",
) -> None:
    """Log error information."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
        "user_id": user_id,
        "severity": severity,
    }
    error_logger.error("Error log", extra=error_data)

def log_info(message: str, extra: Optional[dict] = None) -> None:
    """Log general information."""
    logger.info(message, extra=extra or {})

def log_warning(message: str, extra: Optional[dict] = None) -> None:
    """Log warning information."""
    logger.warning(message, extra=extra or {})

def log_debug(message: str, extra: Optional[dict] = None) -> None:
    """Log debug information."""
    logger.debug(message, extra=extra or {})

def measure_performance(operation_name: str) -> Callable:
    """Decorator to measure and log function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(
                    operation=operation_name,
                    duration=duration,
                    additional_info={"args": str(args), "kwargs": str(kwargs)}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_error(
                    error=e,
                    context={
                        "operation": operation_name,
                        "duration": duration,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                )
                raise
        return wrapper
    return decorator 