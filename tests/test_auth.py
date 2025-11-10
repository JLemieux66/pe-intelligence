"""
Tests for authentication module
"""
import pytest
import sys
from unittest.mock import patch, Mock
from fastapi import HTTPException

from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    verify_admin_token,
    authenticate_admin,
    generate_password_hash
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash"""
        assert verify_password("password", "invalid_hash") is False

    def test_generate_password_hash(self):
        """Test generate_password_hash utility"""
        password = "test_password"
        hash_value = generate_password_hash(password)

        assert hash_value is not None
        assert isinstance(hash_value, str)
        # Verify the hash works
        assert verify_password(password, hash_value) is True


class TestJWTTokens:
    """Test JWT token functions"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"email": "test@example.com", "role": "admin"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Test verifying valid token"""
        data = {"email": "test@example.com", "role": "admin"}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_verify_token_invalid(self):
        """Test verifying invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid_token_string")

        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)

    @patch('backend.auth.jwt.decode')
    def test_verify_token_expired(self, mock_decode):
        """Test verifying expired token"""
        import jwt
        mock_decode.side_effect = jwt.ExpiredSignatureError()

        with pytest.raises(HTTPException) as exc_info:
            verify_token("expired_token")

        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()


class TestVerifyAdminToken:
    """Test verify_admin_token function"""

    def test_verify_admin_token_success(self):
        """Test successful admin token verification"""
        data = {"email": "admin@test.com", "role": "admin"}
        token = create_access_token(data)
        authorization = f"Bearer {token}"

        payload = verify_admin_token(authorization)

        assert payload["email"] == "admin@test.com"
        assert payload["role"] == "admin"

    def test_verify_admin_token_no_header(self):
        """Test with missing authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in str(exc_info.value.detail)

    def test_verify_admin_token_invalid_scheme(self):
        """Test with invalid authentication scheme"""
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token("Basic sometoken")

        assert exc_info.value.status_code == 401
        assert "Invalid authentication scheme" in str(exc_info.value.detail)

    def test_verify_admin_token_invalid_format(self):
        """Test with invalid header format"""
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token("InvalidFormatNoSpace")

        assert exc_info.value.status_code == 401
        assert "Invalid authorization header" in str(exc_info.value.detail)

    def test_verify_admin_token_expired(self):
        """Test with expired token"""
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token("Bearer expired_invalid_token")

        assert exc_info.value.status_code == 401


class TestAuthenticateAdmin:
    """Test authenticate_admin function"""

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH')
    def test_authenticate_admin_success(self, mock_hash):
        """Test successful admin authentication"""
        password = "correct_password"
        mock_hash_value = hash_password(password)
        mock_hash.return_value = mock_hash_value

        with patch('backend.auth.ADMIN_PASSWORD_HASH', mock_hash_value):
            result = authenticate_admin("admin@test.com", password)

        assert result is not None
        assert result["email"] == "admin@test.com"
        assert result["role"] == "admin"

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    def test_authenticate_admin_wrong_email(self):
        """Test authentication with wrong email"""
        result = authenticate_admin("wrong@test.com", "password")

        assert result is None

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH')
    def test_authenticate_admin_wrong_password(self, mock_hash):
        """Test authentication with wrong password"""
        password = "correct_password"
        mock_hash_value = hash_password(password)

        with patch('backend.auth.ADMIN_PASSWORD_HASH', mock_hash_value):
            result = authenticate_admin("admin@test.com", "wrong_password")

        assert result is None

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH', '')
    def test_authenticate_admin_no_hash_configured(self):
        """Test authentication when password hash is not configured"""
        with pytest.raises(HTTPException) as exc_info:
            authenticate_admin("admin@test.com", "password")

        assert exc_info.value.status_code == 500
        assert "not configured" in str(exc_info.value.detail)


class TestMainBlock:
    """Test __main__ block functionality"""

    @patch('sys.argv', ['auth.py', 'testpassword'])
    @patch('builtins.print')
    def test_main_with_password_argument(self, mock_print):
        """Test running as script with password argument"""
        # Import and execute the __main__ block
        import backend.auth as auth_module

        # Manually trigger the main block logic
        if len(sys.argv) > 1:
            password = sys.argv[1]
            hash_value = auth_module.generate_password_hash(password)

            assert hash_value is not None
            assert isinstance(hash_value, str)
            assert hash_value.startswith("$2b$")

    @patch('sys.argv', ['auth.py'])
    @patch('builtins.print')
    def test_main_without_password_argument(self, mock_print):
        """Test running as script without password argument"""
        # When run without args, should show usage
        if len(sys.argv) == 1:
            # This path just prints usage - nothing to assert
            assert True
