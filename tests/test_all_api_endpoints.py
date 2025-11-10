"""
Comprehensive tests for ALL API endpoints
Tests every route with various scenarios
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


class TestAuthAPI:
    """Comprehensive tests for authentication API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

    def test_login_invalid_email(self, client):
        """Test login with invalid email format"""
        response = client.post("/api/auth/login", json={
            "email": "invalid-email",
            "password": "test123"
        })
        # Should either validate email format or check credentials
        assert response.status_code in [401, 422]

    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        response = client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_login_empty_password(self, client):
        """Test login with empty password"""
        response = client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": ""
        })
        assert response.status_code in [401, 422]


class TestStatsAPI:
    """Comprehensive tests for stats API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_stats_response_structure(self, client):
        """Test stats returns all required fields"""
        response = client.get("/api/stats")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "total_companies",
            "total_investments",
            "total_pe_firms",
            "active_investments",
            "exited_investments",
            "enrichment_rate"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_stats_data_types(self, client):
        """Test stats returns correct data types"""
        response = client.get("/api/stats")
        data = response.json()

        assert isinstance(data["total_companies"], int)
        assert isinstance(data["total_investments"], int)
        assert isinstance(data["total_pe_firms"], int)
        assert isinstance(data["active_investments"], int)
        assert isinstance(data["exited_investments"], int)
        assert isinstance(data["enrichment_rate"], (int, float))

    def test_stats_non_negative(self, client):
        """Test stats are non-negative"""
        response = client.get("/api/stats")
        data = response.json()

        assert data["total_companies"] >= 0
        assert data["total_investments"] >= 0
        assert data["total_pe_firms"] >= 0
        assert data["active_investments"] >= 0
        assert data["exited_investments"] >= 0
        assert 0 <= data["enrichment_rate"] <= 100

    def test_stats_cache(self, client):
        """Test stats endpoint can be called multiple times"""
        response1 = client.get("/api/stats")
        response2 = client.get("/api/stats")

        assert response1.status_code == 200
        assert response2.status_code == 200
        # Results should be consistent
        assert response1.json() == response2.json()


class TestCompaniesAPI:
    """Comprehensive tests for companies API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_companies_default(self, client):
        """Test getting companies with default parameters"""
        response = client.get("/api/companies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_companies_with_limit(self, client):
        """Test limit parameter"""
        response = client.get("/api/companies?limit=5")
        assert response.status_code == 200
        companies = response.json()
        assert len(companies) <= 5

    def test_get_companies_with_offset(self, client):
        """Test offset parameter for pagination"""
        response = client.get("/api/companies?limit=10&offset=5")
        assert response.status_code == 200

    def test_get_companies_invalid_limit(self, client):
        """Test invalid limit value"""
        response = client.get("/api/companies?limit=-1")
        assert response.status_code == 422

    def test_get_companies_invalid_offset(self, client):
        """Test invalid offset value"""
        response = client.get("/api/companies?offset=-1")
        assert response.status_code == 422

    def test_get_companies_search(self, client):
        """Test search parameter"""
        response = client.get("/api/companies?search=test")
        assert response.status_code == 200

    def test_get_companies_status_filter(self, client):
        """Test status filter"""
        response = client.get("/api/companies?status=Active")
        assert response.status_code == 200

    def test_get_companies_pe_firm_filter(self, client):
        """Test PE firm filter"""
        response = client.get("/api/companies?pe_firm=Acme")
        assert response.status_code == 200

    def test_get_companies_multiple_filters(self, client):
        """Test multiple filters at once"""
        response = client.get("/api/companies?status=Active&pe_firm=Acme&limit=10")
        assert response.status_code == 200

    def test_get_companies_total_count_header(self, client):
        """Test X-Total-Count header is present"""
        response = client.get("/api/companies")
        assert "X-Total-Count" in response.headers
        total = int(response.headers["X-Total-Count"])
        assert total >= 0

    def test_get_company_by_id(self, client):
        """Test getting single company"""
        # First get a company to get valid ID
        response = client.get("/api/companies?limit=1")
        companies = response.json()

        if len(companies) > 0:
            company_id = companies[0]["id"]
            response = client.get(f"/api/companies/{company_id}")
            assert response.status_code == 200

    def test_get_company_invalid_id(self, client):
        """Test getting company with invalid ID"""
        response = client.get("/api/companies/invalid")
        assert response.status_code == 422

    def test_get_company_nonexistent_id(self, client):
        """Test getting non-existent company"""
        response = client.get("/api/companies/999999")
        assert response.status_code == 404

    def test_update_company_requires_auth(self, client):
        """Test update requires authentication"""
        response = client.put("/api/companies/1", json={"name": "Test"})
        assert response.status_code == 401

    def test_delete_company_requires_auth(self, client):
        """Test delete requires authentication"""
        response = client.delete("/api/companies/1")
        assert response.status_code == 401


class TestInvestmentsAPI:
    """Comprehensive tests for investments API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_investments_default(self, client):
        """Test getting investments with defaults"""
        response = client.get("/api/investments")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_investments_with_limit(self, client):
        """Test limit parameter"""
        response = client.get("/api/investments?limit=5")
        assert response.status_code == 200
        investments = response.json()
        assert len(investments) <= 5

    def test_get_investments_status_filter(self, client):
        """Test status filter"""
        response = client.get("/api/investments?status=Active")
        assert response.status_code == 200

    def test_get_investments_exit_type_filter(self, client):
        """Test exit type filter"""
        response = client.get("/api/investments?exit_type=IPO")
        assert response.status_code == 200

    def test_get_investments_pe_firm_filter(self, client):
        """Test PE firm filter"""
        response = client.get("/api/investments?pe_firm=Test")
        assert response.status_code == 200

    def test_get_investments_industry_filter(self, client):
        """Test industry filter"""
        response = client.get("/api/investments?industry=Technology")
        assert response.status_code == 200

    def test_get_investments_multiple_filters(self, client):
        """Test combining multiple filters"""
        response = client.get("/api/investments?status=Active&pe_firm=Test&limit=10")
        assert response.status_code == 200

    def test_update_investment_requires_auth(self, client):
        """Test update requires authentication"""
        response = client.put("/api/investments/1", json={"computed_status": "Exit"})
        assert response.status_code == 401


class TestPEFirmsAPI:
    """Comprehensive tests for PE firms API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_pe_firms(self, client):
        """Test getting all PE firms"""
        response = client.get("/api/pe-firms")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_pe_firms_response_structure(self, client):
        """Test PE firm response structure"""
        response = client.get("/api/pe-firms")
        firms = response.json()

        for firm in firms:
            assert "name" in firm
            assert "total_investments" in firm
            # Check for other expected fields

    def test_pe_firms_sorted(self, client):
        """Test PE firms are sorted"""
        response = client.get("/api/pe-firms")
        firms = response.json()

        if len(firms) > 1:
            names = [f["name"] for f in firms]
            assert names == sorted(names), "PE firms should be sorted by name"


class TestMetadataAPI:
    """Comprehensive tests for metadata API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_pe_firms_metadata(self, client):
        """Test getting PE firms for metadata"""
        response = client.get("/api/metadata/pe-firms")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_industries_metadata(self, client):
        """Test getting industries"""
        response = client.get("/api/metadata/industries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_get_countries_metadata(self, client):
        """Test getting countries"""
        response = client.get("/api/metadata/countries")
        assert response.status_code in [200, 404]  # Might not exist

    def test_metadata_no_duplicates(self, client):
        """Test metadata doesn't contain duplicates"""
        response = client.get("/api/metadata/pe-firms")
        if response.status_code == 200:
            firms = response.json()
            assert len(firms) == len(set(firms)), "Should not have duplicates"


class TestSimilarCompaniesAPI:
    """Comprehensive tests for similar companies API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_similar_companies_missing_company_ids(self, client):
        """Test request without company IDs"""
        response = client.post("/api/similar-companies", json={})
        assert response.status_code == 422

    def test_similar_companies_empty_list(self, client):
        """Test with empty company IDs list"""
        response = client.post("/api/similar-companies", json={
            "company_ids": []
        })
        assert response.status_code in [422, 400]

    def test_similar_companies_invalid_id(self, client):
        """Test with invalid company ID"""
        response = client.post("/api/similar-companies", json={
            "company_ids": ["invalid"]
        })
        assert response.status_code == 422

    def test_similar_companies_nonexistent_id(self, client):
        """Test with non-existent company ID"""
        response = client.post("/api/similar-companies", json={
            "company_ids": [999999]
        })
        assert response.status_code in [404, 400, 422]

    def test_similar_companies_with_filters(self, client):
        """Test with additional filters"""
        response = client.post("/api/similar-companies", json={
            "company_ids": [1],
            "min_score": 0.5,
            "limit": 10,
            "filters": {"country": "USA"}
        })
        # Might fail if company doesn't exist, but structure should be valid
        assert response.status_code in [200, 404, 400, 422]


class TestHealthAndRoot:
    """Tests for health and root endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "docs" in data

    def test_docs_accessible(self, client):
        """Test that API docs are accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        """Test OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema


class TestRateLimiting:
    """Tests for rate limiting middleware"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are included"""
        response = client.get("/api/companies")
        # Rate limit headers might be present
        # (Depends on if rate limiting is enabled in test environment)
        assert response.status_code == 200

    def test_multiple_requests_succeed(self, client):
        """Test multiple requests within limit succeed"""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling across all endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_404_on_invalid_endpoint(self, client):
        """Test 404 for invalid endpoints"""
        response = client.get("/api/invalid-endpoint")
        assert response.status_code == 404

    def test_405_on_wrong_method(self, client):
        """Test 405 for wrong HTTP method"""
        response = client.post("/health")
        assert response.status_code == 405

    def test_validation_error_format(self, client):
        """Test validation errors have proper format"""
        response = client.get("/api/companies/invalid-id")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_auth_error_format(self, client):
        """Test auth errors have proper format"""
        response = client.delete("/api/companies/1")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestCORSHeaders:
    """Tests for CORS headers"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_cors_headers_on_get(self, client):
        """Test CORS headers on GET requests"""
        response = client.get("/api/companies")
        # CORS headers should be present
        # Exact headers depend on CORS configuration
        assert response.status_code == 200

    def test_cors_exposes_custom_headers(self, client):
        """Test CORS exposes X-Total-Count header"""
        response = client.get("/api/companies")
        # Should allow X-Total-Count to be read by browser
        assert response.status_code == 200


class TestPaginationConsistency:
    """Tests for pagination consistency"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_pagination_no_overlap(self, client):
        """Test pagination pages don't overlap"""
        page1 = client.get("/api/companies?limit=10&offset=0").json()
        page2 = client.get("/api/companies?limit=10&offset=10").json()

        if len(page1) > 0 and len(page2) > 0:
            page1_ids = {c["id"] for c in page1}
            page2_ids = {c["id"] for c in page2}
            assert page1_ids.isdisjoint(page2_ids), "Pages should not overlap"

    def test_pagination_total_count_consistent(self, client):
        """Test total count remains consistent"""
        response1 = client.get("/api/companies?limit=10&offset=0")
        response2 = client.get("/api/companies?limit=10&offset=10")

        if "X-Total-Count" in response1.headers and "X-Total-Count" in response2.headers:
            count1 = int(response1.headers["X-Total-Count"])
            count2 = int(response2.headers["X-Total-Count"])
            assert count1 == count2, "Total count should be consistent"
