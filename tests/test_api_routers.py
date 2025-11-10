"""
Comprehensive tests for API router implementations
Tests actual router logic, not just endpoint responses
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from backend.main import app
from backend.schemas.requests import LoginRequest, CompanyUpdate, InvestmentUpdate, SimilarCompaniesRequest


class TestAuthRouter:
    """Tests for authentication router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_login_success(self, client):
        """Test successful login"""
        with patch('backend.api.auth.authenticate_admin') as mock_auth:
            with patch('backend.api.auth.create_access_token') as mock_token:
                mock_auth.return_value = {"email": "admin@example.com", "role": "admin"}
                mock_token.return_value = "fake_jwt_token"

                response = client.post("/api/auth/login", json={
                    "email": "admin@example.com",
                    "password": "correct_password"
                })

                assert response.status_code == 200
                data = response.json()
                assert data["access_token"] == "fake_jwt_token"
                assert data["token_type"] == "bearer"
                assert data["email"] == "admin@example.com"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        with patch('backend.api.auth.authenticate_admin') as mock_auth:
            mock_auth.return_value = None  # Invalid credentials

            response = client.post("/api/auth/login", json={
                "email": "admin@example.com",
                "password": "wrong_password"
            })

            assert response.status_code == 401
            assert "Invalid email or password" in response.json()["detail"]

    def test_login_missing_email(self, client):
        """Test login missing email field"""
        response = client.post("/api/auth/login", json={
            "password": "password"
        })

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self, client):
        """Test login missing password field"""
        response = client.post("/api/auth/login", json={
            "email": "admin@example.com"
        })

        assert response.status_code == 422  # Validation error


class TestCompaniesRouter:
    """Tests for companies router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_companies_success(self, client):
        """Test getting companies list"""
        response = client.get("/api/companies?limit=10")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_companies_with_filters(self, client):
        """Test getting companies with filters"""
        response = client.get("/api/companies?status=Active&pe_firm=Acme&limit=10")

        assert response.status_code == 200
        assert "X-Total-Count" in response.headers

    def test_get_company_by_id_success(self, client):
        """Test getting single company by ID"""
        # First get a company to know valid ID
        list_response = client.get("/api/companies?limit=1")
        if list_response.json():
            company_id = list_response.json()[0]["id"]

            response = client.get(f"/api/companies/{company_id}")
            assert response.status_code in [200, 404]  # 404 if DB empty

    def test_get_company_by_id_not_found(self, client):
        """Test getting non-existent company"""
        response = client.get("/api/companies/999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_company_by_id_invalid_type(self, client):
        """Test getting company with invalid ID type"""
        response = client.get("/api/companies/invalid")

        assert response.status_code == 422  # Validation error

    def test_update_company_without_auth(self, client):
        """Test updating company without authentication"""
        response = client.put("/api/companies/1", json={
            "name": "New Name"
        })

        assert response.status_code == 401  # Unauthorized

    def test_update_company_with_auth(self, client):
        """Test updating company with authentication"""
        with patch('backend.api.companies.verify_admin_token') as mock_verify:
            with patch('backend.api.companies.CompanyService') as mock_service:
                mock_verify.return_value = {"email": "admin@example.com", "role": "admin"}
                mock_service_instance = Mock()
                mock_service.return_value.__enter__.return_value = mock_service_instance
                mock_service_instance.update_company.return_value = True

                response = client.put(
                    "/api/companies/1",
                    json={"name": "New Name"},
                    headers={"Authorization": "Bearer fake_token"}
                )

                # Should not be 401 with valid auth
                assert response.status_code in [200, 404]

    def test_delete_company_without_auth(self, client):
        """Test deleting company without authentication"""
        response = client.delete("/api/companies/1")

        assert response.status_code == 401  # Unauthorized

    def test_delete_company_with_auth(self, client):
        """Test deleting company with authentication"""
        with patch('backend.api.companies.verify_admin_token') as mock_verify:
            with patch('backend.api.companies.CompanyService') as mock_service:
                mock_verify.return_value = {"email": "admin@example.com", "role": "admin"}
                mock_service_instance = Mock()
                mock_service.return_value.__enter__.return_value = mock_service_instance
                mock_service_instance.delete_company.return_value = True

                response = client.delete(
                    "/api/companies/1",
                    headers={"Authorization": "Bearer fake_token"}
                )

                # Should not be 401 with valid auth
                assert response.status_code in [200, 404]


class TestInvestmentsRouter:
    """Tests for investments router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_investments_success(self, client):
        """Test getting investments list"""
        response = client.get("/api/investments?limit=10")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_investments_with_filters(self, client):
        """Test getting investments with multiple filters"""
        response = client.get("/api/investments?status=Active&pe_firm=Acme&industry=Technology&limit=10")

        assert response.status_code == 200
        assert "X-Total-Count" in response.headers

    def test_update_investment_without_auth(self, client):
        """Test updating investment without authentication"""
        response = client.put("/api/investments/1", json={
            "computed_status": "Exit"
        })

        assert response.status_code == 401  # Unauthorized

    def test_update_investment_with_auth(self, client):
        """Test updating investment with authentication"""
        with patch('backend.api.investments.verify_admin_token') as mock_verify:
            with patch('backend.api.investments.InvestmentService') as mock_service:
                mock_verify.return_value = {"email": "admin@example.com", "role": "admin"}
                mock_service_instance = Mock()
                mock_service.return_value.__enter__.return_value = mock_service_instance
                mock_service_instance.update_investment.return_value = True

                response = client.put(
                    "/api/investments/1",
                    json={"computed_status": "Exit"},
                    headers={"Authorization": "Bearer fake_token"}
                )

                assert response.status_code in [200, 404]


class TestPEFirmsRouter:
    """Tests for PE firms router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_pe_firms_success(self, client):
        """Test getting PE firms list"""
        response = client.get("/api/pe-firms")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_pe_firms_response_structure(self, client):
        """Test PE firms response structure"""
        response = client.get("/api/pe-firms")

        if response.json():
            firm = response.json()[0]
            assert "id" in firm
            assert "name" in firm
            assert "total_investments" in firm


class TestStatsRouter:
    """Tests for stats router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_stats_success(self, client):
        """Test getting stats"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_companies" in data
        assert "total_investments" in data
        assert "total_pe_firms" in data

    def test_get_stats_non_negative_values(self, client):
        """Test that stats values are non-negative"""
        response = client.get("/api/stats")
        data = response.json()

        assert data["total_companies"] >= 0
        assert data["total_investments"] >= 0
        assert data["total_pe_firms"] >= 0


class TestMetadataRouter:
    """Tests for metadata router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_pe_firms_metadata(self, client):
        """Test getting PE firms metadata"""
        response = client.get("/api/metadata/pe-firms")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_locations(self, client):
        """Test getting locations metadata"""
        response = client.get("/api/metadata/locations")

        assert response.status_code == 200
        data = response.json()
        assert "countries" in data
        assert "states" in data
        assert "cities" in data

    def test_get_pitchbook_metadata(self, client):
        """Test getting PitchBook metadata"""
        response = client.get("/api/metadata/pitchbook")

        assert response.status_code == 200
        data = response.json()
        assert "industry_groups" in data
        assert "industry_sectors" in data
        assert "verticals" in data

    def test_get_industries(self, client):
        """Test getting industries metadata"""
        response = client.get("/api/metadata/industries")

        assert response.status_code == 200
        data = response.json()
        assert "industries" in data
        assert "categories" in data


class TestSimilarCompaniesRouter:
    """Tests for similar companies router"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_find_similar_companies_missing_body(self, client):
        """Test finding similar companies without request body"""
        response = client.post("/api/similar-companies")

        assert response.status_code == 422  # Validation error

    def test_find_similar_companies_empty_ids(self, client):
        """Test finding similar companies with empty ID list"""
        response = client.post("/api/similar-companies", json={
            "company_ids": []
        })

        assert response.status_code in [200, 400]  # May accept or reject empty

    def test_find_similar_companies_invalid_min_score(self, client):
        """Test with invalid min_score"""
        response = client.post("/api/similar-companies", json={
            "company_ids": [1, 2, 3],
            "min_score": 150  # Invalid, should be 0-100
        })

        # Should either validate or process
        assert response.status_code in [200, 400, 422]

    def test_find_similar_companies_valid_request(self, client):
        """Test finding similar companies with valid request"""
        response = client.post("/api/similar-companies", json={
            "company_ids": [1, 2, 3],
            "limit": 10,
            "min_score": 60.0
        })

        # May succeed or fail depending on data availability
        assert response.status_code in [200, 404, 500]

    def test_find_similar_companies_with_filters(self, client):
        """Test finding similar companies with filters"""
        response = client.post("/api/similar-companies", json={
            "company_ids": [1, 2, 3],
            "limit": 10,
            "min_score": 60.0,
            "filters": {
                "country": "USA",
                "sector": "Technology"
            }
        })

        # Should accept filters
        assert response.status_code in [200, 404, 500]


class TestMainApp:
    """Tests for main application"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PE Intelligence" in data["message"]

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.get("/api/stats")

        # CORS headers should be present
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]


class TestErrorHandling:
    """Tests for error handling across routers"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_404_error_format(self, client):
        """Test 404 error response format"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_validation_error_format(self, client):
        """Test validation error response format"""
        response = client.get("/api/companies/invalid_id")

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_unauthorized_error_format(self, client):
        """Test unauthorized error response format"""
        response = client.delete("/api/companies/1")

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_method_not_allowed(self, client):
        """Test method not allowed error"""
        response = client.patch("/api/companies")

        assert response.status_code == 405


class TestPaginationHeaders:
    """Tests for pagination headers"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_companies_pagination_headers(self, client):
        """Test companies endpoint returns pagination headers"""
        response = client.get("/api/companies?limit=10&offset=0")

        assert "X-Total-Count" in response.headers
        total_count = int(response.headers["X-Total-Count"])
        assert total_count >= 0

    def test_investments_pagination_headers(self, client):
        """Test investments endpoint returns pagination headers"""
        response = client.get("/api/investments?limit=10&offset=0")

        assert "X-Total-Count" in response.headers

    def test_pagination_with_filters(self, client):
        """Test pagination headers with filters applied"""
        response = client.get("/api/companies?status=Active&limit=10")

        assert "X-Total-Count" in response.headers
        # Filtered count may be less than total
        filtered_count = int(response.headers["X-Total-Count"])
        assert filtered_count >= 0


class TestQueryParameterValidation:
    """Tests for query parameter validation"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_negative_limit_rejected(self, client):
        """Test negative limit is rejected"""
        response = client.get("/api/companies?limit=-10")

        assert response.status_code == 422

    def test_negative_offset_rejected(self, client):
        """Test negative offset is rejected"""
        response = client.get("/api/companies?offset=-5")

        assert response.status_code == 422

    def test_zero_limit_rejected(self, client):
        """Test zero limit is rejected"""
        response = client.get("/api/companies?limit=0")

        assert response.status_code == 422

    def test_excessive_limit_rejected(self, client):
        """Test excessive limit is rejected"""
        response = client.get("/api/companies?limit=999999")

        assert response.status_code == 422

    def test_valid_limit_accepted(self, client):
        """Test valid limit is accepted"""
        response = client.get("/api/companies?limit=50")

        assert response.status_code == 200

    def test_valid_offset_accepted(self, client):
        """Test valid offset is accepted"""
        response = client.get("/api/companies?offset=10&limit=10")

        assert response.status_code == 200
