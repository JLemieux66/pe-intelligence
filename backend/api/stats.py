"""
Statistics API endpoints
"""
from fastapi import APIRouter, Depends
from backend.schemas.responses import StatsResponse
from backend.services import StatsService
from src.models.database_models_v2 import get_session

router = APIRouter(prefix="/api", tags=["statistics"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(session = Depends(get_session)):
    """Get overall portfolio statistics"""
    
    with StatsService(session) as stats_service:
        return stats_service.get_stats()