import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.telegram_service import TelegramService
from app.tests.utils import create_test_user

@pytest.mark.asyncio
class TestTelegramService:
    @pytest.fixture
    def mock_bot(self):
        """Create a mock Telegram bot."""
        with patch('app.services.telegram_service.Bot') as mock:
            bot = AsyncMock()
            mock.return_value = bot
            yield bot

    async def test_start_command(self, db_session: AsyncSession, mock_bot):
        """Test handling of /start command."""
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message
        message = AsyncMock()
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        
        await telegram_service.handle_start(message)
        
        # Verify bot sent welcome message
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "Welcome" in call_args['text']

    async def test_help_command(self, db_session: AsyncSession, mock_bot):
        """Test handling of /help command."""
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message
        message = AsyncMock()
        message.from_user.id = 123456
        
        await telegram_service.handle_help(message)
        
        # Verify bot sent help message
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "help" in call_args['text'].lower()

    async def test_register_user(self, db_session: AsyncSession, mock_bot):
        """Test user registration through Telegram."""
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message
        message = AsyncMock()
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        
        await telegram_service.handle_register(message)
        
        # Verify bot sent registration confirmation
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "registered" in call_args['text'].lower()

    async def test_get_vpn_status(self, db_session: AsyncSession, mock_bot):
        """Test getting VPN status."""
        test_user = await create_test_user(db_session)
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message
        message = AsyncMock()
        message.from_user.id = 123456
        
        await telegram_service.handle_vpn_status(message)
        
        # Verify bot sent status message
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "status" in call_args['text'].lower()

    async def test_get_subscription_info(self, db_session: AsyncSession, mock_bot):
        """Test getting subscription information."""
        test_user = await create_test_user(db_session)
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message
        message = AsyncMock()
        message.from_user.id = 123456
        
        await telegram_service.handle_subscription_info(message)
        
        # Verify bot sent subscription info
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "subscription" in call_args['text'].lower()

    async def test_handle_error(self, db_session: AsyncSession, mock_bot):
        """Test error handling."""
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message
        message = AsyncMock()
        message.from_user.id = 123456
        
        # Simulate an error
        error = Exception("Test error")
        
        await telegram_service.handle_error(message, error)
        
        # Verify bot sent error message
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "error" in call_args['text'].lower()

    async def test_handle_unknown_command(self, db_session: AsyncSession, mock_bot):
        """Test handling of unknown commands."""
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Simulate a message with unknown command
        message = AsyncMock()
        message.from_user.id = 123456
        message.text = "/unknown"
        
        await telegram_service.handle_unknown_command(message)
        
        # Verify bot sent unknown command message
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert "unknown" in call_args['text'].lower()

    async def test_send_notification(self, db_session: AsyncSession, mock_bot):
        """Test sending notifications to users."""
        telegram_service = TelegramService(db_session, mock_bot)
        
        # Test sending notification
        await telegram_service.send_notification(
            user_id=123456,
            message="Test notification"
        )
        
        # Verify bot sent notification
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args[1]
        assert call_args['chat_id'] == 123456
        assert call_args['text'] == "Test notification" 