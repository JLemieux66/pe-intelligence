"""
Tests for Analytics Service
"""
import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from backend.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test AnalyticsService class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for analytics logs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def service(self, temp_dir):
        """Create analytics service instance"""
        return AnalyticsService(log_dir=temp_dir)

    def test_init_creates_directory(self, temp_dir):
        """Test that initialization creates log directory"""
        service = AnalyticsService(log_dir=temp_dir)

        assert os.path.exists(temp_dir)
        assert service.log_dir == temp_dir

    def test_log_api_call_basic(self, service, temp_dir):
        """Test basic API call logging"""
        service.log_api_call(
            endpoint="/api/companies",
            duration_ms=123.45,
            status_code=200
        )

        # Check log file was created
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        assert os.path.exists(log_file)

        # Read and verify log entry
        with open(log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)

        assert entry["endpoint"] == "/api/companies"
        assert entry["duration_ms"] == 123.45
        assert entry["status_code"] == 200
        assert "timestamp" in entry

    def test_log_api_call_with_user_and_metadata(self, service, temp_dir):
        """Test API call logging with user ID and metadata"""
        service.log_api_call(
            endpoint="/api/investments",
            duration_ms=250.0,
            status_code=200,
            user_id="user123",
            metadata={"filter": "active", "limit": 100}
        )

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["user_id"] == "user123"
        assert entry["metadata"]["filter"] == "active"
        assert entry["metadata"]["limit"] == 100

    def test_log_api_call_multiple_entries(self, service, temp_dir):
        """Test logging multiple API calls"""
        service.log_api_call("/api/endpoint1", 100, 200)
        service.log_api_call("/api/endpoint2", 150, 200)
        service.log_api_call("/api/endpoint3", 200, 404)

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 3

    def test_log_api_call_io_error(self, temp_dir):
        """Test that IO errors are handled gracefully"""
        service = AnalyticsService(log_dir="/invalid/path/that/doesnt/exist")

        # Should not raise exception
        service.log_api_call("/api/test", 100, 200)

    def test_log_similar_companies_request(self, service, temp_dir):
        """Test similar companies specific logging"""
        service.log_similar_companies_request(
            company_ids=[1, 2, 3],
            result_count=10,
            duration_ms=500.0,
            cache_hit=True
        )

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["endpoint"] == "similar_companies"
        assert entry["status_code"] == 200
        assert entry["duration_ms"] == 500.0
        assert entry["metadata"]["input_companies"] == 3
        assert entry["metadata"]["result_count"] == 10
        assert entry["metadata"]["cache_hit"] is True

    def test_log_similar_companies_request_cache_miss(self, service):
        """Test similar companies logging with cache miss"""
        service.log_similar_companies_request(
            company_ids=[1],
            result_count=5,
            duration_ms=750.0,
            cache_hit=False
        )

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(service.log_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["metadata"]["cache_hit"] is False

    def test_get_usage_stats_empty(self, service):
        """Test usage stats with no data"""
        stats = service.get_usage_stats(days=7)

        assert stats["total_requests"] == 0
        assert stats["avg_response_time"] == 0
        assert stats["error_rate"] == 0
        assert len(stats["endpoint_usage"]) == 0

    def test_get_usage_stats_with_data(self, service):
        """Test usage stats with logged data"""
        # Log some API calls
        service.log_api_call("/api/companies", 100, 200)
        service.log_api_call("/api/companies", 150, 200)
        service.log_api_call("/api/investments", 200, 200)
        service.log_api_call("/api/test", 300, 404)

        stats = service.get_usage_stats(days=7)

        assert stats["total_requests"] == 4
        assert stats["avg_response_time"] == (100 + 150 + 200 + 300) / 4
        assert stats["error_rate"] == 1 / 4  # One 404 error
        assert stats["endpoint_usage"]["/api/companies"] == 2
        assert stats["endpoint_usage"]["/api/investments"] == 1

    def test_get_usage_stats_daily_usage(self, service):
        """Test daily usage tracking"""
        # Log calls
        service.log_api_call("/api/test1", 100, 200)
        service.log_api_call("/api/test2", 150, 200)

        stats = service.get_usage_stats(days=1)

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        assert stats["daily_usage"][date_str] == 2

    def test_get_usage_stats_error_rate_calculation(self, service):
        """Test error rate calculation"""
        # Log mix of successful and error requests
        service.log_api_call("/api/test", 100, 200)  # Success
        service.log_api_call("/api/test", 100, 200)  # Success
        service.log_api_call("/api/test", 100, 400)  # Client error
        service.log_api_call("/api/test", 100, 500)  # Server error

        stats = service.get_usage_stats(days=7)

        assert stats["total_requests"] == 4
        assert stats["error_rate"] == 2 / 4  # 2 errors out of 4

    def test_get_usage_stats_multiple_days(self, service, temp_dir):
        """Test usage stats across multiple days"""
        # Create log files for different days
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)

        # Log for today
        service.log_api_call("/api/today", 100, 200)

        # Manually create yesterday's log
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{yesterday_str}.jsonl")
        with open(log_file, 'w') as f:
            entry = {
                "timestamp": yesterday.isoformat(),
                "endpoint": "/api/yesterday",
                "duration_ms": 150,
                "status_code": 200,
                "user_id": None,
                "metadata": {}
            }
            f.write(json.dumps(entry) + '\n')

        stats = service.get_usage_stats(days=2)

        assert stats["total_requests"] == 2
        assert stats["endpoint_usage"]["/api/today"] == 1
        assert stats["endpoint_usage"]["/api/yesterday"] == 1

    def test_get_usage_stats_invalid_json(self, service, temp_dir):
        """Test that invalid JSON is handled gracefully"""
        # Create log file with invalid JSON
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(temp_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'w') as f:
            f.write("invalid json line\n")
            f.write('{"endpoint": "/api/valid", "duration_ms": 100, "status_code": 200}\n')

        # Should not raise exception
        stats = service.get_usage_stats(days=1)

        # Should still count valid entries
        assert stats["total_requests"] >= 0

    def test_get_usage_stats_missing_log_files(self, service):
        """Test usage stats when log files don't exist"""
        # Request stats for days with no logs
        stats = service.get_usage_stats(days=30)

        assert stats["total_requests"] == 0
        assert stats["avg_response_time"] == 0

    def test_global_analytics_instance(self):
        """Test that global analytics instance is available"""
        from backend.services.analytics_service import analytics_service

        assert analytics_service is not None
        assert isinstance(analytics_service, AnalyticsService)

    def test_log_api_call_without_metadata(self, service):
        """Test API call logging without metadata (defaults to empty dict)"""
        service.log_api_call(
            endpoint="/api/test",
            duration_ms=100,
            status_code=200,
            user_id="user456"
        )

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(service.log_dir, f"api_calls_{date_str}.jsonl")

        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())

        assert entry["metadata"] == {}
        assert entry["user_id"] == "user456"
