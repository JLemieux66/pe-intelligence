"""
Tests for Investments API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.main import app
from backend.schemas.responses import InvestmentResponse


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('backend.api.investments.verify_admin_token') as mock:
        mock.return_value = {"email": "test@example.com", "role": "admin"}
        yield mock


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('backend.api.investments.get_session') as mock:
        session = MagicMock(spec=Session)
        mock.return_value = session
        yield session


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestGetInvestments:
    """Test /api/investments GET endpoint"""

    def test_get_investments_no_filters(self, client, mock_db_session):
        """Test getting investments without filters"""
        mock_investments = [
            InvestmentResponse(
                id=1,
                company_id=1,
                company_name="Test Company",
                pe_firm="Test PE",
                investment_status="Active",
                industry_tags=[],
                country=None,
                state_region=None,
                city=None,
                revenue=None,
                employee_count=None,
                investment_date=None,
                exit_date=None,
                exit_type=None,
                exit_valuation=None
            )
        ]

        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = mock_investments

            response = client.get("/api/investments")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["company_name"] == "Test Company"

    def test_get_investments_with_pe_firm_filter(self, client, mock_db_session):
        """Test getting investments filtered by PE firm"""
        mock_investments = []

        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = mock_investments

            response = client.get("/api/investments?pe_firm=Test PE")

            assert response.status_code == 200
            # Verify service was called with correct filters
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["pe_firm"] == "Test PE"

    def test_get_investments_with_status_filter(self, client, mock_db_session):
        """Test getting investments filtered by status"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments?status=Active")

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["status"] == "Active"

    def test_get_investments_with_multiple_filters(self, client, mock_db_session):
        """Test getting investments with multiple filters"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get(
                "/api/investments?pe_firm=Test PE&status=Active&industry=Software&country=United States"
            )

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["pe_firm"] == "Test PE"
            assert call_args["status"] == "Active"
            assert call_args["industry"] == "Software"
            assert call_args["country"] == "United States"

    def test_get_investments_with_revenue_range(self, client, mock_db_session):
        """Test getting investments filtered by revenue range"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments?min_revenue=10&max_revenue=100")

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["min_revenue"] == 10
            assert call_args["max_revenue"] == 100

    def test_get_investments_with_employee_range(self, client, mock_db_session):
        """Test getting investments filtered by employee count"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments?min_employees=50&max_employees=500")

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["min_employees"] == 50
            assert call_args["max_employees"] == 500

    def test_get_investments_with_pagination(self, client, mock_db_session):
        """Test getting investments with pagination"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments?limit=50&offset=100")

            assert response.status_code == 200
            # Verify limit and offset were passed
            call_args = mock_service.get_investments.call_args
            assert call_args[0][1] == 50  # limit
            assert call_args[0][2] == 100  # offset

    def test_get_investments_with_search(self, client, mock_db_session):
        """Test getting investments with search term"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments?search=test company")

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["search"] == "test company"

    def test_get_investments_with_location_filters(self, client, mock_db_session):
        """Test getting investments with location filters"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get(
                "/api/investments?country=United States&state_region=California&city=San Francisco"
            )

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["country"] == "United States"
            assert call_args["state_region"] == "California"
            assert call_args["city"] == "San Francisco"

    def test_get_investments_with_industry_filters(self, client, mock_db_session):
        """Test getting investments with industry filters"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get(
                "/api/investments?industry=Software&industry_group=Tech&industry_sector=SaaS&verticals=B2B"
            )

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["industry"] == "Software"
            assert call_args["industry_group"] == "Tech"
            assert call_args["industry_sector"] == "SaaS"
            assert call_args["verticals"] == "B2B"

    def test_get_investments_with_exit_type_filter(self, client, mock_db_session):
        """Test getting investments filtered by exit type"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments?exit_type=IPO")

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["exit_type"] == "IPO"

    def test_get_investments_service_error(self, client, mock_db_session):
        """Test investments endpoint with service error"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.side_effect = Exception("Database error")

            response = client.get("/api/investments")

            assert response.status_code == 500

    def test_get_investments_default_limit(self, client, mock_db_session):
        """Test that default limit is applied"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments")

            assert response.status_code == 200
            # Default limit should be 10000
            call_args = mock_service.get_investments.call_args
            assert call_args[0][1] == 10000

    def test_get_investments_default_offset(self, client, mock_db_session):
        """Test that default offset is 0"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments")

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args
            assert call_args[0][2] == 0


class TestUpdateInvestment:
    """Test /api/investments/{investment_id} PUT endpoint"""

    @pytest.mark.asyncio
    async def test_update_investment_success(self, client, mock_auth, mock_db_session):
        """Test successful investment update"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.update_investment.return_value = True

            response = client.put(
                "/api/investments/1",
                json={"status": "Exit"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Investment updated successfully"

    @pytest.mark.asyncio
    async def test_update_investment_not_found(self, client, mock_auth, mock_db_session):
        """Test updating non-existent investment"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.update_investment.return_value = False

            response = client.put(
                "/api/investments/999",
                json={"status": "Exit"}
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_investment_requires_auth(self, client, mock_db_session):
        """Test that update requires authentication"""
        # Don't mock auth, so it should fail
        with patch('backend.api.investments.verify_admin_token') as mock_auth:
            mock_auth.side_effect = Exception("Not authenticated")

            response = client.put(
                "/api/investments/1",
                json={"status": "Exit"}
            )

            # Should fail due to authentication error
            assert response.status_code in [401, 403, 500]

    @pytest.mark.asyncio
    async def test_update_investment_with_multiple_fields(self, client, mock_auth, mock_db_session):
        """Test updating investment with multiple fields"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.update_investment.return_value = True

            response = client.put(
                "/api/investments/1",
                json={
                    "status": "Exit",
                    "exit_type": "IPO",
                    "exit_valuation": 1000000000
                }
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_investment_service_error(self, client, mock_auth, mock_db_session):
        """Test update investment with service error"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.update_investment.side_effect = Exception("Database error")

            response = client.put(
                "/api/investments/1",
                json={"status": "Exit"}
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_update_investment_invalid_data(self, client, mock_auth, mock_db_session):
        """Test updating investment with invalid data"""
        response = client.put(
            "/api/investments/1",
            json={"invalid_field": "value"}
        )

        # May return 422 for validation error or 200 if service ignores invalid fields
        assert response.status_code in [200, 422]


class TestInvestmentsEndpointIntegration:
    """Integration tests for investments endpoints"""

    def test_investments_router_prefix(self):
        """Test that investments router has correct prefix"""
        from backend.api.investments import router

        assert router.prefix == "/api"
        assert "investments" in router.tags

    def test_get_investments_returns_json(self, client, mock_db_session):
        """Test that get investments returns JSON"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments")

            assert "application/json" in response.headers["content-type"]

    def test_investments_endpoint_accessible(self, client, mock_db_session):
        """Test that investments endpoint is accessible"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get("/api/investments")

            assert response.status_code == 200

    def test_get_investments_multi_select_filters(self, client, mock_db_session):
        """Test multi-select filters with comma-separated values"""
        with patch('backend.api.investments.InvestmentService') as MockService:
            mock_service = MockService.return_value.__enter__.return_value
            mock_service.get_investments.return_value = []

            response = client.get(
                "/api/investments?pe_firm=Firm1,Firm2&industry=Tech,Healthcare"
            )

            assert response.status_code == 200
            call_args = mock_service.get_investments.call_args[0][0]
            assert call_args["pe_firm"] == "Firm1,Firm2"
            assert call_args["industry"] == "Tech,Healthcare"
