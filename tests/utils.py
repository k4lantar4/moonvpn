"""Test utilities for common operations."""

import asyncio
import json
from typing import Any, Dict, Optional, Union
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.models.user import User
from app.models.vpn_config import VPNConfig
from app.models.payment import Payment
from app.models.telegram_user import TelegramUser
from .constants import (
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    TEST_USER_USERNAME,
    TEST_VPN_NAME,
    TEST_VPN_SERVER,
    TEST_VPN_PORT,
    TEST_PAYMENT_AMOUNT,
    TEST_PAYMENT_CURRENCY,
    TEST_TELEGRAM_ID,
    TEST_TELEGRAM_USERNAME
)

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.base import Base
from app.db.base import engine

def get_test_db() -> AsyncSession:
    """Get a test database session."""
    return SessionLocal()

def get_test_client() -> TestClient:
    """Get a test client with test database."""
    return TestClient(app)

async def clear_test_db(db: AsyncSession) -> None:
    """Clear all tables in the test database."""
    for table in reversed(db.get_bind().metadata.sorted_tables):
        await db.execute(table.delete())
    await db.commit()

def create_test_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Create test headers with optional authorization token."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

async def wait_for_condition(
    condition_func,
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """Wait for a condition to be met."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
    return False

def assert_response_schema(
    response: Dict[str, Any],
    schema: Dict[str, Any],
    path: str = ""
) -> None:
    """Assert that a response matches a schema."""
    for key, expected_type in schema.items():
        full_path = f"{path}.{key}" if path else key
        assert key in response, f"Missing key: {full_path}"
        if isinstance(expected_type, dict):
            assert isinstance(response[key], dict), f"Expected dict for {full_path}"
            assert_response_schema(response[key], expected_type, full_path)
        else:
            assert isinstance(response[key], expected_type), \
                f"Expected {expected_type.__name__} for {full_path}, got {type(response[key]).__name__}"

def create_test_file(
    content: Union[str, bytes],
    filename: str,
    content_type: str = "text/plain"
) -> tuple[str, Union[str, bytes], str]:
    """Create a test file for upload testing."""
    return filename, content, content_type

async def create_test_user(
    db: AsyncSession,
    email: str = TEST_USER_EMAIL,
    password: str = TEST_USER_PASSWORD,
    username: str = TEST_USER_USERNAME,
    is_active: bool = True,
    is_superuser: bool = False
) -> User:
    """Create a test user."""
    user = User(
        email=email,
        username=username,
        is_active=is_active,
        is_superuser=is_superuser
    )
    user.set_password(password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_test_vpn_config(
    db: AsyncSession,
    user_id: int,
    name: str = TEST_VPN_NAME,
    server: str = TEST_VPN_SERVER,
    port: int = TEST_VPN_PORT,
    is_active: bool = True
) -> VPNConfig:
    """Create a test VPN configuration."""
    vpn_config = VPNConfig(
        name=name,
        server=server,
        port=port,
        is_active=is_active,
        user_id=user_id
    )
    db.add(vpn_config)
    await db.commit()
    await db.refresh(vpn_config)
    return vpn_config

async def create_test_payment(
    db: AsyncSession,
    user_id: int,
    amount: float = TEST_PAYMENT_AMOUNT,
    currency: str = TEST_PAYMENT_CURRENCY,
    status: str = "completed"
) -> Payment:
    """Create a test payment."""
    payment = Payment(
        amount=amount,
        currency=currency,
        status=status,
        user_id=user_id
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment

async def create_test_telegram_user(
    db: AsyncSession,
    user_id: int,
    telegram_id: int = TEST_TELEGRAM_ID,
    username: str = TEST_TELEGRAM_USERNAME,
    is_active: bool = True
) -> TelegramUser:
    """Create a test Telegram user."""
    telegram_user = TelegramUser(
        telegram_id=telegram_id,
        username=username,
        is_active=is_active,
        user_id=user_id
    )
    db.add(telegram_user)
    await db.commit()
    await db.refresh(telegram_user)
    return telegram_user

def create_test_token(user_id: int, expires_delta: Optional[int] = None) -> str:
    """Create a test JWT token."""
    return create_access_token(user_id, expires_delta) 