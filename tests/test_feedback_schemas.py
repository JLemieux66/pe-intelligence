"""
Tests for feedback schemas
"""
import pytest
from pydantic import ValidationError

from backend.schemas.feedback import (
    SimilarityFeedbackRequest,
    SimilarityFeedbackResponse,
    FeedbackStats
)


class TestSimilarityFeedbackRequest:
    """Test SimilarityFeedbackRequest schema"""

    def test_create_feedback_request_required_fields(self):
        """Test creating feedback request with required fields only"""
        feedback = SimilarityFeedbackRequest(
            source_company_id=1,
            target_company_id=2,
            is_similar=True
        )

        assert feedback.source_company_id == 1
        assert feedback.target_company_id == 2
        assert feedback.is_similar is True
        assert feedback.feedback_reason is None
        assert feedback.user_email is None

    def test_create_feedback_request_all_fields(self):
        """Test creating feedback request with all fields"""
        feedback = SimilarityFeedbackRequest(
            source_company_id=1,
            target_company_id=2,
            is_similar=False,
            feedback_reason="Different business models",
            user_email="user@example.com"
        )

        assert feedback.source_company_id == 1
        assert feedback.target_company_id == 2
        assert feedback.is_similar is False
        assert feedback.feedback_reason == "Different business models"
        assert feedback.user_email == "user@example.com"

    def test_feedback_request_missing_required_field(self):
        """Test that missing required fields raise validation error"""
        with pytest.raises(ValidationError):
            SimilarityFeedbackRequest(
                source_company_id=1,
                # Missing target_company_id
                is_similar=True
            )

    def test_feedback_request_invalid_type(self):
        """Test that invalid field types raise validation error"""
        with pytest.raises(ValidationError):
            SimilarityFeedbackRequest(
                source_company_id="not_an_int",
                target_company_id=2,
                is_similar=True
            )

    def test_feedback_request_is_similar_boolean(self):
        """Test is_similar field accepts boolean values"""
        feedback_true = SimilarityFeedbackRequest(
            source_company_id=1,
            target_company_id=2,
            is_similar=True
        )
        assert feedback_true.is_similar is True

        feedback_false = SimilarityFeedbackRequest(
            source_company_id=1,
            target_company_id=2,
            is_similar=False
        )
        assert feedback_false.is_similar is False

    def test_feedback_request_optional_reason(self):
        """Test feedback_reason is optional"""
        feedback = SimilarityFeedbackRequest(
            source_company_id=1,
            target_company_id=2,
            is_similar=True,
            feedback_reason="They operate in the same market"
        )
        assert feedback.feedback_reason == "They operate in the same market"

    def test_feedback_request_optional_email(self):
        """Test user_email is optional"""
        feedback = SimilarityFeedbackRequest(
            source_company_id=1,
            target_company_id=2,
            is_similar=True,
            user_email="analyst@company.com"
        )
        assert feedback.user_email == "analyst@company.com"


class TestSimilarityFeedbackResponse:
    """Test SimilarityFeedbackResponse schema"""

    def test_create_feedback_response_success(self):
        """Test creating successful feedback response"""
        response = SimilarityFeedbackResponse(
            success=True,
            message="Feedback saved successfully",
            feedback_id=123
        )

        assert response.success is True
        assert response.message == "Feedback saved successfully"
        assert response.feedback_id == 123

    def test_create_feedback_response_failure(self):
        """Test creating failed feedback response"""
        response = SimilarityFeedbackResponse(
            success=False,
            message="Failed to save feedback"
        )

        assert response.success is False
        assert response.message == "Failed to save feedback"
        assert response.feedback_id is None

    def test_feedback_response_without_id(self):
        """Test response without feedback_id"""
        response = SimilarityFeedbackResponse(
            success=True,
            message="Feedback processed"
        )

        assert response.success is True
        assert response.feedback_id is None

    def test_feedback_response_missing_required(self):
        """Test that missing required fields raise error"""
        with pytest.raises(ValidationError):
            SimilarityFeedbackResponse(
                success=True
                # Missing message
            )


class TestFeedbackStats:
    """Test FeedbackStats schema"""

    def test_create_feedback_stats_basic(self):
        """Test creating feedback stats with basic fields"""
        stats = FeedbackStats(
            total_feedback=100,
            positive_feedback=70,
            negative_feedback=30
        )

        assert stats.total_feedback == 100
        assert stats.positive_feedback == 70
        assert stats.negative_feedback == 30
        assert stats.accuracy_score is None

    def test_create_feedback_stats_with_accuracy(self):
        """Test creating feedback stats with accuracy score"""
        stats = FeedbackStats(
            total_feedback=100,
            positive_feedback=70,
            negative_feedback=30,
            accuracy_score=0.85
        )

        assert stats.total_feedback == 100
        assert stats.positive_feedback == 70
        assert stats.negative_feedback == 30
        assert stats.accuracy_score == 0.85

    def test_feedback_stats_zero_values(self):
        """Test stats with zero values"""
        stats = FeedbackStats(
            total_feedback=0,
            positive_feedback=0,
            negative_feedback=0
        )

        assert stats.total_feedback == 0
        assert stats.positive_feedback == 0
        assert stats.negative_feedback == 0

    def test_feedback_stats_validation(self):
        """Test that stats validates field types"""
        with pytest.raises(ValidationError):
            FeedbackStats(
                total_feedback="not_an_int",
                positive_feedback=50,
                negative_feedback=50
            )

    def test_feedback_stats_optional_accuracy(self):
        """Test that accuracy_score is optional"""
        stats = FeedbackStats(
            total_feedback=10,
            positive_feedback=5,
            negative_feedback=5
        )

        assert stats.accuracy_score is None

    def test_feedback_stats_accuracy_as_float(self):
        """Test accuracy_score accepts float values"""
        stats = FeedbackStats(
            total_feedback=100,
            positive_feedback=75,
            negative_feedback=25,
            accuracy_score=0.9234
        )

        assert stats.accuracy_score == 0.9234

    def test_feedback_stats_negative_accuracy(self):
        """Test stats can have accuracy score of 0"""
        stats = FeedbackStats(
            total_feedback=100,
            positive_feedback=50,
            negative_feedback=50,
            accuracy_score=0.0
        )

        assert stats.accuracy_score == 0.0

    def test_feedback_stats_perfect_accuracy(self):
        """Test stats with perfect accuracy score"""
        stats = FeedbackStats(
            total_feedback=100,
            positive_feedback=100,
            negative_feedback=0,
            accuracy_score=1.0
        )

        assert stats.accuracy_score == 1.0
