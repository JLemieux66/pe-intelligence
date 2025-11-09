"""
Base service class with common functionality
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from src.models.database_models_v2 import get_session, get_direct_session


class BaseService:
    """Base service class with common database operations"""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session"""
        self._session = session
        self._owns_session = session is None
    
    @property
    def session(self) -> Session:
        """Get database session"""
        if self._session is None:
            self._session = get_direct_session()
        return self._session
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session if we own it"""
        if self._owns_session and self._session:
            self._session.close()
    
    def close(self):
        """Manually close session if we own it"""
        if self._owns_session and self._session:
            self._session.close()
            self._session = None