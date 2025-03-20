"""
Security middleware for integrating security features into the application.
"""
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from datetime import datetime

from ..core.config.security_config import security_settings
from ..services.security_monitoring import SecurityMonitoringService
from ..services.notification import NotificationService
from ..core.exceptions import SecurityError

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        monitoring_service: Optional[SecurityMonitoringService] = None,
        notification_service: Optional[NotificationService] = None
    ):
        super().__init__(app)
        self.monitoring_service = monitoring_service
        self.notification_service = notification_service
        self.rate_limit_cache: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next):
        try:
            # Start timing the request
            start_time = time.time()

            # Apply security headers
            response = await call_next(request)
            self._add_security_headers(response)

            # Check rate limiting
            if security_settings.RATE_LIMIT_ENABLED:
                await self._check_rate_limit(request)

            # Log security event
            await self._log_security_event(request, response, start_time)

            return response

        except SecurityError as e:
            # Handle security-related errors
            logger.error(f"Security error: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={"detail": str(e)}
            )
        except Exception as e:
            # Handle other errors
            logger.error(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    def _add_security_headers(self, response: Response):
        """Add security headers to the response."""
        for header, value in security_settings.SECURITY_HEADERS.items():
            response.headers[header] = value

    async def _check_rate_limit(self, request: Request):
        """Check if the request exceeds rate limits."""
        client_ip = request.client.host
        current_time = time.time()

        # Get or initialize rate limit data for this IP
        if client_ip not in self.rate_limit_cache:
            self.rate_limit_cache[client_ip] = {
                "requests": 0,
                "window_start": current_time
            }

        rate_limit_data = self.rate_limit_cache[client_ip]

        # Check if we need to reset the window
        if current_time - rate_limit_data["window_start"] > security_settings.RATE_LIMIT_WINDOW:
            rate_limit_data["requests"] = 0
            rate_limit_data["window_start"] = current_time

        # Check if rate limit is exceeded
        if rate_limit_data["requests"] >= security_settings.RATE_LIMIT_MAX_REQUESTS:
            # Log rate limit exceeded event
            if self.monitoring_service:
                await self.monitoring_service._create_alert(
                    "high",
                    f"Rate limit exceeded for IP: {client_ip}",
                    {
                        "event_type": "rate_limit_exceeded",
                        "ip_address": client_ip,
                        "request_count": rate_limit_data["requests"],
                        "threshold": security_settings.RATE_LIMIT_MAX_REQUESTS
                    }
                )

            # Block the IP
            raise SecurityError(
                f"Rate limit exceeded. Please try again in {security_settings.RATE_LIMIT_BLOCK_DURATION} seconds."
            )

        # Increment request count
        rate_limit_data["requests"] += 1

    async def _log_security_event(
        self,
        request: Request,
        response: Response,
        start_time: float
    ):
        """Log security event for monitoring."""
        if not self.monitoring_service:
            return

        # Calculate request duration
        duration = time.time() - start_time

        # Prepare event data
        event_data = {
            "event_type": "http_request",
            "severity": "info",
            "description": f"HTTP {request.method} {request.url.path}",
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "status_code": response.status_code,
            "duration": duration,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "path_params": request.path_params
        }

        # Add user information if available
        if hasattr(request.state, "user"):
            event_data["user_id"] = request.state.user.id

        # Check for suspicious patterns
        if self._is_suspicious_request(request, response):
            event_data["severity"] = "warning"
            event_data["description"] += " (Suspicious activity detected)"

        # Create security event
        await self.monitoring_service._create_alert(
            event_data["severity"],
            event_data["description"],
            event_data
        )

    def _is_suspicious_request(self, request: Request, response: Response) -> bool:
        """Check if the request shows suspicious patterns."""
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["curl", "wget", "python-requests", "go-http-client"]
        if any(agent in user_agent for agent in suspicious_agents):
            return True

        # Check for suspicious paths
        suspicious_paths = ["/admin", "/wp-admin", "/phpmyadmin", "/.env"]
        if any(path in request.url.path.lower() for path in suspicious_paths):
            return True

        # Check for suspicious query parameters
        suspicious_params = ["select", "union", "insert", "update", "delete", "drop"]
        query_params = request.query_params
        if any(param in str(query_params).lower() for param in suspicious_params):
            return True

        # Check for high error rates
        if response.status_code >= 400:
            return True

        return False

    async def cleanup(self):
        """Clean up rate limit cache."""
        current_time = time.time()
        expired_ips = [
            ip for ip, data in self.rate_limit_cache.items()
            if current_time - data["window_start"] > security_settings.RATE_LIMIT_WINDOW
        ]
        for ip in expired_ips:
            del self.rate_limit_cache[ip] 