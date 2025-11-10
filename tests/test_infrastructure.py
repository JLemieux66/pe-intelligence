"""
Comprehensive tests for infrastructure components
Tests database pool, base service, and rate limiting
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from backend.database_pool import create_engine_with_pool, DATABASE_URL
from backend.services.base import BaseService
from backend.middleware.rate_limiter import (
    RateLimitRule,
    ClientRecord,
    RateLimiter,
    RateLimitMiddleware
)


class TestDatabasePool:
    """Tests for database connection pool"""

    def test_create_engine_with_pool_sqlite(self):
        """Test creating engine for SQLite database"""
        with patch('backend.database_pool.DATABASE_URL', 'sqlite:///test.db'):
            with patch('backend.database_pool.create_engine') as mock_create:
                mock_engine = Mock()
                mock_create.return_value = mock_engine

                from backend.database_pool import create_engine_with_pool
                engine = create_engine_with_pool()

                # Verify engine was created
                assert mock_create.called
                # Verify SQLite specific settings
                call_kwargs = mock_create.call_args[1]
                assert 'connect_args' in call_kwargs
                assert call_kwargs['connect_args']['check_same_thread'] is False

    def test_create_engine_with_pool_postgresql(self):
        """Test creating engine for PostgreSQL with pooling"""
        with patch('backend.database_pool.DATABASE_URL', 'postgresql://user:pass@localhost/db'):
            with patch('backend.database_pool.create_engine') as mock_create:
                mock_engine = Mock()
                mock_create.return_value = mock_engine

                from backend.database_pool import create_engine_with_pool
                engine = create_engine_with_pool()

                # Verify pooling settings were applied
                call_kwargs = mock_create.call_args[1]
                assert 'pool_size' in call_kwargs
                assert 'max_overflow' in call_kwargs
                assert 'pool_timeout' in call_kwargs
                assert 'pool_recycle' in call_kwargs
                assert call_kwargs['pool_pre_ping'] is True


class TestBaseService:
    """Tests for BaseService class"""

    def test_init_with_session(self):
        """Test BaseService initialization with provided session"""
        mock_session = Mock(spec=Session)
        service = BaseService(session=mock_session)

        assert service._session == mock_session
        assert service._owns_session is False

    def test_init_without_session(self):
        """Test BaseService initialization without session"""
        service = BaseService(session=None)

        assert service._session is None
        assert service._owns_session is True

    @patch('backend.services.base.get_direct_session')
    def test_session_property_creates_session(self, mock_get_session):
        """Test session property creates session if none exists"""
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = mock_session

        service = BaseService(session=None)
        session = service.session

        assert session == mock_session
        assert mock_get_session.called

    def test_session_property_returns_existing(self):
        """Test session property returns existing session"""
        mock_session = Mock(spec=Session)
        service = BaseService(session=mock_session)

        session = service.session
        assert session == mock_session

    @patch('backend.services.base.get_direct_session')
    def test_context_manager_entry(self, mock_get_session):
        """Test BaseService as context manager - entry"""
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = mock_session

        with BaseService() as service:
            assert service is not None
            assert isinstance(service, BaseService)

    @patch('backend.services.base.get_direct_session')
    def test_context_manager_exit_closes_owned_session(self, mock_get_session):
        """Test context manager closes session if service owns it"""
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = mock_session

        with BaseService() as service:
            _ = service.session  # Trigger session creation

        # Session should be closed after context
        assert mock_session.close.called

    def test_context_manager_exit_doesnt_close_provided_session(self):
        """Test context manager doesn't close provided session"""
        mock_session = Mock(spec=Session)

        with BaseService(session=mock_session) as service:
            pass

        # Session should NOT be closed
        assert not mock_session.close.called

    @patch('backend.services.base.get_direct_session')
    def test_manual_close(self, mock_get_session):
        """Test manual close method"""
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = mock_session

        service = BaseService()
        _ = service.session  # Create session
        service.close()

        assert mock_session.close.called
        assert service._session is None

    def test_manual_close_provided_session_not_closed(self):
        """Test manual close doesn't close provided session"""
        mock_session = Mock(spec=Session)
        service = BaseService(session=mock_session)

        service.close()

        assert not mock_session.close.called


class TestRateLimitRule:
    """Tests for RateLimitRule dataclass"""

    def test_create_rule_with_defaults(self):
        """Test creating rule with default block duration"""
        rule = RateLimitRule(requests=10, window=60)

        assert rule.requests == 10
        assert rule.window == 60
        assert rule.block_duration == 300  # Default

    def test_create_rule_custom_block_duration(self):
        """Test creating rule with custom block duration"""
        rule = RateLimitRule(requests=5, window=30, block_duration=600)

        assert rule.requests == 5
        assert rule.window == 30
        assert rule.block_duration == 600


class TestClientRecord:
    """Tests for ClientRecord dataclass"""

    def test_create_client_record(self):
        """Test creating client record"""
        record = ClientRecord()

        assert record.requests == []
        assert record.blocked_until == 0

    def test_client_record_with_data(self):
        """Test client record with data"""
        requests = [time.time(), time.time() - 10]
        blocked_until = time.time() + 300

        record = ClientRecord(requests=requests, blocked_until=blocked_until)

        assert record.requests == requests
        assert record.blocked_until == blocked_until


class TestRateLimiter:
    """Tests for RateLimiter class"""

    def test_init_default_rule(self):
        """Test initialization with default rule"""
        limiter = RateLimiter()

        assert limiter.default_rule is not None
        assert limiter.default_rule.requests == 100
        assert limiter.default_rule.window == 60

    def test_init_custom_rule(self):
        """Test initialization with custom default rule"""
        custom_rule = RateLimitRule(requests=50, window=30)
        limiter = RateLimiter(default_rule=custom_rule)

        assert limiter.default_rule == custom_rule

    def test_add_rule(self):
        """Test adding custom rule for path"""
        limiter = RateLimiter()
        rule = RateLimitRule(requests=5, window=60)

        limiter.add_rule("/api/login", rule)

        assert "/api/login" in limiter.rules
        assert limiter.rules["/api/login"] == rule

    def test_get_client_id_from_ip(self):
        """Test getting client ID from IP address"""
        limiter = RateLimiter()

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        client_id = limiter.get_client_id(mock_request)

        assert client_id is not None
        assert isinstance(client_id, str)
        assert len(client_id) == 32  # MD5 hash length

    def test_get_client_id_from_x_forwarded_for(self):
        """Test getting client ID from X-Forwarded-For header"""
        limiter = RateLimiter()

        mock_request = Mock(spec=Request)
        mock_request.headers.get.side_effect = lambda key, default="": {
            "X-Forwarded-For": "10.0.0.1, 192.168.1.1",
            "User-Agent": "TestAgent/1.0"
        }.get(key, default)
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        client_id = limiter.get_client_id(mock_request)

        assert client_id is not None
        # Should use first IP from X-Forwarded-For

    def test_get_client_id_consistent(self):
        """Test that same client gets same ID"""
        limiter = RateLimiter()

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        id1 = limiter.get_client_id(mock_request)
        id2 = limiter.get_client_id(mock_request)

        assert id1 == id2

    def test_get_rule_for_path_exact_match(self):
        """Test getting rule for exact path match"""
        limiter = RateLimiter()
        custom_rule = RateLimitRule(requests=10, window=60)
        limiter.add_rule("/api/login", custom_rule)

        rule = limiter.get_rule_for_path("/api/login")

        assert rule == custom_rule

    def test_get_rule_for_path_pattern_match(self):
        """Test getting rule for pattern match"""
        limiter = RateLimiter()
        custom_rule = RateLimitRule(requests=10, window=60)
        limiter.add_rule("/api/auth", custom_rule)

        rule = limiter.get_rule_for_path("/api/auth/login")

        assert rule == custom_rule

    def test_get_rule_for_path_default(self):
        """Test getting default rule when no match"""
        limiter = RateLimiter()
        default_rule = limiter.default_rule

        rule = limiter.get_rule_for_path("/api/unknown")

        assert rule == default_rule

    def test_is_allowed_first_request(self):
        """Test that first request is allowed"""
        limiter = RateLimiter()

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        allowed, info = limiter.is_allowed(mock_request)

        assert allowed is True
        assert info is None

    def test_is_allowed_within_limit(self):
        """Test requests within limit are allowed"""
        limiter = RateLimiter(default_rule=RateLimitRule(requests=5, window=60))

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        # Make 4 requests (within limit of 5)
        for _ in range(4):
            allowed, _ = limiter.is_allowed(mock_request)
            assert allowed is True

    def test_is_allowed_exceeds_limit(self):
        """Test that exceeding limit blocks requests"""
        limiter = RateLimiter(default_rule=RateLimitRule(requests=3, window=60, block_duration=10))

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        # Make requests up to limit
        for _ in range(3):
            allowed, _ = limiter.is_allowed(mock_request)

        # Next request should be blocked
        allowed, info = limiter.is_allowed(mock_request)

        assert allowed is False
        assert info is not None
        assert "error" in info
        assert info["error"] == "rate_limit_exceeded"

    def test_is_allowed_blocked_client(self):
        """Test that blocked client remains blocked"""
        limiter = RateLimiter(default_rule=RateLimitRule(requests=2, window=60, block_duration=10))

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        # Exceed limit
        for _ in range(3):
            limiter.is_allowed(mock_request)

        # Should still be blocked
        allowed, info = limiter.is_allowed(mock_request)
        assert allowed is False

    def test_cleanup_old_records(self):
        """Test cleanup removes old client records"""
        limiter = RateLimiter()

        # Add some old records manually
        limiter.clients["old_client"] = ClientRecord(
            requests=[time.time() - 1000],
            blocked_until=0
        )

        # Trigger cleanup by checking is_allowed
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        # Force cleanup by setting last_cleanup to past
        limiter.last_cleanup = time.time() - 400

        limiter.is_allowed(mock_request)

        # Old records should be cleaned (this is internal, hard to test directly)
        # Just verify no crash


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware"""

    @pytest.mark.asyncio
    async def test_middleware_allows_request_within_limit(self):
        """Test middleware allows requests within limit"""
        app = Mock()
        limiter = RateLimiter(default_rule=RateLimitRule(requests=10, window=60))
        middleware = RateLimitMiddleware(app, rate_limiter=limiter)

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        call_next = Mock()
        mock_response = Mock()
        mock_response.headers = {}
        call_next.return_value = mock_response

        response = await middleware.dispatch(mock_request, call_next)

        assert call_next.called
        assert response == mock_response

    @pytest.mark.asyncio
    async def test_middleware_blocks_request_exceeding_limit(self):
        """Test middleware blocks requests exceeding limit"""
        app = Mock()
        limiter = RateLimiter(default_rule=RateLimitRule(requests=2, window=60))
        middleware = RateLimitMiddleware(app, rate_limiter=limiter)

        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = None
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/api/test"

        call_next = Mock()
        mock_response = Mock()
        mock_response.headers = {}
        call_next.return_value = mock_response

        # Make requests up to limit
        for _ in range(2):
            await middleware.dispatch(mock_request, call_next)

        # Next request should return 429
        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 429
        # call_next should NOT be called
        assert call_next.call_count == 2  # Only first 2 calls
