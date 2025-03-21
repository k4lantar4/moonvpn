"""
Base test configuration and fixtures.
"""

import os
import pytest
from typing import Generator, Dict, Any, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import get_db
from core.database.base import Base
from main import app
from core.config import settings
from core.security import create_access_token
from models.user import User
from models.vpn_config import VPNConfig
from models.payment import Payment
from models.telegram_user import TelegramUser
from .fixtures import test_engine, test_async_session
from .config import test_settings

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test.db"
)

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)

# Create test session factory
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture(scope="session")
def db_engine() -> Generator:
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def db(db_session: Session) -> Generator[Session, None, None]:
    """Get database session."""
    yield db_session

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_vpn_config(db_session: Session, test_user: User) -> VPNConfig:
    """Create test VPN configuration."""
    vpn_config = VPNConfig(
        user_id=test_user.id,
        config_name="test_config",
        config_data="test_config_data",
        is_active=True
    )
    db_session.add(vpn_config)
    db_session.commit()
    db_session.refresh(vpn_config)
    return vpn_config

@pytest.fixture(scope="function")
def test_payment(db_session: Session, test_user: User) -> Payment:
    """Create test payment."""
    payment = Payment(
        user_id=test_user.id,
        amount=10.0,
        currency="USD",
        status="completed",
        payment_method="test_method"
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment

@pytest.fixture(scope="function")
def test_telegram_user(db_session: Session, test_user: User) -> TelegramUser:
    """Create test Telegram user."""
    telegram_user = TelegramUser(
        user_id=test_user.id,
        telegram_id=123456789,
        username="test_telegram_user",
        is_active=True
    )
    db_session.add(telegram_user)
    db_session.commit()
    db_session.refresh(telegram_user)
    return telegram_user

@pytest.fixture(scope="function")
def test_token(test_user: User) -> str:
    """Create test JWT token."""
    return create_access_token(data={"sub": test_user.username})

@pytest.fixture(scope="function")
def authorized_client(client: TestClient, test_token: str) -> TestClient:
    """Create authorized test client."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_token}"
    }
    return client

@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, Any]:
    """Create test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
    }

@pytest.fixture(scope="function")
def test_admin_data() -> Dict[str, Any]:
    """Create test admin data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True,
    }

@pytest.fixture(scope="function")
def test_server_data() -> Dict[str, Any]:
    """Create test server data."""
    return {
        "name": "Test Server",
        "host": "test.example.com",
        "port": 443,
        "protocol": "tcp",
        "status": "active",
        "is_active": True,
        "location": "US",
        "load": 0.0,
        "max_users": 100,
        "current_users": 0,
        "bandwidth_limit": 1000,
        "traffic_used": 0,
    }

@pytest.fixture(scope="function")
def test_vpn_account_data() -> Dict[str, Any]:
    """Create test VPN account data."""
    return {
        "status": "active",
        "is_active": True,
        "traffic_limit": 1000,
        "traffic_used": 0,
        "expires_at": None,
        "last_connection": None,
        "last_ip": None,
        "last_port": None,
    }

@pytest.fixture(scope="function")
def test_payment_data() -> Dict[str, Any]:
    """Create test payment data."""
    return {
        "amount": 10.0,
        "currency": "USD",
        "status": "pending",
        "payment_method": "credit_card",
        "transaction_id": "test_transaction_123",
    }

@pytest.fixture(scope="function")
def test_subscription_data() -> Dict[str, Any]:
    """Create test subscription data."""
    return {
        "status": "active",
        "is_active": True,
        "start_date": None,
        "end_date": None,
        "auto_renew": True,
        "plan_id": 1,
    }

@pytest.fixture(scope="function")
def test_plan_data() -> Dict[str, Any]:
    """Create test plan data."""
    return {
        "name": "Test Plan",
        "description": "Test plan description",
        "price": 10.0,
        "currency": "USD",
        "duration_days": 30,
        "traffic_limit": 1000,
        "is_active": True,
    }

@pytest.fixture(autouse=True)
async def setup_test_db(db_session: AsyncSession):
    """Setup test database."""
    yield
    await clear_test_db(db_session)

@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    return test_settings

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    ) 