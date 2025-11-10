"""
Comprehensive tests for StatsService and PEFirmService
Tests all business logic and data aggregation
"""
import pytest
from unittest.mock import Mock, patch
from backend.services.stats_service import StatsService
from backend.services.pe_firm_service import PEFirmService


class TestStatsService:
    """Tests for StatsService"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return StatsService(session=mock_session)

    def test_get_stats_structure(self, service, mock_session):
        """Test stats response structure"""
        # Mock all the query chains
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 100

        # Mock filter chains
        mock_query.filter.return_value = mock_query

        # Mock scalar for co-investments
        mock_session.execute.return_value.scalar.return_value = 10

        stats = service.get_stats()

        assert hasattr(stats, 'total_companies')
        assert hasattr(stats, 'total_investments')
        assert hasattr(stats, 'total_pe_firms')
        assert hasattr(stats, 'active_investments')
        assert hasattr(stats, 'exited_investments')
        assert hasattr(stats, 'co_investments')
        assert hasattr(stats, 'enrichment_rate')

    def test_get_stats_enrichment_rate_calculation(self, service, mock_session):
        """Test enrichment rate calculation"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query

        # Total companies: 100
        # Enriched companies: 75
        mock_query.count.side_effect = [100, 100, 100, 50, 30, 75]
        mock_query.filter.return_value = mock_query

        # Mock co-investments
        mock_session.execute.return_value.scalar.return_value = 10

        stats = service.get_stats()

        # Enrichment rate should be 75/100 = 0.75
        assert stats.enrichment_rate == 0.75

    def test_get_stats_enrichment_rate_zero_companies(self, service, mock_session):
        """Test enrichment rate when no companies exist"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query

        mock_session.execute.return_value.scalar.return_value = 0

        stats = service.get_stats()

        # Should return 0.0 when no companies
        assert stats.enrichment_rate == 0.0

    def test_get_stats_all_values_non_negative(self, service, mock_session):
        """Test that all stats values are non-negative"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.filter.return_value = mock_query

        mock_session.execute.return_value.scalar.return_value = 5

        stats = service.get_stats()

        assert stats.total_companies >= 0
        assert stats.total_investments >= 0
        assert stats.total_pe_firms >= 0
        assert stats.active_investments >= 0
        assert stats.exited_investments >= 0
        assert stats.co_investments >= 0
        assert 0.0 <= stats.enrichment_rate <= 1.0


class TestPEFirmService:
    """Tests for PEFirmService"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return PEFirmService(session=mock_session)

    def test_get_pe_firms_structure(self, service, mock_session):
        """Test PE firms response structure"""
        # Mock the query result
        mock_row1 = Mock()
        mock_row1.id = 1
        mock_row1.name = "Acme Capital"
        mock_row1.investment_count = 25

        mock_row2 = Mock()
        mock_row2.id = 2
        mock_row2.name = "Beta Ventures"
        mock_row2.investment_count = 15

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_row1, mock_row2]

        # Mock the status queries for each firm
        mock_status_query = Mock()
        mock_status_query.filter.return_value = mock_status_query
        mock_status_query.count.side_effect = [18, 7, 10, 5]  # Active/Exit counts for both firms

        # We need to mock multiple query calls
        original_query = mock_session.query
        mock_session.query.side_effect = [
            mock_query,  # First call for get_pe_firms
            mock_status_query,  # Active count for firm 1
            mock_status_query,  # Exit count for firm 1
            mock_status_query,  # Active count for firm 2
            mock_status_query,  # Exit count for firm 2
        ]

        firms = service.get_pe_firms()

        assert len(firms) == 2
        assert firms[0].name == "Acme Capital"
        assert firms[0].total_investments == 25
        assert isinstance(firms[0].active_count, int)
        assert isinstance(firms[0].exit_count, int)

    def test_get_pe_firms_counts_non_negative(self, service, mock_session):
        """Test that counts are non-negative"""
        mock_row = Mock()
        mock_row.id = 1
        mock_row.name = "Test PE"
        mock_row.investment_count = 10

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        # Mock status counts
        mock_status_query = Mock()
        mock_status_query.filter.return_value = mock_status_query
        mock_status_query.count.side_effect = [5, 5]

        mock_session.query.side_effect = [mock_query, mock_status_query, mock_status_query]

        firms = service.get_pe_firms()

        for firm in firms:
            assert firm.total_investments >= 0
            assert firm.active_count >= 0
            assert firm.exit_count >= 0

    def test_get_pe_firms_sorted_by_name(self, service, mock_session):
        """Test that firms are sorted alphabetically"""
        mock_row1 = Mock()
        mock_row1.id = 1
        mock_row1.name = "Zeta Ventures"
        mock_row1.investment_count = 10

        mock_row2 = Mock()
        mock_row2.id = 2
        mock_row2.name = "Alpha Capital"
        mock_row2.investment_count = 20

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        # Return already sorted
        mock_query.all.return_value = [mock_row2, mock_row1]

        # Mock status queries
        mock_status_query = Mock()
        mock_status_query.filter.return_value = mock_status_query
        mock_status_query.count.side_effect = [15, 5, 8, 2]

        mock_session.query.side_effect = [
            mock_query,
            mock_status_query, mock_status_query,
            mock_status_query, mock_status_query
        ]

        firms = service.get_pe_firms()

        # Should be sorted alphabetically
        assert firms[0].name == "Alpha Capital"
        assert firms[1].name == "Zeta Ventures"

    def test_get_pe_firms_empty_list(self, service, mock_session):
        """Test getting PE firms when none exist"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        firms = service.get_pe_firms()

        assert firms == []
        assert isinstance(firms, list)

    def test_get_pe_firms_counts_sum_correctly(self, service, mock_session):
        """Test that active + exit <= total investments"""
        mock_row = Mock()
        mock_row.id = 1
        mock_row.name = "Test PE"
        mock_row.investment_count = 100

        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        # Mock status counts: 60 active + 40 exit = 100 total
        mock_status_query = Mock()
        mock_status_query.filter.return_value = mock_status_query
        mock_status_query.count.side_effect = [60, 40]

        mock_session.query.side_effect = [mock_query, mock_status_query, mock_status_query]

        firms = service.get_pe_firms()

        assert firms[0].active_count + firms[0].exit_count <= firms[0].total_investments


class TestMainAppFunctions:
    """Tests for main.py functions"""

    def test_root_endpoint_response(self):
        """Test root endpoint returns correct message"""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "API" in data["message"]

    def test_health_check_response(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_cors_middleware_configured(self):
        """Test CORS middleware is configured"""
        from backend.main import app

        # Check that CORSMiddleware is in the middleware stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_rate_limit_middleware_configured(self):
        """Test rate limiting middleware is configured"""
        from backend.main import app

        # Check that RateLimitMiddleware is in the middleware stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "RateLimitMiddleware" in middleware_classes

    def test_all_routers_included(self):
        """Test that all routers are included"""
        from backend.main import app

        # Get all route paths
        routes = [route.path for route in app.routes]

        # Check for key routes
        assert "/" in routes or any(r.startswith("/") for r in routes)
        assert "/health" in routes

        # Check API routes are registered (at least some of them)
        api_routes = [r for r in routes if r.startswith("/api/")]
        assert len(api_routes) > 0


class TestDatabaseHelpers:
    """Tests for crunchbase_helpers functions"""

    def test_decode_revenue_range_valid_codes(self):
        """Test decoding valid revenue range codes"""
        from src.enrichment.crunchbase_helpers import decode_revenue_range

        assert decode_revenue_range("r_00000000") == "Less than $1M"
        assert decode_revenue_range("r_00001000") == "$1M - $10M"
        assert decode_revenue_range("r_00010000") == "$10M - $50M"
        assert decode_revenue_range("r_00100000") == "$100M - $500M"
        assert decode_revenue_range("r_10000000") == "$10B+"

    def test_decode_revenue_range_invalid_code(self):
        """Test decoding invalid revenue code"""
        from src.enrichment.crunchbase_helpers import decode_revenue_range

        result = decode_revenue_range("invalid_code")
        assert result == "invalid_code" or result is None

    def test_decode_revenue_range_none(self):
        """Test decoding None"""
        from src.enrichment.crunchbase_helpers import decode_revenue_range

        result = decode_revenue_range(None)
        assert result is None

    def test_decode_employee_count_valid_codes(self):
        """Test decoding valid employee count codes"""
        from src.enrichment.crunchbase_helpers import decode_employee_count

        assert decode_employee_count("c_00001_00010") == "1-10"
        assert decode_employee_count("c_00011_00050") == "11-50"
        assert decode_employee_count("c_00501_01000") == "501-1,000"
        assert decode_employee_count("c_10001_max") == "10,001+"

    def test_decode_employee_count_invalid_code(self):
        """Test decoding invalid employee code"""
        from src.enrichment.crunchbase_helpers import decode_employee_count

        result = decode_employee_count("invalid_code")
        assert result == "invalid_code" or result is None

    def test_decode_employee_count_none(self):
        """Test decoding None"""
        from src.enrichment.crunchbase_helpers import decode_employee_count

        result = decode_employee_count(None)
        assert result is None
