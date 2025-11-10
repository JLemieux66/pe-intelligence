"""
Comprehensive tests for InvestmentService
Tests all business logic, filtering, and data processing
"""
import pytest
from backend.services.investment_service import InvestmentService
from backend.schemas.requests import InvestmentUpdate
from src.models.database_models_v2 import Company, CompanyPEInvestment, PEFirm, CompanyTag
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Query


class TestInvestmentService:
    """Unit tests for InvestmentService"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance"""
        return InvestmentService(session=mock_session)

    @pytest.fixture
    def sample_company(self):
        """Create sample company"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Test Company"
        company.employee_count = None
        company.projected_employee_count = None
        company.crunchbase_employee_count = None
        company.hq_location = None
        company.hq_country = None
        company.city = None
        company.state_region = None
        company.country = None
        company.crunchbase_url = "https://crunchbase.com/test"
        company.website = "https://test.com"
        company.linkedin_url = "https://linkedin.com/company/test"
        company.industry_category = "Technology"
        company.revenue_range = "r_00100000"
        company.predicted_revenue = 150.0
        company.prediction_confidence = 0.85
        return company

    @pytest.fixture
    def sample_investment(self, sample_company):
        """Create sample investment"""
        investment = Mock(spec=CompanyPEInvestment)
        investment.id = 1
        investment.company_id = 1
        investment.pe_firm_id = 1
        investment.company = sample_company
        investment.pe_firm = Mock(name="Test PE Firm")
        investment.computed_status = "Active"
        investment.raw_status = "Active - Confirmed"
        investment.exit_type = None
        investment.exit_info = None
        investment.investment_year = 2020
        investment.sector_page = "Technology"
        return investment

    # Employee Count Display Tests
    def test_employee_count_pitchbook_priority(self, service, sample_company):
        """Test employee count prioritizes PitchBook data"""
        sample_company.employee_count = 1500
        sample_company.projected_employee_count = 1200
        sample_company.crunchbase_employee_count = "c_01001_05000"

        result = service.get_employee_count_display(sample_company)
        assert result == "1,500"

    def test_employee_count_linkedin_fallback(self, service, sample_company):
        """Test employee count falls back to LinkedIn"""
        sample_company.employee_count = None
        sample_company.projected_employee_count = 2500
        sample_company.crunchbase_employee_count = "c_01001_05000"

        result = service.get_employee_count_display(sample_company)
        assert result == "2,500"

    def test_employee_count_crunchbase_fallback(self, service, sample_company):
        """Test employee count falls back to Crunchbase range"""
        sample_company.employee_count = None
        sample_company.projected_employee_count = None
        sample_company.crunchbase_employee_count = "c_00501_01000"

        with patch('backend.services.investment_service.decode_employee_count', return_value="501-1,000"):
            result = service.get_employee_count_display(sample_company)
            assert result == "501-1,000"

    def test_employee_count_none_when_no_data(self, service, sample_company):
        """Test employee count returns None when no data"""
        result = service.get_employee_count_display(sample_company)
        assert result is None

    # Headquarters Building Tests
    def test_build_headquarters_pitchbook(self, service, sample_company):
        """Test headquarters uses PitchBook data"""
        sample_company.hq_location = "San Francisco, CA"
        sample_company.hq_country = "United States"

        result = service.build_headquarters(sample_company)
        assert result == "San Francisco, CA, United States"

    def test_build_headquarters_fallback_full(self, service, sample_company):
        """Test headquarters falls back to city/state/country"""
        sample_company.city = "New York"
        sample_company.state_region = "NY"
        sample_company.country = "USA"

        result = service.build_headquarters(sample_company)
        assert result == "New York, NY, USA"

    def test_build_headquarters_fallback_partial(self, service, sample_company):
        """Test headquarters with partial fallback data"""
        sample_company.city = "London"
        sample_company.country = "UK"

        result = service.build_headquarters(sample_company)
        assert result == "London, UK"

    def test_build_headquarters_none(self, service, sample_company):
        """Test headquarters returns None when no data"""
        result = service.build_headquarters(sample_company)
        assert result is None

    # Crunchbase URL Tests
    def test_crunchbase_url_direct_access(self, service, sample_company):
        """Test Crunchbase URL direct access"""
        result = service.get_crunchbase_url_with_fallback(sample_company)
        assert result == "https://crunchbase.com/test"

    def test_crunchbase_url_sql_fallback(self, service, mock_session, sample_company):
        """Test Crunchbase URL SQL fallback on AttributeError"""
        sample_company.crunchbase_url = Mock(side_effect=AttributeError)

        # Mock SQL execution
        mock_result = Mock()
        mock_result.fetchone.return_value = ("https://crunchbase.com/fallback",)
        mock_session.execute.return_value = mock_result

        result = service.get_crunchbase_url_with_fallback(sample_company)
        assert result == "https://crunchbase.com/fallback"

    def test_crunchbase_url_fallback_none(self, service, mock_session, sample_company):
        """Test Crunchbase URL fallback returns None on error"""
        sample_company.crunchbase_url = Mock(side_effect=AttributeError)
        mock_session.execute.side_effect = Exception("DB Error")

        result = service.get_crunchbase_url_with_fallback(sample_company)
        assert result is None

    # Company Industries Tests
    def test_get_company_industries(self, service, mock_session):
        """Test getting company industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [("Technology",), ("Software",), ("SaaS",)]

        result = service.get_company_industries(company_id=1)
        assert result == ["Technology", "Software", "SaaS"]

    def test_get_company_industries_excludes_other(self, service, mock_session):
        """Test that 'Other' is excluded from industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [("Technology",)]

        service.get_company_industries(company_id=1)

        # Verify filter excludes 'Other'
        calls = mock_query.filter.call_args_list
        assert any("tag_value != 'Other'" in str(call) or len(call[0]) > 2 for call in calls)

    # Investment Response Building Tests
    def test_build_investment_response(self, service, sample_investment, mock_session):
        """Test building complete investment response"""
        # Mock get_company_industries
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [("Technology",), ("SaaS",)]

        with patch('backend.services.investment_service.decode_revenue_range', return_value="$100M - $500M"):
            response = service.build_investment_response(sample_investment)

        assert response.investment_id == 1
        assert response.company_id == 1
        assert response.company_name == "Test Company"
        assert response.pe_firm_name == "Test PE Firm"
        assert response.status == "Active"
        assert response.industries == ["Technology", "SaaS"]
        assert response.revenue_range == "$100M - $500M"

    def test_build_investment_response_with_exit(self, service, sample_investment, mock_session):
        """Test building investment response with exit data"""
        sample_investment.computed_status = "Exit"
        sample_investment.exit_type = "IPO"
        sample_investment.exit_info = "Acquired by BigCo"

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        with patch('backend.services.investment_service.decode_revenue_range', return_value="$100M - $500M"):
            response = service.build_investment_response(sample_investment)

        assert response.status == "Exit"
        assert response.exit_type == "IPO"
        assert response.exit_info == "Acquired by BigCo"

    # Filter Application Tests
    def test_apply_filters_pe_firm_single(self, service):
        """Test applying single PE firm filter"""
        mock_query = Mock()
        filters = {'pe_firm': 'Acme Capital'}

        result = service.apply_filters(mock_query, filters)
        mock_query.filter.assert_called_once()

    def test_apply_filters_pe_firm_multiple(self, service):
        """Test applying multiple PE firm filter"""
        mock_query = Mock()
        filters = {'pe_firm': 'Acme Capital, Beta Ventures'}

        result = service.apply_filters(mock_query, filters)
        mock_query.filter.assert_called_once()

    def test_apply_filters_status(self, service):
        """Test applying status filter"""
        mock_query = Mock()
        filters = {'status': 'Active'}

        service.apply_filters(mock_query, filters)
        mock_query.filter.assert_called()

    def test_apply_filters_exit_type(self, service):
        """Test applying exit type filter"""
        mock_query = Mock()
        filters = {'exit_type': 'IPO'}

        service.apply_filters(mock_query, filters)
        mock_query.filter.assert_called()

    def test_apply_filters_industry(self, service):
        """Test applying industry filter"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query

        filters = {'industry': 'Technology, Software'}

        service.apply_filters(mock_query, filters)
        mock_query.join.assert_called_once()
        mock_query.distinct.assert_called_once()

    def test_apply_filters_multiple(self, service):
        """Test applying multiple filters"""
        mock_query = Mock()
        filters = {
            'pe_firm': 'Acme',
            'status': 'Active',
            'exit_type': 'IPO'
        }

        service.apply_filters(mock_query, filters)
        # Should call filter multiple times
        assert mock_query.filter.call_count >= 2

    def test_apply_filters_empty(self, service):
        """Test applying no filters"""
        mock_query = Mock()
        filters = {}

        result = service.apply_filters(mock_query, filters)
        # Query should be returned unchanged
        assert result == mock_query


class TestInvestmentServiceIntegration:
    """Integration tests with real database"""

    @pytest.fixture
    def db_service(self, db_session):
        """Create service with real database"""
        return InvestmentService(session=db_session)

    def test_get_investments_no_filters(self, db_service):
        """Test getting investments without filters"""
        investments = db_service.get_investments({}, limit=10, offset=0)

        assert isinstance(investments, list)

    def test_get_investments_with_limit(self, db_service):
        """Test pagination limit"""
        investments = db_service.get_investments({}, limit=5, offset=0)
        assert len(investments) <= 5

    def test_get_investments_with_status_filter(self, db_service):
        """Test filtering by status"""
        investments = db_service.get_investments({'status': 'Active'}, limit=10, offset=0)

        assert isinstance(investments, list)
        # If there are results, verify they match filter
        for inv in investments:
            if hasattr(inv, 'status'):
                assert 'Active' in inv.status or inv.status == 'Active'

    def test_get_investments_with_pe_firm_filter(self, db_service):
        """Test filtering by PE firm"""
        investments = db_service.get_investments({'pe_firm': 'Test'}, limit=10, offset=0)
        assert isinstance(investments, list)

    def test_update_investment_not_found(self, db_service):
        """Test updating non-existent investment"""
        update_data = InvestmentUpdate(computed_status="Exit")
        result = db_service.update_investment(investment_id=999999, investment_update=update_data)

        assert result is False


# Test fixtures
@pytest.fixture
def db_session():
    """Database session fixture"""
    from src.models.database_models_v2 import get_session
    session = get_session()
    yield session
    session.close()
