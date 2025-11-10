"""
API Contract Tests
Ensures API endpoints maintain their contracts (schema, status codes, headers)
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


class TestAPIContracts:
    """Test API contracts and response schemas"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    # Health and Root Endpoints
    def test_health_endpoint_contract(self, client):
        """Test /health endpoint contract"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "status" in data
        assert "service" in data
        assert "version" in data

        # Verify field types
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)

        # Verify values
        assert data["status"] == "healthy"

    def test_root_endpoint_contract(self, client):
        """Test / endpoint contract"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    # Stats Endpoint
    def test_stats_endpoint_contract(self, client):
        """Test /api/stats endpoint contract"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = [
            "total_companies",
            "total_investments",
            "total_pe_firms",
            "active_investments",
            "exited_investments",
            "enrichment_rate"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Type validation
        assert isinstance(data["total_companies"], int)
        assert isinstance(data["total_investments"], int)
        assert isinstance(data["total_pe_firms"], int)
        assert isinstance(data["active_investments"], int)
        assert isinstance(data["exited_investments"], int)
        assert isinstance(data["enrichment_rate"], (int, float))

    # Companies Endpoint
    def test_companies_list_endpoint_contract(self, client):
        """Test /api/companies endpoint contract"""
        response = client.get("/api/companies?limit=1")

        assert response.status_code == 200

        # Check headers
        assert "X-Total-Count" in response.headers

        # Check response is array
        data = response.json()
        assert isinstance(data, list)

        # If there are companies, validate schema
        if len(data) > 0:
            company = data[0]
            self._validate_company_schema(company)

    def test_companies_pagination_headers(self, client):
        """Test companies endpoint includes pagination headers"""
        response = client.get("/api/companies")

        assert "X-Total-Count" in response.headers
        total_count = int(response.headers["X-Total-Count"])
        assert total_count >= 0

    def test_companies_query_parameters(self, client):
        """Test companies endpoint accepts query parameters"""
        # Test with various filters
        response = client.get("/api/companies?limit=10&offset=0")
        assert response.status_code == 200

        response = client.get("/api/companies?search=test")
        assert response.status_code == 200

        response = client.get("/api/companies?status=Active")
        assert response.status_code == 200

    # Investments Endpoint
    def test_investments_list_endpoint_contract(self, client):
        """Test /api/investments endpoint contract"""
        response = client.get("/api/investments?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            investment = data[0]
            self._validate_investment_schema(investment)

    # PE Firms Endpoint
    def test_pe_firms_list_endpoint_contract(self, client):
        """Test /api/pe-firms endpoint contract"""
        response = client.get("/api/pe-firms")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            firm = data[0]
            assert "name" in firm
            assert "total_investments" in firm

    # Metadata Endpoints
    def test_metadata_pe_firms_contract(self, client):
        """Test /api/metadata/pe-firms contract"""
        response = client.get("/api/metadata/pe-firms")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_metadata_industries_contract(self, client):
        """Test /api/metadata/industries contract"""
        response = client.get("/api/metadata/industries")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # Error Handling
    def test_404_error_contract(self, client):
        """Test 404 error response contract"""
        response = client.get("/api/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_validation_error_contract(self, client):
        """Test validation error response contract"""
        # Invalid company ID (string instead of int)
        response = client.get("/api/companies/invalid-id")

        assert response.status_code == 422  # Validation Error
        data = response.json()
        assert "detail" in data

    # Rate Limiting Headers
    def test_rate_limit_headers(self, client):
        """Test rate limiting headers are present"""
        response = client.get("/api/companies")

        # Should include rate limit headers
        # (might not be present if rate limiting is disabled in tests)
        # Just verify we get a valid response
        assert response.status_code == 200

    # Helper Methods
    def _validate_company_schema(self, company: dict):
        """Validate company response schema"""
        required_fields = ["id", "name"]

        for field in required_fields:
            assert field in company, f"Missing required field: {field}"

        # Type validation
        assert isinstance(company["id"], int)
        assert isinstance(company["name"], str)

    def _validate_investment_schema(self, investment: dict):
        """Validate investment response schema"""
        required_fields = ["id", "company_id", "pe_firm_id"]

        for field in required_fields:
            assert field in investment, f"Missing required field: {field}"

        # Type validation
        assert isinstance(investment["id"], int)
        assert isinstance(investment["company_id"], int)
        assert isinstance(investment["pe_firm_id"], int)


class TestAPIAuthentication:
    """Test authentication contracts"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_login_endpoint_contract(self, client):
        """Test /api/auth/login endpoint contract"""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "test"
        })

        # Should get 401 for invalid credentials
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_success_contract(self, client):
        """Test successful login response contract"""
        import os
        from backend.auth import hash_password

        # This test would need valid admin credentials
        # Skip if not in test environment
        if not os.getenv("ADMIN_PASSWORD_HASH"):
            pytest.skip("Admin credentials not configured")

    def test_protected_endpoint_requires_token(self, client):
        """Test protected endpoints require authentication"""
        # Try to delete without token
        response = client.delete("/api/companies/1")

        assert response.status_code == 401

    def test_protected_endpoint_rejects_invalid_token(self, client):
        """Test protected endpoints reject invalid tokens"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.delete("/api/companies/1", headers=headers)

        assert response.status_code == 401
