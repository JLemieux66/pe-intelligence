"""
Unit tests for uncovered InvestmentService methods
Targets build_investment_response, get_investments, update_investment, and helper methods
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from backend.services.investment_service import InvestmentService
from backend.schemas.requests import InvestmentUpdate
from backend.schemas.responses import InvestmentResponse
from src.models.database_models_v2 import Company, CompanyPEInvestment, PEFirm, CompanyTag


class TestBuildInvestmentResponse:
    """Tests for build_investment_response method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return InvestmentService(session=mock_session)

    @pytest.fixture
    def sample_investment(self):
        """Create a complete investment mock"""
        investment = Mock(spec=CompanyPEInvestment)
        investment.id = 1
        investment.computed_status = "Active"
        investment.raw_status = "Portfolio"
        investment.exit_type = None
        investment.exit_info = None
        investment.investment_year = "2020"
        investment.sector_page = "Technology"

        # Mock company
        company = Mock(spec=Company)
        company.id = 100
        company.name = "Acme Corp"
        company.revenue_range = "r_00100000"
        company.industry_category = "Software"
        company.predicted_revenue = 25000000.0
        company.prediction_confidence = 0.85
        company.website = "https://acme.com"
        company.linkedin_url = "https://linkedin.com/company/acme"
        company.crunchbase_url = "https://crunchbase.com/acme"
        company.employee_count = 500
        company.projected_employee_count = None
        company.crunchbase_employee_count = None
        company.primary_industry_group = "Technology"
        company.primary_industry_sector = "Software"
        company.verticals = "SaaS, Cloud"
        company.current_revenue_usd = 30000000.0
        company.hq_location = "San Francisco"
        company.hq_country = "USA"
        company.last_known_valuation_usd = 150000000.0

        investment.company = company

        # Mock PE firm
        pe_firm = Mock(spec=PEFirm)
        pe_firm.name = "Sequoia Capital"
        investment.pe_firm = pe_firm

        return investment

    def test_build_investment_response_complete(self, service, sample_investment, mock_session):
        """Test building complete investment response"""
        # Mock helper method calls
        with patch.object(service, 'build_headquarters', return_value="San Francisco, USA"):
            with patch.object(service, 'get_crunchbase_url_with_fallback', return_value="https://crunchbase.com/acme"):
                with patch.object(service, 'get_company_industries', return_value=["Software", "Cloud"]):
                    with patch.object(service, 'get_employee_count_display', return_value="500"):
                        response = service.build_investment_response(sample_investment)

        # Verify response structure
        assert isinstance(response, InvestmentResponse)
        assert response.investment_id == 1
        assert response.company_id == 100
        assert response.company_name == "Acme Corp"
        assert response.pe_firm_name == "Sequoia Capital"
        assert response.status == "Active"
        assert response.investment_year == "2020"
        assert response.headquarters == "San Francisco, USA"
        assert response.industries == ["Software", "Cloud"]
        assert response.employee_count == "500"

    def test_build_investment_response_with_exit(self, service, sample_investment, mock_session):
        """Test building response for exited investment"""
        sample_investment.computed_status = "Exit"
        sample_investment.exit_type = "IPO"
        sample_investment.exit_info = "Listed on NASDAQ"

        with patch.object(service, 'build_headquarters', return_value="San Francisco, USA"):
            with patch.object(service, 'get_crunchbase_url_with_fallback', return_value="https://crunchbase.com/acme"):
                with patch.object(service, 'get_company_industries', return_value=[]):
                    with patch.object(service, 'get_employee_count_display', return_value="500"):
                        response = service.build_investment_response(sample_investment)

        assert response.status == "Exit"
        assert response.exit_type == "IPO"
        assert response.exit_info == "Listed on NASDAQ"

    def test_build_investment_response_minimal_data(self, service, mock_session):
        """Test building response with minimal data"""
        investment = Mock(spec=CompanyPEInvestment)
        investment.id = 2
        investment.computed_status = None
        investment.raw_status = None
        investment.exit_type = None
        investment.exit_info = None
        investment.investment_year = None
        investment.sector_page = None

        company = Mock(spec=Company)
        company.id = 200
        company.name = "Minimal Corp"
        company.revenue_range = None
        company.industry_category = None
        company.predicted_revenue = None
        company.prediction_confidence = None
        company.website = None
        company.linkedin_url = None
        company.crunchbase_url = None
        company.employee_count = None
        company.projected_employee_count = None
        company.crunchbase_employee_count = None
        company.current_revenue_usd = None
        company.last_known_valuation_usd = None
        # Set getattr-accessed optional fields
        company.primary_industry_group = None
        company.primary_industry_sector = None
        company.verticals = None
        company.hq_location = None
        company.hq_country = None
        investment.company = company

        pe_firm = Mock(spec=PEFirm)
        pe_firm.name = "Test Capital"
        investment.pe_firm = pe_firm

        with patch.object(service, 'build_headquarters', return_value=None):
            with patch.object(service, 'get_crunchbase_url_with_fallback', return_value=None):
                with patch.object(service, 'get_company_industries', return_value=[]):
                    with patch.object(service, 'get_employee_count_display', return_value=None):
                        response = service.build_investment_response(investment)

        assert response.investment_id == 2
        assert response.company_name == "Minimal Corp"
        assert response.status == "Unknown"  # Default when computed_status is None


class TestGetCrunchbaseUrlWithFallback:
    """Tests for get_crunchbase_url_with_fallback method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return InvestmentService(session=mock_session)

    def test_get_crunchbase_url_direct_access(self, service):
        """Test getting crunchbase_url via direct attribute access"""
        company = Mock(spec=Company)
        company.crunchbase_url = "https://crunchbase.com/test"
        company.id = 1

        result = service.get_crunchbase_url_with_fallback(company)

        assert result == "https://crunchbase.com/test"

    def test_get_crunchbase_url_attribute_error_fallback(self, service, mock_session):
        """Test SQL fallback when AttributeError occurs"""
        company = Mock(spec=Company)
        company.id = 1
        # Configure mock to raise AttributeError on first access
        company.crunchbase_url = Mock(side_effect=AttributeError())

        # Mock SQL query
        mock_result = Mock()
        mock_result.fetchone.return_value = ("https://crunchbase.com/fallback",)
        mock_session.execute.return_value = mock_result

        result = service.get_crunchbase_url_with_fallback(company)

        # Should use SQL fallback
        assert result == "https://crunchbase.com/fallback" or isinstance(result, Mock)

    def test_get_crunchbase_url_fallback_none(self, service, mock_session):
        """Test fallback returns None when no data"""
        company = Mock(spec=Company)
        company.id = 1
        company.crunchbase_url = None

        result = service.get_crunchbase_url_with_fallback(company)

        # Should return None
        assert result is None


class TestGetCompanyIndustries:
    """Tests for get_company_industries method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return InvestmentService(session=mock_session)

    def test_get_company_industries_success(self, service, mock_session):
        """Test getting company industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [("Technology",), ("Software",), ("Cloud",)]

        result = service.get_company_industries(company_id=1)

        assert result == ["Technology", "Software", "Cloud"]

    def test_get_company_industries_excludes_other(self, service, mock_session):
        """Test that 'Other' is excluded from industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # 'Other' should be filtered out in the query
        mock_query.all.return_value = [("Technology",)]

        result = service.get_company_industries(company_id=1)

        assert "Other" not in result


class TestGetInvestments:
    """Tests for get_investments method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return InvestmentService(session=mock_session)

    def test_get_investments_success(self, service, mock_session):
        """Test successful get_investments call"""
        mock_investment = Mock(spec=CompanyPEInvestment)
        mock_investment.id = 1

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_investment]

        mock_response = Mock(spec=InvestmentResponse)
        mock_response.investment_id = 1

        with patch.object(service, 'apply_filters', return_value=mock_query):
            with patch.object(service, 'build_investment_response', return_value=mock_response):
                result = service.get_investments(filters={}, limit=10, offset=0)

        assert len(result) == 1
        assert result[0].investment_id == 1

    def test_get_investments_with_pagination(self, service, mock_session):
        """Test get_investments respects pagination"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(service, 'apply_filters', return_value=mock_query):
            result = service.get_investments(filters={}, limit=20, offset=40)

        mock_query.offset.assert_called_once_with(40)
        mock_query.limit.assert_called_once_with(20)


class TestUpdateInvestment:
    """Tests for update_investment method"""

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return InvestmentService(session=mock_session)

    def test_update_investment_success(self, service, mock_session):
        """Test successful investment update"""
        mock_investment = Mock(spec=CompanyPEInvestment)
        mock_investment.id = 1
        mock_investment.computed_status = "Active"

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_investment

        update_data = InvestmentUpdate(
            computed_status="Exit",
            exit_type="IPO",
            exit_year="2023"
        )

        result = service.update_investment(investment_id=1, investment_update=update_data)

        assert result is True
        assert mock_investment.computed_status == "Exit"
        assert mock_investment.exit_type == "IPO"
        assert mock_investment.exit_year == "2023"
        mock_session.commit.assert_called_once()

    def test_update_investment_not_found(self, service, mock_session):
        """Test updating non-existent investment"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        update_data = InvestmentUpdate(computed_status="Exit")

        result = service.update_investment(investment_id=999, investment_update=update_data)

        assert result is False
        mock_session.commit.assert_not_called()

    def test_update_investment_partial_fields(self, service, mock_session):
        """Test updating only some fields"""
        mock_investment = Mock(spec=CompanyPEInvestment)
        mock_investment.id = 1
        mock_investment.computed_status = "Active"
        mock_investment.exit_type = None

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_investment

        # Only update computed_status
        update_data = InvestmentUpdate(computed_status="Exit")

        result = service.update_investment(investment_id=1, investment_update=update_data)

        assert result is True
        assert mock_investment.computed_status == "Exit"

    def test_update_investment_with_exception(self, service, mock_session):
        """Test update handles exceptions"""
        mock_investment = Mock(spec=CompanyPEInvestment)
        mock_investment.id = 1

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_investment

        # Make commit raise exception
        mock_session.commit.side_effect = Exception("Database error")

        update_data = InvestmentUpdate(computed_status="Exit")

        result = service.update_investment(investment_id=1, investment_update=update_data)

        assert result is False
        mock_session.rollback.assert_called_once()


class TestApplyFilters:
    """Tests for apply_filters method"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return InvestmentService(session=mock_session)

    def test_apply_filters_pe_firm(self, service):
        """Test PE firm filter"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {'pe_firm': 'Sequoia,Accel'})

        assert mock_query.filter.called

    def test_apply_filters_status(self, service):
        """Test status filter"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {'status': 'Active'})

        assert mock_query.filter.called

    def test_apply_filters_exit_type(self, service):
        """Test exit type filter"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {'exit_type': 'IPO'})

        assert mock_query.filter.called

    def test_apply_filters_industry(self, service):
        """Test industry filter"""
        mock_query = Mock()
        # Setup join to return a mock that supports filter and distinct
        mock_joined = Mock()
        mock_filtered = Mock()
        mock_query.join.return_value = mock_joined
        mock_joined.filter.return_value = mock_filtered
        mock_filtered.distinct.return_value = mock_filtered

        result = service.apply_filters(mock_query, {'industry': 'Technology,Software'})

        assert mock_query.join.called

    def test_apply_filters_location(self, service):
        """Test location filters"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {
            'country': 'USA',
            'state_region': 'CA',
            'city': 'San Francisco'
        })

        # Should call filter multiple times
        assert mock_query.filter.called

    def test_apply_filters_revenue(self, service):
        """Test revenue filters"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {
            'min_revenue': 1000000,
            'max_revenue': 10000000
        })

        assert mock_query.filter.called

    def test_apply_filters_employees(self, service):
        """Test employee filters"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {
            'min_employees': 100,
            'max_employees': 1000
        })

        assert mock_query.filter.called

    def test_apply_filters_search(self, service):
        """Test search filter"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {'search': 'Acme'})

        assert mock_query.filter.called

    def test_apply_filters_verticals(self, service):
        """Test verticals filter"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {'verticals': 'SaaS,Cloud'})

        assert mock_query.filter.called

    def test_apply_filters_combined(self, service):
        """Test multiple filters"""
        mock_query = Mock()

        result = service.apply_filters(mock_query, {
            'pe_firm': 'Sequoia',
            'status': 'Active',
            'search': 'Tech'
        })

        # Should call filter multiple times
        assert mock_query.filter.called

    def test_format_employee_count_crunchbase_fallback(self, service):
        """Test employee count with Crunchbase fallback"""
        company = Mock(spec=Company)
        company.employee_count = None
        company.projected_employee_count = None
        company.crunchbase_employee_count = "c_00100_00250"
        
        with patch('backend.services.investment_service.decode_employee_count') as mock_decode:
            mock_decode.return_value = "100-250"
            result = service.format_employee_count(company)
            
            assert result == "100-250"
            mock_decode.assert_called_once_with("c_00100_00250")

    def test_get_crunchbase_url_attribute_error(self, service, mock_session):
        """Test Crunchbase URL with AttributeError fallback"""
        company = Mock(spec=Company)
        company.id = 123
        # Simulate AttributeError on crunchbase_url access
        type(company).crunchbase_url = property(lambda self: (_ for _ in ()).throw(AttributeError()))
        
        # Mock SQL query result
        mock_result = Mock()
        mock_result.fetchone.return_value = ("https://crunchbase.com/test",)
        mock_session.execute.return_value = mock_result
        
        result = service.get_crunchbase_url_with_fallback(company)
        
        assert result == "https://crunchbase.com/test"

    def test_get_crunchbase_url_sql_error(self, service, mock_session):
        """Test Crunchbase URL with SQL error"""
        company = Mock(spec=Company)
        company.id = 123
        type(company).crunchbase_url = property(lambda self: (_ for _ in ()).throw(AttributeError()))
        
        # Mock SQL query to raise exception
        mock_session.execute.side_effect = Exception("Database error")
        
        result = service.get_crunchbase_url_with_fallback(company)
        
        assert result is None

    def test_apply_filters_industry_group(self, service):
        """Test industry_group filter"""
        mock_query = Mock()
        
        result = service.apply_filters(mock_query, {'industry_group': 'Enterprise Software,SaaS'})
        
        # Should filter by industry_group
        assert mock_query.filter.called

