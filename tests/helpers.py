"""Helper functions for testing."""

import asyncio
import json
from typing import Any, Callable, Dict, Optional, Union
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
from .config import test_settings

async def create_test_user(
    db: AsyncSession,
    email: str = test_settings.TEST_USER_EMAIL,
    password: str = test_settings.TEST_USER_PASSWORD,
    full_name: str = test_settings.TEST_USER_FULL_NAME,
    is_active: bool = True,
    is_superuser: bool = False
) -> User:
    """Create a test user."""
    user_data = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "is_active": is_active,
        "is_superuser": is_superuser
    }
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_test_vpn_config(
    db: AsyncSession,
    user_id: int,
    name: str = "test_vpn_config",
    server: str = test_settings.TEST_VPN_SERVER,
    port: int = test_settings.TEST_VPN_PORT,
    protocol: str = test_settings.TEST_VPN_PROTOCOL,
    is_active: bool = True
) -> VPNConfig:
    """Create a test VPN configuration."""
    vpn_data = {
        "user_id": user_id,
        "name": name,
        "server": server,
        "port": port,
        "protocol": protocol,
        "is_active": is_active
    }
    vpn_config = VPNConfig(**vpn_data)
    db.add(vpn_config)
    await db.commit()
    await db.refresh(vpn_config)
    return vpn_config

async def create_test_payment(
    db: AsyncSession,
    user_id: int,
    amount: float = test_settings.TEST_PAYMENT_AMOUNT,
    currency: str = test_settings.TEST_PAYMENT_CURRENCY,
    status: str = test_settings.TEST_PAYMENT_STATUS
) -> Payment:
    """Create a test payment."""
    payment_data = {
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "status": status
    }
    payment = Payment(**payment_data)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment

async def create_test_telegram_user(
    db: AsyncSession,
    user_id: int,
    telegram_id: int = test_settings.TEST_TELEGRAM_USER_ID,
    username: str = test_settings.TEST_TELEGRAM_USERNAME,
    is_active: bool = True
) -> TelegramUser:
    """Create a test Telegram user."""
    telegram_data = {
        "user_id": user_id,
        "telegram_id": telegram_id,
        "username": username,
        "is_active": is_active
    }
    telegram_user = TelegramUser(**telegram_data)
    db.add(telegram_user)
    await db.commit()
    await db.refresh(telegram_user)
    return telegram_user

def create_test_token(user_id: int, expires_delta: Optional[int] = None) -> str:
    """Create a test JWT token."""
    return create_access_token(user_id, expires_delta)

async def wait_for_condition(
    condition_func: Callable[[], bool],
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """Wait for a condition to be met."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        if condition_func():
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
        current_path = f"{path}.{key}" if path else key
        assert key in response, f"Missing key: {current_path}"
        
        if isinstance(expected_type, dict):
            assert isinstance(response[key], dict), f"Expected dict for {current_path}"
            assert_response_schema(response[key], expected_type, current_path)
        elif isinstance(expected_type, list):
            assert isinstance(response[key], list), f"Expected list for {current_path}"
            if expected_type:
                for item in response[key]:
                    assert_response_schema(item, expected_type[0], f"{current_path}[]")
        else:
            assert isinstance(response[key], expected_type), \
                f"Expected {expected_type.__name__} for {current_path}, got {type(response[key]).__name__}"

def create_test_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Create test headers with optional authorization token."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def create_test_file(
    content: Union[str, bytes],
    filename: str,
    content_type: str = "text/plain"
) -> tuple[str, Union[str, bytes], str]:
    """Create a test file for upload testing."""
    return filename, content, content_type

async def clear_test_db(db: AsyncSession) -> None:
    """Clear all test data from the database."""
    await db.execute("DELETE FROM telegram_users")
    await db.execute("DELETE FROM payments")
    await db.execute("DELETE FROM vpn_configs")
    await db.execute("DELETE FROM users")
    await db.commit() 