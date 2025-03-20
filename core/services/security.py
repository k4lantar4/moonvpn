"""
Security Enhancement Service for V2Ray Telegram Bot.

This module provides advanced security features including request validation,
suspicious activity detection, and rate limiting.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import ipaddress
import aiohttp
import jwt
import bcrypt
import pyotp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database.models.security import User, Role, Permission, UserSession, SecurityEvent
from ..schemas.security import UserCreate, UserUpdate, Token, TokenPayload
from ..core.config import settings

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

class SecurityService:
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            hashed_password = self.get_password_hash(user_data.password)
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password,
                role_id=user_data.role_id,
                is_active=user_data.is_active,
                is_verified=user_data.is_verified,
                two_factor_enabled=user_data.two_factor_enabled
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_data.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = self.get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    async def create_user_session(self, user: User, ip_address: str, user_agent: str) -> Token:
        """Create a new user session."""
        # Create tokens
        access_token = self.create_access_token(
            data={"sub": user.id, "role": user.role.name}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.id, "role": user.role.name}
        )

        # Create session
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60
        )

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        try:
            payload = self.verify_token(refresh_token)
            if payload.type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            user = self.db.query(User).filter(User.id == payload.sub).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )

            session = self.db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            ).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            # Create new access token
            new_access_token = self.create_access_token(
                data={"sub": user.id, "role": user.role.name}
            )
            session.token = new_access_token
            self.db.commit()

            return Token(
                access_token=new_access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def revoke_session(self, user_id: int, session_id: int) -> bool:
        """Revoke a user session."""
        session = self.db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user_id
        ).first()
        if not session:
            return False

        session.is_active = False
        self.db.commit()
        return True

    async def verify_2fa(self, user_id: int, token: str) -> bool:
        """Verify 2FA token."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.two_factor_enabled or not user.two_factor_secret:
            return False

        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(token)

    async def enable_2fa(self, user_id: int) -> Dict[str, str]:
        """Enable 2FA for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        user.two_factor_enabled = True
        self.db.commit()

        return {
            "secret": secret,
            "qr_code": pyotp.totp.TOTP(secret).provisioning_uri(
                user.username,
                issuer_name="MoonVPN"
            )
        }

    async def log_security_event(self, event_data: Dict[str, Any]) -> SecurityEvent:
        """Log a security event."""
        event = SecurityEvent(**event_data)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event 