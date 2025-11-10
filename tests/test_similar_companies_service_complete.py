"""
Comprehensive tests for Similar Companies Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.services.similar_companies_service import SimilarCompaniesService
from backend.schemas.requests import SimilarCompaniesRequest
from src.models.database_models_v2 import Company, CompanyPEInvestment, CompanyTag


class TestSimilarCompaniesServiceInit:
    """Test initialization and OpenAI setup"""

    @patch('backend.services.similar_companies_service.os.getenv')
    def test_init_without_openai_key(self, mock_getenv):
        """Test initialization without OpenAI API key"""
        mock_getenv.return_value = None
        mock_session = Mock(spec=Session)

        service = SimilarCompaniesService(session=mock_session)

        assert service.session == mock_session
        assert service.openai_client is None

    @patch('backend.services.similar_companies_service.os.getenv')
    @patch('backend.services.similar_companies_service.openai')
    def test_init_with_openai_key(self, mock_openai_module, mock_getenv):
        """Test initialization with OpenAI API key"""
        mock_getenv.return_value = "test-api-key"
        mock_openai_client = Mock()
        mock_openai_module.OpenAI.return_value = mock_openai_client
        mock_session = Mock(spec=Session)

        service = SimilarCompaniesService(session=mock_session)

        assert service.session == mock_session
        assert service.openai_client == mock_openai_client
        mock_openai_module.OpenAI.assert_called_once_with(api_key="test-api-key")

    @patch('backend.services.similar_companies_service.os.getenv')
    def test_init_openai_import_error(self, mock_getenv):
        """Test initialization when openai package is not installed"""
        mock_getenv.return_value = "test-api-key"
        mock_session = Mock(spec=Session)

        with patch('backend.services.similar_companies_service.openai', side_effect=ImportError):
            # The import happens at module level, so we test the service creation doesn't fail
            service = SimilarCompaniesService(session=mock_session)
            assert service.session == mock_session


class TestCalculateSimilarityScore:
    """Test similarity score calculation"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        mock_session = Mock(spec=Session)
        with patch('backend.services.similar_companies_service.os.getenv', return_value=None):
            return SimilarCompaniesService(session=mock_session)

    @pytest.fixture
    def sample_company_a(self):
        """Create sample company A"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Company A"
        company.country = "United States"
        company.hq_city = "San Francisco"
        company.hq_state = "CA"
        company.primary_industry_sector = "Software"
        company.primary_industry_group = "Enterprise Software"
        company.pitchbook_primary_vertical = "SaaS"
        company.pitchbook_business_vertical = "B2B"
        company.current_revenue_usd = 10000000
        company.current_employees = 100
        company.financing_stage = "Series B"
        company.tags = []
        company.investments = []
        return company

    @pytest.fixture
    def sample_company_b(self):
        """Create sample company B"""
        company = Mock(spec=Company)
        company.id = 2
        company.name = "Company B"
        company.country = "United States"
        company.hq_city = "San Francisco"
        company.hq_state = "CA"
        company.primary_industry_sector = "Software"
        company.primary_industry_group = "Enterprise Software"
        company.pitchbook_primary_vertical = "SaaS"
        company.pitchbook_business_vertical = "B2B"
        company.current_revenue_usd = 15000000
        company.current_employees = 150
        company.financing_stage = "Series B"
        company.tags = []
        company.investments = []
        return company

    def test_calculate_similarity_identical_companies(self, service, sample_company_a):
        """Test similarity score between identical companies"""
        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_a
        )

        # Should have high similarity (not 100% due to scoring algorithm)
        assert score > 0.5
        assert len(matching_attrs) > 0
        assert isinstance(attr_scores, dict)
        assert total_checks > 0

    def test_calculate_similarity_similar_companies(self, service, sample_company_a, sample_company_b):
        """Test similarity score between similar companies"""
        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should have reasonable similarity
        assert score >= 0
        assert score <= 1.0
        assert len(matching_attrs) >= 0
        assert isinstance(attr_scores, dict)
        assert total_checks > 0

    def test_calculate_similarity_different_countries(self, service, sample_company_a, sample_company_b):
        """Test similarity when companies are in different countries"""
        sample_company_b.country = "Canada"

        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should have lower similarity due to different country
        assert score >= 0
        assert "country" not in matching_attrs

    def test_calculate_similarity_different_sectors(self, service, sample_company_a, sample_company_b):
        """Test similarity when companies are in different sectors"""
        sample_company_b.primary_industry_sector = "Healthcare"

        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should have lower similarity due to different sector
        assert score >= 0
        assert "primary_industry_sector" not in matching_attrs

    def test_calculate_similarity_with_tags(self, service, sample_company_a, sample_company_b):
        """Test similarity calculation with company tags"""
        tag1 = Mock(spec=CompanyTag)
        tag1.industry_tag = "AI/ML"

        tag2 = Mock(spec=CompanyTag)
        tag2.industry_tag = "AI/ML"

        sample_company_a.tags = [tag1]
        sample_company_b.tags = [tag2]

        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should recognize matching tags
        assert score > 0
        assert total_checks > 0

    def test_calculate_similarity_with_investments(self, service, sample_company_a, sample_company_b):
        """Test similarity calculation with investments"""
        inv1 = Mock(spec=CompanyPEInvestment)
        inv1.pe_firm = Mock()
        inv1.pe_firm.name = "Sequoia"
        inv1.computed_status = "Active"

        inv2 = Mock(spec=CompanyPEInvestment)
        inv2.pe_firm = Mock()
        inv2.pe_firm.name = "Sequoia"
        inv2.computed_status = "Active"

        sample_company_a.investments = [inv1]
        sample_company_b.investments = [inv2]

        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should recognize shared investors
        assert score > 0

    def test_calculate_similarity_different_revenue_sizes(self, service, sample_company_a, sample_company_b):
        """Test similarity with vastly different revenue sizes"""
        sample_company_a.current_revenue_usd = 1000000
        sample_company_b.current_revenue_usd = 1000000000  # 1000x larger

        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should handle large revenue differences
        assert score >= 0
        assert score <= 1.0

    def test_calculate_similarity_none_values(self, service, sample_company_a, sample_company_b):
        """Test similarity calculation with None values"""
        sample_company_a.current_revenue_usd = None
        sample_company_a.current_employees = None
        sample_company_b.current_revenue_usd = None
        sample_company_b.current_employees = None

        score, matching_attrs, attr_scores, semantic_score, total_checks = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Should handle None values gracefully
        assert score >= 0
        assert isinstance(matching_attrs, list)


class TestCompanyToResponse:
    """Test _company_to_response helper method"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        mock_session = Mock(spec=Session)
        with patch('backend.services.similar_companies_service.os.getenv', return_value=None):
            return SimilarCompaniesService(session=mock_session)

    def test_company_to_response_basic(self, service):
        """Test converting company to response format"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Test Company"
        company.website = "https://test.com"
        company.description = "A test company"
        company.country = "United States"
        company.hq_city = "San Francisco"
        company.hq_state = "CA"
        company.primary_industry_sector = "Software"
        company.primary_industry_group = "Enterprise"
        company.pitchbook_primary_vertical = "SaaS"
        company.current_revenue_usd = 10000000
        company.current_employees = 100
        company.financing_stage = "Series B"
        company.last_known_valuation_usd = 50000000
        company.founded_year = 2015
        company.linkedin_url = "https://linkedin.com/company/test"
        company.crunchbase_url = "https://crunchbase.com/test"
        company.investments = []
        company.tags = []

        response = service._company_to_response(company)

        assert response.id == 1
        assert response.name == "Test Company"
        assert response.website == "https://test.com"
        assert response.description == "A test company"
        assert response.country == "United States"

    def test_company_to_response_with_investments(self, service):
        """Test converting company with investments"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Test Company"
        company.website = None
        company.description = None
        company.country = "United States"
        company.hq_city = None
        company.hq_state = None
        company.primary_industry_sector = "Software"
        company.primary_industry_group = None
        company.pitchbook_primary_vertical = None
        company.current_revenue_usd = None
        company.current_employees = None
        company.financing_stage = None
        company.last_known_valuation_usd = None
        company.founded_year = None
        company.linkedin_url = None
        company.crunchbase_url = None

        inv = Mock(spec=CompanyPEInvestment)
        inv.pe_firm = Mock()
        inv.pe_firm.name = "Sequoia"
        inv.pe_firm.id = 1
        inv.computed_status = "Active"

        company.investments = [inv]
        company.tags = []

        response = service._company_to_response(company)

        assert response.id == 1
        assert response.name == "Test Company"
        # Should handle investments
        assert len(response.pe_firms) > 0

    def test_company_to_response_with_tags(self, service):
        """Test converting company with industry tags"""
        company = Mock(spec=Company)
        company.id = 1
        company.name = "Test Company"
        company.website = None
        company.description = None
        company.country = "United States"
        company.hq_city = None
        company.hq_state = None
        company.primary_industry_sector = "Software"
        company.primary_industry_group = None
        company.pitchbook_primary_vertical = None
        company.current_revenue_usd = None
        company.current_employees = None
        company.financing_stage = None
        company.last_known_valuation_usd = None
        company.founded_year = None
        company.linkedin_url = None
        company.crunchbase_url = None
        company.investments = []

        tag1 = Mock(spec=CompanyTag)
        tag1.industry_tag = "AI/ML"
        tag2 = Mock(spec=CompanyTag)
        tag2.industry_tag = "Cloud"

        company.tags = [tag1, tag2]

        response = service._company_to_response(company)

        assert response.id == 1
        assert len(response.industry_tags) == 2
        assert "AI/ML" in response.industry_tags
        assert "Cloud" in response.industry_tags


class TestGenerateReasoningMethods:
    """Test reasoning generation methods"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        mock_session = Mock(spec=Session)
        with patch('backend.services.similar_companies_service.os.getenv', return_value=None):
            return SimilarCompaniesService(session=mock_session)

    @pytest.fixture
    def sample_companies(self):
        """Create sample companies for testing"""
        company_a = Mock(spec=Company)
        company_a.name = "Company A"
        company_a.primary_industry_sector = "Software"
        company_a.country = "United States"
        company_a.current_revenue_usd = 10000000

        company_b = Mock(spec=Company)
        company_b.name = "Company B"
        company_b.primary_industry_sector = "Software"
        company_b.country = "United States"
        company_b.current_revenue_usd = 15000000

        return company_a, company_b

    def test_generate_rule_based_reasoning(self, service, sample_companies):
        """Test rule-based reasoning generation"""
        company_a, company_b = sample_companies
        matching_attrs = ["primary_industry_sector", "country"]
        similarity_score = 0.75

        reasoning = service.generate_rule_based_reasoning(
            company_a, company_b, matching_attrs, similarity_score
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert "Company B" in reasoning or "similar" in reasoning.lower()

    def test_generate_rule_based_reasoning_high_score(self, service, sample_companies):
        """Test reasoning generation with high similarity score"""
        company_a, company_b = sample_companies
        matching_attrs = ["primary_industry_sector", "country", "financing_stage"]
        similarity_score = 0.95

        reasoning = service.generate_rule_based_reasoning(
            company_a, company_b, matching_attrs, similarity_score
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0

    def test_generate_rule_based_reasoning_low_score(self, service, sample_companies):
        """Test reasoning generation with low similarity score"""
        company_a, company_b = sample_companies
        matching_attrs = ["country"]
        similarity_score = 0.35

        reasoning = service.generate_rule_based_reasoning(
            company_a, company_b, matching_attrs, similarity_score
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0

    def test_generate_rule_based_reasoning_no_matches(self, service, sample_companies):
        """Test reasoning generation with no matching attributes"""
        company_a, company_b = sample_companies
        matching_attrs = []
        similarity_score = 0.25

        reasoning = service.generate_rule_based_reasoning(
            company_a, company_b, matching_attrs, similarity_score
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0


class TestFindSimilarCompaniesErrorHandling:
    """Test error handling in find_similar_companies"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        mock_session = Mock(spec=Session)
        with patch('backend.services.similar_companies_service.os.getenv', return_value=None):
            return SimilarCompaniesService(session=mock_session)

    def test_find_similar_companies_no_input_companies(self, service):
        """Test with invalid company IDs"""
        mock_query = Mock()
        service.session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        request = SimilarCompaniesRequest(
            company_ids=[999, 998],
            min_score=0.5,
            limit=10
        )

        with pytest.raises(ValueError, match="No companies found"):
            service.find_similar_companies(request)

    def test_find_similar_companies_with_filters(self, service):
        """Test find_similar_companies with country and sector filters"""
        # Create mock companies
        company_a = Mock(spec=Company)
        company_a.id = 1
        company_a.name = "Input Company"
        company_a.country = "United States"
        company_a.primary_industry_sector = "Software"
        company_a.investments = []
        company_a.tags = []

        company_b = Mock(spec=Company)
        company_b.id = 2
        company_b.name = "Similar Company"
        company_b.country = "United States"
        company_b.primary_industry_sector = "Software"
        company_b.current_revenue_usd = 10000000
        company_b.last_known_valuation_usd = 50000000
        company_b.investments = []
        company_b.tags = []

        # Setup mock query chain
        mock_query = Mock()
        service.session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # First call returns input companies, second returns candidates
        mock_query.all.side_effect = [[company_a], [company_b]]

        # Mock the calculate_similarity_score to return a high score
        with patch.object(service, 'calculate_similarity_score', return_value=(0.8, [], {}, 0.0, 10)):
            with patch.object(service, 'generate_rule_based_reasoning', return_value="Similar companies"):
                with patch.object(service, '_company_to_response', return_value=Mock()):
                    request = SimilarCompaniesRequest(
                        company_ids=[1],
                        min_score=0.5,
                        limit=10,
                        filters={'country': 'United States', 'sector': 'Software'}
                    )

                    result = service.find_similar_companies(request)

                    # Should apply filters
                    assert mock_query.filter.called
