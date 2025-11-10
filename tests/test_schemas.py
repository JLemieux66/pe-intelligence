"""
Comprehensive tests for Pydantic schemas
Tests request and response models with various data scenarios
"""
import pytest
from pydantic import ValidationError
from backend.schemas.requests import (
    LoginRequest,
    LoginResponse,
    SimilarCompaniesRequest,
    CompanyUpdate,
    InvestmentUpdate
)
from backend.schemas.responses import (
    CompanyResponse,
    InvestmentResponse,
    PEFirmResponse,
    StatsResponse,
    SimilarCompanyMatch,
    SimilarCompaniesResponse,
    LocationsResponse,
    PitchBookMetadataResponse,
    IndustriesResponse
)


class TestLoginSchemas:
    """Tests for login request/response schemas"""

    def test_login_request_valid(self):
        """Test valid login request"""
        data = {"email": "admin@example.com", "password": "secure_password"}
        request = LoginRequest(**data)

        assert request.email == "admin@example.com"
        assert request.password == "secure_password"

    def test_login_request_missing_email(self):
        """Test login request missing email"""
        with pytest.raises(ValidationError):
            LoginRequest(password="password")

    def test_login_request_missing_password(self):
        """Test login request missing password"""
        with pytest.raises(ValidationError):
            LoginRequest(email="admin@example.com")

    def test_login_response_valid(self):
        """Test valid login response"""
        data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "bearer",
            "email": "admin@example.com"
        }
        response = LoginResponse(**data)

        assert response.access_token.startswith("eyJ")
        assert response.token_type == "bearer"
        assert response.email == "admin@example.com"


class TestSimilarCompaniesRequest:
    """Tests for similar companies request schema"""

    def test_similar_companies_request_minimal(self):
        """Test request with minimal required fields"""
        data = {"company_ids": [1, 2, 3]}
        request = SimilarCompaniesRequest(**data)

        assert request.company_ids == [1, 2, 3]
        assert request.limit == 20  # Default
        assert request.min_score == 60.0  # Default
        assert request.filters is None  # Default

    def test_similar_companies_request_full(self):
        """Test request with all fields"""
        data = {
            "company_ids": [10, 20],
            "limit": 50,
            "min_score": 75.0,
            "filters": {"country": "USA", "sector": "Technology"}
        }
        request = SimilarCompaniesRequest(**data)

        assert request.company_ids == [10, 20]
        assert request.limit == 50
        assert request.min_score == 75.0
        assert request.filters["country"] == "USA"

    def test_similar_companies_request_empty_ids(self):
        """Test request with empty company IDs"""
        data = {"company_ids": []}
        request = SimilarCompaniesRequest(**data)

        assert request.company_ids == []

    def test_similar_companies_request_missing_ids(self):
        """Test request missing company_ids"""
        with pytest.raises(ValidationError):
            SimilarCompaniesRequest(limit=10)


class TestCompanyUpdate:
    """Tests for company update schema"""

    def test_company_update_empty(self):
        """Test update with no fields (all optional)"""
        update = CompanyUpdate()

        assert update.name is None
        assert update.website is None

    def test_company_update_partial(self):
        """Test update with some fields"""
        data = {
            "name": "Updated Company Name",
            "website": "https://example.com",
            "city": "San Francisco"
        }
        update = CompanyUpdate(**data)

        assert update.name == "Updated Company Name"
        assert update.website == "https://example.com"
        assert update.city == "San Francisco"
        assert update.linkedin_url is None  # Not provided

    def test_company_update_all_fields(self):
        """Test update with all fields"""
        data = {
            "name": "Test Company",
            "website": "https://test.com",
            "linkedin_url": "https://linkedin.com/company/test",
            "crunchbase_url": "https://crunchbase.com/org/test",
            "description": "A test company",
            "city": "New York",
            "state_region": "NY",
            "country": "USA",
            "industry_category": "Technology",
            "revenue_range": "c_10000000_100000000",
            "employee_count": "c_100_250",
            "is_public": True,
            "ipo_exchange": "NYSE",
            "ipo_date": "2023-01-15",
            "primary_industry_group": "IT",
            "primary_industry_sector": "Software",
            "verticals": "SaaS, Cloud",
            "current_revenue_usd": 150.5,
            "last_known_valuation_usd": 1000.0,
            "hq_location": "New York, NY",
            "hq_country": "United States"
        }
        update = CompanyUpdate(**data)

        assert update.name == "Test Company"
        assert update.is_public is True
        assert update.current_revenue_usd == 150.5


class TestInvestmentUpdate:
    """Tests for investment update schema"""

    def test_investment_update_empty(self):
        """Test update with no fields"""
        update = InvestmentUpdate()

        assert update.computed_status is None
        assert update.exit_type is None

    def test_investment_update_status(self):
        """Test updating status fields"""
        data = {
            "computed_status": "Active",
            "raw_status": "Current Investment"
        }
        update = InvestmentUpdate(**data)

        assert update.computed_status == "Active"
        assert update.raw_status == "Current Investment"

    def test_investment_update_exit(self):
        """Test updating exit fields"""
        data = {
            "computed_status": "Exit",
            "exit_type": "IPO",
            "exit_info": "Public offering on NYSE",
            "exit_year": "2023"
        }
        update = InvestmentUpdate(**data)

        assert update.exit_type == "IPO"
        assert update.exit_year == "2023"


class TestCompanyResponse:
    """Tests for company response schema"""

    def test_company_response_minimal(self):
        """Test response with minimal required fields"""
        data = {
            "id": 1,
            "name": "Test Company",
            "pe_firms": ["Acme Capital"],
            "status": "Active"
        }
        response = CompanyResponse(**data)

        assert response.id == 1
        assert response.name == "Test Company"
        assert response.pe_firms == ["Acme Capital"]
        assert response.status == "Active"
        assert response.industries == []  # Default

    def test_company_response_full(self):
        """Test response with all fields"""
        data = {
            "id": 100,
            "name": "Full Company",
            "former_name": "Old Name Inc",
            "pe_firms": ["PE Firm 1", "PE Firm 2"],
            "status": "Active",
            "exit_type": None,
            "investment_year": "2020",
            "headquarters": "San Francisco, CA",
            "website": "https://example.com",
            "linkedin_url": "https://linkedin.com/company/full",
            "crunchbase_url": "https://crunchbase.com/org/full",
            "description": "A comprehensive test company",
            "revenue_range": "$10M - $50M",
            "employee_count": "250",
            "crunchbase_employee_range": "201-500",
            "scraped_employee_count": 250,
            "industry_category": "Technology",
            "industries": ["Software", "SaaS", "Cloud"],
            "total_funding_usd": 50000000,
            "num_funding_rounds": 5,
            "latest_funding_type": "Series C",
            "latest_funding_date": "2023-06-15",
            "funding_stage_encoded": 3,
            "avg_round_size_usd": 10000000,
            "total_investors": 15,
            "predicted_revenue": 25000000.0,
            "prediction_confidence": 0.85,
            "is_public": False,
            "stock_exchange": None,
            "investor_name": "PE Firm 1",
            "investor_status": "Active",
            "investor_holding": "Majority",
            "current_revenue_usd": 45.5,
            "last_known_valuation_usd": 200.0,
            "primary_industry_group": "IT",
            "primary_industry_sector": "Software",
            "hq_location": "San Francisco, CA",
            "hq_country": "United States",
            "last_financing_date": "2023-06-15",
            "last_financing_size_usd": 15.0,
            "last_financing_deal_type": "Series C",
            "verticals": "SaaS, Cloud Computing"
        }
        response = CompanyResponse(**data)

        assert response.id == 100
        assert response.former_name == "Old Name Inc"
        assert len(response.pe_firms) == 2
        assert len(response.industries) == 3
        assert response.predicted_revenue == 25000000.0
        assert response.is_public is False


class TestInvestmentResponse:
    """Tests for investment response schema"""

    def test_investment_response_minimal(self):
        """Test response with minimal fields"""
        data = {
            "investment_id": 1,
            "company_id": 10,
            "company_name": "Test Company",
            "pe_firm_name": "Test PE",
            "status": "Active"
        }
        response = InvestmentResponse(**data)

        assert response.investment_id == 1
        assert response.company_id == 10
        assert response.status == "Active"
        assert response.industries == []  # Default

    def test_investment_response_with_enrichment(self):
        """Test response with enrichment data"""
        data = {
            "investment_id": 5,
            "company_id": 50,
            "company_name": "Enriched Company",
            "pe_firm_name": "Top PE Firm",
            "status": "Active",
            "revenue_range": "$100M - $500M",
            "employee_count": "1,000",
            "industry_category": "Technology",
            "industries": ["Software", "AI"],
            "predicted_revenue": 250000000.0,
            "prediction_confidence": 0.92,
            "headquarters": "Boston, MA",
            "website": "https://enriched.com",
            "primary_industry_group": "IT",
            "current_revenue_usd": 300.0
        }
        response = InvestmentResponse(**data)

        assert response.predicted_revenue == 250000000.0
        assert response.prediction_confidence == 0.92
        assert len(response.industries) == 2


class TestPEFirmResponse:
    """Tests for PE firm response schema"""

    def test_pe_firm_response(self):
        """Test PE firm response"""
        data = {
            "id": 1,
            "name": "Acme Capital",
            "total_investments": 25,
            "active_count": 18,
            "exit_count": 7
        }
        response = PEFirmResponse(**data)

        assert response.id == 1
        assert response.name == "Acme Capital"
        assert response.total_investments == 25
        assert response.active_count == 18
        assert response.exit_count == 7

    def test_pe_firm_response_missing_field(self):
        """Test PE firm response missing required field"""
        with pytest.raises(ValidationError):
            PEFirmResponse(id=1, name="Test", total_investments=10)  # Missing counts


class TestStatsResponse:
    """Tests for stats response schema"""

    def test_stats_response_valid(self):
        """Test valid stats response"""
        data = {
            "total_companies": 1000,
            "total_investments": 1500,
            "total_pe_firms": 50,
            "active_investments": 900,
            "exited_investments": 600,
            "co_investments": 200,
            "enrichment_rate": 0.85
        }
        response = StatsResponse(**data)

        assert response.total_companies == 1000
        assert response.enrichment_rate == 0.85

    def test_stats_response_missing_field(self):
        """Test stats response with missing field"""
        with pytest.raises(ValidationError):
            StatsResponse(
                total_companies=100,
                total_investments=150,
                total_pe_firms=10
                # Missing other required fields
            )


class TestSimilarCompaniesResponse:
    """Tests for similar companies response schema"""

    def test_similar_company_match(self):
        """Test similar company match model"""
        company_data = {
            "id": 1,
            "name": "Match Company",
            "pe_firms": ["PE Firm"],
            "status": "Active"
        }
        match_data = {
            "company": CompanyResponse(**company_data),
            "similarity_score": 85.5,
            "reasoning": "Similar industry and size",
            "matching_attributes": ["industry", "employee_count", "revenue_range"]
        }
        match = SimilarCompanyMatch(**match_data)

        assert match.company.name == "Match Company"
        assert match.similarity_score == 85.5
        assert len(match.matching_attributes) == 3

    def test_similar_companies_response(self):
        """Test full similar companies response"""
        input_company = {
            "id": 1,
            "name": "Input Company",
            "pe_firms": ["PE 1"],
            "status": "Active"
        }
        match_company = {
            "id": 2,
            "name": "Similar Company",
            "pe_firms": ["PE 2"],
            "status": "Active"
        }
        match = {
            "company": CompanyResponse(**match_company),
            "similarity_score": 90.0,
            "reasoning": "Highly similar",
            "matching_attributes": ["industry"]
        }
        data = {
            "input_companies": [CompanyResponse(**input_company)],
            "matches": [SimilarCompanyMatch(**match)],
            "total_results": 1
        }
        response = SimilarCompaniesResponse(**data)

        assert len(response.input_companies) == 1
        assert len(response.matches) == 1
        assert response.total_results == 1
        assert response.matches[0].similarity_score == 90.0


class TestMetadataResponses:
    """Tests for metadata response schemas"""

    def test_locations_response(self):
        """Test locations response"""
        data = {
            "countries": ["USA", "UK", "Canada"],
            "states": ["CA", "NY", "TX"],
            "cities": ["San Francisco", "New York", "Austin"]
        }
        response = LocationsResponse(**data)

        assert len(response.countries) == 3
        assert "USA" in response.countries
        assert len(response.cities) == 3

    def test_locations_response_empty(self):
        """Test locations response with empty lists"""
        data = {
            "countries": [],
            "states": [],
            "cities": []
        }
        response = LocationsResponse(**data)

        assert response.countries == []
        assert response.states == []
        assert response.cities == []

    def test_pitchbook_metadata_response(self):
        """Test PitchBook metadata response"""
        data = {
            "industry_groups": ["IT", "Healthcare"],
            "industry_sectors": ["Software", "Biotech"],
            "verticals": ["SaaS", "Cloud", "AI"],
            "hq_locations": ["San Francisco, CA", "Boston, MA"],
            "hq_countries": ["United States", "United Kingdom"]
        }
        response = PitchBookMetadataResponse(**data)

        assert len(response.industry_groups) == 2
        assert len(response.verticals) == 3
        assert "SaaS" in response.verticals

    def test_industries_response(self):
        """Test industries response"""
        data = {
            "industries": ["Technology", "Healthcare", "Finance"],
            "categories": ["Tech", "Health", "Fin"]
        }
        response = IndustriesResponse(**data)

        assert len(response.industries) == 3
        assert "Technology" in response.industries
        assert len(response.categories) == 3


class TestSchemaValidation:
    """Tests for schema validation edge cases"""

    def test_company_response_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        data = {
            "id": 1,
            "name": "Test",
            "pe_firms": ["PE"],
            "status": "Active",
            "extra_field": "should be ignored"
        }
        response = CompanyResponse(**data)

        assert response.id == 1
        # Extra field should be silently ignored

    def test_company_response_type_coercion(self):
        """Test that types are coerced when possible"""
        data = {
            "id": "1",  # String instead of int
            "name": "Test",
            "pe_firms": ["PE"],
            "status": "Active",
            "total_funding_usd": "1000000"  # String instead of int
        }
        response = CompanyResponse(**data)

        assert response.id == 1  # Coerced to int
        assert response.total_funding_usd == 1000000  # Coerced to int

    def test_invalid_type_raises_error(self):
        """Test that invalid types raise validation error"""
        with pytest.raises(ValidationError):
            CompanyResponse(
                id="not_a_number",  # Can't coerce to int
                name="Test",
                pe_firms=["PE"],
                status="Active"
            )
