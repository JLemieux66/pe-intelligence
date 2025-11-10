"""
Tests for Similar Companies API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.main import app
from backend.schemas.requests import SimilarCompaniesRequest
from backend.schemas.responses import SimilarCompaniesResponse, CompanyResponse, SimilarCompanyMatch


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('backend.api.similar_companies.verify_admin_token') as mock:
        mock.return_value = {"email": "test@example.com", "role": "admin"}
        yield mock


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('backend.api.similar_companies.get_session') as mock:
        session = MagicMock(spec=Session)
        mock.return_value = session
        yield session


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestFindSimilarCompaniesEndpoint:
    """Test /api/similar-companies POST endpoint"""

    def test_find_similar_companies_success(self, client, mock_auth, mock_db_session):
        """Test successful similar companies request"""
        # Mock the service response
        mock_response = SimilarCompaniesResponse(
            input_companies=[],
            matches=[],
            total_candidates=0,
            returned_matches=0
        )

        with patch('backend.api.similar_companies.SimilarCompaniesService') as MockService:
            mock_service = MockService.return_value
            mock_service.find_similar_companies.return_value = mock_response

            response = client.post(
                "/api/similar-companies",
                json={
                    "company_ids": [1, 2],
                    "min_score": 0.5,
                    "limit": 10
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "input_companies" in data
            assert "matches" in data

    def test_find_similar_companies_value_error(self, client, mock_auth, mock_db_session):
        """Test endpoint with ValueError (404)"""
        with patch('backend.api.similar_companies.SimilarCompaniesService') as MockService:
            mock_service = MockService.return_value
            mock_service.find_similar_companies.side_effect = ValueError("No companies found")

            response = client.post(
                "/api/similar-companies",
                json={
                    "company_ids": [999],
                    "min_score": 0.5,
                    "limit": 10
                }
            )

            assert response.status_code == 404
            assert "No companies found" in response.json()["detail"]

    def test_find_similar_companies_server_error(self, client, mock_auth, mock_db_session):
        """Test endpoint with generic exception (500)"""
        with patch('backend.api.similar_companies.SimilarCompaniesService') as MockService:
            mock_service = MockService.return_value
            mock_service.find_similar_companies.side_effect = Exception("Database error")

            response = client.post(
                "/api/similar-companies",
                json={
                    "company_ids": [1],
                    "min_score": 0.5,
                    "limit": 10
                }
            )

            assert response.status_code == 500
            assert "Error finding similar companies" in response.json()["detail"]

    def test_find_similar_companies_with_filters(self, client, mock_auth, mock_db_session):
        """Test endpoint with filters"""
        mock_response = SimilarCompaniesResponse(
            input_companies=[],
            matches=[],
            total_candidates=0,
            returned_matches=0
        )

        with patch('backend.api.similar_companies.SimilarCompaniesService') as MockService:
            mock_service = MockService.return_value
            mock_service.find_similar_companies.return_value = mock_response

            response = client.post(
                "/api/similar-companies",
                json={
                    "company_ids": [1],
                    "min_score": 0.6,
                    "limit": 20,
                    "filters": {
                        "country": "United States",
                        "sector": "Software"
                    }
                }
            )

            assert response.status_code == 200
            # Verify service was called with correct parameters
            mock_service.find_similar_companies.assert_called_once()
            call_args = mock_service.find_similar_companies.call_args[0][0]
            assert call_args.company_ids == [1]
            assert call_args.min_score == 0.6
            assert call_args.limit == 20
            assert call_args.filters == {"country": "United States", "sector": "Software"}


class TestSubmitSimilarityFeedback:
    """Test /api/similar-companies/feedback POST endpoint"""

    def test_submit_feedback_new(self, client, mock_auth, mock_db_session):
        """Test submitting new feedback"""
        # Mock no existing feedback
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                "match_company_id": 2,
                "feedback_type": "good_match",
                "notes": "Great match!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "saved successfully" in data["message"]

        # Verify feedback was added
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_submit_feedback_update_existing(self, client, mock_auth, mock_db_session):
        """Test updating existing feedback"""
        # Mock existing feedback
        existing_feedback = Mock()
        existing_feedback.feedback_type = "not_a_match"

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_feedback

        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                "match_company_id": 2,
                "feedback_type": "good_match"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify feedback was updated (not added)
        assert existing_feedback.feedback_type == "good_match"
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called_once()

    def test_submit_feedback_missing_fields(self, client, mock_auth, mock_db_session):
        """Test submitting feedback with missing required fields"""
        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                # missing match_company_id and feedback_type
            }
        )

        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_submit_feedback_missing_input_company_id(self, client, mock_auth, mock_db_session):
        """Test submitting feedback without input_company_id"""
        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "match_company_id": 2,
                "feedback_type": "good_match"
            }
        )

        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_submit_feedback_missing_match_company_id(self, client, mock_auth, mock_db_session):
        """Test submitting feedback without match_company_id"""
        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                "feedback_type": "good_match"
            }
        )

        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_submit_feedback_missing_feedback_type(self, client, mock_auth, mock_db_session):
        """Test submitting feedback without feedback_type"""
        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                "match_company_id": 2
            }
        )

        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_submit_feedback_server_error(self, client, mock_auth, mock_db_session):
        """Test feedback submission with database error"""
        mock_db_session.query.side_effect = Exception("Database connection failed")

        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                "match_company_id": 2,
                "feedback_type": "good_match"
            }
        )

        assert response.status_code == 500
        assert "Error submitting feedback" in response.json()["detail"]

    def test_submit_feedback_with_notes(self, client, mock_auth, mock_db_session):
        """Test submitting feedback with optional notes"""
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        response = client.post(
            "/api/similar-companies/feedback",
            json={
                "input_company_id": 1,
                "match_company_id": 2,
                "feedback_type": "not_a_match",
                "notes": "Different business models"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_submit_feedback_uses_admin_email(self, client, mock_db_session):
        """Test that feedback captures admin email from auth"""
        with patch('backend.api.similar_companies.verify_admin_token') as mock_auth:
            mock_auth.return_value = {"email": "admin@company.com", "role": "admin"}

            mock_query = Mock()
            mock_db_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            response = client.post(
                "/api/similar-companies/feedback",
                json={
                    "input_company_id": 1,
                    "match_company_id": 2,
                    "feedback_type": "good_match"
                }
            )

            assert response.status_code == 200
            # The admin email should be used when creating feedback
            mock_db_session.add.assert_called_once()
