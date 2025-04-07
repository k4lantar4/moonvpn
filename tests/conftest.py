"""
Pytest Configuration

This file contains pytest fixtures and configuration that are
shared across multiple test modules.
"""

import os
import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi import FastAPI
from httpx import AsyncClient

# Set test environment variables
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Prevent alembic from running migrations in tests
os.environ["SKIP_MIGRATIONS"] = "1"

# Import modules after setting environment variables
from core.config import get_settings
from core.database import Base, engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Create test settings
settings = get_settings()


# Create test database engine
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def setup_database():
    """Set up the test database."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a fresh SQLAlchemy session for each test."""
    connection = await engine.connect()
    transaction = await connection.begin()
    
    session_maker = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        class_=AsyncSession,
    )
    
    async with session_maker() as session:
        yield session
    
    await transaction.rollback()
    await connection.close()


@pytest.fixture
def app() -> FastAPI:
    """Get FastAPI application for testing."""
    from api.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Get test client for FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client 