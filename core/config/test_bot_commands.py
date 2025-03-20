import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, Chat, User
from app.bot.handlers.commands import (
    start_command,
    help_command,
    status_command,
    buy_command,
    settings_command
)
from app.bot.handlers.conversations import (
    handle_registration,
    handle_purchase,
    handle_settings
)
from app.models.user import User as DBUser
from app.services.vpn import VPNService
from app.services.payment import PaymentService

@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.from_user = MagicMock(spec=User)
    update.message.chat.id = 123456789
    update.message.from_user.id = 123456789
    update.message.from_user.username = "testuser"
    update.message.from_user.first_name = "Test"
    update.message.from_user.last_name = "User"
    return update

@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock()
    context.bot = AsyncMock()
    return context

@pytest.fixture
def mock_db_user(db):
    """Create a test database user."""
    user = DBUser(
        telegram_id=123456789,
        username="testuser",
        email="test@example.com",
        phone_number="989123456789",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context, mock_db_user):
    """Test the /start command handler."""
    # Test with existing user
    with patch("app.bot.handlers.commands.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = mock_db_user
        await start_command(mock_update, mock_context)
        mock_context.bot.send_message.assert_called_once()
        assert "Welcome back" in mock_context.bot.send_message.call_args[0][1]

    # Test with new user
    with patch("app.bot.handlers.commands.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = None
        await start_command(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "Welcome to MoonVPN" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    """Test the /help command handler."""
    await help_command(mock_update, mock_context)
    mock_context.bot.send_message.assert_called_once()
    assert "Available commands" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_status_command(mock_update, mock_context, mock_db_user):
    """Test the /status command handler."""
    with patch("app.bot.handlers.commands.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = mock_db_user
        await status_command(mock_update, mock_context)
        mock_context.bot.send_message.assert_called_once()
        assert "Your VPN status" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_buy_command(mock_update, mock_context, mock_db_user):
    """Test the /buy command handler."""
    with patch("app.bot.handlers.commands.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = mock_db_user
        await buy_command(mock_update, mock_context)
        mock_context.bot.send_message.assert_called_once()
        assert "Select a plan" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_settings_command(mock_update, mock_context, mock_db_user):
    """Test the /settings command handler."""
    with patch("app.bot.handlers.commands.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = mock_db_user
        await settings_command(mock_update, mock_context)
        mock_context.bot.send_message.assert_called_once()
        assert "Settings" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_registration_conversation(mock_update, mock_context):
    """Test the registration conversation flow."""
    # Test phone number input
    mock_update.message.text = "989123456789"
    await handle_registration(mock_update, mock_context)
    mock_context.bot.send_message.assert_called()
    assert "Verification code" in mock_context.bot.send_message.call_args[0][1]

    # Test verification code input
    mock_update.message.text = "123456"
    await handle_registration(mock_update, mock_context)
    mock_context.bot.send_message.assert_called()
    assert "Registration completed" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_purchase_conversation(mock_update, mock_context, mock_db_user):
    """Test the purchase conversation flow."""
    with patch("app.bot.handlers.conversations.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = mock_db_user
        # Test plan selection
        mock_update.message.text = "1"
        await handle_purchase(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "Select payment method" in mock_context.bot.send_message.call_args[0][1]

        # Test payment method selection
        mock_update.message.text = "wallet"
        await handle_purchase(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "Processing payment" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_settings_conversation(mock_update, mock_context, mock_db_user):
    """Test the settings conversation flow."""
    with patch("app.bot.handlers.conversations.get_user_by_telegram_id") as mock_get_user:
        mock_get_user.return_value = mock_db_user
        # Test language selection
        mock_update.message.text = "en"
        await handle_settings(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "Language updated" in mock_context.bot.send_message.call_args[0][1]

        # Test notification settings
        mock_update.message.text = "notifications"
        await handle_settings(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "Notification settings" in mock_context.bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_error_handling(mock_update, mock_context):
    """Test error handling in bot commands."""
    # Test invalid command
    mock_update.message.text = "/invalid"
    with patch("app.bot.handlers.commands.start_command") as mock_start:
        mock_start.side_effect = Exception("Test error")
        await start_command(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "An error occurred" in mock_context.bot.send_message.call_args[0][1]

    # Test invalid input in conversation
    mock_update.message.text = "invalid_input"
    with patch("app.bot.handlers.conversations.handle_registration") as mock_registration:
        mock_registration.side_effect = Exception("Test error")
        await handle_registration(mock_update, mock_context)
        mock_context.bot.send_message.assert_called()
        assert "An error occurred" in mock_context.bot.send_message.call_args[0][1] 