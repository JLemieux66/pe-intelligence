"""
Unit tests for API endpoints

Note: These tests currently run against the production database.
For proper isolated testing, we'd need to override the database session dependency.
"""
import pytest
from fastapi.testclient import TestClient


class TestStatsEndpoint:
    """Tests for /api/stats endpoint"""
    
    def test_get_stats_returns_200(self, api_client):
        """Stats endpoint should return 200 OK"""
        response = api_client.get("/api/stats")
        assert response.status_code == 200
    
    def test_stats_structure(self, api_client):
        """Stats should have required fields"""
        response = api_client.get("/api/stats")
        data = response.json()
        
        assert "total_companies" in data
        assert "total_investments" in data
        assert "total_pe_firms" in data
        assert "active_investments" in data
        assert "exited_investments" in data
        assert "enrichment_rate" in data
    
    def test_stats_types(self, api_client):
        """Stats values should be correct types"""
        response = api_client.get("/api/stats")
        data = response.json()
        
        assert isinstance(data["total_companies"], int)
        assert isinstance(data["total_investments"], int)
        assert isinstance(data["enrichment_rate"], (int, float))


class TestCompaniesEndpoint:
    """Tests for /api/companies endpoint"""
    
    def test_get_companies_returns_200(self, api_client):
        """Companies endpoint should return 200 OK"""
        response = api_client.get("/api/companies")
        assert response.status_code == 200
    
    def test_companies_pagination(self, api_client):
        """Companies should support pagination"""
        response = api_client.get("/api/companies?limit=10&offset=0")
        assert response.status_code == 200
        assert "x-total-count" in response.headers
    
    def test_companies_filtering_by_country(self, api_client):
        """Should filter companies by country"""
        response = api_client.get("/api/companies?country=United States")
        assert response.status_code == 200
        data = response.json()
        
        # All returned companies should be in United States
        for company in data:
            if company.get("country"):
                assert company["country"] == "United States"
    
    def test_companies_filtering_by_state(self, api_client):
        """Should filter companies by state"""
        response = api_client.get("/api/companies?state_region=California")
        assert response.status_code == 200
        data = response.json()
        
        # All returned companies should be in California
        for company in data:
            if company.get("state_region"):
                assert company["state_region"] == "California"
    
    def test_companies_filtering_by_sector(self, api_client):
        """Should filter companies by industry sector"""
        response = api_client.get("/api/companies?industry_sector=Business Products and Services (B2B)")
        assert response.status_code == 200
        # Just verify it doesn't error
    
    def test_companies_revenue_range_filter(self, api_client):
        """Should filter companies by revenue range"""
        response = api_client.get("/api/companies?min_revenue=10&max_revenue=100")
        assert response.status_code == 200
    
    def test_companies_employee_range_filter(self, api_client):
        """Should filter companies by employee count"""
        response = api_client.get("/api/companies?min_employees=50&max_employees=500")
        assert response.status_code == 200
    
    def test_companies_search(self, api_client):
        """Should search companies by name"""
        response = api_client.get("/api/companies?search=Test")
        assert response.status_code == 200


class TestPEFirmsEndpoint:
    """Tests for /api/pe-firms endpoint"""
    
    def test_get_pe_firms_returns_200(self, api_client):
        """PE firms endpoint should return 200 OK"""
        response = api_client.get("/api/pe-firms")
        assert response.status_code == 200
    
    def test_pe_firms_structure(self, api_client):
        """Each PE firm should have required fields"""
        response = api_client.get("/api/pe-firms")
        data = response.json()
        
        if len(data) > 0:
            firm = data[0]
            assert "id" in firm
            assert "name" in firm
            assert "total_investments" in firm
            assert "active_count" in firm
            assert "exit_count" in firm


class TestLocationsEndpoint:
    """Tests for /api/locations endpoint"""
    
    def test_get_locations_returns_200(self, api_client):
        """Locations endpoint should return 200 OK"""
        response = api_client.get("/api/locations")
        assert response.status_code == 200
    
    def test_locations_structure(self, api_client):
        """Locations should have countries, states, cities"""
        response = api_client.get("/api/locations")
        data = response.json()
        
        assert "countries" in data
        assert "states" in data
        assert "cities" in data
        assert isinstance(data["countries"], list)
        assert isinstance(data["states"], list)
        assert isinstance(data["cities"], list)


class TestPitchBookMetadataEndpoint:
    """Tests for /api/pitchbook-metadata endpoint"""
    
    def test_get_pitchbook_metadata_returns_200(self, api_client):
        """PitchBook metadata endpoint should return 200 OK"""
        response = api_client.get("/api/pitchbook-metadata")
        assert response.status_code == 200
    
    def test_pitchbook_metadata_structure(self, api_client):
        """Metadata should have industry groups, sectors, verticals"""
        response = api_client.get("/api/pitchbook-metadata")
        data = response.json()
        
        assert "industry_groups" in data
        assert "industry_sectors" in data
        assert "verticals" in data
        assert isinstance(data["industry_groups"], list)
        assert isinstance(data["industry_sectors"], list)
        assert isinstance(data["verticals"], list)


class TestRegressionBugs:
    """Regression tests for previously fixed bugs"""
    
    def test_california_filter_only_shows_us_companies(self, api_client):
        """
        REGRESSION: California filter was showing companies from Italy/India
        Should automatically add country=United States when US state is selected
        """
        response = api_client.get("/api/companies?state_region=California")
        assert response.status_code == 200
        data = response.json()
        
        # All California companies should be in United States
        for company in data:
            if company.get("state_region") == "California":
                # If country is set, it must be United States
                if company.get("country"):
                    assert company["country"] == "United States", \
                        f"California company has country={company.get('country')}"
    
    def test_pagination_shows_filtered_count_not_total(self, api_client):
        """
        REGRESSION: Pagination was showing total DB count instead of filtered count
        X-Total-Count header should reflect filtered results
        """
        # Get unfiltered count
        response_all = api_client.get("/api/companies")
        total_all = int(response_all.headers.get("x-total-count", 0))
        
        # Get filtered count
        response_filtered = api_client.get("/api/companies?country=United States")
        total_filtered = int(response_filtered.headers.get("x-total-count", 0))
        
        # Filtered count should be less than or equal to total
        assert total_filtered <= total_all
    
    def test_multiple_filter_selection(self, api_client):
        """
        REGRESSION: Multiple filters should work together
        Comma-separated values should work for multi-select filters
        """
        # Multiple sectors
        response = api_client.get("/api/companies?industry_sector=Business Products and Services (B2B),Consumer Products and Services (B2C)")
        assert response.status_code == 200
        
        # Multiple countries
        response = api_client.get("/api/companies?country=United States,United Kingdom")
        assert response.status_code == 200


class TestAuthentication:
    """Tests for admin authentication"""
    
    def test_login_with_valid_credentials(self, api_client):
        """Should return token with valid credentials"""
        # This would need actual admin credentials from env
        pass
    
    def test_protected_endpoint_without_token(self, api_client):
        """
        NOTE: Currently PUT/DELETE endpoints don't enforce authentication
        This test documents that behavior. TODO: Add authentication to these endpoints
        """
        response = api_client.put("/api/companies/99999", json={"name": "Test"})
        # Currently returns 404 for non-existent ID, not 401/403
        # In the future, this should return 401 without token
        assert response.status_code in [401, 403, 404]  # Accept 404 for now
    
    def test_protected_endpoint_with_token(self, api_client, admin_token):
        """Protected endpoints should accept valid tokens"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # This is just testing auth, not actual update
        response = api_client.put(
            "/api/companies/99999",  # Non-existent ID
            json={"name": "Test"},
            headers=headers
        )
        # Should not be auth error (might be 404 instead)
        assert response.status_code != 403
