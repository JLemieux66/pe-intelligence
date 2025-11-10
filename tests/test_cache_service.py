"""
Tests for Cache Service
"""
import pytest
import json
import os
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
from backend.services.cache_service import CacheService


class TestCacheService:
    """Test CacheService class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for cache"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def service(self, temp_dir):
        """Create cache service instance"""
        return CacheService(cache_dir=temp_dir, ttl_hours=24)

    def test_init_creates_directory(self, temp_dir):
        """Test that initialization creates cache directory"""
        cache_dir = os.path.join(temp_dir, "new_cache")
        service = CacheService(cache_dir=cache_dir)

        assert os.path.exists(cache_dir)
        assert service.cache_dir == cache_dir
        assert service.ttl_hours == 24

    def test_init_custom_ttl(self, temp_dir):
        """Test initialization with custom TTL"""
        service = CacheService(cache_dir=temp_dir, ttl_hours=48)

        assert service.ttl_hours == 48

    def test_get_cache_key_deterministic(self, service):
        """Test that cache key generation is deterministic"""
        key1 = service._get_cache_key([1, 2, 3], 0.5, 10)
        key2 = service._get_cache_key([1, 2, 3], 0.5, 10)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length

    def test_get_cache_key_order_independent(self, service):
        """Test that cache key is independent of input order"""
        key1 = service._get_cache_key([1, 2, 3], 0.5, 10)
        key2 = service._get_cache_key([3, 2, 1], 0.5, 10)

        assert key1 == key2

    def test_get_cache_key_different_params(self, service):
        """Test that different parameters produce different keys"""
        key1 = service._get_cache_key([1, 2], 0.5, 10)
        key2 = service._get_cache_key([1, 2], 0.6, 10)
        key3 = service._get_cache_key([1, 2], 0.5, 20)

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_set_and_get_cache(self, service):
        """Test setting and getting cache"""
        company_ids = [1, 2, 3]
        result = {"matches": [{"id": 4, "score": 0.8}]}

        service.set(company_ids, 0.5, 10, result)
        cached = service.get(company_ids, 0.5, 10)

        assert cached is not None
        assert cached == result

    def test_get_cache_miss(self, service):
        """Test getting non-existent cache"""
        cached = service.get([1, 2, 3], 0.5, 10)

        assert cached is None

    def test_get_cache_expired(self, service):
        """Test getting expired cache"""
        # Use short TTL
        short_ttl_service = CacheService(cache_dir=service.cache_dir, ttl_hours=0.0001)

        company_ids = [1, 2, 3]
        result = {"matches": []}

        short_ttl_service.set(company_ids, 0.5, 10, result)

        # Wait for cache to expire (slightly more than 0.0001 hours = 0.36 seconds)
        time.sleep(0.5)

        cached = short_ttl_service.get(company_ids, 0.5, 10)

        assert cached is None

    def test_get_cache_invalid_json(self, service, temp_dir):
        """Test handling of invalid JSON in cache file"""
        company_ids = [1, 2, 3]
        cache_key = service._get_cache_key(company_ids, 0.5, 10)
        cache_file = os.path.join(temp_dir, f"{cache_key}.json")

        # Write invalid JSON
        with open(cache_file, 'w') as f:
            f.write("invalid json {")

        cached = service.get(company_ids, 0.5, 10)

        assert cached is None

    def test_set_cache_io_error(self, service):
        """Test that set fails silently on IO error"""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            # Should not raise exception
            service.set([1, 2, 3], 0.5, 10, {"matches": []})

    def test_get_cache_io_error(self, service, temp_dir):
        """Test handling of IO error when reading cache"""
        company_ids = [1, 2, 3]
        cache_key = service._get_cache_key(company_ids, 0.5, 10)
        cache_file = os.path.join(temp_dir, f"{cache_key}.json")

        # Create cache file
        with open(cache_file, 'w') as f:
            json.dump({"matches": []}, f)

        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("Read error")):
            cached = service.get(company_ids, 0.5, 10)
            assert cached is None

    def test_clear_expired_removes_old_entries(self, service, temp_dir):
        """Test clearing expired cache entries"""
        # Create cache with short TTL
        short_ttl_service = CacheService(cache_dir=temp_dir, ttl_hours=0.0001)

        # Add some entries
        short_ttl_service.set([1, 2], 0.5, 10, {"matches": []})
        short_ttl_service.set([3, 4], 0.5, 10, {"matches": []})

        # Wait for expiration
        time.sleep(0.5)

        # Clear expired
        cleared = short_ttl_service.clear_expired()

        assert cleared == 2

    def test_clear_expired_keeps_fresh_entries(self, service):
        """Test that clear_expired keeps non-expired entries"""
        # Add entries
        service.set([1, 2], 0.5, 10, {"matches": []})
        service.set([3, 4], 0.5, 10, {"matches": []})

        # Clear expired (nothing should be cleared)
        cleared = service.clear_expired()

        assert cleared == 0

        # Verify entries still exist
        assert service.get([1, 2], 0.5, 10) is not None
        assert service.get([3, 4], 0.5, 10) is not None

    def test_clear_expired_empty_cache(self, service):
        """Test clearing expired on empty cache"""
        cleared = service.clear_expired()

        assert cleared == 0

    def test_clear_expired_non_json_files(self, service, temp_dir):
        """Test that clear_expired only processes .json files"""
        # Create a non-JSON file
        other_file = os.path.join(temp_dir, "other.txt")
        with open(other_file, 'w') as f:
            f.write("test")

        cleared = service.clear_expired()

        # Should not delete non-JSON file
        assert cleared == 0
        assert os.path.exists(other_file)

    def test_global_cache_instance(self):
        """Test that global cache instance is available"""
        from backend.services.cache_service import cache_service

        assert cache_service is not None
        assert isinstance(cache_service, CacheService)

    def test_set_with_complex_result(self, service):
        """Test caching complex result with datetime objects"""
        company_ids = [1, 2, 3]
        result = {
            "matches": [
                {"id": 4, "score": 0.8, "timestamp": datetime.now()}
            ]
        }

        # Should not raise exception due to default=str
        service.set(company_ids, 0.5, 10, result)

        # Verify it was cached (datetime will be converted to string)
        cached = service.get(company_ids, 0.5, 10)
        assert cached is not None
        assert "matches" in cached

    def test_cache_with_single_company(self, service):
        """Test caching with single company ID"""
        company_ids = [1]
        result = {"matches": [{"id": 2, "score": 0.9}]}

        service.set(company_ids, 0.7, 5, result)
        cached = service.get(company_ids, 0.7, 5)

        assert cached == result

    def test_cache_with_many_companies(self, service):
        """Test caching with many company IDs"""
        company_ids = list(range(1, 51))  # 50 companies
        result = {"matches": []}

        service.set(company_ids, 0.5, 100, result)
        cached = service.get(company_ids, 0.5, 100)

        assert cached == result

    def test_cache_key_with_float_precision(self, service):
        """Test cache key generation with different float precisions"""
        key1 = service._get_cache_key([1, 2], 0.5, 10)
        key2 = service._get_cache_key([1, 2], 0.50, 10)
        key3 = service._get_cache_key([1, 2], 0.500, 10)

        # Should all be the same
        assert key1 == key2 == key3
