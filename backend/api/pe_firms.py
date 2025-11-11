"""
PE Firms API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends
from backend.schemas.responses import PEFirmResponse
from backend.services import PEFirmService
from src.models.database_models_v2 import get_session

router = APIRouter(prefix="/api", tags=["pe-firms"])


@router.get("/pe-firms", response_model=List[PEFirmResponse])
def get_pe_firms(session=Depends(get_session)):
    """Get all PE firms with statistics"""

    with PEFirmService(session) as pe_firm_service:
        return pe_firm_service.get_pe_firms()
