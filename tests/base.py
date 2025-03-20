"""Base class for all tests."""

import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.base import Base
from app.main import app
from .config import test_settings
from .helpers import (
    create_test_user,
    create_test_vpn_config,
    create_test_payment,
    create_test_telegram_user,
    create_test_token,
    wait_for_condition,
    assert_response_schema,
    create_test_headers,
    clear_test_db
)

class TestBase:
    """Base class for all tests."""
    
    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession):
        """Setup and teardown for each test."""
        await clear_test_db(db_session)
        yield
        await clear_test_db(db_session)
    
    @pytest.fixture
    async def db(self, db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        yield db_session
    
    @pytest.fixture
    def client(self) -> Generator[TestClient, None, None]:
        """Get test client."""
        with TestClient(app) as test_client:
            yield test_client
    
    @pytest.fixture
    def test_settings(self):
        """Get test settings."""
        return test_settings
    
    async def wait_for_condition(
        self,
        condition_func,
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a condition to be met."""
        return await wait_for_condition(condition_func, timeout, interval)
    
    def assert_response_schema(
        self,
        response: dict,
        schema: dict,
        path: str = ""
    ) -> None:
        """Assert that a response matches a schema."""
        assert_response_schema(response, schema, path)
    
    def create_test_headers(self, token: str = None) -> dict:
        """Create test headers with optional authorization token."""
        return create_test_headers(token)
    
    async def create_test_user(
        self,
        db: AsyncSession,
        email: str = test_settings.TEST_USER_EMAIL,
        password: str = test_settings.TEST_USER_PASSWORD,
        username: str = test_settings.TEST_USER_USERNAME,
        is_active: bool = True,
        is_superuser: bool = False
    ):
        """Create a test user."""
        return await create_test_user(
            db,
            email,
            password,
            username,
            is_active,
            is_superuser
        )
    
    async def create_test_vpn_config(
        self,
        db: AsyncSession,
        user_id: int,
        name: str = "test_vpn_config",
        server: str = test_settings.TEST_VPN_SERVER,
        port: int = test_settings.TEST_VPN_PORT,
        is_active: bool = True
    ):
        """Create a test VPN configuration."""
        return await create_test_vpn_config(
            db,
            user_id,
            name,
            server,
            port,
            is_active
        )
    
    async def create_test_payment(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float = 10.0,
        currency: str = "USD",
        status: str = "completed"
    ):
        """Create a test payment."""
        return await create_test_payment(
            db,
            user_id,
            amount,
            currency,
            status
        )
    
    async def create_test_telegram_user(
        self,
        db: AsyncSession,
        user_id: int,
        telegram_id: int = 123456789,
        username: str = "test_telegram_user",
        is_active: bool = True
    ):
        """Create a test Telegram user."""
        return await create_test_telegram_user(
            db,
            user_id,
            telegram_id,
            username,
            is_active
        )
    
    def create_test_token(self, user_id: int, expires_delta: int = None) -> str:
        """Create a test JWT token."""
        return create_test_token(user_id, expires_delta) 