"""
Companies API endpoints
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Query, Depends, HTTPException, Response
from backend.schemas.responses import CompanyResponse, SimilarCompaniesResponse
from backend.schemas.requests import CompanyUpdate, SimilarCompaniesRequest
from backend.services import CompanyService
from src.models.database_models_v2 import get_session
from backend.auth import verify_admin_token


router = APIRouter(prefix="/api", tags=["companies"])


@router.get("/companies", response_model=List[CompanyResponse])
def get_companies(
    response: Response,
    search: Optional[str] = Query(None, description="Search company names"),
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name(s), comma-separated for multiple"),
    status: Optional[str] = Query(None, description="Filter by status (Active/Exit)"),
    industry: Optional[str] = Query(None, description="Filter by industry category(ies), comma-separated for multiple"),
    industry_group: Optional[str] = Query(None, description="Filter by PitchBook industry group(s), comma-separated for multiple"),
    industry_sector: Optional[str] = Query(None, description="Filter by PitchBook industry sector(s), comma-separated for multiple"),
    verticals: Optional[str] = Query(None, description="Filter by PitchBook verticals, comma-separated for multiple"),
    country: Optional[str] = Query(None, description="Filter by country/countries, comma-separated for multiple"),
    state_region: Optional[str] = Query(None, description="Filter by state/region(s), comma-separated for multiple"),
    city: Optional[str] = Query(None, description="Filter by city/cities, comma-separated for multiple"),
    revenue_range: Optional[str] = Query(None, description="Filter by revenue range(s), comma-separated for multiple"),
    min_revenue: Optional[float] = Query(None, description="Minimum revenue in millions USD"),
    max_revenue: Optional[float] = Query(None, description="Maximum revenue in millions USD"),
    employee_count: Optional[str] = Query(None, description="Filter by employee count range(s), comma-separated for multiple"),
    min_employees: Optional[int] = Query(None, description="Minimum employee count"),
    max_employees: Optional[int] = Query(None, description="Maximum employee count"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    limit: int = Query(10000, ge=1, le=10000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session = Depends(get_session)
):
    """Get companies (deduplicated across PE firms)"""
    
    # Build filters dictionary
    filters = {
        'search': search,
        'pe_firm': pe_firm,
        'status': status,
        'industry': industry,
        'industry_group': industry_group,
        'industry_sector': industry_sector,
        'verticals': verticals,
        'country': country,
        'state_region': state_region,
        'city': city,
        'revenue_range': revenue_range,
        'min_revenue': min_revenue,
        'max_revenue': max_revenue,
        'employee_count': employee_count,
        'min_employees': min_employees,
        'max_employees': max_employees,
        'is_public': is_public
    }
    
    # Use service to get companies
    with CompanyService(session) as company_service:
        companies, total_count = company_service.get_companies(filters, limit, offset)
        response.headers["X-Total-Count"] = str(total_count)
        return companies


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, session = Depends(get_session)):
    """Get a single company by ID"""
    
    with CompanyService(session) as company_service:
        company = company_service.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company


@router.put("/companies/{company_id}")
async def update_company(company_id: int, company_update: CompanyUpdate, session = Depends(get_session)):
    """Update company details"""
    
    with CompanyService(session) as company_service:
        success = company_service.update_company(company_id, company_update)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Company updated successfully"}


@router.delete("/companies/{company_id}", dependencies=[Depends(verify_admin_token)])
async def delete_company(company_id: int):
    """Delete a company (Admin only)"""
    
    with CompanyService() as company_service:
        success = company_service.delete_company(company_id)
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Company deleted successfully"}