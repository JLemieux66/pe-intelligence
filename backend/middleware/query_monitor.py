"""
Query Monitoring Middleware
Tracks and logs slow database queries for performance analysis
"""
import time
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Slow query threshold in seconds
SLOW_QUERY_THRESHOLD = 1.0  # Log queries taking more than 1 second


class QueryMonitor:
    """Monitor database query performance"""

    def __init__(self, threshold_seconds: float = SLOW_QUERY_THRESHOLD):
        self.threshold = threshold_seconds
        self.total_queries = 0
        self.slow_queries = 0
        self.total_time = 0.0
        self.slowest_query = None
        self.slowest_time = 0.0

    def reset_stats(self):
        """Reset monitoring statistics"""
        self.total_queries = 0
        self.slow_queries = 0
        self.total_time = 0.0
        self.slowest_query = None
        self.slowest_time = 0.0

    def get_stats(self):
        """Get monitoring statistics"""
        avg_time = self.total_time / self.total_queries if self.total_queries > 0 else 0
        return {
            'total_queries': self.total_queries,
            'slow_queries': self.slow_queries,
            'total_time': round(self.total_time, 2),
            'average_time': round(avg_time, 3),
            'slowest_time': round(self.slowest_time, 2),
            'slowest_query': self.slowest_query[:200] if self.slowest_query else None
        }


# Global monitor instance
query_monitor = QueryMonitor()


def setup_query_monitoring(engine: Engine, threshold: float = SLOW_QUERY_THRESHOLD):
    """
    Set up query monitoring for a SQLAlchemy engine.

    Args:
        engine: SQLAlchemy engine instance
        threshold: Threshold in seconds for logging slow queries
    """
    monitor = QueryMonitor(threshold)

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time"""
        conn.info.setdefault('query_start_time', []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query execution time and log slow queries"""
        total = time.time() - conn.info['query_start_time'].pop(-1)

        # Update statistics
        monitor.total_queries += 1
        monitor.total_time += total

        # Track slowest query
        if total > monitor.slowest_time:
            monitor.slowest_time = total
            monitor.slowest_query = statement

        # Log slow queries
        if total > monitor.threshold:
            monitor.slow_queries += 1
            logger.warning(
                f"[SLOW QUERY] {total:.3f}s - {statement[:500]}"
                + ("..." if len(statement) > 500 else "")
            )

            # Log parameters for debugging (sanitized)
            if parameters:
                logger.debug(f"Parameters: {parameters}")

    return monitor


def log_query_stats():
    """Log current query statistics"""
    stats = query_monitor.get_stats()
    logger.info(
        f"[QUERY STATS] Total: {stats['total_queries']}, "
        f"Slow: {stats['slow_queries']}, "
        f"Avg: {stats['average_time']}s, "
        f"Total Time: {stats['total_time']}s"
    )
    if stats['slowest_query']:
        logger.info(f"[SLOWEST QUERY] {stats['slowest_time']}s - {stats['slowest_query']}")
