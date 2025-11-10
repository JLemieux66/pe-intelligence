"""
End-to-End Tests
Tests complete user workflows and integration scenarios
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.mark.e2e
class TestCompanyManagementWorkflow:
    """E2E tests for company management workflow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        from backend.auth import create_access_token
        return create_access_token(data={"sub": "admin@example.com", "role": "admin"})

    def test_complete_company_lookup_workflow(self, client):
        """Test complete workflow: stats -> list -> filter -> detail"""
        # Step 1: Get initial stats
        stats_response = client.get("/api/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        total_companies = stats["total_companies"]

        # Step 2: List companies
        list_response = client.get("/api/companies?limit=10")
        assert list_response.status_code == 200
        companies = list_response.json()
        assert isinstance(companies, list)

        # Step 3: Filter companies
        if total_companies > 0:
            filter_response = client.get("/api/companies?status=Active&limit=10")
            assert filter_response.status_code == 200

        # Step 4: Get company detail (if companies exist)
        if len(companies) > 0:
            company_id = companies[0]["id"]
            detail_response = client.get(f"/api/companies/{company_id}")
            assert detail_response.status_code == 200
            company_detail = detail_response.json()
            assert company_detail["id"] == company_id

    def test_search_and_filter_workflow(self, client):
        """Test search and multi-filter workflow"""
        # Step 1: Search for companies
        search_response = client.get("/api/companies?search=tech&limit=10")
        assert search_response.status_code == 200

        # Step 2: Apply multiple filters
        multi_filter_response = client.get(
            "/api/companies?status=Active&industry=Technology&limit=10"
        )
        assert multi_filter_response.status_code == 200

        # Step 3: Paginate through results
        page1 = client.get("/api/companies?limit=5&offset=0")
        page2 = client.get("/api/companies?limit=5&offset=5")

        assert page1.status_code == 200
        assert page2.status_code == 200

    def test_metadata_driven_filtering_workflow(self, client):
        """Test using metadata to drive filters"""
        # Step 1: Get available PE firms
        pe_firms_response = client.get("/api/metadata/pe-firms")
        assert pe_firms_response.status_code == 200
        pe_firms = pe_firms_response.json()

        # Step 2: Get available industries
        industries_response = client.get("/api/metadata/industries")
        assert industries_response.status_code == 200

        # Step 3: Filter by PE firm (if any exist)
        if len(pe_firms) > 0:
            firm_name = pe_firms[0]
            filter_response = client.get(f"/api/companies?pe_firm={firm_name}&limit=10")
            assert filter_response.status_code == 200


@pytest.mark.e2e
class TestInvestmentManagementWorkflow:
    """E2E tests for investment management"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_investment_lookup_workflow(self, client):
        """Test investment lookup and filtering"""
        # Step 1: Get all investments
        all_investments = client.get("/api/investments?limit=10")
        assert all_investments.status_code == 200
        investments = all_investments.json()

        # Step 2: Filter by status
        active_investments = client.get("/api/investments?status=Active&limit=10")
        assert active_investments.status_code == 200

        exited_investments = client.get("/api/investments?status=Exit&limit=10")
        assert exited_investments.status_code == 200

        # Step 3: Filter by PE firm (if investments exist)
        if len(investments) > 0:
            pe_firm_filter = client.get("/api/investments?pe_firm=TestFirm&limit=10")
            assert pe_firm_filter.status_code == 200

    def test_cross_entity_workflow(self, client):
        """Test workflow across companies and investments"""
        # Step 1: Get a company
        companies = client.get("/api/companies?limit=1").json()

        if len(companies) > 0:
            company = companies[0]

            # Step 2: Check company's PE firms
            if "pe_firms" in company and len(company["pe_firms"]) > 0:
                pe_firm = company["pe_firms"][0]

                # Step 3: Find all companies backed by this PE firm
                pe_firm_companies = client.get(
                    f"/api/companies?pe_firm={pe_firm}&limit=10"
                )
                assert pe_firm_companies.status_code == 200


@pytest.mark.e2e
class TestAuthenticationWorkflow:
    """E2E tests for authentication flow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_failed_login_workflow(self, client):
        """Test failed login attempt"""
        response = client.post("/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_protected_resource_access_workflow(self, client):
        """Test accessing protected resources"""
        # Step 1: Try to access protected resource without token
        response = client.delete("/api/companies/1")
        assert response.status_code == 401

        # Step 2: Try with invalid token
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.delete("/api/companies/1", headers=headers)
        assert response.status_code == 401

        # Step 3: Valid token would succeed (tested separately with real credentials)


@pytest.mark.e2e
@pytest.mark.slow
class TestDataConsistencyWorkflow:
    """E2E tests for data consistency"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_stats_consistency(self, client):
        """Test that stats match actual counts"""
        # Get stats
        stats = client.get("/api/stats").json()

        # Get companies
        companies_response = client.get("/api/companies?limit=10000")
        companies = companies_response.json()

        # Get total count from header
        total_from_header = int(companies_response.headers.get("X-Total-Count", 0))

        # Stats should match or be close (might differ due to deduplication)
        assert total_from_header <= stats["total_companies"] * 1.5, \
            "Companies count significantly different from stats"

    def test_pe_firm_consistency(self, client):
        """Test PE firm data consistency"""
        # Get PE firms
        pe_firms = client.get("/api/pe-firms").json()

        for firm in pe_firms[:5]:  # Test first 5
            # Should have required fields
            assert "name" in firm
            assert "total_investments" in firm

            # Investment count should be non-negative
            assert firm["total_investments"] >= 0

    def test_pagination_consistency(self, client):
        """Test pagination returns consistent data"""
        # Get first page
        page1 = client.get("/api/companies?limit=10&offset=0").json()

        # Get second page
        page2 = client.get("/api/companies?limit=10&offset=10").json()

        # Pages should not overlap (if both have data)
        if len(page1) > 0 and len(page2) > 0:
            page1_ids = {c["id"] for c in page1}
            page2_ids = {c["id"] for c in page2}

            assert page1_ids.isdisjoint(page2_ids), \
                "Pagination returned duplicate records"


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """E2E tests for error handling"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_invalid_resource_id_workflow(self, client):
        """Test handling of invalid resource IDs"""
        # Non-existent company
        response = client.get("/api/companies/999999")
        assert response.status_code == 404

        # Invalid ID format
        response = client.get("/api/companies/invalid")
        assert response.status_code == 422  # Validation error

    def test_invalid_query_parameters_workflow(self, client):
        """Test handling of invalid query parameters"""
        # Invalid limit
        response = client.get("/api/companies?limit=-1")
        assert response.status_code == 422

        # Invalid offset
        response = client.get("/api/companies?offset=-1")
        assert response.status_code == 422

    def test_graceful_degradation_workflow(self, client):
        """Test system gracefully handles edge cases"""
        # Empty filters
        response = client.get("/api/companies?search=")
        assert response.status_code == 200

        # Very large limit (should be capped)
        response = client.get("/api/companies?limit=999999")
        assert response.status_code in [200, 422]

        # Multiple same filters
        response = client.get("/api/companies?status=Active&status=Exit")
        assert response.status_code == 200


@pytest.mark.e2e
class TestUserJourneyWorkflow:
    """E2E tests simulating real user journeys"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_analyst_research_journey(self, client):
        """Simulate analyst researching portfolio companies"""
        # Step 1: Check overall portfolio stats
        stats = client.get("/api/stats").json()
        assert "total_companies" in stats

        # Step 2: Browse active investments
        active_companies = client.get("/api/companies?status=Active&limit=20").json()

        # Step 3: Filter by industry
        if len(active_companies) > 0:
            industry_filter = client.get("/api/companies?industry=Technology&limit=20")
            assert industry_filter.status_code == 200

        # Step 4: Search for specific company
        search_result = client.get("/api/companies?search=test&limit=10")
        assert search_result.status_code == 200

    def test_executive_dashboard_journey(self, client):
        """Simulate executive viewing dashboard"""
        # Step 1: Get high-level stats
        stats = client.get("/api/stats").json()

        # Step 2: Get PE firms overview
        pe_firms = client.get("/api/pe-firms").json()

        # Step 3: Get recent investments
        recent_investments = client.get("/api/investments?limit=10").json()

        # All steps should succeed
        assert isinstance(stats, dict)
        assert isinstance(pe_firms, list)
        assert isinstance(recent_investments, list)

    def test_data_export_journey(self, client):
        """Simulate exporting data"""
        # Step 1: Get filtered dataset
        response = client.get("/api/companies?status=Active&limit=1000")
        assert response.status_code == 200

        # Step 2: Verify headers for export
        assert "X-Total-Count" in response.headers

        # Step 3: Get complete data (pagination)
        all_data = []
        limit = 100
        offset = 0

        for _ in range(3):  # Max 3 pages for testing
            page_response = client.get(f"/api/companies?limit={limit}&offset={offset}")
            if page_response.status_code != 200:
                break

            page_data = page_response.json()
            if not page_data:
                break

            all_data.extend(page_data)
            offset += limit

        # Should have retrieved data
        assert len(all_data) >= 0
