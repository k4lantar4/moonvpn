"""Common test fixtures."""

import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base
from app.main import app
from .helpers import (
    create_test_user,
    create_test_vpn_config,
    create_test_payment,
    create_test_telegram_user,
    create_test_token
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def test_user(db_session) -> AsyncGenerator[User, None]:
    """Create a test user."""
    user = await create_test_user(db_session)
    yield user

@pytest.fixture
async def test_vpn_config(db_session, test_user) -> AsyncGenerator[VPNConfig, None]:
    """Create a test VPN configuration."""
    vpn_config = await create_test_vpn_config(db_session, test_user.id)
    yield vpn_config

@pytest.fixture
async def test_payment(db_session, test_user) -> AsyncGenerator[Payment, None]:
    """Create a test payment."""
    payment = await create_test_payment(db_session, test_user.id)
    yield payment

@pytest.fixture
async def test_telegram_user(db_session, test_user) -> AsyncGenerator[TelegramUser, None]:
    """Create a test Telegram user."""
    telegram_user = await create_test_telegram_user(db_session, test_user.id)
    yield telegram_user

@pytest.fixture
def test_token(test_user) -> str:
    """Create a test JWT token."""
    return create_test_token(test_user.id)

@pytest.fixture
def authorized_client(client: TestClient, test_token: str) -> Generator[TestClient, None, None]:
    """Create an authorized test client."""
    client.headers["Authorization"] = f"Bearer {test_token}"
    yield client
    client.headers.pop("Authorization", None)

@pytest.fixture
async def superuser(db_session) -> AsyncGenerator[User, None]:
    """Create a test superuser."""
    superuser = await create_test_user(
        db_session,
        email="admin@example.com",
        username="admin",
        is_superuser=True
    )
    yield superuser

@pytest.fixture
def superuser_token(superuser) -> str:
    """Create a test JWT token for superuser."""
    return create_test_token(superuser.id)

@pytest.fixture
def superuser_client(client: TestClient, superuser_token: str) -> Generator[TestClient, None, None]:
    """Create an authorized test client for superuser."""
    client.headers["Authorization"] = f"Bearer {superuser_token}"
    yield client
    client.headers.pop("Authorization", None) 