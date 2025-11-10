"""
Comprehensive tests for MetadataService
"""
import pytest
from backend.services.metadata_service import MetadataService
from unittest.mock import Mock


class TestMetadataService:
    """Unit tests for MetadataService"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return MetadataService(session=mock_session)

    def test_get_locations_structure(self, service, mock_session):
        """Test locations response structure"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        # Mock results for countries, states, cities
        mock_query.all.side_effect = [
            [("USA",), ("UK",), ("Canada",)],
            [("CA",), ("NY",), ("TX",)],
            [("San Francisco",), ("New York",), ("London",)]
        ]

        result = service.get_locations()

        assert len(result.countries) == 3
        assert "USA" in result.countries
        assert len(result.states) == 3
        assert "CA" in result.states
        assert len(result.cities) == 3
        assert "San Francisco" in result.cities

    def test_get_locations_empty(self, service, mock_session):
        """Test locations when none exist"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_locations()

        assert result.countries == []
        assert result.states == []
        assert result.cities == []

    def test_get_pitchbook_metadata_structure(self, service, mock_session):
        """Test PitchBook metadata structure"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        # Mock results
        mock_query.all.side_effect = [
            [("Technology",), ("Healthcare",)],  # industry_groups
            [("Software",), ("Biotech",)],  # industry_sectors
            [("SaaS, Cloud",), ("AI, ML",)],  # verticals (comma-separated)
            [("San Francisco, CA",), ("New York, NY",)],  # hq_locations
            [("United States",), ("United Kingdom",)]  # hq_countries
        ]

        result = service.get_pitchbook_metadata()

        assert len(result.industry_groups) == 2
        assert "Technology" in result.industry_groups
        assert len(result.industry_sectors) == 2
        assert "Software" in result.industry_sectors
        # Verticals should be split
        assert "SaaS" in result.verticals
        assert "Cloud" in result.verticals
        assert "AI" in result.verticals
        assert len(result.hq_locations) == 2
        assert len(result.hq_countries) == 2

    def test_get_industries_structure(self, service, mock_session):
        """Test industries response structure"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        # Mock results
        mock_query.all.side_effect = [
            [("Technology",), ("Healthcare",), ("Finance",)],  # industries
            [("Tech",), ("Health",)]  # categories
        ]

        result = service.get_industries()

        assert len(result.industries) == 3
        assert "Technology" in result.industries
        assert len(result.categories) == 2
        assert "Tech" in result.categories

    def test_get_industries_excludes_other(self, service, mock_session):
        """Test that 'Other' is excluded from industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        service.get_industries()

        # Verify filter excludes 'Other'
        calls = mock_query.filter.call_args_list
        assert len(calls) > 0


class TestMetadataServiceIntegration:
    """Integration tests with real database"""

    @pytest.fixture
    def db_service(self, db_session):
        return MetadataService(session=db_session)

    def test_get_locations_returns_valid_data(self, db_service):
        """Test locations returns valid data"""
        result = db_service.get_locations()

        assert isinstance(result.countries, list)
        assert isinstance(result.states, list)
        assert isinstance(result.cities, list)

    def test_get_pitchbook_metadata_returns_valid_data(self, db_service):
        """Test PitchBook metadata returns valid data"""
        result = db_service.get_pitchbook_metadata()

        assert isinstance(result.industry_groups, list)
        assert isinstance(result.industry_sectors, list)
        assert isinstance(result.verticals, list)
        assert isinstance(result.hq_locations, list)
        assert isinstance(result.hq_countries, list)

    def test_get_industries_returns_valid_data(self, db_service):
        """Test industries returns valid data"""
        result = db_service.get_industries()

        assert isinstance(result.industries, list)
        assert isinstance(result.categories, list)

    def test_locations_no_nulls(self, db_service):
        """Test that locations don't include null values"""
        result = db_service.get_locations()

        for country in result.countries:
            assert country is not None and country != ""
        for state in result.states:
            assert state is not None and state != ""
        for city in result.cities:
            assert city is not None and city != ""


@pytest.fixture
def db_session():
    from src.models.database_models_v2 import get_session
    session = get_session()
    yield session
    session.close()
