"""
IP security middleware for handling IP blocking and geolocation-based security.
"""
from typing import Optional, Callable
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session
import geoip2.database
import math

from ..core.config.security_config import security_settings
from ..database.session import SessionLocal
from ..services.security import SecurityService
from ..database.models.security import BlockedIP, UserLocation

class IPSecurityMiddleware(BaseHTTPMiddleware):
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
        self.geoip_reader = None
        if security_settings.GEOLOCATION_ENABLED:
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db_path)
            except Exception as e:
                print(f"Warning: GeoIP database not loaded: {e}")

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip checks for excluded paths and methods
        if (
            request.url.path in self.exclude_paths or
            request.method in self.exclude_methods
        ):
            return await call_next(request)

        # Initialize security service if not already done
        if not self.security_service:
            db = SessionLocal()
            self.security_service = SecurityService(db)

        try:
            # Get client IP
            client_ip = request.client.host

            # Check if IP is blocked
            if await self._is_ip_blocked(client_ip):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: IP is blocked"
                )

            # Check geolocation if enabled and user is authenticated
            if (
                security_settings.GEOLOCATION_ENABLED and
                hasattr(request.state, "user") and
                self.geoip_reader
            ):
                if await self._check_geolocation_anomaly(request):
                    # Log suspicious activity
                    await self.security_service.log_security_event({
                        "event_type": "geolocation_anomaly",
                        "severity": "warning",
                        "description": "Suspicious login location detected",
                        "ip_address": client_ip,
                        "user_id": request.state.user.id,
                        "metadata": {
                            "method": request.method,
                            "path": request.url.path,
                            "user_agent": request.headers.get("user-agent")
                        }
                    })

                    # Block IP if configured to do so
                    if security_settings.IP_BLOCK_ENABLED:
                        await self._block_ip(
                            client_ip,
                            "Suspicious geolocation activity",
                            security_settings.IP_BLOCK_DURATION
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied: Suspicious location"
                        )

            return await call_next(request)

        except HTTPException:
            raise
        except Exception as e:
            # Log unexpected errors
            if self.security_service:
                await self.security_service.log_security_event({
                    "event_type": "error",
                    "severity": "error",
                    "description": f"IP security middleware error: {str(e)}",
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

    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked."""
        blocked_ip = self.security_service.db.query(BlockedIP).filter(
            BlockedIP.ip_address == ip,
            BlockedIP.expires_at > datetime.utcnow()
        ).first()
        return blocked_ip is not None

    async def _block_ip(self, ip: str, reason: str, duration: int):
        """Block an IP address."""
        blocked_ip = BlockedIP(
            ip_address=ip,
            reason=reason,
            blocked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=duration)
        )
        self.security_service.db.add(blocked_ip)
        self.security_service.db.commit()

    async def _check_geolocation_anomaly(self, request: Request) -> bool:
        """Check for suspicious geolocation activity."""
        try:
            # Get current location from IP
            ip_info = self.geoip_reader.city(request.client.host)
            current_location = {
                "latitude": ip_info.location.latitude,
                "longitude": ip_info.location.longitude,
                "country": ip_info.country.iso_code,
                "city": ip_info.city.name
            }

            # Get user's last known location
            last_location = self.security_service.db.query(UserLocation).filter(
                UserLocation.user_id == request.state.user.id
            ).order_by(UserLocation.timestamp.desc()).first()

            if last_location:
                # Calculate distance between locations
                distance = self._calculate_distance(
                    last_location.latitude,
                    last_location.longitude,
                    current_location["latitude"],
                    current_location["longitude"]
                )

                # Check if distance exceeds maximum allowed
                if distance > security_settings.MAX_DISTANCE_KM:
                    return True

            # Update user location
            new_location = UserLocation(
                user_id=request.state.user.id,
                ip_address=request.client.host,
                country=current_location["country"],
                city=current_location["city"],
                latitude=current_location["latitude"],
                longitude=current_location["longitude"]
            )
            self.security_service.db.add(new_location)
            self.security_service.db.commit()

            return False

        except Exception as e:
            # Log error but don't block access on geolocation check failure
            print(f"Geolocation check failed: {e}")
            return False

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula."""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c 