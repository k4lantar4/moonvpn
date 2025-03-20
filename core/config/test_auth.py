import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import create_test_user
from app.core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_login_success(self, db_session, test_user_data):
        """Test successful login."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Attempt login
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, db_session, test_user_data):
        """Test login with invalid credentials."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Attempt login with wrong password
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_refresh_token(self, db_session, test_user_data):
        """Test token refresh."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Login to get tokens
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Attempt token refresh
        response = client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, db_session):
        """Test refresh token with invalid token."""
        response = client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    async def test_get_current_user(self, db_session, test_user_data):
        """Test getting current user information."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False

    async def test_get_current_user_invalid_token(self, db_session):
        """Test getting current user with invalid token."""
        response = client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]

    async def test_register_user(self, db_session):
        """Test user registration."""
        new_user_data = {
            "email": "newuser@example.com",
            "password": "testpassword123",
            "full_name": "New User"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=new_user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == new_user_data["email"]
        assert data["full_name"] == new_user_data["full_name"]
        assert "id" in data
        assert "password" not in data

    async def test_register_existing_user(self, db_session, test_user_data):
        """Test registration with existing email."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Attempt registration with same email
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": test_user_data["email"],
                "password": "testpassword123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_change_password(self, db_session, test_user_data):
        """Test password change."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Change password
        response = client.post(
            f"{settings.API_V1_STR}/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": test_user_data["password"],
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]

    async def test_change_password_wrong_current(self, db_session, test_user_data):
        """Test password change with wrong current password."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Attempt password change with wrong current password
        response = client.post(
            f"{settings.API_V1_STR}/auth/change-password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"] 