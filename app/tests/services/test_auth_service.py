import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.auth import TokenData

pytestmark = pytest.mark.asyncio

class TestAuthService:
    """Test suite for authentication service."""
    
    async def test_create_access_token(self, db_session, test_user_data):
        """Test creating access token with correct data."""
        # Create test user
        user = User(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            phone=test_user_data["phone"],
            hashed_password=test_user_data["password"]  # In real app, this would be hashed
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create token
        auth_service = AuthService(db_session)
        token = await auth_service.create_access_token(user)
        
        # Verify token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(user.id)
        assert "exp" in payload
        assert datetime.fromtimestamp(payload["exp"]) > datetime.utcnow()
    
    async def test_verify_password(self, db_session, test_user_data):
        """Test password verification."""
        # Create test user
        user = User(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            phone=test_user_data["phone"],
            hashed_password=test_user_data["password"]  # In real app, this would be hashed
        )
        db_session.add(user)
        await db_session.commit()
        
        # Test password verification
        auth_service = AuthService(db_session)
        assert await auth_service.verify_password(
            test_user_data["password"], 
            user.hashed_password
        )
        assert not await auth_service.verify_password(
            "wrongpassword", 
            user.hashed_password
        )
    
    async def test_get_current_user(self, db_session, test_user_data):
        """Test getting current user from token."""
        # Create test user
        user = User(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            phone=test_user_data["phone"],
            hashed_password=test_user_data["password"]  # In real app, this would be hashed
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create token
        auth_service = AuthService(db_session)
        token = await auth_service.create_access_token(user)
        
        # Test getting current user
        current_user = await auth_service.get_current_user(token)
        assert current_user.id == user.id
        assert current_user.email == user.email
    
    async def test_get_current_active_user(self, db_session, test_user_data):
        """Test getting current active user."""
        # Create test user
        user = User(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            phone=test_user_data["phone"],
            hashed_password=test_user_data["password"],  # In real app, this would be hashed
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create token
        auth_service = AuthService(db_session)
        token = await auth_service.create_access_token(user)
        
        # Test getting current active user
        current_user = await auth_service.get_current_active_user(token)
        assert current_user.id == user.id
        assert current_user.is_active
        
        # Test inactive user
        user.is_active = False
        await db_session.commit()
        with pytest.raises(ValueError):
            await auth_service.get_current_active_user(token)
    
    async def test_authenticate_user(self, db_session, test_user_data):
        """Test user authentication."""
        # Create test user
        user = User(
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            phone=test_user_data["phone"],
            hashed_password=test_user_data["password"]  # In real app, this would be hashed
        )
        db_session.add(user)
        await db_session.commit()
        
        # Test authentication
        auth_service = AuthService(db_session)
        authenticated_user = await auth_service.authenticate_user(
            test_user_data["email"],
            test_user_data["password"]
        )
        assert authenticated_user.id == user.id
        
        # Test wrong credentials
        assert not await auth_service.authenticate_user(
            test_user_data["email"],
            "wrongpassword"
        ) 