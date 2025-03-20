"""
Unit tests for the Telegram bot service.
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.telegram import TelegramUser, TelegramChat
from app.services.telegram_bot_service import TelegramBotService
from app.schemas.telegram import TelegramUserCreate, TelegramChatCreate
from app.models.user import User

pytestmark = pytest.mark.asyncio

class TestTelegramBotService:
    """Test cases for TelegramBotService."""

    async def test_create_telegram_user(self, db_session: AsyncSession, test_user):
        """Test creating a new Telegram user."""
        # Arrange
        telegram_user_data = TelegramUserCreate(
            user_id=test_user.id,
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            language_code="en",
            is_active=True
        )
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        telegram_user = await telegram_bot_service.create_telegram_user(telegram_user_data)

        # Assert
        assert telegram_user.user_id == test_user.id
        assert telegram_user.telegram_id == telegram_user_data.telegram_id
        assert telegram_user.username == telegram_user_data.username
        assert telegram_user.first_name == telegram_user_data.first_name
        assert telegram_user.last_name == telegram_user_data.last_name
        assert telegram_user.language_code == telegram_user_data.language_code
        assert telegram_user.is_active == telegram_user_data.is_active

    async def test_create_telegram_chat(self, db_session: AsyncSession, test_telegram_user):
        """Test creating a new Telegram chat."""
        # Arrange
        chat_data = TelegramChatCreate(
            telegram_user_id=test_telegram_user.id,
            chat_id=123456789,
            chat_type="private",
            title="Test Chat",
            is_active=True
        )
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        chat = await telegram_bot_service.create_chat(chat_data)

        # Assert
        assert chat.telegram_user_id == test_telegram_user.id
        assert chat.chat_id == chat_data.chat_id
        assert chat.chat_type == chat_data.chat_type
        assert chat.title == chat_data.title
        assert chat.is_active == chat_data.is_active

    async def test_get_telegram_user(self, db_session: AsyncSession, test_telegram_user):
        """Test retrieving a Telegram user."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        telegram_user = await telegram_bot_service.get_telegram_user(test_telegram_user.id)

        # Assert
        assert telegram_user is not None
        assert telegram_user.id == test_telegram_user.id
        assert telegram_user.telegram_id == test_telegram_user.telegram_id
        assert telegram_user.username == test_telegram_user.username

    async def test_get_telegram_user_by_telegram_id(self, db_session: AsyncSession, test_telegram_user):
        """Test retrieving a Telegram user by Telegram ID."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        telegram_user = await telegram_bot_service.get_telegram_user_by_telegram_id(
            test_telegram_user.telegram_id
        )

        # Assert
        assert telegram_user is not None
        assert telegram_user.id == test_telegram_user.id
        assert telegram_user.telegram_id == test_telegram_user.telegram_id

    async def test_get_user_chats(self, db_session: AsyncSession, test_telegram_user, test_telegram_chat):
        """Test retrieving all chats for a Telegram user."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        chats = await telegram_bot_service.get_user_chats(test_telegram_user.id)

        # Assert
        assert len(chats) > 0
        assert any(chat.id == test_telegram_chat.id for chat in chats)

    async def test_update_telegram_user_status(self, db_session: AsyncSession, test_telegram_user):
        """Test updating Telegram user status."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        await telegram_bot_service.update_telegram_user_status(test_telegram_user.id, False)

        # Assert
        updated_user = await telegram_bot_service.get_telegram_user(test_telegram_user.id)
        assert updated_user.is_active is False

    async def test_update_chat_status(self, db_session: AsyncSession, test_telegram_chat):
        """Test updating chat status."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        await telegram_bot_service.update_chat_status(test_telegram_chat.id, False)

        # Assert
        updated_chat = await telegram_bot_service.get_chat(test_telegram_chat.id)
        assert updated_chat.is_active is False

    async def test_delete_telegram_user(self, db_session: AsyncSession, test_telegram_user):
        """Test deleting a Telegram user."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        await telegram_bot_service.delete_telegram_user(test_telegram_user.id)

        # Assert
        deleted_user = await telegram_bot_service.get_telegram_user(test_telegram_user.id)
        assert deleted_user is None

    async def test_delete_chat(self, db_session: AsyncSession, test_telegram_chat):
        """Test deleting a chat."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)

        # Act
        await telegram_bot_service.delete_chat(test_telegram_chat.id)

        # Assert
        deleted_chat = await telegram_bot_service.get_chat(test_telegram_chat.id)
        assert deleted_chat is None

    async def test_send_message(self, db_session: AsyncSession, test_telegram_chat):
        """Test sending a message to a chat."""
        # Arrange
        telegram_bot_service = TelegramBotService(db_session)
        message = "Test message"

        # Act
        sent_message = await telegram_bot_service.send_message(
            test_telegram_chat.chat_id,
            message
        )

        # Assert
        assert sent_message is not None
        assert sent_message.chat_id == test_telegram_chat.chat_id
        assert sent_message.text == message
        assert sent_message.sent_at is not None 