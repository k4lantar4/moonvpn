from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from app.models.user import User
from app.models.vpn_config import VPNConfig
from app.models.payment import Payment
from app.models.telegram_user import TelegramUser
from app.schemas.vpn_config import VPNConfigCreate
from app.schemas.payment import PaymentCreate
from app.schemas.telegram_user import TelegramUserCreate

def create_test_user(
    email: str = f"test_{uuid4()}@example.com",
    username: str = f"test_user_{uuid4()}",
    password: str = "test_password123",
    is_active: bool = True,
    is_superuser: bool = False
) -> User:
    """Create a test user with default or custom values."""
    return User(
        email=email,
        username=username,
        hashed_password=password,  # In real tests, this should be hashed
        is_active=is_active,
        is_superuser=is_superuser
    )

def create_test_vpn_config(
    user_id: int,
    name: str = f"test_config_{uuid4()}",
    server: str = "test.server.com",
    port: int = 1194,
    protocol: str = "udp",
    cipher: str = "AES-256-CBC",
    auth: str = "SHA256",
    ca_cert: str = "test_ca_cert",
    client_cert: str = "test_client_cert",
    client_key: str = "test_client_key",
    tls_auth: Optional[str] = "test_tls_auth",
    is_active: bool = True
) -> VPNConfig:
    """Create a test VPN configuration."""
    config_data = VPNConfigCreate(
        name=name,
        server=server,
        port=port,
        protocol=protocol,
        cipher=cipher,
        auth=auth,
        ca_cert=ca_cert,
        client_cert=client_cert,
        client_key=client_key,
        tls_auth=tls_auth,
        is_active=is_active
    )
    return VPNConfig(**config_data.dict(), user_id=user_id)

def create_test_payment(
    user_id: int,
    amount: float = 10.0,
    currency: str = "USD",
    payment_method: str = "credit_card",
    status: str = "completed",
    transaction_id: str = f"test_tx_{uuid4()}",
    created_at: Optional[datetime] = None
) -> Payment:
    """Create a test payment record."""
    if created_at is None:
        created_at = datetime.utcnow()
    
    payment_data = PaymentCreate(
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        status=status,
        transaction_id=transaction_id
    )
    return Payment(**payment_data.dict(), user_id=user_id, created_at=created_at)

def create_test_telegram_user(
    user_id: int,
    telegram_id: int = 123456789,
    username: str = f"test_telegram_{uuid4()}",
    first_name: str = "Test",
    last_name: Optional[str] = "User",
    is_active: bool = True
) -> TelegramUser:
    """Create a test Telegram user."""
    telegram_data = TelegramUserCreate(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active
    )
    return TelegramUser(**telegram_data.dict(), user_id=user_id)

def create_test_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a test JWT token."""
    from app.core.security import create_access_token
    return create_access_token(
        data={"sub": str(user_id)},
        expires_delta=expires_delta or timedelta(minutes=15)
    ) 