"""
Complete tests for Companies API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from backend.main import app
from backend.schemas.responses import CompanyResponse
from backend.schemas.requests import CompanyUpdate


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def mock_get_session():
    """Mock database session"""
    with patch('backend.api.companies.get_session') as mock:
        yield mock


@pytest.fixture
def mock_company_service():
    """Mock CompanyService"""
    with patch('backend.api.companies.CompanyService') as MockService:
        mock_service = MagicMock()
        MockService.return_value.__enter__.return_value = mock_service
        MockService.return_value.__exit__.return_value = None
        yield mock_service


class TestGetCompanies:
    """Test GET /api/companies endpoint"""

    def test_get_companies_no_filters(self, client, mock_get_session, mock_company_service):
        """Test getting companies without filters"""
        mock_company_service.get_companies.return_value = ([], 0)

        response = client.get("/api/companies")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.headers["X-Total-Count"] == "0"
        mock_company_service.get_companies.assert_called_once()

    def test_get_companies_with_search(self, client, mock_get_session, mock_company_service):
        """Test getting companies with search filter"""
        mock_companies = [
            {"id": 1, "name": "Test Company", "country": "US"}
        ]
        mock_company_service.get_companies.return_value = (mock_companies, 1)

        response = client.get("/api/companies?search=Test")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.headers["X-Total-Count"] == "1"

        # Verify search filter was passed
        call_args = mock_company_service.get_companies.call_args[0][0]
        assert call_args['search'] == 'Test'

    def test_get_companies_with_pe_firm_filter(self, client, mock_get_session, mock_company_service):
        """Test filtering by PE firm"""
        mock_company_service.get_companies.return_value = ([], 0)

        response = client.get("/api/companies?pe_firm=Sequoia")

        assert response.status_code == 200
        call_args = mock_company_service.get_companies.call_args[0][0]
        assert call_args['pe_firm'] == 'Sequoia'

    def test_get_companies_with_multiple_filters(self, client, mock_get_session, mock_company_service):
        """Test with multiple filters"""
        mock_company_service.get_companies.return_value = ([], 5)

        response = client.get(
            "/api/companies?country=United%20States&industry=Software&min_revenue=10&is_public=true"
        )

        assert response.status_code == 200
        call_args = mock_company_service.get_companies.call_args[0][0]
        assert call_args['country'] == 'United States'
        assert call_args['industry'] == 'Software'
        assert call_args['min_revenue'] == 10.0
        assert call_args['is_public'] is True

    def test_get_companies_with_pagination(self, client, mock_get_session, mock_company_service):
        """Test pagination parameters"""
        mock_company_service.get_companies.return_value = ([], 100)

        response = client.get("/api/companies?limit=50&offset=20")

        assert response.status_code == 200
        # Verify pagination was passed to service
        _, limit, offset = mock_company_service.get_companies.call_args[0]
        assert limit == 50
        assert offset == 20

    def test_get_companies_with_revenue_range(self, client, mock_get_session, mock_company_service):
        """Test revenue range filters"""
        mock_company_service.get_companies.return_value = ([], 10)

        response = client.get("/api/companies?min_revenue=5&max_revenue=100")

        assert response.status_code == 200
        call_args = mock_company_service.get_companies.call_args[0][0]
        assert call_args['min_revenue'] == 5.0
        assert call_args['max_revenue'] == 100.0

    def test_get_companies_with_employee_range(self, client, mock_get_session, mock_company_service):
        """Test employee count filters"""
        mock_company_service.get_companies.return_value = ([], 10)

        response = client.get("/api/companies?min_employees=50&max_employees=500")

        assert response.status_code == 200
        call_args = mock_company_service.get_companies.call_args[0][0]
        assert call_args['min_employees'] == 50
        assert call_args['max_employees'] == 500


class TestGetCompanyById:
    """Test GET /api/companies/{company_id} endpoint"""

    def test_get_company_success(self, client, mock_get_session, mock_company_service):
        """Test getting a company by ID successfully"""
        mock_company = {"id": 1, "name": "Test Company", "country": "US"}
        mock_company_service.get_company_by_id.return_value = mock_company

        response = client.get("/api/companies/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Company"
        mock_company_service.get_company_by_id.assert_called_once_with(1)

    def test_get_company_not_found(self, client, mock_get_session, mock_company_service):
        """Test getting non-existent company"""
        mock_company_service.get_company_by_id.return_value = None

        response = client.get("/api/companies/999")

        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]


class TestUpdateCompany:
    """Test PUT /api/companies/{company_id} endpoint"""

    @patch('backend.api.companies.verify_admin_token')
    def test_update_company_success(self, mock_auth, client, mock_get_session, mock_company_service):
        """Test successful company update"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_company_service.update_company.return_value = True

        response = client.put(
            "/api/companies/1",
            json={"name": "Updated Company"}
        )

        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]
        mock_company_service.update_company.assert_called_once()

    @patch('backend.api.companies.verify_admin_token')
    def test_update_company_not_found(self, mock_auth, client, mock_get_session, mock_company_service):
        """Test updating non-existent company"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_company_service.update_company.return_value = False

        response = client.put(
            "/api/companies/999",
            json={"name": "Updated Company"}
        )

        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]


class TestDeleteCompany:
    """Test DELETE /api/companies/{company_id} endpoint"""

    @patch('backend.api.companies.verify_admin_token')
    def test_delete_company_success(self, mock_auth, client, mock_get_session, mock_company_service):
        """Test successful company deletion"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_company_service.delete_company.return_value = True

        response = client.delete("/api/companies/1")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        mock_company_service.delete_company.assert_called_once_with(1)

    @patch('backend.api.companies.verify_admin_token')
    def test_delete_company_not_found(self, mock_auth, client, mock_get_session, mock_company_service):
        """Test deleting non-existent company"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_company_service.delete_company.return_value = False

        response = client.delete("/api/companies/999")

        assert response.status_code == 404
        assert "Company not found" in response.json()["detail"]
