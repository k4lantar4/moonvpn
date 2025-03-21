"""
Advanced security middleware combining IP security and proxy detection.
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session

from ..core.config.security_config import security_settings
from ..database.session import SessionLocal
from ..services.security import SecurityService
from ..services.proxy_detection import ProxyDetectionService
from .ip_security_middleware import IPSecurityMiddleware

class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[list] = None,
        exclude_methods: Optional[list] = None,
        geoip_db_path: str = "GeoLite2-City.mmdb"
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.exclude_methods = exclude_methods or ["OPTIONS"]
        self.security_service = None
        self.proxy_service = None
        self.ip_security = IPSecurityMiddleware(
            app,
            exclude_paths,
            exclude_methods,
            geoip_db_path
        )

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip checks for excluded paths and methods
        if (
            request.url.path in self.exclude_paths or
            request.method in self.exclude_methods
        ):
            return await call_next(request)

        # Initialize services if not already done
        if not self.security_service:
            db = SessionLocal()
            self.security_service = SecurityService(db)
            self.proxy_service = ProxyDetectionService()

        try:
            # Run IP security checks first
            await self.ip_security.dispatch(request, call_next)

            # Check for proxy/VPN usage if enabled
            if (
                security_settings.PROXY_DETECTION_ENABLED and
                any(request.url.path.startswith(path.replace("*", ""))
                    for path in security_settings.PROXY_CHECK_ENDPOINTS)
            ):
                # Get client IP
                client_ip = request.client.host

                # Skip check for whitelisted IPs
                if client_ip not in security_settings.PROXY_WHITELIST:
                    proxy_check = await self.proxy_service.is_suspicious(request)

                    if proxy_check["is_suspicious"]:
                        # Log suspicious proxy activity
                        await self.security_service.log_security_event({
                            "event_type": "proxy_detected",
                            "severity": proxy_check["risk_level"],
                            "description": "Suspicious proxy/VPN activity detected",
                            "ip_address": client_ip,
                            "metadata": {
                                "proxy_check": proxy_check,
                                "method": request.method,
                                "path": request.url.path,
                                "user_agent": request.headers.get("user-agent")
                            }
                        })

                        # Block high-risk proxy connections if configured
                        if (
                            security_settings.PROXY_BLOCK_HIGH_RISK and
                            proxy_check["risk_level"] == "high"
                        ):
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Access denied: High-risk proxy detected"
                            )

            response = await call_next(request)

            # Add security headers
            for header, value in security_settings.SECURITY_HEADERS.items():
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

        except HTTPException:
            raise
        except Exception as e:
            # Log unexpected errors
            if self.security_service:
                await self.security_service.log_security_event({
                    "event_type": "error",
                    "severity": "error",
                    "description": f"Advanced security middleware error: {str(e)}",
                    "ip_address": request.client.host,
                    "metadata": {
                        "method": request.method,
                        "path": request.url.path,
                        "user_agent": request.headers.get("user-agent")
                    }
                })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            ) 