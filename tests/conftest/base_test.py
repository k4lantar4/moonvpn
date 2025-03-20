"""
Base test class providing common functionality for all tests.
"""
import asyncio
from typing import Any, Dict, Generator, Optional
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.base import Base
from tests.conftest.base_config import get_test_settings

class BaseTestCase:
    """Base test class with common functionality."""
    
    @pytest.fixture(autouse=True)
    async def setup(self) -> Generator[None, None, None]:
        """Setup test environment."""
        # Get test settings
        self.settings = get_test_settings()
        
        # Create test database engine
        self.engine = create_async_engine(
            self.settings.TEST_DATABASE_URL,
            echo=self.settings.TEST_DATABASE_ECHO,
            poolclass=NullPool,
        )
        
        # Create test session
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield
        
        # Cleanup
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
    
    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """Get database session."""
        async with self.async_session() as session:
            yield session
    
    @pytest.fixture
    def event_loop(self) -> Generator[asyncio.AbstractEventLoop, None, None]:
        """Get event loop."""
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()
    
    async def create_test_user(self, session: AsyncSession, **kwargs: Any) -> Dict[str, Any]:
        """Create a test user."""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        user_data = {
            "phone": self.settings.TEST_USER_PHONE,
            "email": self.settings.TEST_USER_EMAIL,
            "hashed_password": get_password_hash(self.settings.TEST_USER_PASSWORD),
            "is_active": True,
            "is_superuser": False,
            **kwargs
        }
        
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user_data
    
    async def create_test_admin(self, session: AsyncSession, **kwargs: Any) -> Dict[str, Any]:
        """Create a test admin user."""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        admin_data = {
            "phone": self.settings.TEST_ADMIN_PHONE,
            "email": self.settings.TEST_ADMIN_EMAIL,
            "hashed_password": get_password_hash(self.settings.TEST_ADMIN_PASSWORD),
            "is_active": True,
            "is_superuser": True,
            **kwargs
        }
        
        admin = User(**admin_data)
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        
        return admin_data
    
    async def get_test_token(self, session: AsyncSession, user_data: Dict[str, Any]) -> str:
        """Get test JWT token."""
        from app.core.security import create_access_token
        
        return create_access_token(
            subject=user_data["phone"],
            expires_delta=self.settings.TEST_JWT_EXPIRE_MINUTES
        )
    
    async def get_test_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get test headers with optional token."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers 