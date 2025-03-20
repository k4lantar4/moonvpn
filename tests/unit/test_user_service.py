"""
Unit tests for the user service.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate

pytestmark = pytest.mark.asyncio

class TestUserService:
    """Test cases for UserService."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        # Arrange
        user_data = UserCreate(
            phone="+989123456789",
            password="test_password123",
            email="test@example.com",
            full_name="Test User"
        )
        user_service = UserService(db_session)

        # Act
        user = await user_service.create_user(user_data)

        # Assert
        assert user.phone == user_data.phone
        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
        assert user.is_active is True
        assert user.is_admin is False

    async def test_get_user_by_id(self, db_session: AsyncSession, test_user: User):
        """Test retrieving a user by ID."""
        # Arrange
        user_service = UserService(db_session)

        # Act
        user = await user_service.get_user_by_id(test_user.id)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.phone == test_user.phone
        assert user.email == test_user.email

    async def test_get_user_by_phone(self, db_session: AsyncSession, test_user: User):
        """Test retrieving a user by phone number."""
        # Arrange
        user_service = UserService(db_session)

        # Act
        user = await user_service.get_user_by_phone(test_user.phone)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.phone == test_user.phone

    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """Test updating a user."""
        # Arrange
        user_service = UserService(db_session)
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )

        # Act
        updated_user = await user_service.update_user(test_user.id, update_data)

        # Assert
        assert updated_user.id == test_user.id
        assert updated_user.full_name == update_data.full_name
        assert updated_user.email == update_data.email
        assert updated_user.phone == test_user.phone  # Phone should not change

    async def test_delete_user(self, db_session: AsyncSession, test_user: User):
        """Test deleting a user."""
        # Arrange
        user_service = UserService(db_session)

        # Act
        await user_service.delete_user(test_user.id)

        # Assert
        deleted_user = await user_service.get_user_by_id(test_user.id)
        assert deleted_user is None

    async def test_verify_password(self, db_session: AsyncSession, test_user: User):
        """Test password verification."""
        # Arrange
        user_service = UserService(db_session)
        correct_password = "test_password123"
        wrong_password = "wrong_password"

        # Act & Assert
        assert await user_service.verify_password(test_user.id, correct_password) is True
        assert await user_service.verify_password(test_user.id, wrong_password) is False

    async def test_change_password(self, db_session: AsyncSession, test_user: User):
        """Test changing user password."""
        # Arrange
        user_service = UserService(db_session)
        new_password = "new_password123"

        # Act
        await user_service.change_password(test_user.id, new_password)

        # Assert
        assert await user_service.verify_password(test_user.id, new_password) is True
        assert await user_service.verify_password(test_user.id, "test_password123") is False 