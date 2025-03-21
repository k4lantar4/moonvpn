"""
Test suite for security features.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch

from core.services.security_monitoring import SecurityMonitoringService
from core.services.notification import NotificationService
from core.middleware.security_middleware import SecurityMiddleware
from core.config.security_config import security_settings
from core.exceptions import SecurityError

@pytest.fixture
def test_client(app):
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def monitoring_service(mock_db):
    """Create a security monitoring service instance."""
    return SecurityMonitoringService(mock_db)

@pytest.fixture
def notification_service():
    """Create a notification service instance."""
    return NotificationService()

@pytest.fixture
def security_middleware(monitoring_service, notification_service):
    """Create a security middleware instance."""
    return SecurityMiddleware(
        app=Mock(),
        monitoring_service=monitoring_service,
        notification_service=notification_service
    )

class TestSecurityMonitoring:
    """Test security monitoring service."""

    async def test_start_monitoring(self, monitoring_service):
        """Test starting the monitoring service."""
        await monitoring_service.start_monitoring()
        assert len(monitoring_service.monitoring_tasks) > 0

    async def test_stop_monitoring(self, monitoring_service):
        """Test stopping the monitoring service."""
        await monitoring_service.start_monitoring()
        await monitoring_service.stop_monitoring()
        assert len(monitoring_service.monitoring_tasks) == 0

    async def test_create_alert(self, monitoring_service):
        """Test creating a security alert."""
        severity = "high"
        message = "Test alert"
        details = {"test": "data"}

        await monitoring_service._create_alert(severity, message, details)
        
        # Verify alert was created
        mock_db = monitoring_service.db
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_monitor_failed_logins(self, monitoring_service):
        """Test monitoring failed login attempts."""
        # Mock database query
        monitoring_service.db.query.return_value.filter.return_value.count.return_value = 6

        # Run monitoring task
        task = asyncio.create_task(monitoring_service._monitor_failed_logins())
        await asyncio.sleep(0.1)  # Allow task to run
        task.cancel()

        # Verify alert was created
        mock_db = monitoring_service.db
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_monitor_api_errors(self, monitoring_service):
        """Test monitoring API errors."""
        # Mock database query
        monitoring_service.db.query.return_value.filter.return_value.count.return_value = 11

        # Run monitoring task
        task = asyncio.create_task(monitoring_service._monitor_api_errors())
        await asyncio.sleep(0.1)  # Allow task to run
        task.cancel()

        # Verify alert was created
        mock_db = monitoring_service.db
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

class TestNotificationService:
    """Test notification service."""

    async def test_send_alert(self, notification_service):
        """Test sending alerts through multiple channels."""
        severity = "high"
        message = "Test alert"
        details = {"test": "data"}
        channels = ["email", "webhook"]

        await notification_service.send_alert(severity, message, details, channels)

        # Verify email was sent
        with patch("aiosmtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__aenter__.return_value.send_message.assert_called_once()

        # Verify webhook was called
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()

    async def test_send_to_admin_group(self, notification_service):
        """Test sending notifications to admin groups."""
        group_id = "SECURITY"
        message = "Test admin notification"
        channels = ["email", "telegram"]

        await notification_service.send_to_admin_group(group_id, message, channels)

        # Verify email was sent
        with patch("aiosmtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__aenter__.return_value.send_message.assert_called_once()

        # Verify Telegram message was sent
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()

class TestSecurityMiddleware:
    """Test security middleware."""

    async def test_rate_limit(self, security_middleware):
        """Test rate limiting functionality."""
        request = Mock()
        request.client.host = "127.0.0.1"

        # Make requests up to the limit
        for _ in range(security_settings.RATE_LIMIT_MAX_REQUESTS):
            await security_middleware._check_rate_limit(request)

        # Next request should be blocked
        with pytest.raises(SecurityError):
            await security_middleware._check_rate_limit(request)

    async def test_security_headers(self, security_middleware):
        """Test security headers are added to response."""
        response = Mock()
        security_middleware._add_security_headers(response)

        # Verify all security headers are set
        for header, value in security_settings.SECURITY_HEADERS.items():
            response.headers.__setitem__.assert_any_call(header, value)

    async def test_suspicious_request_detection(self, security_middleware):
        """Test detection of suspicious requests."""
        request = Mock()
        response = Mock()
        response.status_code = 200

        # Test suspicious user agent
        request.headers.get.return_value = "curl/7.64.1"
        assert security_middleware._is_suspicious_request(request, response)

        # Test suspicious path
        request.url.path = "/admin"
        request.headers.get.return_value = "Mozilla/5.0"
        assert security_middleware._is_suspicious_request(request, response)

        # Test suspicious query parameters
        request.url.path = "/api"
        request.query_params = {"select": "users"}
        assert security_middleware._is_suspicious_request(request, response)

        # Test high error rate
        response.status_code = 500
        assert security_middleware._is_suspicious_request(request, response)

    async def test_cleanup(self, security_middleware):
        """Test rate limit cache cleanup."""
        # Add some test data
        security_middleware.rate_limit_cache = {
            "127.0.0.1": {
                "requests": 5,
                "window_start": datetime.utcnow().timestamp() - security_settings.RATE_LIMIT_WINDOW - 1
            },
            "192.168.1.1": {
                "requests": 3,
                "window_start": datetime.utcnow().timestamp()
            }
        }

        await security_middleware.cleanup()

        # Verify expired IP was removed
        assert "127.0.0.1" not in security_middleware.rate_limit_cache
        assert "192.168.1.1" in security_middleware.rate_limit_cache

class TestSecurityInitializer:
    """Test security initializer."""

    async def test_initialize(self, app):
        """Test security services initialization."""
        from core.security.init import SecurityInitializer

        initializer = SecurityInitializer(app)
        await initializer.initialize()

        # Verify middleware was added
        assert any(isinstance(m, SecurityMiddleware) for m in app.user_middleware)

        # Cleanup
        await initializer.shutdown()

    async def test_shutdown(self, app):
        """Test security services shutdown."""
        from core.security.init import SecurityInitializer

        initializer = SecurityInitializer(app)
        await initializer.initialize()
        await initializer.shutdown()

        # Verify cleanup task was cancelled
        assert initializer.cleanup_task.cancelled() 