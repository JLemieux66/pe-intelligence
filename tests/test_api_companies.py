"""
Tests for Companies API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.main import app
from backend.schemas.responses import CompanyResponse


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('backend.api.companies.verify_admin_token') as mock:
        mock.return_value = {"email": "admin@test.com", "role": "admin"}
        yield mock


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('backend.api.companies.get_session') as mock:
        session = MagicMock(spec=Session)
        mock.return_value = session
        yield session


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestGetCompanies:
    """Test /api/companies GET endpoint"""

    def test_get_companies_no_filters(self, client, mock_db_session):
        """Test getting companies without filters"""
        mock_companies = [
            CompanyResponse(
                id=1,
                name="Test Company",
                pe_firms=["Test PE"],
                investment_status="Active",
                country=None,
                state_region=None,
                city=None,
                revenue=None,
                employee_count=None,
                industry_tags=[]
            )
        ]

        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = (mock_companies, 1)

            response = client.get("/api/companies")

            assert response.status_code == 200
            assert "X-Total-Count" in response.headers
            assert response.headers["X-Total-Count"] == "1"
            data = response.json()
            assert len(data) == 1

    def test_get_companies_with_search(self, client, mock_db_session):
        """Test getting companies with search term"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?search=test")

            assert response.status_code == 200
            # Verify service was called with search filter
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["search"] == "test"

    def test_get_companies_with_pe_firm_filter(self, client, mock_db_session):
        """Test filtering by PE firm"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?pe_firm=Test PE")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["pe_firm"] == "Test PE"

    def test_get_companies_with_status_filter(self, client, mock_db_session):
        """Test filtering by status"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?status=Active")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["status"] == "Active"

    def test_get_companies_with_industry_filter(self, client, mock_db_session):
        """Test filtering by industry"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?industry=Software")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["industry"] == "Software"

    def test_get_companies_with_location_filters(self, client, mock_db_session):
        """Test filtering by location"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get(
                "/api/companies?country=United States&state_region=California&city=San Francisco"
            )

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["country"] == "United States"
            assert call_args[0][0]["state_region"] == "California"
            assert call_args[0][0]["city"] == "San Francisco"

    def test_get_companies_with_revenue_range(self, client, mock_db_session):
        """Test filtering by revenue range"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?min_revenue=10&max_revenue=100")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["min_revenue"] == 10.0
            assert call_args[0][0]["max_revenue"] == 100.0

    def test_get_companies_with_employee_range(self, client, mock_db_session):
        """Test filtering by employee count"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?min_employees=50&max_employees=500")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["min_employees"] == 50
            assert call_args[0][0]["max_employees"] == 500

    def test_get_companies_with_pagination(self, client, mock_db_session):
        """Test pagination parameters"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?limit=50&offset=100")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][1] == 50  # limit
            assert call_args[0][2] == 100  # offset

    def test_get_companies_with_is_public_filter(self, client, mock_db_session):
        """Test filtering by public status"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies?is_public=true")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][0]["is_public"] == True

    def test_get_companies_with_multiple_filters(self, client, mock_db_session):
        """Test multiple filters combined"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get(
                "/api/companies?pe_firm=Test PE&status=Active&industry=Software&country=United States"
            )

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            filters = call_args[0][0]
            assert filters["pe_firm"] == "Test PE"
            assert filters["status"] == "Active"
            assert filters["industry"] == "Software"
            assert filters["country"] == "United States"


class TestGetCompanyById:
    """Test /api/companies/{company_id} GET endpoint"""

    def test_get_company_by_id_success(self, client, mock_db_session):
        """Test getting single company by ID"""
        mock_company = CompanyResponse(
            id=1,
            name="Test Company",
            pe_firms=["Test PE"],
            investment_status="Active",
            country=None,
            state_region=None,
            city=None,
            revenue=None,
            employee_count=None,
            industry_tags=[]
        )

        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_company_by_id.return_value = mock_company

            response = client.get("/api/companies/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "Test Company"

    def test_get_company_by_id_not_found(self, client, mock_db_session):
        """Test getting non-existent company"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_company_by_id.return_value = None

            response = client.get("/api/companies/999")

            assert response.status_code == 404
            assert "Company not found" in response.json()["detail"]


class TestUpdateCompany:
    """Test /api/companies/{company_id} PUT endpoint"""

    def test_update_company_success(self, client, mock_auth, mock_db_session):
        """Test successful company update"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.update_company.return_value = True

            response = client.put(
                "/api/companies/1",
                json={"name": "Updated Company"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Company updated successfully"

    def test_update_company_not_found(self, client, mock_auth, mock_db_session):
        """Test updating non-existent company"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.update_company.return_value = False

            response = client.put(
                "/api/companies/999",
                json={"name": "Updated Company"}
            )

            assert response.status_code == 404
            assert "Company not found" in response.json()["detail"]

    def test_update_company_requires_auth(self, client, mock_db_session):
        """Test that update requires authentication"""
        with patch('backend.api.companies.verify_admin_token') as mock_auth:
            mock_auth.side_effect = Exception("Not authenticated")

            response = client.put(
                "/api/companies/1",
                json={"name": "Updated Company"}
            )

            assert response.status_code in [401, 403, 500]


class TestDeleteCompany:
    """Test /api/companies/{company_id} DELETE endpoint"""

    def test_delete_company_success(self, client, mock_auth, mock_db_session):
        """Test successful company deletion"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.delete_company.return_value = True

            response = client.delete("/api/companies/1")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Company deleted successfully"

    def test_delete_company_not_found(self, client, mock_auth, mock_db_session):
        """Test deleting non-existent company"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.delete_company.return_value = False

            response = client.delete("/api/companies/999")

            assert response.status_code == 404
            assert "Company not found" in response.json()["detail"]

    def test_delete_company_requires_auth(self, client, mock_db_session):
        """Test that delete requires authentication"""
        with patch('backend.api.companies.verify_admin_token') as mock_auth:
            mock_auth.side_effect = Exception("Not authenticated")

            response = client.delete("/api/companies/1")

            assert response.status_code in [401, 403, 500]


class TestCompaniesEndpointIntegration:
    """Integration tests for companies endpoints"""

    def test_companies_router_configured(self):
        """Test that companies router is configured"""
        from backend.api.companies import router

        assert router.prefix == "/api"
        assert "companies" in router.tags

    def test_companies_endpoints_registered(self):
        """Test that all endpoints are registered"""
        from backend.main import app

        paths = [route.path for route in app.routes]

        assert any("/api/companies" in path for path in paths)

    def test_get_companies_default_limit(self, client, mock_db_session):
        """Test default limit is 10000"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][1] == 10000  # Default limit

    def test_get_companies_default_offset(self, client, mock_db_session):
        """Test default offset is 0"""
        with patch('backend.api.companies.CompanyService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_companies.return_value = ([], 0)

            response = client.get("/api/companies")

            assert response.status_code == 200
            call_args = mock_service.get_companies.call_args
            assert call_args[0][2] == 0  # Default offset
