"""
Security headers middleware for adding security headers to all responses.
"""
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.config.security_config import security_settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = security_settings.SECURITY_HEADERS

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers to response
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Add CORS headers if enabled
        if security_settings.CORS_ENABLED:
            response.headers["Access-Control-Allow-Origin"] = ", ".join(
                security_settings.CORS_ORIGINS
            )
            response.headers["Access-Control-Allow-Methods"] = ", ".join(
                security_settings.CORS_METHODS
            )
            response.headers["Access-Control-Allow-Headers"] = ", ".join(
                security_settings.CORS_HEADERS
            )
            if security_settings.CORS_CREDENTIALS:
                response.headers["Access-Control-Allow-Credentials"] = "true"

        return response 