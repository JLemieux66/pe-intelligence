"""
Tests for StatsService
Tests statistics calculation and aggregation
"""
import pytest
from backend.services.stats_service import StatsService
from unittest.mock import Mock


class TestStatsService:
    """Test suite for StatsService"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance"""
        return StatsService(session=mock_session)

    def test_get_stats_structure(self, service, mock_session):
        """Test that get_stats returns correct structure"""
        # Mock the query results
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query

        # Mock scalar for enrichment rate
        mock_session.query.return_value.filter.return_value.count.side_effect = [100, 80]

        stats = service.get_stats()

        # Verify structure
        assert "total_companies" in stats
        assert "total_investments" in stats
        assert "total_pe_firms" in stats
        assert "active_investments" in stats
        assert "exited_investments" in stats
        assert "enrichment_rate" in stats

    def test_enrichment_rate_calculation(self, service, mock_session):
        """Test enrichment rate calculation"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query

        # 80 out of 100 enriched
        mock_session.query.return_value.filter.return_value.count.side_effect = [100, 80, 0, 0, 0]

        stats = service.get_stats()

        assert stats["enrichment_rate"] == 80.0

    def test_enrichment_rate_zero_companies(self, service, mock_session):
        """Test enrichment rate with no companies"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query

        stats = service.get_stats()

        assert stats["enrichment_rate"] == 0.0


class TestStatsServiceIntegration:
    """Integration tests with real database"""

    @pytest.fixture
    def db_service(self, db_session):
        """Create service with real database"""
        return StatsService(session=db_session)

    def test_get_stats_returns_valid_data(self, db_service):
        """Test that get_stats returns valid data types"""
        stats = db_service.get_stats()

        assert isinstance(stats["total_companies"], int)
        assert isinstance(stats["total_investments"], int)
        assert isinstance(stats["total_pe_firms"], int)
        assert isinstance(stats["active_investments"], int)
        assert isinstance(stats["exited_investments"], int)
        assert isinstance(stats["enrichment_rate"], (int, float))

    def test_stats_non_negative(self, db_service):
        """Test that all stats are non-negative"""
        stats = db_service.get_stats()

        assert stats["total_companies"] >= 0
        assert stats["total_investments"] >= 0
        assert stats["total_pe_firms"] >= 0
        assert stats["active_investments"] >= 0
        assert stats["exited_investments"] >= 0
        assert stats["enrichment_rate"] >= 0
        assert stats["enrichment_rate"] <= 100


@pytest.fixture
def db_session():
    """Database session fixture"""
    from src.models.database_models_v2 import get_session
    session = get_session()
    yield session
    session.close()
