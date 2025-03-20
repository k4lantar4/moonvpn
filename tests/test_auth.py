import pytest
from fastapi import status
from app.core.security import create_access_token
from app.models.user import User
from .base import TestBase
from .helpers import create_test_user

class TestAuth(TestBase):
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, client, db_session):
        """Test successful login."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Login request
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, db_session):
        """Test login with invalid credentials."""
        # Create test user
        await create_test_user(db_session)
        
        # Login request with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user."""
        # Create inactive test user
        user = await create_test_user(db_session, is_active=False)
        
        # Login request
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        assert "detail" in data
        assert "Inactive user" in data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token(self, client, db_session):
        """Test token refresh."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Get refresh token
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        refresh_token = response.json()["refresh_token"]
        
        # Refresh token request
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client):
        """Test refresh token with invalid token."""
        # Refresh token request with invalid token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        assert "detail" in data
        assert "Invalid refresh token" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, db_session):
        """Test get current user."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Get access token
        token = create_access_token(user.id)
        
        # Get current user request
        response = client.get(
            "/api/v1/auth/me",
            headers=self.get_auth_headers(token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name
        assert data["is_active"] == user.is_active
        assert data["is_superuser"] == user.is_superuser

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client):
        """Test get current user with invalid token."""
        # Get current user request with invalid token
        response = client.get(
            "/api/v1/auth/me",
            headers=self.get_auth_headers("invalid_token")
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        assert "detail" in data
        assert "Invalid authentication credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, client, db_session):
        """Test get current user with expired token."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Get expired access token
        token = create_access_token(user.id, expires_delta=-1)
        
        # Get current user request
        response = client.get(
            "/api/v1/auth/me",
            headers=self.get_auth_headers(token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        assert "detail" in data
        assert "Token has expired" in data["detail"] 