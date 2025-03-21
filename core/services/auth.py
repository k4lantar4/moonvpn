"""
Authentication service for handling user authentication and session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import jwt
import bcrypt
from fastapi import HTTPException, status
from pyotp import TOTP

from core.config import settings
from core.database.models import User
from core.schemas.auth import TokenPayload, LoginRequest, RegisterRequest, PasswordResetRequest
from core.exceptions import SecurityError

class AuthenticationService:
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with username and password."""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            if not user or not self._verify_password(password, user.password_hash):
                raise SecurityError("Invalid credentials")

            # Check if 2FA is enabled
            if user.two_factor_enabled:
                return {"requires_2fa": True, "user_id": user.id}

            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)

            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user_id": user.id
            }

        except Exception as e:
            raise SecurityError(f"Authentication failed: {str(e)}")

    async def verify_2fa(self, user_id: int, code: str) -> Dict[str, Any]:
        """Verify 2FA code and return tokens if valid."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.two_factor_enabled:
                raise SecurityError("2FA not enabled")

            totp = TOTP(user.two_factor_secret)
            if not totp.verify(code):
                raise SecurityError("Invalid 2FA code")

            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)

            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user_id": user.id
            }

        except Exception as e:
            raise SecurityError(f"2FA verification failed: {str(e)}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            payload = self._verify_token(refresh_token)
            user = self.db.query(User).filter(User.id == payload["sub"]).first()
            if not user:
                raise SecurityError("User not found")

            # Generate new access token
            access_token = self._create_access_token(user)

            return {
                "access_token": access_token,
                "token_type": "bearer"
            }

        except Exception as e:
            raise SecurityError(f"Token refresh failed: {str(e)}")

    async def enable_2fa(self, user_id: int) -> Dict[str, Any]:
        """Enable 2FA for user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise SecurityError("User not found")

            # Generate 2FA secret
            secret = TOTP.generate_secret()
            user.two_factor_secret = secret
            user.two_factor_enabled = True
            self.db.commit()

            # Generate QR code URL
            totp = TOTP(secret)
            qr_code_url = totp.provisioning_uri(
                user.username,
                issuer_name=settings.TWO_FACTOR_ISSUER
            )

            return {
                "secret": secret,
                "qr_code_url": qr_code_url
            }

        except Exception as e:
            raise SecurityError(f"Failed to enable 2FA: {str(e)}")

    async def disable_2fa(self, user_id: int, code: str) -> bool:
        """Disable 2FA for user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.two_factor_enabled:
                raise SecurityError("2FA not enabled")

            # Verify code
            totp = TOTP(user.two_factor_secret)
            if not totp.verify(code):
                raise SecurityError("Invalid 2FA code")

            # Disable 2FA
            user.two_factor_enabled = False
            user.two_factor_secret = None
            self.db.commit()

            return True

        except Exception as e:
            raise SecurityError(f"Failed to disable 2FA: {str(e)}")

    def _create_access_token(self, user: User) -> str:
        """Create access token."""
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def _create_refresh_token(self, user: User) -> str:
        """Create refresh token."""
        to_encode = {
            "sub": user.id,
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire)
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def _verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.JWTError:
            raise SecurityError("Invalid token")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def register_user(self, data: RegisterRequest) -> User:
        """Register a new user."""
        # Check if user exists
        if self.db.query(User).filter(User.email == data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new user
        user = User(
            username=data.username,
            email=data.email,
            password_hash=self.get_password_hash(data.password),
            status="active",
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def reset_password(self, data: PasswordResetRequest) -> bool:
        """Request password reset."""
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            # Don't reveal if email exists
            return True
            
        # Generate reset token
        reset_token = self._create_access_token(user)
        
        # TODO: Send reset email with token
        # For now, just return success
        return True
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify a JWT token."""
        try:
            payload = self._verify_token(token)
            return TokenPayload(**payload)
        except Exception as e:
            raise SecurityError(f"Could not validate credentials: {str(e)}")
    
    def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        payload = self.verify_token(token)
        user = self.db.query(User).filter(User.id == payload.sub).first()
        if not user:
            raise SecurityError("User not found")
        return user 