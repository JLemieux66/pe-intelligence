"""
Companies API endpoints
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Query, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.schemas.responses import CompanyResponse, SimilarCompaniesResponse
from backend.schemas.requests import CompanyUpdate, CompanyCreate, SimilarCompaniesRequest
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
    # Filter operators
    filter_operator: Optional[str] = Query("AND", description="Global operator for combining filters (AND/OR)"),
    search_exact: Optional[bool] = Query(False, description="Use exact matching for search (default: False for partial match)"),
    pe_firm_operator: Optional[str] = Query("OR", description="Operator for multiple PE firms (AND/OR)"),
    industry_operator: Optional[str] = Query("OR", description="Operator for multiple industries (AND/OR)"),
    industry_group_operator: Optional[str] = Query("OR", description="Operator for multiple industry groups (AND/OR)"),
    industry_sector_operator: Optional[str] = Query("OR", description="Operator for multiple industry sectors (AND/OR)"),
    verticals_operator: Optional[str] = Query("OR", description="Operator for multiple verticals (AND/OR)"),
    country_operator: Optional[str] = Query("OR", description="Operator for multiple countries (AND/OR)"),
    state_region_operator: Optional[str] = Query("OR", description="Operator for multiple states (AND/OR)"),
    city_operator: Optional[str] = Query("OR", description="Operator for multiple cities (AND/OR)"),
    # NOT operators (negation)
    pe_firm_not: Optional[bool] = Query(False, description="Exclude companies with these PE firms"),
    industry_not: Optional[bool] = Query(False, description="Exclude companies with these industries"),
    industry_group_not: Optional[bool] = Query(False, description="Exclude companies with these industry groups"),
    industry_sector_not: Optional[bool] = Query(False, description="Exclude companies with these industry sectors"),
    verticals_not: Optional[bool] = Query(False, description="Exclude companies with these verticals"),
    country_not: Optional[bool] = Query(False, description="Exclude companies in these countries"),
    state_region_not: Optional[bool] = Query(False, description="Exclude companies in these states"),
    city_not: Optional[bool] = Query(False, description="Exclude companies in these cities"),
    # Data quality filters
    has_linkedin_url: Optional[bool] = Query(None, description="Filter by LinkedIn URL presence (true=has, false=missing)"),
    has_website: Optional[bool] = Query(None, description="Filter by website presence (true=has, false=missing)"),
    has_revenue: Optional[bool] = Query(None, description="Filter by revenue data presence (true=has, false=missing)"),
    has_employees: Optional[bool] = Query(None, description="Filter by employee count presence (true=has, false=missing)"),
    has_description: Optional[bool] = Query(None, description="Filter by description presence (true=has, false=missing)"),
    # Date range filters
    founded_year_min: Optional[int] = Query(None, description="Minimum founded year"),
    founded_year_max: Optional[int] = Query(None, description="Maximum founded year"),
    investment_year_min: Optional[int] = Query(None, description="Minimum investment year"),
    investment_year_max: Optional[int] = Query(None, description="Maximum investment year"),
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
        'is_public': is_public,
        # Filter operators
        'filter_operator': filter_operator,
        'search_exact': search_exact,
        'pe_firm_operator': pe_firm_operator,
        'industry_operator': industry_operator,
        'industry_group_operator': industry_group_operator,
        'industry_sector_operator': industry_sector_operator,
        'verticals_operator': verticals_operator,
        'country_operator': country_operator,
        'state_region_operator': state_region_operator,
        'city_operator': city_operator,
        # NOT operators
        'pe_firm_not': pe_firm_not,
        'industry_not': industry_not,
        'industry_group_not': industry_group_not,
        'industry_sector_not': industry_sector_not,
        'verticals_not': verticals_not,
        'country_not': country_not,
        'state_region_not': state_region_not,
        'city_not': city_not,
        # Data quality filters
        'has_linkedin_url': has_linkedin_url,
        'has_website': has_website,
        'has_revenue': has_revenue,
        'has_employees': has_employees,
        'has_description': has_description,
        # Date range filters
        'founded_year_min': founded_year_min,
        'founded_year_max': founded_year_max,
        'investment_year_min': investment_year_min,
        'investment_year_max': investment_year_max
    }
    
    # Use service to get companies
    with CompanyService(session) as company_service:
        companies, total_count = company_service.get_companies(filters, limit, offset)
        response.headers["X-Total-Count"] = str(total_count)
        return companies


@router.post("/companies", response_model=CompanyResponse, dependencies=[Depends(verify_admin_token)])
async def create_company(company_create: CompanyCreate, session = Depends(get_session)):
    """
    Create a new company with all associated data (Admin only)

    This endpoint allows creating a company with:
    - Basic company information (name, website, description, etc.)
    - Geographic data (country, state, city, HQ location)
    - Industry classification (category, sector, verticals)
    - Employee and revenue data
    - Funding information
    - IPO/public company data
    - Associated tags (industry tags, etc.)
    - Funding rounds
    - PE firm investments

    The only required field is `name`. All other fields are optional.

    Example minimal request:
    ```json
    {
        "name": "Acme Corporation"
    }
    ```

    Example full request:
    ```json
    {
        "name": "Acme Corporation",
        "website": "https://acme.com",
        "description": "Leading enterprise software company",
        "country": "United States",
        "city": "San Francisco",
        "state_region": "California",
        "industry_category": "Software",
        "primary_industry_sector": "Enterprise Software",
        "employee_count": 500,
        "current_revenue_usd": 50.0,
        "founded_year": 2015,
        "tags": [
            {"tag_category": "industry", "tag_value": "SaaS"},
            {"tag_category": "industry", "tag_value": "Analytics"}
        ],
        "funding_rounds": [
            {
                "announced_on": "2020-05-15",
                "investment_type": "series_b",
                "money_raised_usd": 25000000,
                "investor_names": "Sequoia Capital, Andreessen Horowitz",
                "num_investors": 2
            }
        ],
        "pe_investments": [
            {
                "pe_firm_name": "Vista Equity Partners",
                "computed_status": "Active",
                "investment_year": "2020"
            }
        ]
    }
    ```
    """

    with CompanyService(session) as company_service:
        company_response = company_service.create_company(company_create)
        if not company_response:
            raise HTTPException(
                status_code=400,
                detail="Company creation failed. Company with this name/website may already exist."
            )
        return company_response


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