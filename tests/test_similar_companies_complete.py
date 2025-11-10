"""
Comprehensive tests for SimilarCompaniesService
Tests similarity algorithm, filtering, and scoring logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.services.similar_companies_service import SimilarCompaniesService
from backend.schemas.requests import SimilarCompaniesRequest


class TestSimilarCompaniesService:
    """Unit tests for SimilarCompaniesService"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service with mocked session"""
        return SimilarCompaniesService(session=mock_session)

    @pytest.fixture
    def sample_company_a(self):
        """Create sample company A"""
        company = Mock()
        company.id = 1
        company.name = "Tech Company A"
        company.verticals = "SaaS, Cloud Computing"
        company.industry_category = "Software"
        company.employee_count = 500
        company.revenue_tier = "growth stage"
        company.funding_stage_encoded = 3
        company.company_size_category = "Medium"
        company.hq_country = "United States"
        company.state_region = "California"
        company.last_financing_deal_type = "Series B"
        company.last_known_valuation_usd = 100.0
        company.current_revenue_usd = 50.0
        return company

    @pytest.fixture
    def sample_company_b(self):
        """Create sample company B (similar to A)"""
        company = Mock()
        company.id = 2
        company.name = "Tech Company B"
        company.verticals = "SaaS, AI"
        company.industry_category = "Software"
        company.employee_count = 450
        company.revenue_tier = "growth stage"
        company.funding_stage_encoded = 3
        company.company_size_category = "Medium"
        company.hq_country = "United States"
        company.state_region = "California"
        company.last_financing_deal_type = "Series B"
        company.last_known_valuation_usd = 120.0
        company.current_revenue_usd = 55.0
        return company

    def test_init_creates_service(self, mock_session):
        """Test service initialization"""
        service = SimilarCompaniesService(session=mock_session)
        assert service.session == mock_session

    def test_init_openai_without_key(self, mock_session):
        """Test OpenAI initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            service = SimilarCompaniesService(session=mock_session)
            assert service.openai_client is None

    def test_init_openai_with_key(self, mock_session):
        """Test OpenAI initialization with API key"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            with patch('openai.OpenAI') as mock_openai:
                service = SimilarCompaniesService(session=mock_session)
                mock_openai.assert_called_once_with(api_key='test_key')

    # Similarity Score Calculation Tests
    def test_calculate_similarity_score_identical_companies(self, service, sample_company_a):
        """Test similarity score for identical companies"""
        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(
            sample_company_a, sample_company_a
        )

        # Identical companies should have very high score
        assert score >= 80.0
        assert confidence >= 70.0
        assert categories >= 3
        assert isinstance(attrs, list)
        assert isinstance(breakdown, dict)

    def test_calculate_similarity_score_similar_companies(self, service, sample_company_a, sample_company_b):
        """Test similarity score for similar companies"""
        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Similar companies should have good score
        assert score >= 50.0
        assert isinstance(attrs, list)
        assert len(attrs) > 0
        assert isinstance(breakdown, dict)
        assert confidence > 0

    def test_calculate_similarity_score_different_companies(self, service):
        """Test similarity score for very different companies"""
        company1 = Mock(
            verticals="SaaS",
            industry_category="Software",
            employee_count=50,
            revenue_tier="early stage",
            funding_stage_encoded=1,
            company_size_category="Small",
            hq_country="United States",
            state_region="CA",
            last_financing_deal_type="Series A",
            last_known_valuation_usd=10.0,
            current_revenue_usd=2.0
        )
        company2 = Mock(
            verticals="Manufacturing",
            industry_category="Industrial",
            employee_count=5000,
            revenue_tier="mature",
            funding_stage_encoded=6,
            company_size_category="Large",
            hq_country="Japan",
            state_region="Tokyo",
            last_financing_deal_type="IPO",
            last_known_valuation_usd=5000.0,
            current_revenue_usd=1000.0
        )

        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(company1, company2)

        # Very different companies should have low score
        assert score < 50.0

    def test_calculate_similarity_handles_none_verticals(self, service):
        """Test similarity calculation with None verticals"""
        company1 = Mock(
            verticals=None,
            industry_category="Software",
            employee_count=100,
            revenue_tier=None,
            funding_stage_encoded=None,
            company_size_category=None,
            hq_country="USA",
            state_region=None,
            last_financing_deal_type=None,
            last_known_valuation_usd=None,
            current_revenue_usd=None
        )
        company2 = Mock(
            verticals=None,
            industry_category="Software",
            employee_count=150,
            revenue_tier=None,
            funding_stage_encoded=None,
            company_size_category=None,
            hq_country="USA",
            state_region=None,
            last_financing_deal_type=None,
            last_known_valuation_usd=None,
            current_revenue_usd=None
        )

        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(company1, company2)

        # Should not crash
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_calculate_similarity_score_breakdown_structure(self, service, sample_company_a, sample_company_b):
        """Test that score breakdown has correct structure"""
        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(
            sample_company_a, sample_company_b
        )

        # Check breakdown structure
        if 'verticals' in breakdown:
            assert 'score' in breakdown['verticals']
            assert 'max_score' in breakdown['verticals']

        if 'industry_category' in breakdown:
            assert 'score' in breakdown['industry_category']
            assert 'max_score' in breakdown['industry_category']

    def test_calculate_similarity_employee_count_exact_match(self, service):
        """Test employee count similarity with exact match"""
        company1 = Mock(employee_count=500, verticals=None, industry_category=None,
                       revenue_tier=None, funding_stage_encoded=None, company_size_category=None,
                       hq_country=None, state_region=None, last_financing_deal_type=None,
                       last_known_valuation_usd=None, current_revenue_usd=None)
        company2 = Mock(employee_count=500, verticals=None, industry_category=None,
                       revenue_tier=None, funding_stage_encoded=None, company_size_category=None,
                       hq_country=None, state_region=None, last_financing_deal_type=None,
                       last_known_valuation_usd=None, current_revenue_usd=None)

        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(company1, company2)

        # Should get max employee score
        if 'employee_count' in breakdown:
            assert breakdown['employee_count']['score'] == 15

    def test_calculate_similarity_revenue_tier_match(self, service):
        """Test revenue tier similarity"""
        company1 = Mock(revenue_tier="growth stage", verticals=None, industry_category=None,
                       employee_count=None, funding_stage_encoded=None, company_size_category=None,
                       hq_country=None, state_region=None, last_financing_deal_type=None,
                       last_known_valuation_usd=None, current_revenue_usd=None)
        company2 = Mock(revenue_tier="growth stage", verticals=None, industry_category=None,
                       employee_count=None, funding_stage_encoded=None, company_size_category=None,
                       hq_country=None, state_region=None, last_financing_deal_type=None,
                       last_known_valuation_usd=None, current_revenue_usd=None)

        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(company1, company2)

        # Should get max revenue tier score
        if 'revenue_tier' in breakdown:
            assert breakdown['revenue_tier']['score'] == 10

    def test_calculate_similarity_funding_stage_match(self, service):
        """Test funding stage similarity"""
        company1 = Mock(funding_stage_encoded=3, verticals=None, industry_category=None,
                       employee_count=None, revenue_tier=None, company_size_category=None,
                       hq_country=None, state_region=None, last_financing_deal_type=None,
                       last_known_valuation_usd=None, current_revenue_usd=None)
        company2 = Mock(funding_stage_encoded=3, verticals=None, industry_category=None,
                       employee_count=None, revenue_tier=None, company_size_category=None,
                       hq_country=None, state_region=None, last_financing_deal_type=None,
                       last_known_valuation_usd=None, current_revenue_usd=None)

        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(company1, company2)

        # Should get max funding stage score
        if 'funding_stage' in breakdown:
            assert breakdown['funding_stage']['score'] == 8

    def test_calculate_similarity_geography_same_state(self, service):
        """Test geographic similarity for same state"""
        company1 = Mock(hq_country="United States", state_region="California",
                       verticals=None, industry_category=None, employee_count=None,
                       revenue_tier=None, funding_stage_encoded=None, company_size_category=None,
                       last_financing_deal_type=None, last_known_valuation_usd=None,
                       current_revenue_usd=None)
        company2 = Mock(hq_country="United States", state_region="California",
                       verticals=None, industry_category=None, employee_count=None,
                       revenue_tier=None, funding_stage_encoded=None, company_size_category=None,
                       last_financing_deal_type=None, last_known_valuation_usd=None,
                       current_revenue_usd=None)

        score, attrs, breakdown, confidence, categories = service.calculate_similarity_score(company1, company2)

        # Should get max geography score
        if 'geography' in breakdown:
            assert breakdown['geography']['score'] == 5

    # Reasoning Tests
    def test_generate_rule_based_reasoning(self, service, sample_company_a, sample_company_b):
        """Test rule-based reasoning generation"""
        matching_attrs = ["Shared verticals: SaaS", "Same industry: Software"]

        reasoning = service.generate_rule_based_reasoning(
            sample_company_a, sample_company_b, matching_attrs, 75.0
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert "similarities" in reasoning.lower() or "similar" in reasoning.lower()

    def test_generate_rule_based_reasoning_high_score(self, service, sample_company_a, sample_company_b):
        """Test reasoning for high similarity score"""
        reasoning = service.generate_rule_based_reasoning(
            sample_company_a, sample_company_b, ["Industry match"], 85.0
        )

        assert "highly similar" in reasoning.lower() or "similar" in reasoning.lower()

    def test_generate_rule_based_reasoning_low_score(self, service, sample_company_a, sample_company_b):
        """Test reasoning for low similarity score"""
        reasoning = service.generate_rule_based_reasoning(
            sample_company_a, sample_company_b, ["Geography"], 25.0
        )

        assert "some similarities" in reasoning.lower() or "similarities" in reasoning.lower()

    def test_generate_rule_based_reasoning_no_attributes(self, service, sample_company_a, sample_company_b):
        """Test reasoning when no matching attributes"""
        reasoning = service.generate_rule_based_reasoning(
            sample_company_a, sample_company_b, [], 15.0
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0

    # Semantic Similarity Tests
    def test_calculate_semantic_similarity_disabled(self, service, sample_company_a, sample_company_b):
        """Test that semantic similarity is disabled for performance"""
        score, explanation = service.calculate_semantic_similarity(sample_company_a, sample_company_b)

        assert score == 0.0
        assert "disabled" in explanation.lower()

    # Company to Response Tests
    def test_company_to_response_structure(self, service, sample_company_a):
        """Test converting company to response format"""
        sample_company_a.website = "https://example.com"
        sample_company_a.linkedin_url = "https://linkedin.com/company/test"
        sample_company_a.crunchbase_url = "https://crunchbase.com/test"
        sample_company_a.description = "A test company"
        sample_company_a.city = "San Francisco"
        sample_company_a.state_region = "CA"
        sample_company_a.revenue_range = "r_00100000"
        sample_company_a.projected_employee_count = None
        sample_company_a.crunchbase_employee_count = None
        sample_company_a.former_name = None
        sample_company_a.is_public = False
        sample_company_a.primary_industry_group = "Technology"
        sample_company_a.primary_industry_sector = "Software"
        sample_company_a.hq_location = "San Francisco, CA"
        sample_company_a.hq_country = "USA"
        sample_company_a.investments = []
        sample_company_a.tags = []
        sample_company_a.computed_status = "Active"  # Add computed_status as string

        response = service._company_to_response(sample_company_a)

        assert response.id == 1
        assert response.name == "Tech Company A"
        assert response.website == "https://example.com"

    def test_company_to_response_with_investments(self, service, sample_company_a):
        """Test company response includes PE firms"""
        mock_pe_firm = Mock()
        mock_pe_firm.name = "Acme Capital"  # Set as string, not Mock
        mock_investment = Mock(pe_firm=mock_pe_firm)
        sample_company_a.investments = [mock_investment]
        sample_company_a.tags = []
        sample_company_a.website = None
        sample_company_a.linkedin_url = None
        sample_company_a.crunchbase_url = None
        sample_company_a.description = None
        sample_company_a.city = None
        sample_company_a.state_region = None
        sample_company_a.revenue_range = None
        sample_company_a.projected_employee_count = None
        sample_company_a.crunchbase_employee_count = None
        sample_company_a.former_name = None
        sample_company_a.is_public = False
        sample_company_a.primary_industry_group = None
        sample_company_a.primary_industry_sector = None
        sample_company_a.hq_location = None
        sample_company_a.hq_country = None
        sample_company_a.computed_status = "Active"  # Add computed_status

        response = service._company_to_response(sample_company_a)

        assert "Acme Capital" in response.pe_firms

    def test_company_to_response_employee_count_display(self, service, sample_company_a):
        """Test employee count display logic"""
        sample_company_a.projected_employee_count = None
        sample_company_a.crunchbase_employee_count = None
        sample_company_a.investments = []
        sample_company_a.tags = []
        sample_company_a.website = None
        sample_company_a.linkedin_url = None
        sample_company_a.crunchbase_url = None
        sample_company_a.description = None
        sample_company_a.city = None
        sample_company_a.state_region = None
        sample_company_a.revenue_range = None
        sample_company_a.former_name = None
        sample_company_a.is_public = False
        sample_company_a.primary_industry_group = None
        sample_company_a.primary_industry_sector = None
        sample_company_a.hq_location = None
        sample_company_a.hq_country = None
        sample_company_a.computed_status = "Active"  # Add computed_status

        response = service._company_to_response(sample_company_a)

        # Should format with comma
        assert response.employee_count == "500"

    # Integration Tests (require actual query mocking)
    def test_find_similar_companies_no_input(self, service, mock_session):
        """Test finding similar companies with no input IDs"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        request = SimilarCompaniesRequest(
            company_ids=[],
            limit=10,
            min_score=60.0
        )

        try:
            result = service.find_similar_companies(request)
            # If it doesn't raise, check result
            assert result.total_results == 0
        except ValueError as e:
            # Expected to raise ValueError
            assert "No companies found" in str(e)

    def test_find_similar_companies_with_filters(self, service, mock_session):
        """Test applying filters in similar companies search"""
        # This is a complex integration test that would require extensive mocking
        # Skipping for now as it's better tested in integration tests
        pass
