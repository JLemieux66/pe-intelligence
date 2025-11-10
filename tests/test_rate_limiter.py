"""
Tests for Rate Limiter Middleware
"""
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, FastAPI
from starlette.responses import Response, JSONResponse

from backend.middleware.rate_limiter import (
    RateLimitRule,
    ClientRecord,
    RateLimiter,
    RateLimitMiddleware,
    create_rate_limiter
)


class TestRateLimitRule:
    """Test RateLimitRule dataclass"""

    def test_create_rule_basic(self):
        """Test creating basic rate limit rule"""
        rule = RateLimitRule(requests=100, window=60)

        assert rule.requests == 100
        assert rule.window == 60
        assert rule.block_duration == 300  # Default

    def test_create_rule_custom_block_duration(self):
        """Test creating rule with custom block duration"""
        rule = RateLimitRule(requests=50, window=30, block_duration=600)

        assert rule.requests == 50
        assert rule.window == 30
        assert rule.block_duration == 600


class TestClientRecord:
    """Test ClientRecord dataclass"""

    def test_create_client_record_default(self):
        """Test creating client record with defaults"""
        record = ClientRecord()

        assert record.requests == []
        assert record.blocked_until == 0

    def test_create_client_record_with_data(self):
        """Test creating client record with data"""
        record = ClientRecord(requests=[1.0, 2.0, 3.0], blocked_until=100.0)

        assert len(record.requests) == 3
        assert record.blocked_until == 100.0


class TestRateLimiter:
    """Test RateLimiter class"""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter instance"""
        return RateLimiter()

    def test_init_default(self):
        """Test initialization with default rule"""
        limiter = RateLimiter()

        assert limiter.default_rule is not None
        assert limiter.default_rule.requests == 100
        assert limiter.default_rule.window == 60
        assert isinstance(limiter.clients, dict)
        assert isinstance(limiter.rules, dict)

    def test_init_custom_rule(self):
        """Test initialization with custom rule"""
        custom_rule = RateLimitRule(requests=50, window=30)
        limiter = RateLimiter(default_rule=custom_rule)

        assert limiter.default_rule.requests == 50
        assert limiter.default_rule.window == 30

    def test_add_rule(self, limiter):
        """Test adding custom rule for path"""
        rule = RateLimitRule(requests=10, window=60)
        limiter.add_rule("/api/auth/login", rule)

        assert "/api/auth/login" in limiter.rules
        assert limiter.rules["/api/auth/login"] == rule

    def test_get_client_id_with_ip(self, limiter):
        """Test getting client ID from IP address"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Mozilla/5.0"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        client_id = limiter.get_client_id(request)

        assert client_id is not None
        assert isinstance(client_id, str)
        assert len(client_id) == 32  # MD5 hash

    def test_get_client_id_with_forwarded_for(self, limiter):
        """Test getting client ID from X-Forwarded-For header"""
        request = Mock(spec=Request)
        request.headers = {
            "X-Forwarded-For": "203.0.113.1, 198.51.100.1",
            "User-Agent": "Mozilla/5.0"
        }
        request.client = Mock()
        request.client.host = "192.168.1.1"

        client_id = limiter.get_client_id(request)

        assert client_id is not None
        # Should use first IP from X-Forwarded-For
        assert isinstance(client_id, str)

    def test_get_client_id_no_client(self, limiter):
        """Test getting client ID when request.client is None"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Mozilla/5.0"}
        request.client = None

        client_id = limiter.get_client_id(request)

        assert client_id is not None
        assert isinstance(client_id, str)

    def test_get_client_id_deterministic(self, limiter):
        """Test that client ID is deterministic"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Mozilla/5.0"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        client_id1 = limiter.get_client_id(request)
        client_id2 = limiter.get_client_id(request)

        assert client_id1 == client_id2

    def test_get_rule_for_path_exact_match(self, limiter):
        """Test getting rule with exact path match"""
        custom_rule = RateLimitRule(requests=5, window=60)
        limiter.add_rule("/api/auth/login", custom_rule)

        rule = limiter.get_rule_for_path("/api/auth/login")

        assert rule == custom_rule

    def test_get_rule_for_path_pattern_match(self, limiter):
        """Test getting rule with pattern match"""
        custom_rule = RateLimitRule(requests=50, window=60)
        limiter.add_rule("/api/companies", custom_rule)

        rule = limiter.get_rule_for_path("/api/companies/123")

        assert rule == custom_rule

    def test_get_rule_for_path_default(self, limiter):
        """Test getting default rule for unknown path"""
        rule = limiter.get_rule_for_path("/api/unknown")

        assert rule == limiter.default_rule

    def test_is_allowed_first_request(self, limiter):
        """Test that first request is allowed"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        is_allowed, info = limiter.is_allowed(request)

        assert is_allowed is True
        assert "X-RateLimit-Limit" in info
        assert info["X-RateLimit-Limit"] == "100"

    def test_is_allowed_multiple_requests(self, limiter):
        """Test multiple requests under limit"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # Make 5 requests
        for i in range(5):
            is_allowed, info = limiter.is_allowed(request)
            assert is_allowed is True

    def test_is_allowed_rate_limit_exceeded(self):
        """Test rate limit exceeded"""
        # Create limiter with very strict limit
        rule = RateLimitRule(requests=2, window=60, block_duration=10)
        limiter = RateLimiter(default_rule=rule)

        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # Make requests up to limit
        limiter.is_allowed(request)
        limiter.is_allowed(request)

        # Third request should be blocked
        is_allowed, info = limiter.is_allowed(request)

        assert is_allowed is False
        assert "error" in info
        assert info["error"] == "rate_limit_exceeded"
        assert "retry_after" in info

    def test_is_allowed_blocked_client(self):
        """Test that blocked client remains blocked"""
        rule = RateLimitRule(requests=1, window=60, block_duration=10)
        limiter = RateLimiter(default_rule=rule)

        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # Exceed limit
        limiter.is_allowed(request)
        limiter.is_allowed(request)

        # Should still be blocked
        is_allowed, info = limiter.is_allowed(request)

        assert is_allowed is False
        assert "retry_after" in info

    def test_is_allowed_cleanup_old_requests(self):
        """Test that old requests are cleaned up"""
        rule = RateLimitRule(requests=2, window=1)  # 1 second window
        limiter = RateLimiter(default_rule=rule)

        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # Make 2 requests
        limiter.is_allowed(request)
        limiter.is_allowed(request)

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        is_allowed, info = limiter.is_allowed(request)
        assert is_allowed is True

    def test_cleanup_old_records(self, limiter):
        """Test cleanup of old client records"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # Create request
        limiter.is_allowed(request)

        # Manually set old timestamp
        client_id = limiter.get_client_id(request)
        limiter.clients[client_id].requests = [time.time() - 1000]

        # Run cleanup
        limiter._cleanup_old_records()

        # Client should be removed
        assert client_id not in limiter.clients

    def test_cleanup_preserves_active_clients(self, limiter):
        """Test that cleanup preserves active clients"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # Create request
        limiter.is_allowed(request)

        client_id = limiter.get_client_id(request)

        # Run cleanup
        limiter._cleanup_old_records()

        # Client should still exist
        assert client_id in limiter.clients

    def test_cleanup_preserves_blocked_clients(self, limiter):
        """Test that cleanup preserves blocked clients"""
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        client_id = limiter.get_client_id(request)

        # Set client as blocked
        limiter.clients[client_id].blocked_until = time.time() + 100
        limiter.clients[client_id].requests = []

        # Run cleanup
        limiter._cleanup_old_records()

        # Blocked client should still exist
        assert client_id in limiter.clients

    def test_periodic_cleanup_triggered(self, limiter):
        """Test that cleanup is triggered periodically"""
        # Set last cleanup to old time
        limiter.last_cleanup = time.time() - 400

        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/api/test"

        # This should trigger cleanup
        with patch.object(limiter, '_cleanup_old_records') as mock_cleanup:
            limiter.is_allowed(request)
            mock_cleanup.assert_called_once()


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app"""
        return FastAPI()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance"""
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_dispatch_health_check_bypassed(self, middleware):
        """Test that health check bypasses rate limiting"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/health"

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_docs_bypassed(self, middleware):
        """Test that docs bypass rate limiting"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/docs"

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_allowed_request(self, middleware):
        """Test dispatching allowed request"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        call_next.assert_called_once_with(request)
        # Should have rate limit headers
        assert "X-RateLimit-Limit" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_exceeded(self):
        """Test dispatching request that exceeds rate limit"""
        app = FastAPI()
        strict_limiter = RateLimiter(
            default_rule=RateLimitRule(requests=1, window=60, block_duration=10)
        )
        middleware = RateLimitMiddleware(app, rate_limiter=strict_limiter)

        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        call_next = AsyncMock(return_value=Response())

        # First request should succeed
        await middleware.dispatch(request, call_next)

        # Second request should be blocked
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_adds_rate_limit_headers(self, middleware):
        """Test that rate limit headers are added to response"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_middleware_default_rules_configured(self, middleware):
        """Test that middleware configures default rules"""
        # Check login endpoint has strict rule
        rule = middleware.rate_limiter.get_rule_for_path("/api/auth/login")
        assert rule.requests == 5
        assert rule.window == 60
        assert rule.block_duration == 600

        # Check companies endpoint has custom rule
        rule = middleware.rate_limiter.get_rule_for_path("/api/companies")
        assert rule.requests == 50


class TestCreateRateLimiter:
    """Test create_rate_limiter utility function"""

    def test_create_rate_limiter_default(self):
        """Test creating rate limiter with defaults"""
        limiter = create_rate_limiter()

        assert limiter.default_rule.requests == 100
        assert limiter.default_rule.window == 60
        # Should have strict auth rule
        assert "/api/auth/login" in limiter.rules

    def test_create_rate_limiter_custom_defaults(self):
        """Test creating rate limiter with custom defaults"""
        limiter = create_rate_limiter(default_requests=50, default_window=30)

        assert limiter.default_rule.requests == 50
        assert limiter.default_rule.window == 30

    def test_create_rate_limiter_no_strict_auth(self):
        """Test creating rate limiter without strict auth"""
        limiter = create_rate_limiter(strict_auth=False)

        assert "/api/auth/login" not in limiter.rules

    def test_create_rate_limiter_strict_auth(self):
        """Test that strict auth creates login rule"""
        limiter = create_rate_limiter(strict_auth=True)

        assert "/api/auth/login" in limiter.rules
        rule = limiter.rules["/api/auth/login"]
        assert rule.requests == 5
        assert rule.window == 60
        assert rule.block_duration == 600
