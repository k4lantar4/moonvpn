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
from app.models.user import User
from app.core.security import create_access_token

class TestBase:
    """Base class for all tests."""
    
    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession) -> AsyncGenerator[None, None]:
        """Setup test environment."""
        await clear_test_db(db_session)
        yield
        await db_session.rollback()
    
    @pytest.fixture
    async def db(self, db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        yield db_session
    
    @pytest.fixture
    def client(self) -> Generator[TestClient, None, None]:
        """Get test client."""
        with TestClient(app) as c:
            yield c
    
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
    
    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> User:
        """Create test user."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False
        }
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_user_token(self, test_user: User) -> str:
        """Get test user token."""
        return create_access_token(test_user.id)
    
    @pytest.fixture
    async def test_superuser(self, db_session: AsyncSession) -> User:
        """Create test superuser."""
        user_data = {
            "email": "admin@example.com",
            "password": "adminpassword123",
            "full_name": "Admin User",
            "is_active": True,
            "is_superuser": True
        }
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_superuser_token(self, test_superuser: User) -> str:
        """Get test superuser token."""
        return create_access_token(test_superuser.id)
    
    @pytest.fixture
    def test_user_data(self) -> dict:
        """Get test user data."""
        return {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False
        }
    
    @pytest.fixture
    def test_superuser_data(self) -> dict:
        """Get test superuser data."""
        return {
            "email": "admin@example.com",
            "password": "adminpassword123",
            "full_name": "Admin User",
            "is_active": True,
            "is_superuser": True
        }
    
    async def create_test_user(self, db_session: AsyncSession, **kwargs) -> User:
        """Create a test user with custom data."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False,
            **kwargs
        }
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    def get_auth_headers(self, token: str) -> dict:
        """Get authentication headers."""
        return {"Authorization": f"Bearer {token}"}
    
    def assert_response(self, response, status_code: int = 200):
        """Assert response status code."""
        assert response.status_code == status_code
    
    def assert_response_data(self, response, expected_data: dict):
        """Assert response data matches expected data."""
        data = response.json()
        for key, value in expected_data.items():
            assert data[key] == value
    
    def assert_response_list(self, response, expected_length: int = None):
        """Assert response is a list with expected length."""
        data = response.json()
        assert isinstance(data, list)
        if expected_length is not None:
            assert len(data) == expected_length
    
    def assert_response_error(self, response, status_code: int, error_message: str):
        """Assert response is an error with expected message."""
        assert response.status_code == status_code
        data = response.json()
        assert error_message in data["detail"]
    
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