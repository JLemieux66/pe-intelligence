"""
Tests for Metadata API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.main import app
from backend.schemas.responses import LocationsResponse, PitchBookMetadataResponse, IndustriesResponse


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('backend.api.metadata.get_session') as mock:
        session = MagicMock(spec=Session)
        mock.return_value = session
        yield session


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestGetLocations:
    """Test /api/locations GET endpoint"""

    def test_get_locations_success(self, client, mock_db_session):
        """Test successful locations retrieval"""
        mock_response = LocationsResponse(
            countries=["United States", "Canada"],
            states=["California", "Texas"],
            cities=["San Francisco", "Austin"]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_locations.return_value = mock_response

            response = client.get("/api/locations")

            assert response.status_code == 200
            data = response.json()
            assert "countries" in data
            assert "states" in data
            assert "cities" in data
            assert len(data["countries"]) == 2
            assert "United States" in data["countries"]

    def test_get_locations_empty(self, client, mock_db_session):
        """Test locations retrieval with empty data"""
        mock_response = LocationsResponse(
            countries=[],
            states=[],
            cities=[]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_locations.return_value = mock_response

            response = client.get("/api/locations")

            assert response.status_code == 200
            data = response.json()
            assert data["countries"] == []
            assert data["states"] == []
            assert data["cities"] == []

    def test_get_locations_service_error(self, client, mock_db_session):
        """Test locations endpoint with service error"""
        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_locations.side_effect = Exception("Database error")

            response = client.get("/api/locations")

            assert response.status_code == 500

    def test_get_locations_uses_session(self, client, mock_db_session):
        """Test that locations endpoint uses database session"""
        mock_response = LocationsResponse(countries=[], states=[], cities=[])

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_locations.return_value = mock_response

            response = client.get("/api/locations")

            # Verify MetadataService was called with session
            MockService.assert_called_once()


class TestGetPitchBookMetadata:
    """Test /api/pitchbook-metadata GET endpoint"""

    def test_get_pitchbook_metadata_success(self, client, mock_db_session):
        """Test successful PitchBook metadata retrieval"""
        mock_response = PitchBookMetadataResponse(
            industry_groups=["Software", "Healthcare"],
            industry_sectors=["Technology", "Biotech"],
            verticals=["SaaS", "Medical Devices"],
            hq_locations=["San Francisco, CA", "Boston, MA"]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_pitchbook_metadata.return_value = mock_response

            response = client.get("/api/pitchbook-metadata")

            assert response.status_code == 200
            data = response.json()
            assert "industry_groups" in data
            assert "industry_sectors" in data
            assert "verticals" in data
            assert "hq_locations" in data
            assert len(data["industry_groups"]) == 2

    def test_get_pitchbook_metadata_empty(self, client, mock_db_session):
        """Test PitchBook metadata retrieval with empty data"""
        mock_response = PitchBookMetadataResponse(
            industry_groups=[],
            industry_sectors=[],
            verticals=[],
            hq_locations=[]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_pitchbook_metadata.return_value = mock_response

            response = client.get("/api/pitchbook-metadata")

            assert response.status_code == 200
            data = response.json()
            assert all(len(data[key]) == 0 for key in data)

    def test_get_pitchbook_metadata_service_error(self, client, mock_db_session):
        """Test PitchBook metadata endpoint with service error"""
        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_pitchbook_metadata.side_effect = Exception("Database error")

            response = client.get("/api/pitchbook-metadata")

            assert response.status_code == 500

    def test_get_pitchbook_metadata_uses_session(self, client, mock_db_session):
        """Test that PitchBook metadata endpoint uses database session"""
        mock_response = PitchBookMetadataResponse(
            industry_groups=[],
            industry_sectors=[],
            verticals=[],
            hq_locations=[]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_pitchbook_metadata.return_value = mock_response

            response = client.get("/api/pitchbook-metadata")

            # Verify MetadataService was called
            MockService.assert_called_once()


class TestGetIndustries:
    """Test /api/industries GET endpoint"""

    def test_get_industries_success(self, client, mock_db_session):
        """Test successful industries retrieval"""
        mock_response = IndustriesResponse(
            industries=["Technology", "Healthcare", "Finance"],
            categories=["Software", "Biotech", "FinTech"]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_industries.return_value = mock_response

            response = client.get("/api/industries")

            assert response.status_code == 200
            data = response.json()
            assert "industries" in data
            assert "categories" in data
            assert len(data["industries"]) == 3
            assert "Technology" in data["industries"]

    def test_get_industries_empty(self, client, mock_db_session):
        """Test industries retrieval with empty data"""
        mock_response = IndustriesResponse(
            industries=[],
            categories=[]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_industries.return_value = mock_response

            response = client.get("/api/industries")

            assert response.status_code == 200
            data = response.json()
            assert data["industries"] == []
            assert data["categories"] == []

    def test_get_industries_service_error(self, client, mock_db_session):
        """Test industries endpoint with service error"""
        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_industries.side_effect = Exception("Database error")

            response = client.get("/api/industries")

            assert response.status_code == 500

    def test_get_industries_uses_session(self, client, mock_db_session):
        """Test that industries endpoint uses database session"""
        mock_response = IndustriesResponse(industries=[], categories=[])

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_industries.return_value = mock_response

            response = client.get("/api/industries")

            # Verify MetadataService was called
            MockService.assert_called_once()

    def test_get_industries_large_dataset(self, client, mock_db_session):
        """Test industries retrieval with large dataset"""
        mock_response = IndustriesResponse(
            industries=[f"Industry {i}" for i in range(100)],
            categories=[f"Category {i}" for i in range(50)]
        )

        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_industries.return_value = mock_response

            response = client.get("/api/industries")

            assert response.status_code == 200
            data = response.json()
            assert len(data["industries"]) == 100
            assert len(data["categories"]) == 50


class TestMetadataEndpointsIntegration:
    """Integration tests for metadata endpoints"""

    def test_all_metadata_endpoints_accessible(self, client, mock_db_session):
        """Test that all metadata endpoints are accessible"""
        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_locations.return_value = LocationsResponse(
                countries=[], states=[], cities=[]
            )
            mock_service.get_pitchbook_metadata.return_value = PitchBookMetadataResponse(
                industry_groups=[], industry_sectors=[], verticals=[], hq_locations=[]
            )
            mock_service.get_industries.return_value = IndustriesResponse(
                industries=[], categories=[]
            )

            # Test all endpoints
            locations_response = client.get("/api/locations")
            pitchbook_response = client.get("/api/pitchbook-metadata")
            industries_response = client.get("/api/industries")

            assert locations_response.status_code == 200
            assert pitchbook_response.status_code == 200
            assert industries_response.status_code == 200

    def test_metadata_endpoints_return_json(self, client, mock_db_session):
        """Test that all metadata endpoints return JSON"""
        with patch('backend.api.metadata.MetadataService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_locations.return_value = LocationsResponse(
                countries=[], states=[], cities=[]
            )

            response = client.get("/api/locations")

            assert "application/json" in response.headers["content-type"]

    def test_metadata_router_prefix(self):
        """Test that metadata router has correct prefix"""
        from backend.api.metadata import router

        assert router.prefix == "/api"
        assert "metadata" in router.tags
