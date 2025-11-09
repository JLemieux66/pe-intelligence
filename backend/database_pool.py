"""
Database connection pooling for improved performance
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Database configuration with connection pooling
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pe_portfolio_v2.db")

# Connection pool settings
POOL_SIZE = 10  # Number of connections to maintain
MAX_OVERFLOW = 20  # Additional connections beyond pool_size
POOL_TIMEOUT = 30  # Seconds to wait for connection
POOL_RECYCLE = 3600  # Seconds before recreating connection

def create_engine_with_pool():
    """Create SQLAlchemy engine with connection pooling"""
    if DATABASE_URL.startswith("sqlite"):
        # SQLite doesn't support connection pooling
        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL with connection pooling
        return create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before use
            echo=False  # Set to True for SQL debugging
        )

# Global engine instance
engine = create_engine_with_pool()