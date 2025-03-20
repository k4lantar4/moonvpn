import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.models.user import User
from app.tests.utils import create_test_user, get_test_user_data

@pytest.mark.asyncio
class TestUserService:
    async def test_create_user(self, db_session: AsyncSession):
        """Test user creation."""
        user_data = get_test_user_data()
        user_service = UserService(db_session)
        
        user = await user_service.create_user(**user_data)
        
        assert user.email == user_data["email"]
        assert user.full_name == user_data["full_name"]
        assert user.phone == user_data["phone"]
        assert user.is_active is True
        assert user.is_admin is False

    async def test_get_user_by_email(self, db_session: AsyncSession):
        """Test retrieving user by email."""
        test_user = await create_test_user(db_session)
        user_service = UserService(db_session)
        
        user = await user_service.get_user_by_email(test_user.email)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_user_by_id(self, db_session: AsyncSession):
        """Test retrieving user by ID."""
        test_user = await create_test_user(db_session)
        user_service = UserService(db_session)
        
        user = await user_service.get_user_by_id(test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_update_user(self, db_session: AsyncSession):
        """Test user update."""
        test_user = await create_test_user(db_session)
        user_service = UserService(db_session)
        
        update_data = {
            "full_name": "Updated Name",
            "phone": "+989876543210"
        }
        
        updated_user = await user_service.update_user(test_user.id, **update_data)
        
        assert updated_user.full_name == update_data["full_name"]
        assert updated_user.phone == update_data["phone"]
        assert updated_user.email == test_user.email  # Unchanged

    async def test_deactivate_user(self, db_session: AsyncSession):
        """Test user deactivation."""
        test_user = await create_test_user(db_session)
        user_service = UserService(db_session)
        
        deactivated_user = await user_service.deactivate_user(test_user.id)
        
        assert deactivated_user.is_active is False

    async def test_activate_user(self, db_session: AsyncSession):
        """Test user activation."""
        test_user = await create_test_user(db_session, is_active=False)
        user_service = UserService(db_session)
        
        activated_user = await user_service.activate_user(test_user.id)
        
        assert activated_user.is_active is True

    async def test_get_users(self, db_session: AsyncSession):
        """Test retrieving multiple users."""
        await create_test_user(db_session, email="user1@example.com")
        await create_test_user(db_session, email="user2@example.com")
        user_service = UserService(db_session)
        
        users = await user_service.get_users()
        
        assert len(users) >= 2
        assert any(user.email == "user1@example.com" for user in users)
        assert any(user.email == "user2@example.com" for user in users)

    async def test_delete_user(self, db_session: AsyncSession):
        """Test user deletion."""
        test_user = await create_test_user(db_session)
        user_service = UserService(db_session)
        
        await user_service.delete_user(test_user.id)
        
        deleted_user = await user_service.get_user_by_id(test_user.id)
        assert deleted_user is None 