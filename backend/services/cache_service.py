"""
Caching service for expensive operations like similar companies analysis
"""
import json
import hashlib
from typing import Optional, Any, List
from datetime import datetime, timedelta
import sqlite3
import os

class CacheService:
    """Simple file-based cache for similar companies results"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, company_ids: List[int], min_score: float, limit: int) -> str:
        """Generate cache key from parameters"""
        key_data = {
            "company_ids": sorted(company_ids),
            "min_score": min_score,
            "limit": limit
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, company_ids: List[int], min_score: float, limit: int) -> Optional[dict]:
        """Get cached similar companies result"""
        cache_key = self._get_cache_key(company_ids, min_score, limit)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check if cache is expired
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_time > timedelta(hours=self.ttl_hours):
            os.remove(cache_file)
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(self, company_ids: List[int], min_score: float, limit: int, result: dict) -> None:
        """Cache similar companies result"""
        cache_key = self._get_cache_key(company_ids, min_score, limit)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except IOError:
            pass  # Fail silently if caching fails
    
    def clear_expired(self) -> int:
        """Clear expired cache entries"""
        cleared = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.cache_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if datetime.now() - file_time > timedelta(hours=self.ttl_hours):
                    os.remove(file_path)
                    cleared += 1
        return cleared

# Global cache instance
cache_service = CacheService()