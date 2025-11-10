"""
Complete tests for Investments API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from backend.main import app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def mock_get_session():
    """Mock database session"""
    with patch('backend.api.investments.get_session') as mock:
        yield mock


@pytest.fixture
def mock_investment_service():
    """Mock InvestmentService"""
    with patch('backend.api.investments.InvestmentService') as MockService:
        mock_service = MagicMock()
        MockService.return_value.__enter__.return_value = mock_service
        MockService.return_value.__exit__.return_value = None
        yield mock_service


class TestGetInvestments:
    """Test GET /api/investments endpoint"""

    def test_get_investments_no_filters(self, client, mock_get_session, mock_investment_service):
        """Test getting investments without filters"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        mock_investment_service.get_investments.assert_called_once()

    def test_get_investments_with_pe_firm(self, client, mock_get_session, mock_investment_service):
        """Test filtering by PE firm"""
        mock_investments = [
            {"id": 1, "company_name": "Test Co", "pe_firm": "Sequoia"}
        ]
        mock_investment_service.get_investments.return_value = mock_investments

        response = client.get("/api/investments?pe_firm=Sequoia")

        assert response.status_code == 200
        assert len(response.json()) == 1

        # Verify filter was passed
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['pe_firm'] == 'Sequoia'

    def test_get_investments_with_status_filter(self, client, mock_get_session, mock_investment_service):
        """Test filtering by investment status"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?status=Active")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['status'] == 'Active'

    def test_get_investments_with_exit_type(self, client, mock_get_session, mock_investment_service):
        """Test filtering by exit type"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?exit_type=IPO")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['exit_type'] == 'IPO'

    def test_get_investments_with_industry_filters(self, client, mock_get_session, mock_investment_service):
        """Test filtering by industry"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?industry=Software&industry_sector=SaaS")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['industry'] == 'Software'
        assert call_args['industry_sector'] == 'SaaS'

    def test_get_investments_with_geo_filters(self, client, mock_get_session, mock_investment_service):
        """Test filtering by geography"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?country=United%20States&state_region=CA&city=San%20Francisco")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['country'] == 'United States'
        assert call_args['state_region'] == 'CA'
        assert call_args['city'] == 'San Francisco'

    def test_get_investments_with_revenue_filters(self, client, mock_get_session, mock_investment_service):
        """Test filtering by revenue range"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?min_revenue=10&max_revenue=100")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['min_revenue'] == 10.0
        assert call_args['max_revenue'] == 100.0

    def test_get_investments_with_employee_filters(self, client, mock_get_session, mock_investment_service):
        """Test filtering by employee count"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?min_employees=50&max_employees=500")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['min_employees'] == 50
        assert call_args['max_employees'] == 500

    def test_get_investments_with_search(self, client, mock_get_session, mock_investment_service):
        """Test search functionality"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?search=Tesla")

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['search'] == 'Tesla'

    def test_get_investments_with_pagination(self, client, mock_get_session, mock_investment_service):
        """Test pagination parameters"""
        mock_investment_service.get_investments.return_value = []

        response = client.get("/api/investments?limit=50&offset=20")

        assert response.status_code == 200
        # Verify pagination was passed to service
        _, limit, offset = mock_investment_service.get_investments.call_args[0]
        assert limit == 50
        assert offset == 20

    def test_get_investments_with_all_filters(self, client, mock_get_session, mock_investment_service):
        """Test with multiple filters combined"""
        mock_investment_service.get_investments.return_value = []

        response = client.get(
            "/api/investments?pe_firm=Sequoia&status=Active&industry=Software&"
            "country=United%20States&min_revenue=5&max_employees=200"
        )

        assert response.status_code == 200
        call_args = mock_investment_service.get_investments.call_args[0][0]
        assert call_args['pe_firm'] == 'Sequoia'
        assert call_args['status'] == 'Active'
        assert call_args['industry'] == 'Software'
        assert call_args['country'] == 'United States'
        assert call_args['min_revenue'] == 5.0
        assert call_args['max_employees'] == 200


class TestUpdateInvestment:
    """Test PUT /api/investments/{investment_id} endpoint"""

    @patch('backend.api.investments.verify_admin_token')
    def test_update_investment_success(self, mock_auth, client, mock_get_session, mock_investment_service):
        """Test successful investment update"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_investment_service.update_investment.return_value = True

        response = client.put(
            "/api/investments/1",
            json={"status": "Exit"}
        )

        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]
        mock_investment_service.update_investment.assert_called_once()

    @patch('backend.api.investments.verify_admin_token')
    def test_update_investment_not_found(self, mock_auth, client, mock_get_session, mock_investment_service):
        """Test updating non-existent investment"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_investment_service.update_investment.return_value = False

        response = client.put(
            "/api/investments/999",
            json={"status": "Exit"}
        )

        assert response.status_code == 404
        assert "Investment not found" in response.json()["detail"]

    @patch('backend.api.investments.verify_admin_token')
    def test_update_investment_with_multiple_fields(self, mock_auth, client, mock_get_session, mock_investment_service):
        """Test updating multiple investment fields"""
        mock_auth.return_value = {"email": "admin@test.com"}
        mock_investment_service.update_investment.return_value = True

        response = client.put(
            "/api/investments/1",
            json={
                "status": "Exit",
                "exit_type": "IPO",
                "exit_date": "2024-01-15"
            }
        )

        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]
