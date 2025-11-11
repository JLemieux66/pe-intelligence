"""
Query Result Caching Middleware
Provides in-memory caching with TTL for expensive database queries
"""
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json


class QueryCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self):
        self._cache = {}
        self._expiry = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None

        # Check if expired
        if key in self._expiry and datetime.now() > self._expiry[key]:
            # Clean up expired entry
            del self._cache[key]
            del self._expiry[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def delete(self, key: str):
        """Remove value from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._expiry.clear()

    def get_stats(self):
        """Get cache statistics"""
        now = datetime.now()
        active_entries = sum(1 for k, v in self._expiry.items() if v > now)
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries
        }


# Global cache instance
query_cache = QueryCache()


def cache_result(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Args:
        ttl_seconds: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key (default uses function name)

    Example:
        @cache_result(ttl_seconds=600, key_prefix="stats")
        def get_dashboard_stats():
            return expensive_query()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            prefix = key_prefix or func.__name__

            # Create a stable key from arguments
            key_parts = [prefix]

            # Add positional arguments (skip 'self' for methods)
            for arg in args:
                if not hasattr(arg, '__dict__'):  # Skip complex objects like 'self'
                    key_parts.append(str(arg))

            # Add keyword arguments
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached = query_cache.get(cache_key)
            if cached is not None:
                print(f"[CACHE HIT] {cache_key}")
                return cached

            # Execute function and cache result
            print(f"[CACHE MISS] {cache_key}")
            result = func(*args, **kwargs)
            query_cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: Optional[str] = None):
    """
    Invalidate cache entries matching a pattern.
    If pattern is None, clears all cache.

    Args:
        pattern: String pattern to match cache keys (simple substring match)
    """
    if pattern is None:
        query_cache.clear()
        print("[CACHE] Cleared all entries")
    else:
        keys_to_delete = [k for k in query_cache._cache.keys() if pattern in k]
        for key in keys_to_delete:
            query_cache.delete(key)
        print(f"[CACHE] Invalidated {len(keys_to_delete)} entries matching '{pattern}'")
