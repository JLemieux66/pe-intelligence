"""
Unit tests for uncovered CompanyService methods
Targets build_company_response, get_companies, get_company_by_id, update_company, delete_company
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from backend.services.company_service import CompanyService
from backend.schemas.requests import CompanyUpdate
from backend.schemas.responses import CompanyResponse
from src.models.database_models_v2 import Company, CompanyPEInvestment, PEFirm, CompanyTag, FundingRound


class TestBuildCompanyResponse:
    """Tests for build_company_response method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return CompanyService(session=mock_session)

    @pytest.fixture
    def sample_company(self):
        """Create a complete company mock"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Acme Corp"
        company.former_name = "Acme Inc"
        company.website = "https://acme.com"
        company.linkedin_url = "https://linkedin.com/company/acme"
        company.crunchbase_url = "https://crunchbase.com/acme"
        company.description = "A test company"
        company.revenue_range = "r_00100000"
        company.employee_count = 500
        company.projected_employee_count = None
        company.crunchbase_employee_count = None
        company.industry_category = "Software"
        company.total_funding_usd = 50000000.0
        company.num_funding_rounds = 3
        company.latest_funding_type = "Series B"
        company.latest_funding_date = datetime(2023, 6, 15)
        company.funding_stage_encoded = 3
        company.avg_round_size_usd = 16666667  # Must be integer
        company.total_investors = 10
        company.predicted_revenue = 25000000.0
        company.prediction_confidence = 0.85
        company.is_public = False
        company.ipo_exchange = None
        company.investor_name = "Test Investor"
        company.investor_status = "Lead"
        company.investor_holding = "20%"
        company.current_revenue_usd = 30000000.0
        company.last_known_valuation_usd = 150000000.0
        company.primary_industry_group = "Technology"
        company.primary_industry_sector = "Software"
        company.hq_location = "San Francisco"
        company.hq_country = "USA"
        company.last_financing_date = datetime(2023, 6, 15)
        company.last_financing_size_usd = 20000000.0
        company.last_financing_deal_type = "Series B"
        company.verticals = "SaaS, Cloud"
        company.city = None
        company.state_region = None
        company.country = None
        return company

    def test_build_company_response_complete(self, service, sample_company, mock_session):
        """Test building complete company response"""
        # Mock helper method calls
        with patch.object(service, 'get_company_pe_firms', return_value=["PE Firm A", "PE Firm B"]):
            with patch.object(service, 'get_company_status', return_value="Active"):
                with patch.object(service, 'get_company_investment_year', return_value="2020"):
                    with patch.object(service, 'get_company_exit_type', return_value=None):
                        with patch.object(service, 'build_headquarters', return_value="San Francisco, USA"):
                            with patch.object(service, 'get_company_industries', return_value=["Software", "Cloud"]):
                                with patch.object(service, 'get_employee_count_display', return_value="500"):
                                    response = service.build_company_response(sample_company)

        # Verify response structure
        assert isinstance(response, CompanyResponse)
        assert response.id == 1
        assert response.name == "Acme Corp"
        assert response.former_name == "Acme Inc"
        assert response.pe_firms == ["PE Firm A", "PE Firm B"]
        assert response.status == "Active"
        assert response.investment_year == "2020"
        assert response.exit_type is None
        assert response.headquarters == "San Francisco, USA"
        assert response.website == "https://acme.com"
        assert response.linkedin_url == "https://linkedin.com/company/acme"
        assert response.crunchbase_url == "https://crunchbase.com/acme"
        assert response.description == "A test company"
        assert response.revenue_range == "$100M - $500M"
        assert response.employee_count == "500"
        assert response.industry_category == "Software"
        assert response.industries == ["Software", "Cloud"]

    def test_build_company_response_minimal_data(self, service, mock_session):
        """Test building response with minimal company data"""
        company = Mock(spec=Company)
        company.id = 2
        company.name = "Minimal Corp"
        company.former_name = None
        company.website = None
        company.linkedin_url = None
        company.crunchbase_url = None
        company.description = None
        company.revenue_range = None
        company.employee_count = None
        company.projected_employee_count = None
        company.crunchbase_employee_count = None
        company.industry_category = None
        company.total_funding_usd = None
        company.num_funding_rounds = None
        company.latest_funding_type = None
        company.latest_funding_date = None
        company.funding_stage_encoded = None
        company.avg_round_size_usd = None
        company.total_investors = None
        company.predicted_revenue = None
        company.prediction_confidence = None
        company.is_public = False
        company.ipo_exchange = None
        company.current_revenue_usd = None
        company.last_known_valuation_usd = None
        company.last_financing_date = None
        company.last_financing_size_usd = None
        # Set getattr-accessed optional fields to None explicitly
        company.investor_name = None
        company.investor_status = None
        company.investor_holding = None
        company.primary_industry_group = None
        company.primary_industry_sector = None
        company.hq_location = None
        company.hq_country = None
        company.last_financing_deal_type = None
        company.verticals = None

        with patch.object(service, 'get_company_pe_firms', return_value=[]):
            with patch.object(service, 'get_company_status', return_value="Unknown"):
                with patch.object(service, 'get_company_investment_year', return_value=None):
                    with patch.object(service, 'get_company_exit_type', return_value=None):
                        with patch.object(service, 'build_headquarters', return_value=None):
                            with patch.object(service, 'get_company_industries', return_value=[]):
                                with patch.object(service, 'get_employee_count_display', return_value=None):
                                    response = service.build_company_response(company)

        assert response.id == 2
        assert response.name == "Minimal Corp"
        assert response.pe_firms == []
        assert response.status == "Unknown"

    def test_build_company_response_with_dates(self, service, sample_company, mock_session):
        """Test date formatting in response"""
        sample_company.latest_funding_date = datetime(2023, 6, 15)
        sample_company.last_financing_date = datetime(2023, 6, 15)

        with patch.object(service, 'get_company_pe_firms', return_value=[]):
            with patch.object(service, 'get_company_status', return_value="Active"):
                with patch.object(service, 'get_company_investment_year', return_value="2020"):
                    with patch.object(service, 'get_company_exit_type', return_value=None):
                        with patch.object(service, 'build_headquarters', return_value=None):
                            with patch.object(service, 'get_company_industries', return_value=[]):
                                with patch.object(service, 'get_employee_count_display', return_value=None):
                                    response = service.build_company_response(sample_company)

        assert response.latest_funding_date == "2023-06-15T00:00:00"
        assert response.last_financing_date == "2023-06-15T00:00:00"


class TestGetCompanies:
    """Tests for get_companies method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return CompanyService(session=mock_session)

    def test_get_companies_success(self, service, mock_session):
        """Test successful get_companies call"""
        # Mock company
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.name = "Test Company"

        # Mock query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_company]

        # Mock apply_filters to return query unchanged
        with patch.object(service, 'apply_filters', return_value=mock_query):
            # Mock build_company_response
            mock_response = Mock(spec=CompanyResponse)
            mock_response.id = 1
            with patch.object(service, 'build_company_response', return_value=mock_response):
                companies, total = service.get_companies(filters={}, limit=10, offset=0)

        assert len(companies) == 1
        assert total == 1
        assert companies[0].id == 1

    def test_get_companies_empty_result(self, service, mock_session):
        """Test get_companies with no results"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(service, 'apply_filters', return_value=mock_query):
            companies, total = service.get_companies(filters={}, limit=10, offset=0)

        assert companies == []
        assert total == 0

    def test_get_companies_with_pagination(self, service, mock_session):
        """Test get_companies respects pagination"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(service, 'apply_filters', return_value=mock_query):
            companies, total = service.get_companies(filters={}, limit=20, offset=40)

        # Verify offset and limit were called
        mock_query.offset.assert_called_once_with(40)
        mock_query.limit.assert_called_once_with(20)
        assert total == 100


class TestGetCompanyById:
    """Tests for get_company_by_id method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return CompanyService(session=mock_session)

    def test_get_company_by_id_found(self, service, mock_session):
        """Test getting company by ID when it exists"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.name = "Found Company"

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        mock_response = Mock(spec=CompanyResponse)
        mock_response.id = 1
        mock_response.name = "Found Company"

        with patch.object(service, 'build_company_response', return_value=mock_response):
            result = service.get_company_by_id(company_id=1)

        assert result is not None
        assert result.id == 1
        assert result.name == "Found Company"

    def test_get_company_by_id_not_found(self, service, mock_session):
        """Test getting company by ID when it doesn't exist"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = service.get_company_by_id(company_id=999)

        assert result is None


class TestUpdateCompany:
    """Tests for update_company method"""

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return CompanyService(session=mock_session)

    def test_update_company_success(self, service, mock_session):
        """Test successful company update"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.name = "Old Name"
        mock_company.website = "https://old.com"

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        update_data = CompanyUpdate(
            name="New Name",
            website="https://new.com",
            description="Updated description"
        )

        result = service.update_company(company_id=1, company_update=update_data)

        assert result is True
        assert mock_company.name == "New Name"
        assert mock_company.website == "https://new.com"
        assert mock_company.description == "Updated description"
        mock_session.commit.assert_called_once()

    def test_update_company_not_found(self, service, mock_session):
        """Test updating non-existent company"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        update_data = CompanyUpdate(name="New Name")

        result = service.update_company(company_id=999, company_update=update_data)

        assert result is False
        mock_session.commit.assert_not_called()

    def test_update_company_partial_fields(self, service, mock_session):
        """Test updating only some fields"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1
        mock_company.name = "Original Name"
        mock_company.website = "https://original.com"
        mock_company.description = "Original description"

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        # Only update name
        update_data = CompanyUpdate(name="Updated Name")

        result = service.update_company(company_id=1, company_update=update_data)

        assert result is True
        assert mock_company.name == "Updated Name"
        # Other fields should remain unchanged
        assert mock_company.website == "https://original.com"

    def test_update_company_all_fields(self, service, mock_session):
        """Test updating all available fields"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        update_data = CompanyUpdate(
            name="New Name",
            website="https://new.com",
            linkedin_url="https://linkedin.com/new",
            crunchbase_url="https://crunchbase.com/new",
            description="New description",
            city="New York",
            state_region="NY",
            country="USA",
            industry_category="Technology",
            revenue_range="r_00100000",
            employee_count="c_00501_01000",
            is_public=True,
            ipo_exchange="NASDAQ",
            ipo_date="2023-01-01",
            primary_industry_group="IT",
            primary_industry_sector="Software",
            verticals="SaaS, Cloud",
            current_revenue_usd=50000000.0,
            last_known_valuation_usd=200000000.0,
            hq_location="NYC",
            hq_country="USA"
        )

        result = service.update_company(company_id=1, company_update=update_data)

        assert result is True
        assert mock_company.name == "New Name"
        assert mock_company.website == "https://new.com"
        assert mock_company.city == "New York"
        assert mock_company.is_public is True
        assert mock_company.verticals == "SaaS, Cloud"
        mock_session.commit.assert_called_once()


class TestDeleteCompany:
    """Tests for delete_company method"""

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session.delete = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return CompanyService(session=mock_session)

    def test_delete_company_success(self, service, mock_session):
        """Test successful company deletion"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1

        # Mock main company query
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        # Mock deletion queries
        mock_delete_query = Mock()
        mock_delete_query.filter.return_value = mock_delete_query
        mock_delete_query.delete.return_value = None

        # Configure query to return delete queries for related data
        def query_side_effect(model):
            if model == Company:
                return mock_query
            else:
                return mock_delete_query

        mock_session.query.side_effect = query_side_effect

        result = service.delete_company(company_id=1)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_company)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    def test_delete_company_not_found(self, service, mock_session):
        """Test deleting non-existent company"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = service.delete_company(company_id=999)

        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_delete_company_with_exception(self, service, mock_session):
        """Test delete company handles exceptions"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        # Mock deletion queries that raise exception
        mock_delete_query = Mock()
        mock_delete_query.filter.return_value = mock_delete_query
        mock_delete_query.delete.side_effect = Exception("Database error")

        def query_side_effect(model):
            if model == Company:
                return mock_query
            else:
                return mock_delete_query

        mock_session.query.side_effect = query_side_effect

        result = service.delete_company(company_id=1)

        assert result is False
        mock_session.rollback.assert_called_once()

    def test_delete_company_cascade_deletes(self, service, mock_session):
        """Test that delete removes related records"""
        mock_company = Mock(spec=Company)
        mock_company.id = 1

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_company

        # Track delete calls
        delete_calls = []
        mock_delete_query = Mock()

        def delete_side_effect():
            delete_calls.append("deleted")
            return None

        mock_delete_query.filter.return_value = mock_delete_query
        mock_delete_query.delete.side_effect = delete_side_effect

        def query_side_effect(model):
            if model == Company:
                return mock_query
            else:
                return mock_delete_query

        mock_session.query.side_effect = query_side_effect

        result = service.delete_company(company_id=1)

        assert result is True
        # Should delete: investments, tags, funding rounds
        assert len(delete_calls) == 3
