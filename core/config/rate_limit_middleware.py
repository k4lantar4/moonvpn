"""
Rate limiting middleware for protecting against brute force attacks and DoS attempts.
"""
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session

from ..core.config.security_config import security_settings
from ..database.session import SessionLocal
from ..services.security import SecurityService

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[list] = None,
        exclude_methods: Optional[list] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.exclude_methods = exclude_methods or ["OPTIONS"]
        self.security_service = None
        self.rate_limit_cache: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for excluded paths and methods
        if (
            request.url.path in self.exclude_paths or
            request.method in self.exclude_methods or
            not security_settings.RATE_LIMIT_ENABLED
        ):
            return await call_next(request)

        # Initialize security service if not already done
        if not self.security_service:
            db = SessionLocal()
            self.security_service = SecurityService(db)

        # Get client identifier (IP or user ID if authenticated)
        client_id = self._get_client_identifier(request)
        if not client_id:
            return await call_next(request)

        # Check rate limit
        if not self._check_rate_limit(client_id, request):
            # Log rate limit exceeded event
            await self.security_service.log_security_event({
                "event_type": "rate_limit_exceeded",
                "severity": "warning",
                "description": f"Rate limit exceeded for {client_id}",
                "ip_address": request.client.host,
                "metadata": {
                    "method": request.method,
                    "path": request.url.path,
                    "user_agent": request.headers.get("user-agent")
                }
            })
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )

        # Update rate limit cache
        self._update_rate_limit(client_id)

        return await call_next(request)

    def _get_client_identifier(self, request: Request) -> Optional[str]:
        """Get client identifier for rate limiting."""
        # If user is authenticated, use user ID
        if hasattr(request.state, "user"):
            return f"user_{request.state.user.id}"

        # Otherwise, use IP address
        return request.client.host

    def _check_rate_limit(self, client_id: str, request: Request) -> bool:
        """Check if request is within rate limit."""
        now = datetime.utcnow()
        window = timedelta(seconds=security_settings.RATE_LIMIT_PERIOD)

        # Get request history for client
        request_history = self.rate_limit_cache.get(client_id, [])
        
        # Remove old requests outside the window
        request_history = [
            timestamp for timestamp in request_history
            if now - timestamp < window
        ]

        # Check if request count exceeds limit
        if len(request_history) >= security_settings.RATE_LIMIT_REQUESTS:
            return False

        # Update request history
        request_history.append(now)
        self.rate_limit_cache[client_id] = request_history

        return True

    def _update_rate_limit(self, client_id: str):
        """Update rate limit cache."""
        now = datetime.utcnow()
        window = timedelta(seconds=security_settings.RATE_LIMIT_PERIOD)

        # Get request history for client
        request_history = self.rate_limit_cache.get(client_id, [])
        
        # Remove old requests outside the window
        request_history = [
            timestamp for timestamp in request_history
            if now - timestamp < window
        ]

        # Add new request
        request_history.append(now)
        self.rate_limit_cache[client_id] = request_history

    def _cleanup_old_entries(self):
        """Clean up old entries from rate limit cache."""
        now = datetime.utcnow()
        window = timedelta(seconds=security_settings.RATE_LIMIT_PERIOD)

        for client_id in list(self.rate_limit_cache.keys()):
            request_history = [
                timestamp for timestamp in self.rate_limit_cache[client_id]
                if now - timestamp < window
            ]
            
            if request_history:
                self.rate_limit_cache[client_id] = request_history
            else:
                del self.rate_limit_cache[client_id] 