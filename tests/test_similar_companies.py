"""
Comprehensive tests for similar companies feature
"""
import pytest
from unittest.mock import Mock, patch
from backend.services.similar_companies_service import SimilarCompaniesService
from backend.schemas.similar_companies import SimilarCompaniesRequest

class TestSimilarCompaniesService:
    """Test suite for similar companies service"""
    
    @pytest.fixture
    def service(self):
        return SimilarCompaniesService()
    
    @pytest.fixture
    def mock_companies(self):
        """Mock company data for testing"""
        return [
            Mock(
                id=1,
                name="TechCorp",
                industry="Technology",
                stage="Series B",
                location="San Francisco",
                employee_count=150,
                revenue_range="$10M-$50M",
                tags=[Mock(tag_value="SaaS"), Mock(tag_value="B2B")]
            ),
            Mock(
                id=2,
                name="DataInc",
                industry="Technology", 
                stage="Series A",
                location="New York",
                employee_count=75,
                revenue_range="$1M-$10M",
                tags=[Mock(tag_value="Analytics"), Mock(tag_value="B2B")]
            )
        ]
    
    def test_calculate_similarity_score(self, service, mock_companies):
        """Test similarity score calculation"""
        company1, company2 = mock_companies
        
        score, breakdown = service._calculate_similarity_score(company1, company2)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert isinstance(breakdown, dict)
        assert "industry" in breakdown
        assert "stage" in breakdown
        assert "location" in breakdown
    
    def test_industry_similarity(self, service):
        """Test industry similarity scoring"""
        score = service._calculate_industry_similarity("Technology", "Technology")
        assert score == 20.0  # Perfect match
        
        score = service._calculate_industry_similarity("Technology", "Healthcare")
        assert score == 0.0  # No match
    
    def test_stage_similarity(self, service):
        """Test funding stage similarity scoring"""
        score = service._calculate_stage_similarity("Series A", "Series A")
        assert score == 15.0  # Perfect match
        
        score = service._calculate_stage_similarity("Series A", "Series B")
        assert score > 0  # Adjacent stages should have some similarity
    
    @patch('backend.services.similar_companies_service.get_db_session')
    def test_find_similar_companies_empty_result(self, mock_db, service):
        """Test handling of empty results"""
        mock_session = Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        request = SimilarCompaniesRequest(company_ids=[999], min_score=30, limit=5)
        result = service.find_similar_companies(request)
        
        assert result.total_results == 0
        assert len(result.matches) == 0
    
    @patch('backend.services.similar_companies_service.openai_client')
    @patch('backend.services.similar_companies_service.get_db_session')
    def test_ai_reasoning_generation(self, mock_db, mock_openai, service, mock_companies):
        """Test AI reasoning generation"""
        # Mock database response
        mock_session = Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = mock_companies
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="These companies are similar because..."))]
        mock_openai.chat.completions.create.return_value = mock_response
        
        request = SimilarCompaniesRequest(company_ids=[1], min_score=0, limit=5)
        result = service.find_similar_companies(request)
        
        # Verify OpenAI was called
        mock_openai.chat.completions.create.assert_called_once()
        
        # Verify reasoning is included
        if result.matches:
            assert result.matches[0].ai_reasoning is not None

class TestSimilarCompaniesAPI:
    """Test suite for similar companies API endpoints"""
    
    def test_request_validation(self):
        """Test request schema validation"""
        # Valid request
        request = SimilarCompaniesRequest(company_ids=[1, 2], min_score=30, limit=5)
        assert request.company_ids == [1, 2]
        assert request.min_score == 30
        assert request.limit == 5
        
        # Test defaults
        request = SimilarCompaniesRequest(company_ids=[1])
        assert request.min_score == 30.0
        assert request.limit == 10
    
    def test_invalid_company_ids(self):
        """Test validation of company IDs"""
        with pytest.raises(ValueError):
            SimilarCompaniesRequest(company_ids=[], min_score=30, limit=5)
    
    def test_score_range_validation(self):
        """Test min_score validation"""
        with pytest.raises(ValueError):
            SimilarCompaniesRequest(company_ids=[1], min_score=-1, limit=5)
        
        with pytest.raises(ValueError):
            SimilarCompaniesRequest(company_ids=[1], min_score=101, limit=5)

if __name__ == "__main__":
    pytest.main([__file__])