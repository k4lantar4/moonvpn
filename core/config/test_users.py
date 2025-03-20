import pytest
from fastapi import status
from app.models.user import User
from .base import TestBase
from .helpers import create_test_user

class TestUsers(TestBase):
    """Test user management endpoints."""

    @pytest.mark.asyncio
    async def test_create_user(self, client, db_session):
        """Test create user."""
        # Create user request
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "is_active": True,
            "is_superuser": False
        }
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_201_CREATED)
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] == user_data["is_active"]
        assert data["is_superuser"] == user_data["is_superuser"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client, db_session):
        """Test create user with duplicate email."""
        # Create existing user
        await create_test_user(db_session)
        
        # Create user request with duplicate email
        user_data = {
            "email": "test@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "is_active": True,
            "is_superuser": False
        }
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        assert "detail" in data
        assert "Email already registered" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_users(self, client, db_session):
        """Test get users list."""
        # Create test users
        await create_test_user(db_session)
        await create_test_user(db_session, email="user2@example.com")
        
        # Get users request
        response = client.get(
            "/api/v1/users/",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all(isinstance(user, dict) for user in data)
        assert all("id" in user for user in data)
        assert all("email" in user for user in data)
        assert all("full_name" in user for user in data)

    @pytest.mark.asyncio
    async def test_get_user(self, client, db_session):
        """Test get user by ID."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Get user request
        response = client.get(
            f"/api/v1/users/{user.id}",
            headers=self.get_auth_headers(self.test_superuser_token)
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
    async def test_get_user_not_found(self, client):
        """Test get non-existent user."""
        # Get user request with non-existent ID
        response = client.get(
            "/api/v1/users/999",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_user(self, client, db_session):
        """Test update user."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Update user request
        update_data = {
            "full_name": "Updated User",
            "is_active": False
        }
        response = client.put(
            f"/api/v1/users/{user.id}",
            json=update_data,
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["full_name"] == update_data["full_name"]
        assert data["is_active"] == update_data["is_active"]
        assert data["is_superuser"] == user.is_superuser

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client):
        """Test update non-existent user."""
        # Update user request with non-existent ID
        update_data = {
            "full_name": "Updated User",
            "is_active": False
        }
        response = client.put(
            "/api/v1/users/999",
            json=update_data,
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_user(self, client, db_session):
        """Test delete user."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Delete user request
        response = client.delete(
            f"/api/v1/users/{user.id}",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_204_NO_CONTENT)
        
        # Verify user is deleted
        response = client.get(
            f"/api/v1/users/{user.id}",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        self.assert_response(response, status.HTTP_404_NOT_FOUND)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client):
        """Test delete non-existent user."""
        # Delete user request with non-existent ID
        response = client.delete(
            "/api/v1/users/999",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_password(self, client, db_session):
        """Test update user password."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Update password request
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123"
        }
        response = client.put(
            f"/api/v1/users/{user.id}/password",
            json=password_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert "message" in data
        assert "Password updated successfully" in data["message"]
        
        # Verify new password works
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": user.email,
                "password": "newpassword123"
            }
        )
        self.assert_response(response, status.HTTP_200_OK)

    @pytest.mark.asyncio
    async def test_update_password_wrong_current(self, client, db_session):
        """Test update password with wrong current password."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Update password request with wrong current password
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        response = client.put(
            f"/api/v1/users/{user.id}/password",
            json=password_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        assert "detail" in data
        assert "Current password is incorrect" in data["detail"] 