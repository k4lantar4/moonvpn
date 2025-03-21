from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.vpn import VPNConfig, Subscription
from app.models.payment import Payment
from app.models.telegram import TelegramUser
from app.core.security import get_password_hash

async def create_test_user(
    db_session: AsyncSession,
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
    is_active: bool = True,
    is_superuser: bool = False,
    **kwargs: Any
) -> User:
    """Create a test user."""
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
        **kwargs
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

async def create_test_vpn_config(
    db_session: AsyncSession,
    user_id: int,
    server: str = "test.vpn.server",
    port: int = 1194,
    protocol: str = "udp",
    is_active: bool = True,
    **kwargs: Any
) -> VPNConfig:
    """Create a test VPN configuration."""
    vpn_config = VPNConfig(
        user_id=user_id,
        server=server,
        port=port,
        protocol=protocol,
        is_active=is_active,
        **kwargs
    )
    db_session.add(vpn_config)
    await db_session.commit()
    await db_session.refresh(vpn_config)
    return vpn_config

async def create_test_subscription(
    db_session: AsyncSession,
    user_id: int,
    plan_type: str = "premium",
    duration_days: int = 30,
    is_active: bool = True,
    **kwargs: Any
) -> Subscription:
    """Create a test subscription."""
    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        duration_days=duration_days,
        is_active=is_active,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=duration_days),
        **kwargs
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription

async def create_test_payment(
    db_session: AsyncSession,
    user_id: int,
    amount: float = 29.99,
    currency: str = "USD",
    status: str = "pending",
    **kwargs: Any
) -> Payment:
    """Create a test payment."""
    payment = Payment(
        user_id=user_id,
        amount=amount,
        currency=currency,
        status=status,
        created_at=datetime.utcnow(),
        **kwargs
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment

async def create_test_telegram_user(
    db_session: AsyncSession,
    user_id: int,
    telegram_id: int = 123456789,
    username: Optional[str] = "testuser",
    first_name: Optional[str] = "Test",
    last_name: Optional[str] = "User",
    is_active: bool = True,
    **kwargs: Any
) -> TelegramUser:
    """Create a test Telegram user."""
    telegram_user = TelegramUser(
        user_id=user_id,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        **kwargs
    )
    db_session.add(telegram_user)
    await db_session.commit()
    await db_session.refresh(telegram_user)
    return telegram_user

def get_test_user_data(**kwargs: Any) -> Dict[str, Any]:
    """Get test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        **kwargs
    }

def get_test_admin_data(**kwargs: Any) -> Dict[str, Any]:
    """Get test admin data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True,
        **kwargs
    }

def get_test_token_data(
    user_id: int,
    expires_delta: timedelta = timedelta(minutes=15)
) -> Dict[str, Any]:
    """Generate test token data."""
    expire = datetime.utcnow() + expires_delta
    return {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }

async def create_test_admin(
    db: AsyncSession,
    email: str = "admin@example.com",
    password: str = "adminpassword123",
    full_name: str = "Admin User",
    phone: str = "+989123456788"
) -> User:
    """Create a test admin user in the database."""
    return await create_test_user(
        db=db,
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        is_active=True,
        is_superuser=True
    ) 