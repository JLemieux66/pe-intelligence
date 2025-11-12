"""
Database connection pooling for improved performance
OPTIMIZED: Tuned pool settings for production workloads
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Database configuration with connection pooling
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pe_portfolio_v2.db")

# Connection pool settings - OPTIMIZED for production
POOL_SIZE = 20  # Increased from 10 - Number of persistent connections
MAX_OVERFLOW = 40  # Increased from 20 - Additional connections during spikes
POOL_TIMEOUT = 30  # Seconds to wait for connection
POOL_RECYCLE = 1800  # Reduced from 3600 - Recycle connections every 30 min to prevent stale connections
POOL_PRE_PING = True  # Verify connections before use (prevents "server has gone away" errors)

def create_engine_with_pool():
    """
    Create SQLAlchemy engine with optimized connection pooling.
    OPTIMIZED: Increased pool size and improved connection health checks.
    """
    if DATABASE_URL.startswith("sqlite"):
        # SQLite doesn't support connection pooling
        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL with optimized connection pooling
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=POOL_PRE_PING,  # Verify connections before use
            echo=False  # Set to True for SQL debugging
        )

        # Log connection pool stats periodically
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log when new connections are created"""
            # This helps monitor connection pool usage
            pass

        return engine

# Global engine instance
engine = create_engine_with_pool()

# Setup query monitoring for performance tracking
try:
    from backend.middleware.query_monitor import setup_query_monitoring
    setup_query_monitoring(engine, threshold=1.0)
    print("[OK] Query monitoring enabled (threshold: 1.0s)")
except ImportError:
    print("[WARNING] Query monitoring not available")

# Session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function for FastAPI to get database sessions.

    Yields a database session and ensures it's closed after use.
    Use this with FastAPI's Depends() for dependency injection.

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()