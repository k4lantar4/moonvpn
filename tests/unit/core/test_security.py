"""Unit tests for security functionality."""

import pytest
from datetime import datetime, timedelta
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    verify_token,
    generate_refresh_token,
    verify_refresh_token
)

class TestPasswordSecurity:
    """Test password security functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed_password = get_password_hash(password)
        
        assert hashed_password != password
        assert verify_password(password, hashed_password) is True
        assert verify_password("wrongpassword", hashed_password) is False

    def test_password_hash_uniqueness(self):
        """Test that password hashes are unique."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Should be different due to salt
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

class TestTokenSecurity:
    """Test token security functions."""
    
    def test_access_token_creation(self):
        """Test access token creation."""
        user_id = 123
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_verification(self):
        """Test access token verification."""
        user_id = 123
        token = create_access_token(user_id)
        
        # Verify valid token
        decoded = verify_token(token)
        assert decoded is not None
        assert decoded["sub"] == str(user_id)
        assert "exp" in decoded
        
        # Verify expired token
        expired_token = create_access_token(
            user_id,
            expires_delta=timedelta(seconds=-1)
        )
        assert verify_token(expired_token) is None

    def test_refresh_token_creation(self):
        """Test refresh token creation."""
        user_id = 123
        token = generate_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_verification(self):
        """Test refresh token verification."""
        user_id = 123
        token = generate_refresh_token(user_id)
        
        # Verify valid token
        decoded = verify_refresh_token(token)
        assert decoded is not None
        assert decoded["sub"] == str(user_id)
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
        
        # Verify expired token
        expired_token = generate_refresh_token(
            user_id,
            expires_delta=timedelta(seconds=-1)
        )
        assert verify_refresh_token(expired_token) is None

    def test_invalid_token_handling(self):
        """Test handling of invalid tokens."""
        invalid_tokens = [
            "",  # Empty token
            "invalid.token.format",  # Invalid format
            "not.a.jwt.token",  # Not a JWT token
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"  # Invalid signature
        ]
        
        for token in invalid_tokens:
            assert verify_token(token) is None
            assert verify_refresh_token(token) is None 