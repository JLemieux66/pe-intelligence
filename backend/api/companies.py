"""
Companies API endpoints
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Query, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.schemas.responses import CompanyResponse, SimilarCompaniesResponse
from backend.schemas.requests import CompanyUpdate, SimilarCompaniesRequest
from backend.services import CompanyService
from src.models.database_models_v2 import get_session
from backend.auth import verify_admin_token
import io
import csv
from datetime import datetime


router = APIRouter(prefix="/api", tags=["companies"])


@router.get("/companies", response_model=List[CompanyResponse])
def get_companies(
    response: Response,
    search: Optional[str] = Query(None, description="Search company names"),
    search_mode: str = Query("contains", description="Search mode: 'contains' (partial match) or 'exact' (exact match)"),
    filter_mode: str = Query("any", description="Multi-select filter mode: 'any' (OR logic) or 'all' (AND logic)"),
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
        'search_mode': search_mode,
        'filter_mode': filter_mode,
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


@router.get("/companies/export/with-revenue")
def export_companies_with_revenue(
    response: Response,
    session = Depends(get_session)
):
    """
    Export ALL companies WITH PitchBook revenue data as CSV for ML training.

    This endpoint returns a comprehensive dataset including:
    - Revenue (target variable)
    - Employee counts (from multiple sources)
    - Funding data
    - Industry classifications
    - Location data
    - PE firm relationships
    - Financial metrics
    - Derived features for ML
    """

    # Filter to only include companies with revenue data
    filters = {
        'min_revenue': 0  # Only companies with revenue > 0
    }

    # Get all companies with revenue (no limit)
    with CompanyService(session) as company_service:
        companies, total_count = company_service.get_companies(filters, limit=10000, offset=0)

        if not companies:
            raise HTTPException(status_code=404, detail="No companies with revenue data found")

        # Create CSV in memory
        output = io.StringIO()

        # Define all fields for ML training
        fieldnames = [
            # Core identifiers
            'id',
            'name',
            'website',

            # TARGET VARIABLE
            'current_revenue_usd',

            # Financial data
            'last_known_valuation_usd',
            'last_financing_date',
            'last_financing_size_usd',
            'total_funding_usd',
            'num_funding_rounds',

            # Employee data (multiple sources)
            'employee_count',  # Best available
            'scraped_employee_count',  # LinkedIn
            'crunchbase_employee_range',

            # Industry classification
            'primary_industry_group',
            'primary_industry_sector',
            'verticals',

            # Location data
            'hq_location',
            'hq_country',
            'headquarters',
            'country',
            'state_region',
            'city',

            # PE firm relationships
            'pe_firms',  # Comma-separated list
            'investor_name',
            'investor_status',
            'investor_holding',

            # Company stage & status
            'status',
            'funding_stage',
            'is_public',
            'ipo_date',
            'ipo_exchange',
            'ipo_valuation_usd',

            # Dates
            'founded_date',
            'closed_date',

            # Social & web presence
            'linkedin_url',
            'crunchbase_url',
            'twitter_url',

            # ML predictions (if available)
            'predicted_revenue',
            'prediction_confidence',

            # Derived features
            'valuation_to_revenue_ratio',
            'avg_funding_per_round',
            'has_multiple_pe_firms',
            'is_exited'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write each company
        for company in companies:
            # Calculate derived features
            valuation_to_revenue = None
            if company.current_revenue_usd and company.last_known_valuation_usd:
                valuation_to_revenue = company.last_known_valuation_usd / company.current_revenue_usd

            avg_funding_per_round = None
            if company.total_funding_usd and company.num_funding_rounds and company.num_funding_rounds > 0:
                avg_funding_per_round = company.total_funding_usd / company.num_funding_rounds

            has_multiple_pe_firms = len(company.pe_firms) > 1 if company.pe_firms else False
            is_exited = company.status == 'Exit'

            row = {
                'id': company.id,
                'name': company.name,
                'website': company.website,
                'current_revenue_usd': company.current_revenue_usd,
                'last_known_valuation_usd': company.last_known_valuation_usd,
                'last_financing_date': company.last_financing_date,
                'last_financing_size_usd': company.last_financing_size_usd,
                'total_funding_usd': company.total_funding_usd,
                'num_funding_rounds': company.num_funding_rounds,
                'employee_count': company.employee_count,
                'scraped_employee_count': company.scraped_employee_count,
                'crunchbase_employee_range': company.crunchbase_employee_range,
                'primary_industry_group': company.primary_industry_group,
                'primary_industry_sector': company.primary_industry_sector,
                'verticals': company.verticals,
                'hq_location': company.hq_location,
                'hq_country': company.hq_country,
                'headquarters': company.headquarters,
                'country': company.country,
                'state_region': company.state_region,
                'city': company.city,
                'pe_firms': ', '.join(company.pe_firms) if company.pe_firms else '',
                'investor_name': company.investor_name,
                'investor_status': company.investor_status,
                'investor_holding': company.investor_holding,
                'status': company.status,
                'funding_stage': company.funding_stage,
                'is_public': company.is_public,
                'ipo_date': company.ipo_date,
                'ipo_exchange': company.ipo_exchange,
                'ipo_valuation_usd': company.ipo_valuation_usd,
                'founded_date': company.founded_date,
                'closed_date': company.closed_date,
                'linkedin_url': company.linkedin_url,
                'crunchbase_url': company.crunchbase_url,
                'twitter_url': company.twitter_url,
                'predicted_revenue': company.predicted_revenue,
                'prediction_confidence': company.prediction_confidence,
                'valuation_to_revenue_ratio': valuation_to_revenue,
                'avg_funding_per_round': avg_funding_per_round,
                'has_multiple_pe_firms': has_multiple_pe_firms,
                'is_exited': is_exited
            }

            writer.writerow(row)

        # Prepare the response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"companies_with_revenue_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Count": str(total_count)
            }
        )


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, session = Depends(get_session)):
    """Get a single company by ID"""
    
    with CompanyService(session) as company_service:
        company = company_service.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company


@router.put("/companies/{company_id}", dependencies=[Depends(verify_admin_token)])
async def update_company(company_id: int, company_update: CompanyUpdate, session = Depends(get_session)):
    """Update company details (Admin only)"""
    
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


@router.get("/companies/{company_id}/funding-rounds")
def get_company_funding_rounds(company_id: int, session = Depends(get_session)):
    """Get funding rounds for a specific company"""
    from src.models.database_models_v2 import Company, FundingRound

    # Check if company exists
    company = session.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get funding rounds
    funding_rounds = session.query(FundingRound).filter(
        FundingRound.company_id == company_id
    ).order_by(FundingRound.announced_on.desc()).all()

    # Convert to response format
    return [{
        'id': fr.id,
        'announced_on': fr.announced_on.isoformat() if fr.announced_on else None,
        'investment_type': fr.investment_type,
        'money_raised_usd': fr.money_raised_usd,
        'investor_names': fr.investor_names,
        'num_investors': fr.num_investors
    } for fr in funding_rounds]