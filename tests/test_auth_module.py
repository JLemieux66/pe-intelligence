"""
Comprehensive tests for backend.auth module
Tests all authentication functions including password hashing, JWT tokens, and admin auth
"""
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from fastapi import HTTPException
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    verify_admin_token,
    authenticate_admin,
    generate_password_hash,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class TestPasswordHashing:
    """Tests for password hashing functions"""

    def test_hash_password_creates_valid_hash(self):
        """Test that hash_password creates a valid bcrypt hash"""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # Bcrypt hashes start with $2b$
        assert hashed.startswith('$2')

    def test_hash_password_different_each_time(self):
        """Test that hashing same password twice produces different hashes (salt)"""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different due to salt

    def test_verify_password_correct(self):
        """Test verify_password with correct password"""
        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password with incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test verify_password with empty password"""
        hashed = hash_password("not_empty")
        assert verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test verify_password with invalid hash format"""
        result = verify_password("password", "not_a_valid_hash")
        assert result is False

    def test_generate_password_hash(self):
        """Test generate_password_hash utility function"""
        password = "test123"
        hash_value = generate_password_hash(password)

        assert hash_value is not None
        assert isinstance(hash_value, str)
        assert verify_password(password, hash_value) is True


class TestJWTTokens:
    """Tests for JWT token creation and verification"""

    def test_create_access_token(self):
        """Test creating a JWT access token"""
        data = {"sub": "user@example.com", "role": "admin"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_contains_data(self):
        """Test that created token contains the provided data"""
        data = {"sub": "test@example.com", "role": "admin", "custom": "value"}
        token = create_access_token(data)

        # Decode without verification to check contents
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "admin"
        assert decoded["custom"] == "value"
        assert "exp" in decoded  # Expiration should be added

    def test_create_token_adds_expiration(self):
        """Test that token includes expiration time"""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert "exp" in decoded
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()

        # Should expire in approximately ACCESS_TOKEN_EXPIRE_MINUTES
        time_diff = (exp_time - now).total_seconds() / 60
        assert ACCESS_TOKEN_EXPIRE_MINUTES - 1 <= time_diff <= ACCESS_TOKEN_EXPIRE_MINUTES + 1

    def test_verify_token_valid(self):
        """Test verifying a valid token"""
        data = {"sub": "user@example.com", "role": "admin"}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "admin"

    def test_verify_token_expired(self):
        """Test verifying an expired token"""
        # Create token with past expiration
        data = {"sub": "user@example.com"}
        past_time = datetime.utcnow() - timedelta(minutes=10)
        to_encode = data.copy()
        to_encode.update({"exp": past_time})
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_invalid_signature(self):
        """Test verifying token with invalid signature"""
        # Create token with wrong secret
        data = {"sub": "user@example.com"}
        wrong_token = jwt.encode(data, "wrong_secret_key", algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(wrong_token)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_token_malformed(self):
        """Test verifying malformed token"""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.valid.token")

        assert exc_info.value.status_code == 401


class TestAdminTokenVerification:
    """Tests for verify_admin_token function"""

    def test_verify_admin_token_valid(self):
        """Test verify_admin_token with valid bearer token"""
        data = {"sub": "admin@example.com", "role": "admin"}
        token = create_access_token(data)
        authorization = f"Bearer {token}"

        payload = verify_admin_token(authorization)

        assert payload["sub"] == "admin@example.com"
        assert payload["role"] == "admin"

    def test_verify_admin_token_no_header(self):
        """Test verify_admin_token with no authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(None)

        assert exc_info.value.status_code == 401
        assert "not authenticated" in exc_info.value.detail.lower()

    def test_verify_admin_token_invalid_scheme(self):
        """Test verify_admin_token with non-Bearer scheme"""
        token = create_access_token({"sub": "user@example.com"})
        authorization = f"Basic {token}"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(authorization)

        assert exc_info.value.status_code == 401
        assert "scheme" in exc_info.value.detail.lower()

    def test_verify_admin_token_malformed_header(self):
        """Test verify_admin_token with malformed header"""
        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token("MalformedHeaderNoSpace")

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_admin_token_expired(self):
        """Test verify_admin_token with expired token"""
        # Create expired token
        data = {"sub": "admin@example.com"}
        past_time = datetime.utcnow() - timedelta(minutes=10)
        to_encode = data.copy()
        to_encode.update({"exp": past_time})
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        authorization = f"Bearer {expired_token}"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(authorization)

        assert exc_info.value.status_code == 401


class TestAuthenticateAdmin:
    """Tests for authenticate_admin function"""

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH')
    def test_authenticate_admin_success(self, mock_hash):
        """Test successful admin authentication"""
        password = "correct_password"
        mock_hash.__bool__ = Mock(return_value=True)
        mock_hash.__str__ = Mock(return_value=hash_password(password))

        with patch('backend.auth.verify_password', return_value=True):
            result = authenticate_admin('admin@test.com', password)

        assert result is not None
        assert result["email"] == "admin@test.com"
        assert result["role"] == "admin"

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    def test_authenticate_admin_wrong_email(self):
        """Test authentication with wrong email"""
        result = authenticate_admin('wrong@test.com', 'password')
        assert result is None

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH', '')
    def test_authenticate_admin_no_password_configured(self):
        """Test authentication when password hash not configured"""
        with pytest.raises(HTTPException) as exc_info:
            authenticate_admin('admin@test.com', 'password')

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail.lower()

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH')
    def test_authenticate_admin_wrong_password(self, mock_hash):
        """Test authentication with wrong password"""
        mock_hash.__bool__ = Mock(return_value=True)
        mock_hash.__str__ = Mock(return_value=hash_password("correct"))

        with patch('backend.auth.verify_password', return_value=False):
            result = authenticate_admin('admin@test.com', 'wrong_password')

        assert result is None

    @patch('backend.auth.ADMIN_EMAIL', 'admin@test.com')
    @patch('backend.auth.ADMIN_PASSWORD_HASH')
    def test_authenticate_admin_case_sensitive_email(self, mock_hash):
        """Test that email is case sensitive"""
        mock_hash.__bool__ = Mock(return_value=True)

        result = authenticate_admin('ADMIN@TEST.COM', 'password')
        assert result is None  # Email doesn't match


class TestAuthIntegration:
    """Integration tests for full authentication flow"""

    def test_full_auth_flow(self):
        """Test complete flow: hash password -> authenticate -> create token -> verify token"""
        # Setup
        password = "test_password_123"
        email = "test@example.com"
        password_hash = hash_password(password)

        # Verify password works
        assert verify_password(password, password_hash) is True

        # Create token
        data = {"sub": email, "role": "admin"}
        token = create_access_token(data)

        # Verify token
        payload = verify_token(token)
        assert payload["sub"] == email
        assert payload["role"] == "admin"

        # Verify via admin token function
        authorization = f"Bearer {token}"
        admin_payload = verify_admin_token(authorization)
        assert admin_payload["sub"] == email

    def test_token_lifecycle(self):
        """Test token from creation through various verification methods"""
        # Create token
        data = {"sub": "user@example.com", "role": "admin", "permissions": ["read", "write"]}
        token = create_access_token(data)

        # Verify directly
        payload1 = verify_token(token)
        assert payload1["sub"] == data["sub"]
        assert payload1["role"] == data["role"]
        assert payload1["permissions"] == data["permissions"]

        # Verify via admin function
        payload2 = verify_admin_token(f"Bearer {token}")
        assert payload2["sub"] == payload1["sub"]
        assert payload2["role"] == payload1["role"]
