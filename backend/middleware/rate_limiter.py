"""
Rate Limiting Middleware for FastAPI
Protects against brute force attacks and DoS
"""
import time
from typing import Dict, Optional, Callable
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import hashlib


@dataclass
class RateLimitRule:
    """Rate limit configuration"""
    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    block_duration: int = 300  # How long to block after exceeding limit (5 minutes)


@dataclass
class ClientRecord:
    """Track client requests"""
    requests: list = field(default_factory=list)
    blocked_until: float = 0


class RateLimiter:
    """
    In-memory rate limiter
    For production, consider using Redis for distributed rate limiting
    """

    def __init__(self, default_rule: Optional[RateLimitRule] = None):
        """Initialize rate limiter"""
        if default_rule is None:
            # Default: 100 requests per minute
            default_rule = RateLimitRule(requests=100, window=60)

        self.default_rule = default_rule
        self.clients: Dict[str, ClientRecord] = defaultdict(ClientRecord)
        self.rules: Dict[str, RateLimitRule] = {}

        # Cleanup old records periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def add_rule(self, path_pattern: str, rule: RateLimitRule):
        """Add custom rate limit rule for specific path"""
        self.rules[path_pattern] = rule

    def get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use X-Forwarded-For if behind proxy, otherwise use direct IP
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Include user agent for better fingerprinting
        user_agent = request.headers.get("User-Agent", "")

        # Create hash to save memory
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.md5(identifier.encode()).hexdigest()

    def get_rule_for_path(self, path: str) -> RateLimitRule:
        """Get rate limit rule for specific path"""
        # Check for exact match first
        if path in self.rules:
            return self.rules[path]

        # Check for pattern matches
        for pattern, rule in self.rules.items():
            if pattern in path or path.startswith(pattern):
                return rule

        return self.default_rule

    def is_allowed(self, request: Request) -> tuple[bool, Optional[dict]]:
        """
        Check if request is allowed
        Returns (is_allowed, rate_limit_info)
        """
        # Perform periodic cleanup
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_records()
            self.last_cleanup = current_time

        client_id = self.get_client_id(request)
        client_record = self.clients[client_id]

        # Check if client is currently blocked
        if client_record.blocked_until > current_time:
            remaining = int(client_record.blocked_until - current_time)
            return False, {
                "error": "rate_limit_exceeded",
                "message": f"Too many requests. Please try again in {remaining} seconds.",
                "retry_after": remaining
            }

        # Get applicable rule
        rule = self.get_rule_for_path(request.url.path)

        # Clean up old requests outside the window
        cutoff_time = current_time - rule.window
        client_record.requests = [
            req_time for req_time in client_record.requests
            if req_time > cutoff_time
        ]

        # Check if limit exceeded
        if len(client_record.requests) >= rule.requests:
            # Block the client
            client_record.blocked_until = current_time + rule.block_duration
            remaining = rule.block_duration

            return False, {
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Blocked for {rule.block_duration} seconds.",
                "retry_after": remaining
            }

        # Record this request
        client_record.requests.append(current_time)

        # Calculate rate limit headers
        remaining_requests = rule.requests - len(client_record.requests)
        reset_time = int(current_time + rule.window)

        return True, {
            "X-RateLimit-Limit": str(rule.requests),
            "X-RateLimit-Remaining": str(remaining_requests),
            "X-RateLimit-Reset": str(reset_time)
        }

    def _cleanup_old_records(self):
        """Remove old client records to prevent memory bloat"""
        current_time = time.time()
        clients_to_remove = []

        for client_id, record in self.clients.items():
            # Remove if no recent requests and not blocked
            if (not record.requests or
                    max(record.requests) < current_time - self.cleanup_interval) and \
                    record.blocked_until < current_time:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.clients[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        """Initialize middleware"""
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

        # Configure stricter limits for authentication endpoints
        self.rate_limiter.add_rule(
            "/api/auth/login",
            RateLimitRule(requests=5, window=60, block_duration=600)  # 5 per minute, block 10 mins
        )

        # Configure limits for mutation endpoints
        for path in ["/api/companies", "/api/investments", "/api/pe-firms"]:
            self.rate_limiter.add_rule(
                path,
                RateLimitRule(requests=50, window=60)  # 50 per minute
            )

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting"""
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check rate limit
        is_allowed, info = self.rate_limiter.is_allowed(request)

        if not is_allowed:
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content=info,
                headers={"Retry-After": str(info.get("retry_after", 60))}
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if info:
            for header, value in info.items():
                if header.startswith("X-RateLimit"):
                    response.headers[header] = value

        return response


# Utility function to create configured rate limiter
def create_rate_limiter(
    default_requests: int = 100,
    default_window: int = 60,
    strict_auth: bool = True
) -> RateLimiter:
    """
    Create a configured rate limiter

    Args:
        default_requests: Default number of requests allowed
        default_window: Default time window in seconds
        strict_auth: Whether to enforce strict limits on auth endpoints

    Returns:
        Configured RateLimiter instance
    """
    limiter = RateLimiter(
        default_rule=RateLimitRule(
            requests=default_requests,
            window=default_window
        )
    )

    if strict_auth:
        # Strict limits for authentication to prevent brute force
        limiter.add_rule(
            "/api/auth/login",
            RateLimitRule(requests=5, window=60, block_duration=600)
        )

    return limiter
