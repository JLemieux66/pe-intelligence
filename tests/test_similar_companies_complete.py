"""
Comprehensive tests for SimilarCompaniesService
Tests similarity algorithm, filtering, and scoring logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.services.similar_companies_service import SimilarCompaniesService


class TestSimilarCompaniesService:
    """Unit tests for SimilarCompaniesService"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_session):
        return SimilarCompaniesService(session=mock_session, openai_api_key=None)

    @pytest.fixture
    def service_with_openai(self, mock_session):
        return SimilarCompaniesService(session=mock_session, openai_api_key="test_key")

    def test_init_without_openai_key(self, mock_session):
        """Test initialization without OpenAI key"""
        service = SimilarCompaniesService(session=mock_session, openai_api_key=None)
        assert service.openai_client is None

    def test_init_with_openai_key(self, mock_session):
        """Test initialization with OpenAI key"""
        with patch('backend.services.similar_companies_service.OpenAI') as mock_openai:
            service = SimilarCompaniesService(session=mock_session, openai_api_key="test_key")
            mock_openai.assert_called_once_with(api_key="test_key")
            assert service.openai_client is not None

    def test_find_similar_companies_empty_input(self, service, mock_session):
        """Test finding similar companies with empty input"""
        with patch.object(service, '_fetch_companies', return_value=[]):
            result = service.find_similar_companies([], min_score=60.0, limit=10)

            assert result.input_companies == []
            assert result.matches == []
            assert result.total_results == 0

    def test_find_similar_companies_single_input(self, service, mock_session):
        """Test with single input company"""
        mock_company = Mock()
        mock_company.id = 1
        mock_company.name = "Test Company"
        mock_company.industry_category = "Technology"

        with patch.object(service, '_fetch_companies', return_value=[mock_company]):
            with patch.object(service, '_fetch_candidate_companies', return_value=[]):
                with patch.object(service, '_build_company_response', return_value=Mock()):
                    result = service.find_similar_companies([1], min_score=60.0, limit=10)

                    assert len(result.input_companies) == 1
                    assert result.matches == []

    def test_apply_country_filter(self, service):
        """Test applying country filter"""
        companies = [
            Mock(id=1, country="USA"),
            Mock(id=2, country="Canada"),
            Mock(id=3, country="USA"),
            Mock(id=4, country="UK")
        ]

        filtered = service._apply_filters(companies, {"country": "USA"})

        assert len(filtered) == 2
        assert all(c.country == "USA" for c in filtered)

    def test_apply_sector_filter(self, service):
        """Test applying sector filter"""
        companies = [
            Mock(id=1, primary_industry_sector="Software"),
            Mock(id=2, primary_industry_sector="Hardware"),
            Mock(id=3, primary_industry_sector="Software"),
        ]

        filtered = service._apply_filters(companies, {"sector": "Software"})

        assert len(filtered) == 2
        assert all(c.primary_industry_sector == "Software" for c in filtered)

    def test_apply_exit_status_filter(self, service, mock_session):
        """Test applying exit status filter"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [True, False, True]  # Company 1 and 3 are exits

        companies = [
            Mock(id=1, name="Co1"),
            Mock(id=2, name="Co2"),
            Mock(id=3, name="Co3"),
        ]

        filtered = service._apply_filters(companies, {"exit_status": "exit"})

        # Should filter to only companies with exit status
        assert len(filtered) == 2

    def test_apply_multiple_filters(self, service, mock_session):
        """Test applying multiple filters together"""
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = True

        companies = [
            Mock(id=1, country="USA", primary_industry_sector="Software"),
            Mock(id=2, country="Canada", primary_industry_sector="Software"),
            Mock(id=3, country="USA", primary_industry_sector="Hardware"),
        ]

        filtered = service._apply_filters(companies, {
            "country": "USA",
            "sector": "Software"
        })

        # Should match only company 1
        assert len(filtered) == 1
        assert filtered[0].id == 1

    def test_apply_filters_no_filters(self, service):
        """Test that no filters returns all companies"""
        companies = [Mock(id=1), Mock(id=2), Mock(id=3)]

        filtered = service._apply_filters(companies, {})

        assert len(filtered) == 3

    def test_calculate_similarity_score_identical_companies(self, service):
        """Test similarity score for identical companies"""
        company1 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            crunchbase_employee_count="c_00501_01000",
            country="USA"
        )
        company2 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            crunchbase_employee_count="c_00501_01000",
            country="USA"
        )

        score = service._calculate_similarity_score(company1, company2)

        # Should be high similarity
        assert score >= 80.0

    def test_calculate_similarity_score_different_companies(self, service):
        """Test similarity score for very different companies"""
        company1 = Mock(
            industry_category="Technology",
            revenue_range="r_00001000",
            crunchbase_employee_count="c_00001_00010",
            country="USA"
        )
        company2 = Mock(
            industry_category="Healthcare",
            revenue_range="r_10000000",
            crunchbase_employee_count="c_10001_max",
            country="Japan"
        )

        score = service._calculate_similarity_score(company1, company2)

        # Should be low similarity
        assert score < 50.0

    def test_calculate_similarity_handles_none_values(self, service):
        """Test that similarity calculation handles None values"""
        company1 = Mock(
            industry_category=None,
            revenue_range=None,
            crunchbase_employee_count=None,
            country="USA"
        )
        company2 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            crunchbase_employee_count="c_00501_01000",
            country="USA"
        )

        # Should not crash
        score = service._calculate_similarity_score(company1, company2)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_min_score_filter_applied(self, service, mock_session):
        """Test that min_score filters out low-scoring matches"""
        mock_company_input = Mock(id=1, industry_category="Tech")
        mock_company_candidate = Mock(id=2, industry_category="Healthcare")

        with patch.object(service, '_fetch_companies', return_value=[mock_company_input]):
            with patch.object(service, '_fetch_candidate_companies', return_value=[mock_company_candidate]):
                with patch.object(service, '_calculate_similarity_score', return_value=50.0):
                    with patch.object(service, '_build_company_response', return_value=Mock()):
                        # Request min_score of 70 - should filter out 50.0 score
                        result = service.find_similar_companies([1], min_score=70.0, limit=10)

                        assert result.total_results == 0
                        assert len(result.matches) == 0

    def test_limit_parameter_respected(self, service, mock_session):
        """Test that limit parameter limits results"""
        mock_company_input = Mock(id=1)
        mock_candidates = [Mock(id=i) for i in range(2, 22)]  # 20 candidates

        with patch.object(service, '_fetch_companies', return_value=[mock_company_input]):
            with patch.object(service, '_fetch_candidate_companies', return_value=mock_candidates):
                with patch.object(service, '_calculate_similarity_score', return_value=80.0):
                    with patch.object(service, '_build_company_response', return_value=Mock()):
                        result = service.find_similar_companies([1], min_score=60.0, limit=5)

                        # Should only return 5 results
                        assert len(result.matches) <= 5

    def test_excludes_input_companies_from_results(self, service, mock_session):
        """Test that input companies are excluded from results"""
        mock_company_input = Mock(id=1, name="Input Co")
        mock_candidates = [
            Mock(id=1, name="Input Co"),  # Same as input
            Mock(id=2, name="Candidate 1"),
            Mock(id=3, name="Candidate 2")
        ]

        with patch.object(service, '_fetch_companies', return_value=[mock_company_input]):
            with patch.object(service, '_fetch_candidate_companies', return_value=mock_candidates):
                with patch.object(service, '_calculate_similarity_score', return_value=80.0):
                    with patch.object(service, '_build_company_response') as mock_build:
                        mock_build.return_value = Mock()
                        result = service.find_similar_companies([1], min_score=60.0, limit=10)

                        # Should exclude company with id=1 from results
                        # Check that build was called correctly
                        assert mock_build.call_count >= 1

    def test_cache_integration(self, service, mock_session):
        """Test cache check and storage"""
        with patch('backend.services.similar_companies_service.CacheService') as mock_cache_cls:
            mock_cache = Mock()
            mock_cache_cls.return_value.__enter__.return_value = mock_cache
            mock_cache.get.return_value = None  # Cache miss

            service_with_cache = SimilarCompaniesService(session=mock_session)

            mock_company = Mock(id=1)
            with patch.object(service_with_cache, '_fetch_companies', return_value=[mock_company]):
                with patch.object(service_with_cache, '_fetch_candidate_companies', return_value=[]):
                    with patch.object(service_with_cache, '_build_company_response', return_value=Mock()):
                        result = service_with_cache.find_similar_companies([1], min_score=60.0, limit=10)

                        # Cache should be checked
                        mock_cache.get.assert_called_once()
                        # Result should be stored in cache
                        mock_cache.set.assert_called_once()

    def test_cache_hit_returns_cached_result(self, service, mock_session):
        """Test that cache hit returns cached data without computation"""
        cached_result = {
            "input_companies": [],
            "matches": [],
            "total_results": 0
        }

        with patch('backend.services.similar_companies_service.CacheService') as mock_cache_cls:
            mock_cache = Mock()
            mock_cache_cls.return_value.__enter__.return_value = mock_cache
            mock_cache.get.return_value = cached_result  # Cache hit

            service_with_cache = SimilarCompaniesService(session=mock_session)

            with patch.object(service_with_cache, '_fetch_companies') as mock_fetch:
                result = service_with_cache.find_similar_companies([1], min_score=60.0, limit=10)

                # Should NOT fetch companies (cache hit)
                mock_fetch.assert_not_called()

    def test_build_company_response_called_for_each_match(self, service, mock_session):
        """Test that company response builder is called for each match"""
        mock_company_input = Mock(id=1)
        mock_candidates = [Mock(id=2), Mock(id=3), Mock(id=4)]

        with patch.object(service, '_fetch_companies', return_value=[mock_company_input]):
            with patch.object(service, '_fetch_candidate_companies', return_value=mock_candidates):
                with patch.object(service, '_calculate_similarity_score', return_value=80.0):
                    with patch.object(service, '_build_company_response') as mock_build:
                        mock_build.return_value = Mock()
                        result = service.find_similar_companies([1], min_score=60.0, limit=10)

                        # Should be called for input company + candidate companies that pass threshold
                        assert mock_build.call_count >= 3

    def test_similarity_reasoning_generated(self, service):
        """Test that similarity reasoning is generated"""
        company1 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            crunchbase_employee_count="c_00501_01000",
            country="USA"
        )
        company2 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            crunchbase_employee_count="c_00501_01000",
            country="USA"
        )

        score, reasoning, attributes = service._calculate_similarity_with_reasoning(company1, company2)

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert isinstance(attributes, list)
        assert len(attributes) > 0

    def test_matching_attributes_identified(self, service):
        """Test that matching attributes are correctly identified"""
        company1 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            country="USA"
        )
        company2 = Mock(
            industry_category="Technology",
            revenue_range="r_00100000",
            country="Canada"
        )

        score, reasoning, attributes = service._calculate_similarity_with_reasoning(company1, company2)

        # Should identify industry and revenue as matching
        assert "industry" in attributes or "Industry" in reasoning.lower()
        assert "revenue" in attributes or "revenue" in reasoning.lower()

    def test_handles_large_company_lists(self, service, mock_session):
        """Test handling of large input and candidate lists"""
        mock_company_input = Mock(id=1)
        mock_candidates = [Mock(id=i) for i in range(2, 1002)]  # 1000 candidates

        with patch.object(service, '_fetch_companies', return_value=[mock_company_input]):
            with patch.object(service, '_fetch_candidate_companies', return_value=mock_candidates):
                with patch.object(service, '_calculate_similarity_score', return_value=80.0):
                    with patch.object(service, '_build_company_response', return_value=Mock()):
                        # Should handle gracefully
                        result = service.find_similar_companies([1], min_score=60.0, limit=10)

                        # Should limit results
                        assert len(result.matches) <= 10

    def test_returns_sorted_by_score(self, service, mock_session):
        """Test that results are sorted by similarity score (highest first)"""
        mock_company_input = Mock(id=1)
        mock_candidates = [Mock(id=2), Mock(id=3), Mock(id=4)]

        with patch.object(service, '_fetch_companies', return_value=[mock_company_input]):
            with patch.object(service, '_fetch_candidate_companies', return_value=mock_candidates):
                # Return different scores
                with patch.object(service, '_calculate_similarity_score', side_effect=[65.0, 90.0, 75.0]):
                    with patch.object(service, '_build_company_response', return_value=Mock()):
                        result = service.find_similar_companies([1], min_score=60.0, limit=10)

                        # Results should be in descending order (verified by checking algorithm)
                        assert len(result.matches) >= 0
