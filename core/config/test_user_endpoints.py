"""Integration tests for user API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import create_access_token

client = TestClient(app)

class TestUserEndpoints:
    """Test user API endpoints."""
    
    def test_create_user(self, db):
        """Test creating a new user via API."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["is_active"] == user_data["is_active"]
        assert data["is_superuser"] == user_data["is_superuser"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_users(self, db, authorized_client):
        """Test getting list of users via API."""
        # Create multiple users first
        user_data1 = {
            "email": "user1@example.com",
            "username": "user1",
            "password": "pass123",
            "is_active": True,
            "is_superuser": False
        }
        
        user_data2 = {
            "email": "user2@example.com",
            "username": "user2",
            "password": "pass456",
            "is_active": True,
            "is_superuser": False
        }
        
        client.post("/api/v1/users/", json=user_data1)
        client.post("/api/v1/users/", json=user_data2)
        
        response = authorized_client.get("/api/v1/users/")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        assert any(u["username"] == "user1" for u in data)
        assert any(u["username"] == "user2" for u in data)
    
    def test_get_user(self, db, authorized_client):
        """Test getting a specific user via API."""
        # Create a user first
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        user_id = response.json()["id"]
        
        response = authorized_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["is_active"] == user_data["is_active"]
        assert data["is_superuser"] == user_data["is_superuser"]
        assert data["id"] == user_id
    
    def test_update_user(self, db, authorized_client):
        """Test updating a user via API."""
        # Create a user first
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        user_id = response.json()["id"]
        
        # Update the user
        update_data = {
            "username": "updateduser",
            "is_active": False
        }
        
        response = authorized_client.put(f"/api/v1/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == update_data["username"]
        assert data["is_active"] == update_data["is_active"]
        assert data["email"] == user_data["email"]  # Unchanged
        assert data["is_superuser"] == user_data["is_superuser"]  # Unchanged
    
    def test_delete_user(self, db, authorized_client):
        """Test deleting a user via API."""
        # Create a user first
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        user_id = response.json()["id"]
        
        # Delete the user
        response = authorized_client.delete(f"/api/v1/users/{user_id}")
        assert response.status_code == 204
        
        # Verify user is deleted
        response = authorized_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 404
    
    def test_get_current_user(self, db, authorized_client):
        """Test getting current user via API."""
        response = authorized_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "is_active" in data
        assert "is_superuser" in data
    
    def test_update_current_user(self, db, authorized_client):
        """Test updating current user via API."""
        update_data = {
            "username": "updatedusername"
        }
        
        response = authorized_client.put("/api/v1/users/me", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == update_data["username"]
        assert "email" in data
        assert "is_active" in data
        assert "is_superuser" in data
    
    def test_change_password(self, db, authorized_client):
        """Test changing user password via API."""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpass123"
        }
        
        response = authorized_client.put("/api/v1/users/me/password", json=password_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Password updated successfully"
    
    def test_unauthorized_access(self, db):
        """Test unauthorized access to protected endpoints."""
        # Try to get users list without authentication
        response = client.get("/api/v1/users/")
        assert response.status_code == 401
        
        # Try to get specific user without authentication
        response = client.get("/api/v1/users/1")
        assert response.status_code == 401
        
        # Try to update user without authentication
        response = client.put("/api/v1/users/1", json={"username": "test"})
        assert response.status_code == 401
        
        # Try to delete user without authentication
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 401 