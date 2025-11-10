"""
Comprehensive tests for CompanyService
Tests business logic, filtering, and data processing
"""
import pytest
from backend.services.company_service import CompanyService
from src.models.database_models_v2 import Company, PEFirm, CompanyPEInvestment
from unittest.mock import Mock, MagicMock


class TestCompanyService:
    """Test suite for CompanyService"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance"""
        return CompanyService(session=mock_session)

    @pytest.fixture
    def sample_company(self):
        """Create sample company for testing"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Test Company"
        company.employee_count = 1000
        company.projected_employee_count = None
        company.crunchbase_employee_count = None
        company.hq_location = "San Francisco"
        company.hq_country = "United States"
        company.city = None
        company.state_region = None
        company.country = None
        return company

    def test_get_employee_count_display_pitchbook(self, service, sample_company):
        """Test employee count display prioritizes PitchBook data"""
        sample_company.employee_count = 1234
        sample_company.projected_employee_count = 2000
        sample_company.crunchbase_employee_count = "c_01001_05000"

        result = service.get_employee_count_display(sample_company)
        assert result == "1,234", "Should prioritize PitchBook employee count"

    def test_get_employee_count_display_linkedin(self, service, sample_company):
        """Test employee count falls back to LinkedIn data"""
        sample_company.employee_count = None
        sample_company.projected_employee_count = 2500
        sample_company.crunchbase_employee_count = "c_01001_05000"

        result = service.get_employee_count_display(sample_company)
        assert result == "2,500", "Should use LinkedIn count when PitchBook unavailable"

    def test_get_employee_count_display_crunchbase(self, service, sample_company):
        """Test employee count falls back to Crunchbase range"""
        sample_company.employee_count = None
        sample_company.projected_employee_count = None
        sample_company.crunchbase_employee_count = "c_00501_01000"

        result = service.get_employee_count_display(sample_company)
        assert result == "501-1,000", "Should decode Crunchbase range"

    def test_get_employee_count_display_none(self, service, sample_company):
        """Test employee count returns None when no data"""
        sample_company.employee_count = None
        sample_company.projected_employee_count = None
        sample_company.crunchbase_employee_count = None

        result = service.get_employee_count_display(sample_company)
        assert result is None, "Should return None when no data available"

    def test_build_headquarters_pitchbook(self, service, sample_company):
        """Test headquarters uses PitchBook location"""
        result = service.build_headquarters(sample_company)
        assert result == "San Francisco, United States"

    def test_build_headquarters_fallback(self, service, sample_company):
        """Test headquarters falls back to city/state/country"""
        sample_company.hq_location = None
        sample_company.hq_country = None
        sample_company.city = "New York"
        sample_company.state_region = "NY"
        sample_company.country = "USA"

        result = service.build_headquarters(sample_company)
        assert result == "New York, NY, USA"

    def test_build_headquarters_partial(self, service, sample_company):
        """Test headquarters with partial data"""
        sample_company.hq_location = None
        sample_company.hq_country = None
        sample_company.city = "Boston"
        sample_company.state_region = None
        sample_company.country = "USA"

        result = service.build_headquarters(sample_company)
        assert result == "Boston, USA"

    def test_build_headquarters_none(self, service, sample_company):
        """Test headquarters returns None when no data"""
        sample_company.hq_location = None
        sample_company.hq_country = None
        sample_company.city = None
        sample_company.state_region = None
        sample_company.country = None

        result = service.build_headquarters(sample_company)
        assert result is None

    def test_get_company_pe_firms(self, service, mock_session):
        """Test retrieving PE firms for a company"""
        # Mock query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [("PE Firm 1",), ("PE Firm 2",)]

        result = service.get_company_pe_firms(company_id=1)

        assert result == ["PE Firm 1", "PE Firm 2"]
        mock_session.query.assert_called_once()

    def test_get_company_status_active(self, service, mock_session):
        """Test company status prioritizes Active"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [("Active",), ("Exit",)]

        result = service.get_company_status(company_id=1)
        assert result == "Active", "Should prioritize Active over Exit"

    def test_get_company_status_exit_only(self, service, mock_session):
        """Test company status returns Exit when only status"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [("Exit",)]

        result = service.get_company_status(company_id=1)
        assert result == "Exit"

    def test_revenue_range_codes(self, service):
        """Test revenue range code mappings"""
        assert service.REVENUE_RANGE_CODES["$1M - $10M"] == "r_00001000"
        assert service.REVENUE_RANGE_CODES["$10B+"] == "r_10000000"
        assert "$1M" in service.REVENUE_RANGE_CODES

    def test_employee_count_codes(self, service):
        """Test employee count code mappings"""
        assert service.EMPLOYEE_COUNT_CODES["1-10"] == "c_00001_00010"
        assert service.EMPLOYEE_COUNT_CODES["10,001+"] == "c_10001_max"


class TestCompanyServiceIntegration:
    """Integration tests for CompanyService with real database"""

    @pytest.fixture
    def db_service(self, db_session):
        """Create service with real database session"""
        return CompanyService(session=db_session)

    def test_get_companies_no_filters(self, db_service):
        """Test getting companies without filters"""
        companies, total = db_service.get_companies({}, limit=10, offset=0)

        # Should return some companies (or empty list if DB is empty)
        assert isinstance(companies, list)
        assert isinstance(total, int)
        assert total >= 0

    def test_get_companies_with_limit(self, db_service):
        """Test pagination limit"""
        companies, total = db_service.get_companies({}, limit=5, offset=0)

        assert len(companies) <= 5, "Should respect limit"

    def test_get_companies_with_offset(self, db_service):
        """Test pagination offset"""
        all_companies, total = db_service.get_companies({}, limit=100, offset=0)
        offset_companies, _ = db_service.get_companies({}, limit=100, offset=1)

        if len(all_companies) > 1:
            # If we have multiple companies, offset should skip first one
            assert all_companies[0] != offset_companies[0] if offset_companies else True

    def test_get_company_by_id_not_found(self, db_service):
        """Test getting non-existent company"""
        company = db_service.get_company_by_id(company_id=999999)
        assert company is None, "Should return None for non-existent company"

    def test_update_company_not_found(self, db_service):
        """Test updating non-existent company"""
        from backend.schemas.requests import CompanyUpdate

        update_data = CompanyUpdate(name="New Name")
        result = db_service.update_company(company_id=999999, company_update=update_data)

        assert result is False, "Should return False for non-existent company"

    def test_delete_company_not_found(self, db_service):
        """Test deleting non-existent company"""
        result = db_service.delete_company(company_id=999999)
        assert result is False, "Should return False for non-existent company"


# Shared fixtures
@pytest.fixture
def db_session():
    """Database session fixture"""
    from src.models.database_models_v2 import get_session
    session = get_session()
    yield session
    session.close()
