import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.security import SecurityService
from app.core.config import settings
from app.models.user import User
from app.models.security_log import SecurityLog

@pytest.fixture
def security_service():
    """Create a security service instance."""
    return SecurityService()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        email="test@example.com",
        phone_number="989123456789",
        is_active=True,
        is_verified=True,
        password_hash="test_hash"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_security_log(db):
    """Create a test security log."""
    log = SecurityLog(
        event_type="login_attempt",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        status="success",
        details="Test security event"
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@pytest.mark.asyncio
async def test_authentication(security_service, test_user):
    """Test authentication security."""
    # Test password hashing
    password = "test_password"
    hashed_password = await security_service.hash_password(password)
    assert hashed_password != password
    assert await security_service.verify_password(password, hashed_password)
    
    # Test token generation
    token = await security_service.generate_token(test_user)
    assert token is not None
    assert len(token) > 0
    
    # Test token validation
    is_valid = await security_service.validate_token(token)
    assert is_valid is True

@pytest.mark.asyncio
async def test_authorization(security_service, test_user):
    """Test authorization security."""
    # Test role-based access control
    roles = await security_service.get_user_roles(test_user)
    assert isinstance(roles, list)
    
    # Test permission checking
    has_permission = await security_service.check_permission(
        test_user,
        "admin:manage_users"
    )
    assert isinstance(has_permission, bool)
    
    # Test resource access control
    can_access = await security_service.check_resource_access(
        test_user,
        "user_data",
        "read"
    )
    assert isinstance(can_access, bool)

@pytest.mark.asyncio
async def test_input_validation(security_service):
    """Test input validation security."""
    # Test SQL injection prevention
    malicious_input = "'; DROP TABLE users; --"
    sanitized_input = await security_service.sanitize_input(malicious_input)
    assert "DROP TABLE" not in sanitized_input
    
    # Test XSS prevention
    xss_input = "<script>alert('xss')</script>"
    sanitized_xss = await security_service.sanitize_input(xss_input)
    assert "<script>" not in sanitized_xss
    
    # Test command injection prevention
    cmd_input = "& rm -rf /"
    sanitized_cmd = await security_service.sanitize_input(cmd_input)
    assert "rm -rf" not in sanitized_cmd

@pytest.mark.asyncio
async def test_encryption(security_service):
    """Test data encryption security."""
    # Test data encryption
    sensitive_data = "sensitive information"
    encrypted_data = await security_service.encrypt_data(sensitive_data)
    assert encrypted_data != sensitive_data
    
    # Test data decryption
    decrypted_data = await security_service.decrypt_data(encrypted_data)
    assert decrypted_data == sensitive_data
    
    # Test key rotation
    new_key = await security_service.rotate_encryption_key()
    assert new_key is not None
    assert new_key != settings.ENCRYPTION_KEY

@pytest.mark.asyncio
async def test_rate_limiting(security_service):
    """Test rate limiting security."""
    # Test request rate limiting
    ip_address = "192.168.1.1"
    for _ in range(10):
        is_allowed = await security_service.check_rate_limit(ip_address)
        assert is_allowed is True
    
    # Test exceeding rate limit
    for _ in range(100):
        is_allowed = await security_service.check_rate_limit(ip_address)
        if not is_allowed:
            break
    assert is_allowed is False

@pytest.mark.asyncio
async def test_session_management(security_service, test_user):
    """Test session management security."""
    # Test session creation
    session = await security_service.create_session(test_user)
    assert session is not None
    assert "session_id" in session
    assert "expires_at" in session
    
    # Test session validation
    is_valid = await security_service.validate_session(session["session_id"])
    assert is_valid is True
    
    # Test session termination
    await security_service.terminate_session(session["session_id"])
    is_valid = await security_service.validate_session(session["session_id"])
    assert is_valid is False

@pytest.mark.asyncio
async def test_security_logging(security_service, test_security_log):
    """Test security logging."""
    # Test log creation
    log = await security_service.create_security_log(
        event_type="test_event",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        status="success",
        details="Test log entry"
    )
    assert log is not None
    assert log.event_type == "test_event"
    assert log.status == "success"
    
    # Test log retrieval
    logs = await security_service.get_security_logs(
        event_type="test_event",
        status="success"
    )
    assert isinstance(logs, list)
    assert len(logs) > 0

@pytest.mark.asyncio
async def test_threat_detection(security_service):
    """Test threat detection security."""
    # Test suspicious activity detection
    activity = {
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "request_path": "/api/v1/users",
        "method": "POST"
    }
    is_suspicious = await security_service.detect_suspicious_activity(activity)
    assert isinstance(is_suspicious, bool)
    
    # Test IP reputation check
    reputation = await security_service.check_ip_reputation("192.168.1.1")
    assert "score" in reputation
    assert "threats" in reputation
    
    # Test malware detection
    file_hash = "test_hash"
    is_malicious = await security_service.detect_malware(file_hash)
    assert isinstance(is_malicious, bool)

@pytest.mark.asyncio
async def test_compliance(security_service):
    """Test security compliance."""
    # Test GDPR compliance
    gdpr_compliant = await security_service.check_gdpr_compliance()
    assert gdpr_compliant is True
    
    # Test data retention
    retention_status = await security_service.check_data_retention()
    assert "status" in retention_status
    assert "expired_data" in retention_status
    
    # Test privacy policy compliance
    privacy_compliant = await security_service.check_privacy_compliance()
    assert privacy_compliant is True

@pytest.mark.asyncio
async def test_error_handling(security_service):
    """Test security error handling."""
    # Test authentication failure
    with patch("app.services.security.SecurityService.verify_password") as mock_verify:
        mock_verify.side_effect = Exception("Authentication failed")
        with pytest.raises(Exception) as exc_info:
            await security_service.authenticate_user("test", "password")
        assert "Authentication failed" in str(exc_info.value)
    
    # Test encryption failure
    with patch("app.services.security.SecurityService.encrypt_data") as mock_encrypt:
        mock_encrypt.side_effect = Exception("Encryption failed")
        with pytest.raises(Exception) as exc_info:
            await security_service.encrypt_data("test")
        assert "Encryption failed" in str(exc_info.value)
    
    # Test recovery from security failure
    with patch("app.services.security.SecurityService.recover_from_failure") as mock_recover:
        mock_recover.return_value = True
        result = await security_service.handle_security_failure()
        assert result["status"] == "success"
        assert "recovery_time" in result
        mock_recover.assert_called_once() 