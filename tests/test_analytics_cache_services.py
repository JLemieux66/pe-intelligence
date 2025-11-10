"""
Comprehensive tests for AnalyticsService and CacheService
"""
import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from backend.services.analytics_service import AnalyticsService
from backend.services.cache_service import CacheService


class TestAnalyticsService:
    """Tests for AnalyticsService"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for analytics logs"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def service(self, temp_dir):
        """Create analytics service"""
        return AnalyticsService(log_dir=temp_dir)

    def test_log_api_call(self, service, temp_dir):
        """Test logging API call"""
        service.log_api_call(
            endpoint="/api/companies",
            duration_ms=123.45,
            status_code=200,
            user_id="test_user"
        )

        # Verify log file was created
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")
        assert os.path.exists(log_file)

        # Verify content
        with open(log_file, 'r') as f:
            content = f.read()
            entry = json.loads(content.strip())
            assert entry["endpoint"] == "/api/companies"
            assert entry["duration_ms"] == 123.45
            assert entry["status_code"] == 200
            assert entry["user_id"] == "test_user"

    def test_log_api_call_with_metadata(self, service, temp_dir):
        """Test logging with metadata"""
        metadata = {"query": "test", "limit": 10}
        service.log_api_call(
            endpoint="/api/search",
            duration_ms=50.0,
            status_code=200,
            metadata=metadata
        )

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            entry = json.loads(f.read().strip())
            assert entry["metadata"] == metadata

    def test_log_similar_companies_request(self, service, temp_dir):
        """Test logging similar companies request"""
        service.log_similar_companies_request(
            company_ids=[1, 2, 3],
            result_count=5,
            duration_ms=250.0,
            cache_hit=True
        )

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            entry = json.loads(f.read().strip())
            assert entry["endpoint"] == "similar_companies"
            assert entry["metadata"]["input_companies"] == 3
            assert entry["metadata"]["result_count"] == 5
            assert entry["metadata"]["cache_hit"] is True

    def test_get_usage_stats_empty(self, service):
        """Test getting usage stats with no data"""
        stats = service.get_usage_stats(days=7)

        assert stats["total_requests"] == 0
        assert stats["avg_response_time"] == 0
        assert stats["error_rate"] == 0

    def test_get_usage_stats_with_data(self, service, temp_dir):
        """Test getting usage stats with data"""
        # Create log entries
        service.log_api_call("/api/companies", 100.0, 200)
        service.log_api_call("/api/investments", 150.0, 200)
        service.log_api_call("/api/stats", 50.0, 200)
        service.log_api_call("/api/error", 100.0, 500)

        stats = service.get_usage_stats(days=1)

        assert stats["total_requests"] == 4
        assert stats["avg_response_time"] == 100.0  # (100+150+50+100)/4
        assert stats["error_rate"] == 0.25  # 1/4

    def test_log_file_creation_per_day(self, service, temp_dir):
        """Test that log files are created per day"""
        service.log_api_call("/api/test", 100.0, 200)

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        expected_file = f"api_calls_{date_str}.jsonl"

        files = os.listdir(temp_dir)
        assert expected_file in files

    def test_failed_log_silently(self, service):
        """Test that logging failures don't raise exceptions"""
        # Use invalid directory
        service.log_dir = "/invalid/path/that/doesnt/exist"

        # Should not raise exception
        service.log_api_call("/api/test", 100.0, 200)


class TestCacheService:
    """Tests for CacheService"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for cache"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def service(self, temp_dir):
        """Create cache service"""
        return CacheService(cache_dir=temp_dir, ttl_hours=1)

    def test_cache_key_generation(self, service):
        """Test cache key is generated consistently"""
        key1 = service._get_cache_key([1, 2, 3], 0.5, 10)
        key2 = service._get_cache_key([1, 2, 3], 0.5, 10)
        key3 = service._get_cache_key([3, 2, 1], 0.5, 10)  # Same IDs, different order

        assert key1 == key2  # Same parameters -> same key
        assert key1 == key3  # Order shouldn't matter (sorted)

    def test_cache_key_different_params(self, service):
        """Test different parameters generate different keys"""
        key1 = service._get_cache_key([1, 2, 3], 0.5, 10)
        key2 = service._get_cache_key([1, 2, 3], 0.6, 10)  # Different min_score
        key3 = service._get_cache_key([1, 2, 3], 0.5, 20)  # Different limit

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_cache_set_and_get(self, service):
        """Test setting and getting cache"""
        company_ids = [1, 2, 3]
        result = {"matches": [{"id": 4, "score": 0.8}]}

        service.set(company_ids, 0.5, 10, result)
        cached = service.get(company_ids, 0.5, 10)

        assert cached == result

    def test_cache_miss(self, service):
        """Test cache miss returns None"""
        cached = service.get([999], 0.5, 10)
        assert cached is None

    def test_cache_expiration(self, service, temp_dir):
        """Test cache expiration"""
        company_ids = [1, 2, 3]
        result = {"matches": []}

        service.set(company_ids, 0.5, 10, result)

        # Manually set file time to past
        cache_key = service._get_cache_key(company_ids, 0.5, 10)
        cache_file = os.path.join(temp_dir, f"{cache_key}.json")

        # Set file modification time to 2 hours ago
        two_hours_ago = (datetime.now() - timedelta(hours=2)).timestamp()
        os.utime(cache_file, (two_hours_ago, two_hours_ago))

        # Should return None (expired)
        cached = service.get(company_ids, 0.5, 10)
        assert cached is None

        # File should be removed
        assert not os.path.exists(cache_file)

    def test_clear_expired(self, service, temp_dir):
        """Test clearing expired cache entries"""
        # Create some cache entries
        service.set([1], 0.5, 10, {"test": 1})
        service.set([2], 0.5, 10, {"test": 2})

        # Make one expired
        cache_key = service._get_cache_key([1], 0.5, 10)
        cache_file = os.path.join(temp_dir, f"{cache_key}.json")
        two_hours_ago = (datetime.now() - timedelta(hours=2)).timestamp()
        os.utime(cache_file, (two_hours_ago, two_hours_ago))

        # Clear expired
        cleared = service.clear_expired()

        assert cleared == 1

        # Verify only expired one was removed
        assert not os.path.exists(cache_file)
        cache_key2 = service._get_cache_key([2], 0.5, 10)
        cache_file2 = os.path.join(temp_dir, f"{cache_key2}.json")
        assert os.path.exists(cache_file2)

    def test_cache_invalid_json_returns_none(self, service, temp_dir):
        """Test that invalid JSON in cache returns None"""
        company_ids = [1, 2, 3]

        # Manually write invalid JSON
        cache_key = service._get_cache_key(company_ids, 0.5, 10)
        cache_file = os.path.join(temp_dir, f"{cache_key}.json")

        with open(cache_file, 'w') as f:
            f.write("invalid json{")

        # Should return None
        cached = service.get(company_ids, 0.5, 10)
        assert cached is None

    def test_cache_set_failure_silent(self, service):
        """Test that cache set failures are silent"""
        # Use invalid directory
        service.cache_dir = "/invalid/path"

        # Should not raise exception
        service.set([1], 0.5, 10, {"test": 1})

    def test_cache_handles_complex_results(self, service):
        """Test caching complex nested structures"""
        complex_result = {
            "matches": [
                {
                    "id": 1,
                    "name": "Company A",
                    "score": 0.95,
                    "metadata": {"industry": "Tech", "employees": 500}
                }
            ],
            "total": 100,
            "query_time_ms": 123.45
        }

        service.set([1, 2], 0.7, 20, complex_result)
        cached = service.get([1, 2], 0.7, 20)

        assert cached == complex_result
