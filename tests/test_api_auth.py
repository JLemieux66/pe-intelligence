"""
Tests for Auth API endpoint
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestLoginEndpoint:
    """Test /api/auth/login endpoint"""

    @patch('backend.api.auth.authenticate_admin')
    @patch('backend.api.auth.create_access_token')
    def test_login_success(self, mock_create_token, mock_auth, client):
        """Test successful login"""
        mock_auth.return_value = {"email": "admin@test.com", "role": "admin"}
        mock_create_token.return_value = "test_token_12345"

        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "correct_password"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token_12345"
        assert data["token_type"] == "bearer"
        assert data["email"] == "admin@test.com"

    @patch('backend.api.auth.authenticate_admin')
    def test_login_invalid_credentials(self, mock_auth, client):
        """Test login with invalid credentials"""
        mock_auth.return_value = None

        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "wrong_password"}
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com"}  # Missing password
        )

        assert response.status_code == 422

    @patch('backend.api.auth.authenticate_admin')
    @patch('backend.api.auth.create_access_token')
    def test_login_creates_jwt_token(self, mock_create_token, mock_auth, client):
        """Test that login creates JWT token with correct data"""
        mock_auth.return_value = {"email": "user@test.com", "role": "admin"}
        mock_create_token.return_value = "jwt_token"

        response = client.post(
            "/api/auth/login",
            json={"email": "user@test.com", "password": "password"}
        )

        assert response.status_code == 200
        # Verify create_access_token was called with correct data
        mock_create_token.assert_called_once()
        call_args = mock_create_token.call_args[1]["data"]
        assert call_args["sub"] == "user@test.com"
        assert call_args["role"] == "admin"
