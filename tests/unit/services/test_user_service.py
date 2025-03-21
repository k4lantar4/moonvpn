"""Unit tests for user service."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user import UserService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    TelegramUserCreate,
    TelegramUserUpdate
)
from app.models.user import User, TelegramUser

class TestUser:
    """Test user operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db: AsyncSession):
        """Test creating a new user."""
        user_service = UserService(db)
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        assert user.email == user_data.email
        assert user.username == user_data.username
        assert user.is_active == user_data.is_active
        assert user.is_superuser == user_data.is_superuser
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_users(self, db: AsyncSession):
        """Test getting list of users."""
        user_service = UserService(db)
        
        # Create multiple users
        user_data1 = UserCreate(
            email="user1@example.com",
            username="user1",
            password="pass123",
            is_active=True,
            is_superuser=False
        )
        
        user_data2 = UserCreate(
            email="user2@example.com",
            username="user2",
            password="pass456",
            is_active=True,
            is_superuser=False
        )
        
        await user_service.create_user(user_data1)
        await user_service.create_user(user_data2)
        
        users = await user_service.get_users()
        assert len(users) == 2
        assert any(u.username == "user1" for u in users)
        assert any(u.username == "user2" for u in users)
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db: AsyncSession):
        """Test getting user by email."""
        user_service = UserService(db)
        
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        await user_service.create_user(user_data)
        
        user = await user_service.get_user_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_update_user(self, db: AsyncSession):
        """Test updating a user."""
        user_service = UserService(db)
        
        # Create a user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        # Update the user
        update_data = UserUpdate(
            username="updateduser",
            is_active=False
        )
        
        updated_user = await user_service.update_user(user.id, update_data)
        
        assert updated_user.username == update_data.username
        assert updated_user.is_active == update_data.is_active
        assert updated_user.email == user.email  # Unchanged
        assert updated_user.is_superuser == user.is_superuser  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_user(self, db: AsyncSession):
        """Test deleting a user."""
        user_service = UserService(db)
        
        # Create a user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        # Delete the user
        await user_service.delete_user(user.id)
        
        # Verify user is deleted
        deleted_user = await user_service.get_user(user.id)
        assert deleted_user is None

class TestTelegramUser:
    """Test Telegram user operations."""
    
    @pytest.mark.asyncio
    async def test_create_telegram_user(self, db: AsyncSession):
        """Test creating a new Telegram user."""
        user_service = UserService(db)
        
        # Create a regular user first
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        # Create Telegram user
        telegram_data = TelegramUserCreate(
            user_id=user.id,
            telegram_id=123456789,
            username="telegramuser",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        
        telegram_user = await user_service.create_telegram_user(telegram_data)
        
        assert telegram_user.user_id == telegram_data.user_id
        assert telegram_user.telegram_id == telegram_data.telegram_id
        assert telegram_user.username == telegram_data.username
        assert telegram_user.first_name == telegram_data.first_name
        assert telegram_user.last_name == telegram_data.last_name
        assert telegram_user.is_active == telegram_data.is_active
        assert telegram_user.id is not None
    
    @pytest.mark.asyncio
    async def test_get_telegram_users(self, db: AsyncSession):
        """Test getting list of Telegram users."""
        user_service = UserService(db)
        
        # Create a regular user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        # Create multiple Telegram users
        telegram_data1 = TelegramUserCreate(
            user_id=user.id,
            telegram_id=123456789,
            username="telegramuser1",
            first_name="Test",
            last_name="User1",
            is_active=True
        )
        
        telegram_data2 = TelegramUserCreate(
            user_id=user.id,
            telegram_id=987654321,
            username="telegramuser2",
            first_name="Test",
            last_name="User2",
            is_active=True
        )
        
        await user_service.create_telegram_user(telegram_data1)
        await user_service.create_telegram_user(telegram_data2)
        
        telegram_users = await user_service.get_telegram_users(user_id=user.id)
        assert len(telegram_users) == 2
        assert any(t.username == "telegramuser1" for t in telegram_users)
        assert any(t.username == "telegramuser2" for t in telegram_users)
    
    @pytest.mark.asyncio
    async def test_update_telegram_user(self, db: AsyncSession):
        """Test updating a Telegram user."""
        user_service = UserService(db)
        
        # Create a regular user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        # Create Telegram user
        telegram_data = TelegramUserCreate(
            user_id=user.id,
            telegram_id=123456789,
            username="telegramuser",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        
        telegram_user = await user_service.create_telegram_user(telegram_data)
        
        # Update the Telegram user
        update_data = TelegramUserUpdate(
            username="updatedtelegramuser",
            is_active=False
        )
        
        updated_telegram_user = await user_service.update_telegram_user(telegram_user.id, update_data)
        
        assert updated_telegram_user.username == update_data.username
        assert updated_telegram_user.is_active == update_data.is_active
        assert updated_telegram_user.telegram_id == telegram_user.telegram_id  # Unchanged
        assert updated_telegram_user.first_name == telegram_user.first_name  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_telegram_user(self, db: AsyncSession):
        """Test deleting a Telegram user."""
        user_service = UserService(db)
        
        # Create a regular user
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            is_active=True,
            is_superuser=False
        )
        
        user = await user_service.create_user(user_data)
        
        # Create Telegram user
        telegram_data = TelegramUserCreate(
            user_id=user.id,
            telegram_id=123456789,
            username="telegramuser",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        
        telegram_user = await user_service.create_telegram_user(telegram_data)
        
        # Delete the Telegram user
        await user_service.delete_telegram_user(telegram_user.id)
        
        # Verify Telegram user is deleted
        deleted_telegram_user = await user_service.get_telegram_user(telegram_user.id)
        assert deleted_telegram_user is None 