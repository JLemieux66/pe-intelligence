"""
Analytics service for tracking usage and performance metrics
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter

class AnalyticsService:
    """Simple analytics tracking for API usage and performance"""
    
    def __init__(self, log_dir: str = "analytics"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def log_api_call(self, endpoint: str, duration_ms: float, status_code: int, 
                     user_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Log API call metrics"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        # Write to daily log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"api_calls_{date_str}.jsonl")
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except IOError:
            pass  # Fail silently
    
    def log_similar_companies_request(self, company_ids: List[int], result_count: int, 
                                    duration_ms: float, cache_hit: bool = False):
        """Log similar companies specific metrics"""
        self.log_api_call(
            endpoint="similar_companies",
            duration_ms=duration_ms,
            status_code=200,
            metadata={
                "input_companies": len(company_ids),
                "result_count": result_count,
                "cache_hit": cache_hit
            }
        )
    
    def get_usage_stats(self, days: int = 7) -> Dict:
        """Get usage statistics for the last N days"""
        stats = {
            "total_requests": 0,
            "avg_response_time": 0,
            "endpoint_usage": Counter(),
            "daily_usage": defaultdict(int),
            "error_rate": 0
        }
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        total_duration = 0
        error_count = 0
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"api_calls_{date_str}.jsonl")
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            entry = json.loads(line.strip())
                            stats["total_requests"] += 1
                            stats["endpoint_usage"][entry["endpoint"]] += 1
                            stats["daily_usage"][date_str] += 1
                            total_duration += entry["duration_ms"]
                            
                            if entry["status_code"] >= 400:
                                error_count += 1
                except (IOError, json.JSONDecodeError):
                    continue
        
        if stats["total_requests"] > 0:
            stats["avg_response_time"] = total_duration / stats["total_requests"]
            stats["error_rate"] = error_count / stats["total_requests"]
        
        return stats

# Global analytics instance
analytics_service = AnalyticsService()