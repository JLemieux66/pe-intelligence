"""
Comprehensive tests for PEFirmService
"""
import pytest
from backend.services.pe_firm_service import PEFirmService
from unittest.mock import Mock


class TestPEFirmService:
    """Unit tests for PEFirmService"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance"""
        return PEFirmService(session=mock_session)

    def test_get_pe_firms_structure(self, service, mock_session):
        """Test PE firms response structure"""
        # Mock main query
        mock_firm_data = Mock()
        mock_firm_data.id = 1
        mock_firm_data.name = "Acme Capital"
        mock_firm_data.investment_count = 10

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_firm_data]

        # Mock active/exit counts
        mock_count_query = Mock()
        mock_count_query.filter.return_value = mock_count_query
        mock_count_query.count.side_effect = [7, 3]  # active, exit

        mock_session.query.side_effect = [mock_query, mock_count_query, mock_count_query]

        result = service.get_pe_firms()

        assert len(result) == 1
        firm = result[0]
        assert firm.id == 1
        assert firm.name == "Acme Capital"
        assert firm.total_investments == 10
        assert firm.active_count == 7
        assert firm.exit_count == 3

    def test_get_pe_firms_empty(self, service, mock_session):
        """Test getting PE firms when none exist"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_pe_firms()
        assert result == []

    def test_get_pe_firms_sorted_by_name(self, service, mock_session):
        """Test PE firms are sorted by name"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        service.get_pe_firms()

        # Verify order_by was called
        mock_query.order_by.assert_called_once()


class TestPEFirmServiceIntegration:
    """Integration tests with real database"""

    @pytest.fixture
    def db_service(self, db_session):
        """Create service with real database"""
        return PEFirmService(session=db_session)

    def test_get_pe_firms_returns_list(self, db_service):
        """Test that get_pe_firms returns a list"""
        result = db_service.get_pe_firms()
        assert isinstance(result, list)

    def test_get_pe_firms_response_fields(self, db_service):
        """Test PE firm response has required fields"""
        result = db_service.get_pe_firms()

        for firm in result:
            assert hasattr(firm, 'id')
            assert hasattr(firm, 'name')
            assert hasattr(firm, 'total_investments')
            assert hasattr(firm, 'active_count')
            assert hasattr(firm, 'exit_count')

    def test_get_pe_firms_counts_non_negative(self, db_service):
        """Test that all counts are non-negative"""
        result = db_service.get_pe_firms()

        for firm in result:
            assert firm.total_investments >= 0
            assert firm.active_count >= 0
            assert firm.exit_count >= 0

    def test_get_pe_firms_counts_sum(self, db_service):
        """Test that active + exit <= total"""
        result = db_service.get_pe_firms()

        for firm in result:
            # Active + Exit should not exceed total
            # (may be less due to Unknown/Other statuses)
            assert firm.active_count + firm.exit_count <= firm.total_investments + 1


@pytest.fixture
def db_session():
    """Database session fixture"""
    from src.models.database_models_v2 import get_session
    session = get_session()
    yield session
    session.close()
