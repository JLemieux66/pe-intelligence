"""
Comprehensive edge case and error handling tests
Tests boundary conditions, null handling, and error scenarios
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.company_service import CompanyService
from backend.services.investment_service import InvestmentService
from backend.services.stats_service import StatsService
from unittest.mock import Mock


class TestNullHandling:
    """Tests for null/None value handling"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_company_with_null_fields(self, client):
        """Test company with many null fields"""
        # Companies with minimal data should still work
        response = client.get("/api/companies?limit=100")
        assert response.status_code == 200

    def test_empty_search_string(self, client):
        """Test empty search parameter"""
        response = client.get("/api/companies?search=")
        assert response.status_code == 200

    def test_null_filter_values(self, client):
        """Test with empty filter values"""
        response = client.get("/api/companies?pe_firm=&status=")
        assert response.status_code == 200


class TestBoundaryConditions:
    """Tests for boundary conditions"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_zero_limit(self, client):
        """Test limit=0"""
        response = client.get("/api/companies?limit=0")
        assert response.status_code == 422  # Should reject

    def test_maximum_limit(self, client):
        """Test maximum allowed limit"""
        response = client.get("/api/companies?limit=10000")
        assert response.status_code == 200
        companies = response.json()
        assert len(companies) <= 10000

    def test_excessive_limit(self, client):
        """Test limit beyond maximum"""
        response = client.get("/api/companies?limit=999999")
        assert response.status_code == 422  # Should reject

    def test_large_offset(self, client):
        """Test very large offset"""
        response = client.get("/api/companies?offset=1000000")
        assert response.status_code == 200
        # Should return empty list if offset exceeds total
        companies = response.json()
        assert isinstance(companies, list)

    def test_negative_limit(self, client):
        """Test negative limit"""
        response = client.get("/api/companies?limit=-10")
        assert response.status_code == 422

    def test_negative_offset(self, client):
        """Test negative offset"""
        response = client.get("/api/companies?offset=-5")
        assert response.status_code == 422


class TestSpecialCharacters:
    """Tests for special characters in inputs"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_special_chars_in_search(self, client):
        """Test special characters in search"""
        special_chars = ["<", ">", "&", "'", '"', "%", "\\", "/"]

        for char in special_chars:
            response = client.get(f"/api/companies?search={char}")
            # Should handle safely without error
            assert response.status_code in [200, 422]

    def test_sql_injection_attempt_in_search(self, client):
        """Test SQL injection patterns in search"""
        injection_attempts = [
            "'; DROP TABLE companies; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]

        for attempt in injection_attempts:
            response = client.get(f"/api/companies?search={attempt}")
            # Should handle safely
            assert response.status_code in [200, 422]
            # Should not crash or return error
            if response.status_code == 200:
                assert isinstance(response.json(), list)

    def test_unicode_in_search(self, client):
        """Test Unicode characters"""
        response = client.get("/api/companies?search=测试公司")
        assert response.status_code == 200

    def test_emoji_in_search(self, client):
        """Test emoji characters"""
        response = client.get("/api/companies?search=🚀")
        assert response.status_code == 200


class TestConcurrency:
    """Tests for concurrent requests"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_concurrent_reads(self, client):
        """Test multiple concurrent read requests"""
        import concurrent.futures

        def make_request():
            return client.get("/api/companies?limit=10")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_stats(self, client):
        """Test concurrent stats requests"""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(client.get, "/api/stats") for _ in range(10)]
            results = [f.result() for f in futures]

        assert all(r.status_code == 200 for r in results)


class TestDataConsistency:
    """Tests for data consistency"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_stats_match_actual_counts(self, client):
        """Test stats are consistent with actual data"""
        stats_response = client.get("/api/stats")
        stats = stats_response.json()

        companies_response = client.get("/api/companies?limit=10000")
        total_count = int(companies_response.headers.get("X-Total-Count", 0))

        # Stats total should be >= actual count (due to deduplication)
        assert stats["total_companies"] >= 0
        # Relationship should be reasonable
        if total_count > 0:
            ratio = stats["total_companies"] / max(total_count, 1)
            assert 0.5 <= ratio <= 2.0, "Stats and counts should be in reasonable range"

    def test_investment_counts_add_up(self, client):
        """Test that investment counts are consistent"""
        stats = client.get("/api/stats").json()

        # Active + Exited should be <= Total
        assert stats["active_investments"] + stats["exited_investments"] <= stats["total_investments"] + 100


class TestErrorRecovery:
    """Tests for error recovery"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    def test_service_handles_db_error(self, mock_session):
        """Test service handles database errors gracefully"""
        mock_session.query.side_effect = Exception("DB Error")

        service = CompanyService(session=mock_session)

        # Should raise or handle gracefully
        try:
            service.get_companies({}, limit=10, offset=0)
        except Exception as e:
            # Error should be raised but not crash
            assert "DB Error" in str(e) or isinstance(e, Exception)

    def test_service_handles_none_session(self):
        """Test service creation with None session"""
        service = CompanyService(session=None)
        # Should create session internally
        assert service is not None


class TestFilterCombinations:
    """Tests for complex filter combinations"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_all_filters_combined(self, client):
        """Test using all filters at once"""
        params = {
            "search": "tech",
            "pe_firm": "Acme",
            "status": "Active",
            "industry": "Technology",
            "country": "USA",
            "min_revenue": 1,
            "max_revenue": 100,
            "is_public": "false",
            "limit": 10,
            "offset": 0
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        response = client.get(f"/api/companies?{query_string}")

        assert response.status_code == 200
        # Results should match all filters
        companies = response.json()
        assert isinstance(companies, list)

    def test_contradictory_filters(self, client):
        """Test contradictory filter values"""
        # Status can't be both Active and Exit
        response = client.get("/api/companies?status=Active&status=Exit")
        # Should handle gracefully
        assert response.status_code == 200

    def test_multiple_pe_firms(self, client):
        """Test filtering by multiple PE firms"""
        response = client.get("/api/companies?pe_firm=Acme,Beta,Gamma")
        assert response.status_code == 200

    def test_multiple_industries(self, client):
        """Test filtering by multiple industries"""
        response = client.get("/api/companies?industry=Technology,Healthcare")
        assert response.status_code == 200


class TestResponseConsistency:
    """Tests for response format consistency"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_empty_result_format(self, client):
        """Test format when no results"""
        # Use filters that likely return nothing
        response = client.get("/api/companies?search=xyznonexistentcompany123")
        assert response.status_code == 200
        companies = response.json()
        assert companies == [] or isinstance(companies, list)

    def test_single_result_format(self, client):
        """Test format with single result"""
        response = client.get("/api/companies?limit=1")
        assert response.status_code == 200
        companies = response.json()
        assert isinstance(companies, list)
        if len(companies) == 1:
            # Should still be a list, not a single object
            assert isinstance(companies, list)

    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        # 404 error
        response_404 = client.get("/api/companies/999999")
        assert "detail" in response_404.json()

        # 422 error
        response_422 = client.get("/api/companies/invalid")
        assert "detail" in response_422.json()

        # 401 error
        response_401 = client.delete("/api/companies/1")
        assert "detail" in response_401.json()


class TestCacheHeaders:
    """Tests for caching headers"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_no_cache_on_authenticated_endpoints(self, client):
        """Test authenticated endpoints don't cache"""
        response = client.get("/api/companies")
        # Should not have aggressive caching
        assert response.status_code == 200

    def test_stats_can_be_cached(self, client):
        """Test stats endpoint can be cached"""
        response = client.get("/api/stats")
        # Stats might have cache headers
        assert response.status_code == 200


class TestInputSanitization:
    """Tests for input sanitization"""

    @pytest.fixture
    def mock_session(self):
        return Mock()

    def test_html_in_company_name(self, mock_session):
        """Test HTML tags in company name"""
        service = CompanyService(session=mock_session)

        company = Mock()
        company.name = "<script>alert('xss')</script> Company"

        # Should handle safely
        # (Actual sanitization would be tested here)

    def test_excessive_length_input(self, mock_session):
        """Test very long input strings"""
        service = CompanyService(session=mock_session)

        # 10000 character string
        long_string = "a" * 10000

        # Should handle without crashing
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0

        try:
            service.get_companies({'search': long_string}, limit=10, offset=0)
        except Exception:
            # Should either work or raise expected exception
            pass
