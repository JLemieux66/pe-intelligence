"""
Metadata API endpoints (locations, industries, etc.)
"""
from fastapi import APIRouter, Depends
from backend.schemas.responses import LocationsResponse, PitchBookMetadataResponse, IndustriesResponse
from backend.services import MetadataService
from src.models.database_models_v2 import get_session

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/locations", response_model=LocationsResponse)
def get_locations(session = Depends(get_session)):
    """Get all unique locations (countries, states, cities)"""
    
    with MetadataService(session) as metadata_service:
        return metadata_service.get_locations()


@router.get("/pitchbook-metadata", response_model=PitchBookMetadataResponse)
def get_pitchbook_metadata(session = Depends(get_session)):
    """Get PitchBook-specific metadata (industry groups, sectors, verticals, HQ locations)"""
    
    with MetadataService(session) as metadata_service:
        return metadata_service.get_pitchbook_metadata()


@router.get("/industries", response_model=IndustriesResponse)
def get_industries(session = Depends(get_session)):
    """Get all unique industry tags and categories"""
    
    with MetadataService(session) as metadata_service:
        return metadata_service.get_industries()