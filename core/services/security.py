"""
Security Enhancement Service for V2Ray Telegram Bot.

This module provides advanced security features including request validation,
suspicious activity detection, and rate limiting.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import ipaddress
import aiohttp

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests: Dict[str, List[datetime]] = {}

    async def is_rate_limited(self, key: str) -> bool:
        now = datetime.now()
        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < timedelta(seconds=self.time_window)
        ]

        # Check if limit exceeded
        if len(self.requests[key]) >= self.max_requests:
            return True

        # Add new request
        self.requests[key].append(now)
        return False

class SecurityEnhancer:
    def __init__(self, config: dict, db_connection, notification_service):
        self.config = config
        self.db = db_connection
        self.notifier = notification_service
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_activities: Dict[str, List[dict]] = {}
        self.rate_limiters = {
            'login': RateLimiter(5, 300),  # 5 attempts per 5 minutes
            'payment': RateLimiter(10, 3600),  # 10 attempts per hour
            'api': RateLimiter(100, 60)  # 100 requests per minute
        }

    async def setup_security(self):
        """Initialize security components"""
        await self._setup_firewall_rules()
        await self._setup_ddos_protection()
        await self._setup_intrusion_detection()
        await self._load_blocked_ips()

    async def validate_request(self, request: dict) -> bool:
        """Validate incoming requests"""
        try:
            ip = request.get('ip')
            user_id = request.get('user_id')
            action = request.get('action')

            # Basic validation
            if not all([ip, action]):
                return False

            # Check if IP is blocked
            if await self._is_ip_blocked(ip):
                await self._log_security_event(
                    'blocked_ip_attempt',
                    {'ip': ip, 'action': action}
                )
                return False

            # Rate limiting check
            if not await self._check_rate_limit(ip, action):
                await self._handle_rate_limit_exceeded(ip, user_id)
                return False

            # Suspicious activity detection
            if await self._detect_suspicious_activity(request):
                await self._handle_suspicious_activity(ip, user_id)
                return False

            return True

        except Exception as e:
            await self._log_security_event(
                'security_validation_error',
                {'error': str(e), 'request': request}
            )
            return False

    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        if ip in self.blocked_ips:
            block_time = self.blocked_ips[ip]
            if datetime.now() - block_time < timedelta(hours=24):
                return True
            else:
                del self.blocked_ips[ip]
        return False

    async def _check_rate_limit(self, ip: str, action: str) -> bool:
        """Check if request exceeds rate limit"""
        limiter = self.rate_limiters.get(action, self.rate_limiters['api'])
        return not await limiter.is_rate_limited(ip)

    async def _detect_suspicious_activity(self, request: dict) -> bool:
        """Check for suspicious patterns"""
        checks = [
            self._check_multiple_failed_logins,
            self._check_unusual_traffic_patterns,
            self._check_geolocation_anomalies,
            self._check_proxy_usage
        ]

        for check in checks:
            if await check(request):
                return True

        return False

    async def _check_multiple_failed_logins(self, request: dict) -> bool:
        """Check for multiple failed login attempts"""
        ip = request.get('ip')
        if not ip:
            return False

        failed_attempts = await self.db.login_attempts.count_documents({
            'ip': ip,
            'success': False,
            'timestamp': {
                '$gte': datetime.now() - timedelta(minutes=15)
            }
        })

        return failed_attempts >= 5

    async def _check_unusual_traffic_patterns(self, request: dict) -> bool:
        """Check for unusual traffic patterns"""
        user_id = request.get('user_id')
        if not user_id:
            return False

        # Get user's average daily requests
        daily_stats = await self.db.user_activity.find_one({
            'user_id': user_id,
            'date': datetime.now().date()
        })

        if daily_stats:
            avg_requests = daily_stats.get('average_requests', 0)
            current_requests = daily_stats.get('current_requests', 0)
            return current_requests > avg_requests * 3

        return False

    async def _check_geolocation_anomalies(self, request: dict) -> bool:
        """Check for suspicious location changes"""
        user_id = request.get('user_id')
        ip = request.get('ip')
        if not all([user_id, ip]):
            return False

        try:
            # Get IP geolocation
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ip-api.com/json/{ip}") as response:
                    location_data = await response.json()

            # Get user's last known location
            last_location = await self.db.user_locations.find_one({
                'user_id': user_id
            }, sort=[('timestamp', -1)])

            if last_location:
                # Calculate distance between locations
                if self._calculate_location_distance(
                    last_location['location'],
                    location_data
                ) > 1000:  # More than 1000km
                    return True

            # Update user's location history
            await self.db.user_locations.insert_one({
                'user_id': user_id,
                'ip': ip,
                'location': location_data,
                'timestamp': datetime.now()
            })

            return False

        except Exception:
            return False

    async def _check_proxy_usage(self, request: dict) -> bool:
        """Check if request is coming through proxy/VPN"""
        ip = request.get('ip')
        if not ip:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://proxycheck.io/v2/{ip}?key={self.config['proxycheck_api_key']}"
                ) as response:
                    proxy_data = await response.json()

            return proxy_data.get(ip, {}).get('proxy') == 'yes'

        except Exception:
            return False

    async def _handle_suspicious_activity(self, ip: str, user_id: Optional[int]):
        """Handle detected suspicious activity"""
        # Block IP temporarily
        self.blocked_ips[ip] = datetime.now()

        # Log suspicious activity
        await self._log_security_event(
            'suspicious_activity',
            {
                'ip': ip,
                'user_id': user_id,
                'timestamp': datetime.now()
            }
        )

        # Notify admins
        await self.notifier.notify_admin(
            f"🚨 Suspicious activity detected!\n"
            f"IP: {ip}\n"
            f"User ID: {user_id or 'Unknown'}\n"
            f"Time: {datetime.now()}"
        )

    async def _log_security_event(self, event_type: str, data: dict):
        """Log security-related events"""
        try:
            await self.db.security_events.insert_one({
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.now()
            })
        except Exception as e:
            await self.notifier.notify_admin(
                f"Error logging security event: {str(e)}"
            ) 