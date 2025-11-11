"""
Investments API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Query, Depends, HTTPException
from backend.schemas.responses import InvestmentResponse
from backend.schemas.requests import InvestmentUpdate
from backend.services import InvestmentService
from src.models.database_models_v2 import get_session
from backend.auth import verify_admin_token


router = APIRouter(prefix="/api", tags=["investments"])


@router.get("/companies/{company_id}/investments", response_model=List[InvestmentResponse])
def get_company_investments(
    company_id: int,
    session=Depends(get_session)
):
    """Get all investments for a specific company"""
    with InvestmentService(session) as investment_service:
        # Get investments filtered by company_id
        filters = {'company_id': company_id}
        return investment_service.get_investments(filters, limit=1000, offset=0)


@router.get("/investments", response_model=List[InvestmentResponse])
def get_investments(
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name(s), comma-separated for multiple"),
    status: Optional[str] = Query(None, description="Filter by status (Active/Exit)"),
    exit_type: Optional[str] = Query(None, description="Filter by exit type (IPO/Acquisition)"),
    industry: Optional[str] = Query(None, description="Filter by industry(ies), comma-separated"),
    industry_group: Optional[str] = Query(None, description="Filter by PitchBook industry group(s)"),
    industry_sector: Optional[str] = Query(None, description="Filter by PitchBook industry sector(s)"),
    verticals: Optional[str] = Query(None, description="Filter by PitchBook verticals, comma-separated for multiple"),
    country: Optional[str] = Query(None, description="Filter by country/countries, comma-separated for multiple"),
    state_region: Optional[str] = Query(None, description="Filter by state/region(s), comma-separated for multiple"),
    city: Optional[str] = Query(None, description="Filter by city/cities, comma-separated for multiple"),
    min_revenue: Optional[float] = Query(None, description="Minimum revenue in millions USD"),
    max_revenue: Optional[float] = Query(None, description="Maximum revenue in millions USD"),
    min_employees: Optional[int] = Query(None, description="Minimum employee count"),
    max_employees: Optional[int] = Query(None, description="Maximum employee count"),
    search: Optional[str] = Query(None, description="Search company names"),
    limit: int = Query(10000, ge=1, le=10000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    session=Depends(get_session)
):
    """Get all investments with filters (supports multi-select with comma-separated values)"""

    # Build filters dictionary
    filters = {
        'pe_firm': pe_firm,
        'status': status,
        'exit_type': exit_type,
        'industry': industry,
        'industry_group': industry_group,
        'industry_sector': industry_sector,
        'verticals': verticals,
        'country': country,
        'state_region': state_region,
        'city': city,
        'min_revenue': min_revenue,
        'max_revenue': max_revenue,
        'min_employees': min_employees,
        'max_employees': max_employees,
        'search': search
    }

    # Use service to get investments
    with InvestmentService(session) as investment_service:
        return investment_service.get_investments(filters, limit, offset)


@router.put("/investments/{investment_id}", dependencies=[Depends(verify_admin_token)])
async def update_investment(investment_id: int, investment_update: InvestmentUpdate, session=Depends(get_session)):
    """Update investment details (Admin only)"""

    with InvestmentService(session) as investment_service:
        success = investment_service.update_investment(investment_id, investment_update)
        if not success:
            raise HTTPException(status_code=404, detail="Investment not found")
        return {"message": "Investment updated successfully"}
