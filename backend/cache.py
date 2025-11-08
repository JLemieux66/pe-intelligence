"""
Simple in-memory caching for expensive queries
Thread-safe TTL cache implementation
"""
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, Any, Callable
import functools


class SimpleCache:
    """Thread-safe TTL cache"""
    
    def __init__(self):
        self._cache = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if datetime.utcnow() < expiry:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        with self._lock:
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def delete(self, key: str):
        """Delete specific cache entry"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]


# Global cache instance
cache = SimpleCache()


def cached(ttl_seconds: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results
    
    Args:
        ttl_seconds: Time to live in seconds (default 5 minutes)
        key_func: Optional function to generate cache key from args
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator
