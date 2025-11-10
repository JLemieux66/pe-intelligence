"""
Comprehensive tests for MetadataService
Tests all metadata retrieval and parsing logic
"""
import pytest
from unittest.mock import Mock, patch
from backend.services.metadata_service import MetadataService


class TestMetadataService:
    """Unit tests for MetadataService"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return MetadataService(session=mock_session)

    def test_get_locations_all_fields(self, service, mock_session):
        """Test getting locations with all fields populated"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        # Mock returns for countries, states, cities
        mock_query.all.side_effect = [
            [("USA",), ("Canada",), ("UK",)],  # countries
            [("CA",), ("NY",), ("TX",)],  # states
            [("San Francisco",), ("New York",), ("London",)]  # cities
        ]

        result = service.get_locations()

        assert result.countries == ["USA", "Canada", "UK"]
        assert result.states == ["CA", "NY", "TX"]
        assert result.cities == ["San Francisco", "New York", "London"]

    def test_get_locations_empty(self, service, mock_session):
        """Test getting locations when database is empty"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.side_effect = [[], [], []]

        result = service.get_locations()

        assert result.countries == []
        assert result.states == []
        assert result.cities == []

    def test_get_locations_filters_none_values(self, service, mock_session):
        """Test that None values are filtered out"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        # Include some None values and empty strings
        mock_query.all.side_effect = [
            [("USA",), (None,), ("",), ("Canada",)],
            [("CA",), (None,)],
            [("SF",), ("",), (None,)]
        ]

        result = service.get_locations()

        # Should exclude None and empty strings
        assert "USA" in result.countries
        assert "Canada" in result.countries
        assert None not in result.countries
        assert "" not in result.countries

    def test_get_pitchbook_metadata_all_fields(self, service, mock_session):
        """Test getting PitchBook metadata with all fields"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("IT",), ("Healthcare",)],  # industry_groups
            [("Software",), ("Biotech",)],  # industry_sectors
            [("SaaS, Cloud",), ("AI, ML",)],  # verticals (comma-separated)
            [("San Francisco, CA",), ("Boston, MA",)],  # hq_locations
            [("United States",), ("United Kingdom",)]  # hq_countries
        ]

        result = service.get_pitchbook_metadata()

        assert "IT" in result.industry_groups
        assert "Healthcare" in result.industry_groups
        assert "Software" in result.industry_sectors
        assert "Biotech" in result.industry_sectors
        assert "SaaS" in result.verticals
        assert "Cloud" in result.verticals
        assert "AI" in result.verticals
        assert "ML" in result.verticals
        assert "San Francisco, CA" in result.hq_locations
        assert "United States" in result.hq_countries

    def test_get_pitchbook_metadata_parses_comma_separated_verticals(self, service, mock_session):
        """Test that comma-separated verticals are properly parsed"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("IT",)],  # industry_groups
            [("Software",)],  # industry_sectors
            [("SaaS, Cloud, AI",), ("ML, Analytics",)],  # verticals with multiple values
            [("San Francisco",)],  # hq_locations
            [("USA",)]  # hq_countries
        ]

        result = service.get_pitchbook_metadata()

        # All should be split and cleaned
        assert "SaaS" in result.verticals
        assert "Cloud" in result.verticals
        assert "AI" in result.verticals
        assert "ML" in result.verticals
        assert "Analytics" in result.verticals
        # Should be sorted
        assert result.verticals == sorted(result.verticals)

    def test_get_pitchbook_metadata_handles_empty_verticals(self, service, mock_session):
        """Test handling of empty/None verticals"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("IT",)],
            [("Software",)],
            [(None,), ("",), ("  ",)],  # Empty verticals
            [("SF",)],
            [("USA",)]
        ]

        result = service.get_pitchbook_metadata()

        # Should handle empty values gracefully
        assert result.verticals == []

    def test_get_pitchbook_metadata_deduplicates_verticals(self, service, mock_session):
        """Test that duplicate verticals are removed"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("IT",)],
            [("Software",)],
            [("SaaS, Cloud",), ("SaaS, AI",), ("Cloud",)],  # Duplicates
            [("SF",)],
            [("USA",)]
        ]

        result = service.get_pitchbook_metadata()

        # Should deduplicate
        assert result.verticals.count("SaaS") == 1
        assert result.verticals.count("Cloud") == 1

    def test_get_industries_all_fields(self, service, mock_session):
        """Test getting industries with all fields"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("Technology",), ("Healthcare",), ("Finance",)],  # industries
            [("Tech",), ("Health",), ("Fin",)]  # categories
        ]

        result = service.get_industries()

        assert "Technology" in result.industries
        assert "Healthcare" in result.industries
        assert "Finance" in result.industries
        assert "Tech" in result.categories

    def test_get_industries_excludes_other(self, service, mock_session):
        """Test that 'Other' is excluded from industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("Technology",), ("Software",)],  # 'Other' already filtered by query
            [("Tech",)]
        ]

        result = service.get_industries()

        # Verify filter was called with proper conditions
        filter_calls = mock_query.filter.call_args_list
        # Should have filter for tag_category == 'industry' and tag_value != 'Other'
        assert len(filter_calls) >= 2

    def test_get_industries_empty(self, service, mock_session):
        """Test getting industries when none exist"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.side_effect = [[], []]

        result = service.get_industries()

        assert result.industries == []
        assert result.categories == []

    def test_get_industries_filters_none_values(self, service, mock_session):
        """Test that None values are filtered in industries"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("Tech",), (None,), ("",), ("Software",)],
            [("Category1",), (None,)]
        ]

        result = service.get_industries()

        assert "Tech" in result.industries
        assert "Software" in result.industries
        assert None not in result.industries
        assert "" not in result.industries

    def test_service_uses_base_service_session(self, service, mock_session):
        """Test that service properly uses base service session"""
        assert service.session == mock_session

    def test_all_queries_order_results(self, service, mock_session):
        """Test that all metadata queries order results"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        # Call each method
        service.get_locations()
        service.get_pitchbook_metadata()
        service.get_industries()

        # Verify order_by was called multiple times
        assert mock_query.order_by.call_count >= 10  # Multiple fields per method

    def test_get_locations_sorted_alphabetically(self, service, mock_session):
        """Test that location results are sorted"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        # Return unsorted data
        mock_query.all.side_effect = [
            [("Zambia",), ("USA",), ("Canada",)],
            [("WY",), ("CA",), ("NY",)],
            [("Zurich",), ("Austin",), ("Boston",)]
        ]

        result = service.get_locations()

        # order_by should have been called to sort
        assert mock_query.order_by.call_count == 3

    def test_get_pitchbook_metadata_verticals_trimmed(self, service, mock_session):
        """Test that verticals are trimmed of whitespace"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_query.all.side_effect = [
            [("IT",)],
            [("Software",)],
            [("  SaaS  , Cloud,  AI  ",)],  # Extra whitespace
            [("SF",)],
            [("USA",)]
        ]

        result = service.get_pitchbook_metadata()

        # Should be properly trimmed
        assert "SaaS" in result.verticals
        assert "  SaaS  " not in result.verticals
        assert "Cloud" in result.verticals
        assert "AI" in result.verticals
