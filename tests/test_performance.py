"""
Performance Tests
Tests response times, load handling, and performance regression
"""
import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_health_endpoint_response_time(self, client):
        """Health endpoint should respond in < 100ms"""
        start = time.time()
        response = client.get("/health")
        duration = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert duration < 100, f"Health check took {duration:.2f}ms, should be < 100ms"

    def test_stats_endpoint_response_time(self, client):
        """Stats endpoint should respond in < 2 seconds"""
        start = time.time()
        response = client.get("/api/stats")
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration < 2000, f"Stats took {duration:.2f}ms, should be < 2000ms"

    def test_companies_list_response_time(self, client):
        """Companies list should respond in < 3 seconds"""
        start = time.time()
        response = client.get("/api/companies?limit=100")
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration < 3000, f"Companies list took {duration:.2f}ms, should be < 3000ms"

    def test_companies_with_filters_response_time(self, client):
        """Filtered companies should respond in < 3 seconds"""
        start = time.time()
        response = client.get("/api/companies?status=Active&limit=100")
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration < 3000, f"Filtered companies took {duration:.2f}ms"

    def test_pagination_performance(self, client):
        """Test pagination doesn't degrade with offset"""
        # First page
        start = time.time()
        response1 = client.get("/api/companies?limit=10&offset=0")
        duration1 = (time.time() - start) * 1000

        # Later page
        start = time.time()
        response2 = client.get("/api/companies?limit=10&offset=100")
        duration2 = (time.time() - start) * 1000

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Later pages shouldn't be more than 50% slower
        assert duration2 < duration1 * 1.5, \
            f"Pagination degraded: {duration1:.2f}ms -> {duration2:.2f}ms"

    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import concurrent.futures

        def make_request():
            response = client.get("/api/companies?limit=10")
            return response.status_code

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(status == 200 for status in results)

    def test_large_limit_performance(self, client):
        """Test performance with large limits"""
        start = time.time()
        response = client.get("/api/companies?limit=1000")
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        # Large limits should still respond in < 5 seconds
        assert duration < 5000, f"Large limit took {duration:.2f}ms"

    def test_search_query_performance(self, client):
        """Test search query performance"""
        start = time.time()
        response = client.get("/api/companies?search=test&limit=100")
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration < 3000, f"Search took {duration:.2f}ms"

    def test_metadata_endpoint_performance(self, client):
        """Metadata endpoints should be fast"""
        endpoints = [
            "/api/metadata/pe-firms",
            "/api/metadata/industries",
            "/api/metadata/countries"
        ]

        for endpoint in endpoints:
            start = time.time()
            response = client.get(endpoint)
            duration = (time.time() - start) * 1000

            assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist
            if response.status_code == 200:
                assert duration < 1000, f"{endpoint} took {duration:.2f}ms"


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database queries"""

    @pytest.fixture
    def db_session(self):
        """Database session"""
        from src.models.database_models_v2 import get_session
        session = get_session()
        yield session
        session.close()

    def test_company_query_performance(self, db_session):
        """Test basic company query performance"""
        from src.models.database_models_v2 import Company

        start = time.time()
        companies = db_session.query(Company).limit(100).all()
        duration = (time.time() - start) * 1000

        assert duration < 1000, f"Company query took {duration:.2f}ms"

    def test_investment_query_performance(self, db_session):
        """Test investment query performance"""
        from src.models.database_models_v2 import CompanyPEInvestment

        start = time.time()
        investments = db_session.query(CompanyPEInvestment).limit(100).all()
        duration = (time.time() - start) * 1000

        assert duration < 1000, f"Investment query took {duration:.2f}ms"

    def test_join_query_performance(self, db_session):
        """Test join query performance"""
        from src.models.database_models_v2 import Company, CompanyPEInvestment, PEFirm

        start = time.time()
        results = db_session.query(Company, CompanyPEInvestment, PEFirm).join(
            CompanyPEInvestment
        ).join(PEFirm).limit(100).all()
        duration = (time.time() - start) * 1000

        assert duration < 2000, f"Join query took {duration:.2f}ms"


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage tests"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_large_response_memory(self, client):
        """Test memory usage with large responses"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Make request for large dataset
        response = client.get("/api/companies?limit=1000")

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        assert response.status_code == 200
        # Memory increase should be reasonable (< 50MB for this request)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB"

    def test_repeated_requests_no_memory_leak(self, client):
        """Test for memory leaks with repeated requests"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Baseline
        for _ in range(10):
            client.get("/api/companies?limit=10")

        memory_baseline = process.memory_info().rss / 1024 / 1024

        # Make many more requests
        for _ in range(100):
            client.get("/api/companies?limit=10")

        memory_after = process.memory_info().rss / 1024 / 1024
        memory_increase = memory_after - memory_baseline

        # Should not increase significantly (< 20MB)
        assert memory_increase < 20, f"Possible memory leak: {memory_increase:.2f}MB increase"


@pytest.mark.performance
@pytest.mark.slow
class TestLoadTesting:
    """Load testing scenarios"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_sustained_load(self, client):
        """Test sustained load over time"""
        import concurrent.futures

        def make_requests(num_requests):
            for _ in range(num_requests):
                response = client.get("/api/companies?limit=10")
                assert response.status_code == 200

        # Simulate 5 users making 20 requests each
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_requests, 20) for _ in range(5)]
            for future in futures:
                future.result()  # Will raise if any failed

    def test_spike_load(self, client):
        """Test handling spike in traffic"""
        import concurrent.futures

        def make_request():
            return client.get("/api/companies?limit=10")

        # Sudden spike of 50 concurrent requests
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in futures]

        duration = time.time() - start

        # All should succeed
        assert all(r.status_code == 200 for r in results)

        # Should complete within reasonable time (< 30 seconds)
        assert duration < 30, f"Spike load took {duration:.2f}s"
