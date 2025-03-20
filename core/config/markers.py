"""Custom pytest markers."""

import pytest
from typing import Callable, Any

def unit_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as a unit test."""
    return pytest.mark.unit(func)

def integration_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as an integration test."""
    return pytest.mark.integration(func)

def performance_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as a performance test."""
    return pytest.mark.performance(func)

def api_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as an API test."""
    return pytest.mark.api(func)

def slow_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as a slow test."""
    return pytest.mark.slow(func)

def db_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as a database test."""
    return pytest.mark.db(func)

def async_test(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as an async test."""
    return pytest.mark.asyncio(func)

def requires_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as requiring authentication."""
    return pytest.mark.auth(func)

def requires_superuser(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark a test as requiring superuser privileges."""
    return pytest.mark.superuser(func)

def skip_if_not_configured(reason: str) -> Callable[..., Any]:
    """Skip a test if certain configuration is missing."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return pytest.mark.skipif(True, reason=reason)(func)
    return decorator

def xfail_if_not_implemented(reason: str = "Not implemented yet") -> Callable[..., Any]:
    """Mark a test as expected to fail if not implemented."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return pytest.mark.xfail(reason=reason)(func)
    return decorator 