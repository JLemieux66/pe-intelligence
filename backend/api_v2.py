"""
FastAPI Backend for PE Portfolio Companies V2
REST API endpoints using v2 database schema
Updated: Added admin edit endpoints (PUT/DELETE) and authentication
Version: 1.2 - Debug prediction_confidence and funding data retrieval
"""
from fastapi import FastAPI, Query, HTTPException, Header, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from src.models.database_models_v2 import get_session, PEFirm, Company, CompanyPEInvestment, FundingRound
from src.enrichment.crunchbase_helpers import decode_revenue_range, decode_employee_count
from backend.auth import authenticate_admin, create_access_token, verify_admin_token
import os

def get_employee_count_display(company):
    """
    Get employee count for display - returns the best available value.
    Priority: PitchBook/exact count > projected LinkedIn count > Crunchbase range
    """
    # Check PitchBook employee_count first (from PitchBook ingestion)
    if hasattr(company, 'employee_count') and company.employee_count:
        return f"{company.employee_count:,}"  # e.g., "1,234"
    # If we have exact LinkedIn count, format it nicely
    elif company.projected_employee_count:
        return f"{company.projected_employee_count:,}"  # e.g., "1,234"
    # Fall back to Crunchbase range
    elif company.crunchbase_employee_count:
        return decode_employee_count(company.crunchbase_employee_count)  # e.g., "501-1,000"
    return None

# Reverse mappings for filtering (both full ranges and partial values)
REVENUE_RANGE_CODES = {
    "Less than $1M": "r_00000000",
    "$1M - $10M": "r_00001000",
    "$10M - $50M": "r_00010000",
    "$50M - $100M": "r_00050000",
    "$100M - $500M": "r_00100000",
    "$500M - $1B": "r_00500000",
    "$1B - $10B": "r_01000000",
    "$10B+": "r_10000000",
    # Partial matches for convenience
    "$1M": "r_00001000",
    "$10M": "r_00010000",
    "$50M": "r_00050000",
    "$100M": "r_00100000",
    "$500M": "r_00500000",
    "$1B": "r_01000000",
    "$10B": "r_10000000"
}

EMPLOYEE_COUNT_CODES = {
    # Exact decoded values (what users see in the API)
    "1-10": "c_00001_00010",
    "11-50": "c_00011_00050",
    "51-100": "c_00051_00100",
    "101-250": "c_00101_00250",
    "251-500": "c_00251_00500",
    "501-1,000": "c_00501_01000",
    "1,001-5,000": "c_01001_05000",
    "5,001-10,000": "c_05001_10000",
    "10,001+": "c_10001_max"
}
from sqlalchemy import func, or_, desc, case
from sqlalchemy.orm import joinedload

# Initialize FastAPI
app = FastAPI(
    title="PE Portfolio API V2",
    description="REST API for Private Equity Portfolio Companies",
    version="2.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],  # Expose custom header to frontend
)

# Response Models
class CompanyResponse(BaseModel):
    id: int
    name: str
    former_name: Optional[str] = None  # Former/previous company name (fka/formerly)
    pe_firms: List[str]  # Can have multiple PE firms
    status: str
    exit_type: Optional[str] = None
    investment_year: Optional[str] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    description: Optional[str] = None
    # Enrichment data
    revenue_range: Optional[str] = None
    employee_count: Optional[str] = None  # Display value (prefer scraped, fallback to Crunchbase)
    crunchbase_employee_range: Optional[str] = None  # Crunchbase range (e.g., "501-1,000")
    scraped_employee_count: Optional[int] = None  # LinkedIn exact count
    industry_category: Optional[str] = None
    industries: Optional[List[str]] = []  # Individual industry tags as array
    # Funding data
    total_funding_usd: Optional[int] = None
    num_funding_rounds: Optional[int] = None
    latest_funding_type: Optional[str] = None
    latest_funding_date: Optional[str] = None
    funding_stage_encoded: Optional[int] = None
    avg_round_size_usd: Optional[int] = None
    total_investors: Optional[int] = None
    # Predictions
    predicted_revenue: Optional[float] = None  # ML-predicted revenue in USD
    prediction_confidence: Optional[float] = None  # Confidence score 0-1
    is_public: Optional[bool] = False
    stock_exchange: Optional[str] = None
    # PitchBook data
    investor_name: Optional[str] = None  # PE firm name from PitchBook
    investor_status: Optional[str] = None
    investor_holding: Optional[str] = None
    current_revenue_usd: Optional[float] = None  # Revenue in millions USD
    last_known_valuation_usd: Optional[float] = None  # Valuation in millions USD
    primary_industry_group: Optional[str] = None
    primary_industry_sector: Optional[str] = None
    hq_location: Optional[str] = None
    hq_country: Optional[str] = None
    last_financing_date: Optional[str] = None
    last_financing_size_usd: Optional[float] = None
    last_financing_deal_type: Optional[str] = None
    verticals: Optional[str] = None

    class Config:
        from_attributes = True


class InvestmentResponse(BaseModel):
    investment_id: int
    company_id: int
    company_name: str
    pe_firm_name: str
    status: str
    raw_status: Optional[str] = None
    exit_type: Optional[str] = None
    exit_info: Optional[str] = None
    investment_year: Optional[str] = None
    sector: Optional[str] = None
    # Company enrichment data
    revenue_range: Optional[str] = None
    employee_count: Optional[str] = None
    industry_category: Optional[str] = None  # Comma-separated for backward compatibility
    industries: Optional[List[str]] = []  # Individual industry tags as array
    predicted_revenue: Optional[float] = None  # ML-predicted revenue in USD
    prediction_confidence: Optional[float] = None  # Confidence score 0-1
    headquarters: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    # PitchBook data
    primary_industry_group: Optional[str] = None
    primary_industry_sector: Optional[str] = None
    verticals: Optional[str] = None
    current_revenue_usd: Optional[float] = None
    hq_location: Optional[str] = None
    hq_country: Optional[str] = None
    last_known_valuation_usd: Optional[float] = None
    
    class Config:
        from_attributes = True


class PEFirmResponse(BaseModel):
    id: int
    name: str
    total_investments: int
    active_count: int
    exit_count: int
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_companies: int
    total_investments: int
    total_pe_firms: int
    active_investments: int
    exited_investments: int
    co_investments: int
    enrichment_rate: float


# Authentication Models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    email: str

@app.get("/")
def read_root():
    """API root endpoint"""
    return {
        "message": "PE Portfolio API V2",
        "version": "2.0.0",
        "endpoints": {
            "companies": "/api/companies",
            "investments": "/api/investments",
            "pe_firms": "/api/pe-firms",
            "stats": "/api/stats",
            "auth": "/api/auth/login"
        }
    }

@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """
    Login endpoint for admin authentication
    Returns JWT token on successful login
    """
    user = authenticate_admin(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        email=user["email"]
    )


@app.get("/api/stats", response_model=StatsResponse)
def get_stats():
    """Get overall portfolio statistics"""
    session = get_session()
    
    try:
        total_companies = session.query(Company).count()
        total_investments = session.query(CompanyPEInvestment).count()
        total_pe_firms = session.query(PEFirm).count()
        
        active_investments = session.query(CompanyPEInvestment).filter_by(computed_status='Active').count()
        exit_investments = session.query(CompanyPEInvestment).filter_by(computed_status='Exit').count()
        
        # Co-investments: companies with multiple PE firms
        co_investments = session.query(Company.id).join(CompanyPEInvestment).group_by(Company.id).having(
            func.count(CompanyPEInvestment.pe_firm_id) > 1
        ).count()
        
        # Enrichment rate: companies with LinkedIn URLs
        enriched = session.query(Company).filter(Company.linkedin_url != None).count()
        enrichment_rate = (enriched / total_companies * 100) if total_companies > 0 else 0
        
        return StatsResponse(
            total_companies=total_companies,
            total_investments=total_investments,
            total_pe_firms=total_pe_firms,
            active_investments=active_investments,
            exited_investments=exit_investments,
            co_investments=co_investments,
            enrichment_rate=round(enrichment_rate, 1)
        )
    finally:
        session.close()


@app.get("/api/pe-firms", response_model=List[PEFirmResponse])
def get_pe_firms():
    """Get all PE firms with statistics"""
    session = get_session()
    
    try:
        # Get all PE firms
        firms = session.query(PEFirm).all()
        
        # Get investment counts in a single query using GROUP BY
        investment_stats = session.query(
            CompanyPEInvestment.pe_firm_id,
            func.count(CompanyPEInvestment.id).label('total'),
            func.sum(case((CompanyPEInvestment.computed_status == 'Active', 1), else_=0)).label('active'),
            func.sum(case((CompanyPEInvestment.computed_status == 'Exit', 1), else_=0)).label('exited')
        ).group_by(CompanyPEInvestment.pe_firm_id).all()
        
        # Create a lookup dictionary for fast access
        stats_dict = {
            stat.pe_firm_id: {
                'total': stat.total,
                'active': stat.active,
                'exited': stat.exited
            }
            for stat in investment_stats
        }
        
        # Build result list
        result = []
        for firm in firms:
            stats = stats_dict.get(firm.id, {'total': 0, 'active': 0, 'exited': 0})
            result.append(PEFirmResponse(
                id=firm.id,
                name=firm.name,
                total_investments=stats['total'],
                active_count=stats['active'],
                exit_count=stats['exited']
            ))
        
        return result
    finally:
        session.close()


@app.get("/api/locations")
def get_locations():
    """Get all unique locations (countries, states, cities) with counts"""
    session = get_session()
    
    try:
        # Get countries with counts
        countries = session.query(
            Company.country,
            func.count(Company.id).label('count')
        ).filter(
            Company.country != None,
            Company.country != ''
        ).group_by(Company.country).order_by(desc('count')).all()
        
        # Get states/regions with counts (grouped by country for better organization)
        states = session.query(
            Company.state_region,
            Company.country,
            func.count(Company.id).label('count')
        ).filter(
            Company.state_region != None,
            Company.state_region != ''
        ).group_by(Company.state_region, Company.country).order_by(desc('count')).all()
        
        # Get cities with counts (limited to top cities to avoid overwhelming UI)
        cities = session.query(
            Company.city,
            Company.state_region,
            Company.country,
            func.count(Company.id).label('count')
        ).filter(
            Company.city != None,
            Company.city != ''
        ).group_by(Company.city, Company.state_region, Company.country).order_by(desc('count')).limit(100).all()
        
        return {
            "countries": [{"name": c[0], "count": c[1]} for c in countries],
            "states": [{"name": s[0], "country": s[1], "count": s[2]} for s in states],
            "cities": [{"name": c[0], "state": c[1], "country": c[2], "count": c[3]} for c in cities]
        }
    finally:
        session.close()


@app.get("/api/pitchbook-metadata")
def get_pitchbook_metadata():
    """Get all unique PitchBook industry groups, sectors, and verticals"""
    session = get_session()
    
    try:
        # Get all unique industry groups
        groups = session.query(Company.primary_industry_group).filter(
            Company.primary_industry_group != None,
            Company.primary_industry_group != ''
        ).distinct().all()
        
        # Get all unique industry sectors
        sectors = session.query(Company.primary_industry_sector).filter(
            Company.primary_industry_sector != None,
            Company.primary_industry_sector != ''
        ).distinct().all()
        
        # Get all unique verticals (need to split comma-separated values)
        vertical_rows = session.query(Company.verticals).filter(
            Company.verticals != None,
            Company.verticals != ''
        ).all()
        
        # Parse comma-separated verticals
        all_verticals = set()
        for row in vertical_rows:
            if row[0]:
                verticals_list = [v.strip() for v in row[0].split(',')]
                all_verticals.update(verticals_list)
        
        return {
            "industry_groups": sorted([g[0] for g in groups if g[0]]),
            "industry_sectors": sorted([s[0] for s in sectors if s[0]]),
            "verticals": sorted(list(all_verticals))
        }
    finally:
        session.close()


@app.get("/api/investments", response_model=List[InvestmentResponse])
def get_investments(
    pe_firm: Optional[str] = Query(None, description="Filter by PE firm name(s), comma-separated for multiple"),
    status: Optional[str] = Query(None, description="Filter by status (Active/Exit)"),
    exit_type: Optional[str] = Query(None, description="Filter by exit type (IPO/Acquisition)"),
    industry: Optional[str] = Query(None, description="Filter by industry category(ies), comma-separated for multiple"),
    industry_group: Optional[str] = Query(None, description="Filter by PitchBook industry group(s), comma-separated for multiple"),
    industry_sector: Optional[str] = Query(None, description="Filter by PitchBook industry sector(s), comma-separated for multiple"),
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
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get all investments with filters (supports multi-select with comma-separated values)"""
    session = get_session()
    
    try:
        query = session.query(CompanyPEInvestment).join(Company).join(PEFirm)
        
        # Apply filters with multi-select support
        if pe_firm:
            pe_firms = [f.strip() for f in pe_firm.split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))
        
        if status:
            query = query.filter(CompanyPEInvestment.computed_status.ilike(f"%{status}%"))
        
        if exit_type:
            query = query.filter(CompanyPEInvestment.exit_type.ilike(f"%{exit_type}%"))
        
        if industry:
            from src.models.database_models_v2 import CompanyTag
            # Filter by individual industry tags instead of string matching
            industries = [i.strip() for i in industry.split(',')]
            # Join with company_tags table and filter by industry tags
            query = query.join(CompanyTag, Company.id == CompanyTag.company_id).filter(
                CompanyTag.tag_category == 'industry',
                CompanyTag.tag_value.in_(industries)
            ).distinct()
        
        # PitchBook filters
        if industry_group:
            groups = [g.strip() for g in industry_group.split(',')]
            query = query.filter(
                Company.primary_industry_group != None,
                Company.primary_industry_group.in_(groups)
            )
        
        if industry_sector:
            sectors = [s.strip() for s in industry_sector.split(',')]
            query = query.filter(
                Company.primary_industry_sector != None,
                Company.primary_industry_sector.in_(sectors)
            )
        
        if verticals:
            # Verticals are comma-separated in the database, so we need to check if any match
            vertical_list = [v.strip() for v in verticals.split(',')]
            vertical_conditions = [Company.verticals.ilike(f"%{v}%") for v in vertical_list]
            query = query.filter(
                Company.verticals != None,
                or_(*vertical_conditions)
            )
        
        # Location filters
        if country:
            countries = [c.strip() for c in country.split(',')]
            query = query.filter(
                Company.country != None,
                Company.country.in_(countries)
            )
        
        if state_region:
            states = [s.strip() for s in state_region.split(',')]
            query = query.filter(
                Company.state_region != None,
                Company.state_region.in_(states)
            )
        
        if city:
            cities = [c.strip() for c in city.split(',')]
            query = query.filter(
                Company.city != None,
                Company.city.in_(cities)
            )
        
        # Revenue filters
        if min_revenue is not None:
            query = query.filter(Company.current_revenue_usd >= min_revenue)
        
        if max_revenue is not None:
            query = query.filter(Company.current_revenue_usd <= max_revenue)
        
        # Employee count filters
        if min_employees is not None:
            # Try to parse employee_count field (which might be a range like "101-250")
            query = query.filter(
                or_(
                    Company.projected_employee_count >= min_employees,
                    Company.employee_count >= min_employees,
                    Company.crunchbase_employee_count.ilike(f"%{min_employees}%")
                )
            )
        
        if max_employees is not None:
            query = query.filter(
                or_(
                    Company.projected_employee_count <= max_employees,
                    Company.employee_count <= max_employees,
                    Company.crunchbase_employee_count.ilike(f"%{max_employees}%")
                )
            )
        
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%"))
        
        # Order by company name
        query = query.order_by(Company.name)
        
        # Apply pagination
        investments = query.offset(offset).limit(limit).all()
        
        # Format response
        result = []
        for inv in investments:
            # Build headquarters from geographic fields (prioritize PitchBook data)
            hq_parts = []
            
            # Use PitchBook location first if available
            if inv.company.hq_location:
                hq_parts.append(inv.company.hq_location)
                if inv.company.hq_country:
                    hq_parts.append(inv.company.hq_country)
            # Fall back to city/state/country
            else:
                if inv.company.city:
                    hq_parts.append(inv.company.city)
                if inv.company.state_region:
                    hq_parts.append(inv.company.state_region)
                if inv.company.country:
                    hq_parts.append(inv.company.country)
            
            headquarters = ", ".join(hq_parts) if hq_parts else None
            
            # WORKAROUND: Get crunchbase_url via raw SQL if model cache issue on Railway
            crunchbase_url = None
            try:
                # Try direct attribute access first
                crunchbase_url = inv.company.crunchbase_url
            except AttributeError:
                # Model cache issue - use raw SQL fallback
                try:
                    from sqlalchemy import text
                    cb_result = session.execute(
                        text("SELECT crunchbase_url FROM companies WHERE id = :id"),
                        {"id": inv.company.id}
                    ).fetchone()
                    if cb_result:
                        crunchbase_url = cb_result[0]
                except Exception as e:
                    print(f"[ERROR] Failed to get crunchbase_url for company {inv.company.id}: {e}")
                    crunchbase_url = None
            
            # Get individual industry tags for this company (excluding "Other")
            from src.models.database_models_v2 import CompanyTag
            industry_tags = session.query(CompanyTag.tag_value).filter(
                CompanyTag.company_id == inv.company.id,
                CompanyTag.tag_category == 'industry',
                CompanyTag.tag_value != 'Other'
            ).all()
            industries_list = [tag[0] for tag in industry_tags]
            
            result.append(InvestmentResponse(
                investment_id=inv.id,
                company_id=inv.company.id,
                company_name=inv.company.name,
                pe_firm_name=inv.pe_firm.name,
                status=inv.computed_status or 'Unknown',
                raw_status=inv.raw_status,
                exit_type=inv.exit_type,
                exit_info=inv.exit_info,
                investment_year=inv.investment_year,
                sector=inv.sector_page,
                revenue_range=decode_revenue_range(inv.company.revenue_range),
                employee_count=get_employee_count_display(inv.company),
                industry_category=inv.company.industry_category,
                industries=industries_list,
                predicted_revenue=inv.company.predicted_revenue,
                prediction_confidence=inv.company.prediction_confidence,
                headquarters=headquarters,
                website=inv.company.website,
                linkedin_url=inv.company.linkedin_url,
                crunchbase_url=crunchbase_url,
                # PitchBook data
                primary_industry_group=getattr(inv.company, 'primary_industry_group', None),
                primary_industry_sector=getattr(inv.company, 'primary_industry_sector', None),
                verticals=getattr(inv.company, 'verticals', None),
                current_revenue_usd=float(inv.company.current_revenue_usd) if getattr(inv.company, 'current_revenue_usd', None) else None,
                hq_location=getattr(inv.company, 'hq_location', None),
                hq_country=getattr(inv.company, 'hq_country', None),
                last_known_valuation_usd=float(inv.company.last_known_valuation_usd) if getattr(inv.company, 'last_known_valuation_usd', None) else None
            ))
        
        return result
    finally:
        session.close()


@app.get("/api/companies", response_model=List[CompanyResponse])
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
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get companies (deduplicated across PE firms)"""
    session = get_session()
    
    try:
        # Start with base query - always join to get PE firm data
        query = session.query(Company).join(Company.investments).join(CompanyPEInvestment.pe_firm)
        
        # Apply all filters
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%"))
        
        # PE Firm filter
        if pe_firm:
            pe_firms = [f.strip() for f in pe_firm.split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))
        
        # Status filter
        if status:
            query = query.filter(CompanyPEInvestment.computed_status.ilike(f"%{status}%"))
        
        if industry:
            from src.models.database_models_v2 import CompanyTag
            # Filter by individual industry tags instead of string matching
            industries = [i.strip() for i in industry.split(',')]
            # Join with company_tags table and filter by industry tags
            query = query.join(CompanyTag, Company.id == CompanyTag.company_id).filter(
                CompanyTag.tag_category == 'industry',
                CompanyTag.tag_value.in_(industries)
            ).distinct()
        
        # PitchBook filters
        if industry_group:
            groups = [g.strip() for g in industry_group.split(',')]
            query = query.filter(
                Company.primary_industry_group != None,
                Company.primary_industry_group.in_(groups)
            )
        
        if industry_sector:
            sectors = [s.strip() for s in industry_sector.split(',')]
            query = query.filter(
                Company.primary_industry_sector != None,
                Company.primary_industry_sector.in_(sectors)
            )
        
        if verticals:
            # Verticals are comma-separated in the database, so we need to check if any match
            vertical_list = [v.strip() for v in verticals.split(',')]
            vertical_conditions = [Company.verticals.ilike(f"%{v}%") for v in vertical_list]
            query = query.filter(
                Company.verticals != None,
                or_(*vertical_conditions)
            )
        
        # Location filters
        if country:
            countries = [c.strip() for c in country.split(',')]
            query = query.filter(
                Company.country != None,
                Company.country.in_(countries)
            )
        
        if state_region:
            states = [s.strip() for s in state_region.split(',')]
            
            # If filtering by state but no country filter is set,
            # automatically filter to US for US states to avoid bad data
            us_states = {'California', 'New York', 'Texas', 'Florida', 'Massachusetts', 
                        'Washington', 'Illinois', 'Georgia', 'Colorado', 'Virginia',
                        'North Carolina', 'Pennsylvania', 'Ohio', 'Michigan', 'Arizona',
                        'Minnesota', 'New Jersey', 'Maryland', 'Wisconsin', 'Indiana',
                        'Tennessee', 'Missouri', 'Connecticut', 'Oregon', 'Nevada',
                        'Utah', 'Iowa', 'Kansas', 'Arkansas', 'Mississippi', 'Alabama',
                        'Louisiana', 'Kentucky', 'South Carolina', 'Oklahoma', 'New Mexico',
                        'Nebraska', 'West Virginia', 'Idaho', 'Hawaii', 'New Hampshire',
                        'Maine', 'Montana', 'Rhode Island', 'Delaware', 'South Dakota',
                        'North Dakota', 'Alaska', 'Vermont', 'Wyoming', 'District of Columbia'}
            
            # Check if any of the selected states are US states
            selected_us_states = [s for s in states if s in us_states]
            
            if selected_us_states and not country:
                # If US states selected and no country filter, add US country filter
                query = query.filter(
                    Company.country == 'United States',
                    Company.state_region != None,
                    Company.state_region.in_(states)
                )
            else:
                # Otherwise just filter by state
                query = query.filter(
                    Company.state_region != None,
                    Company.state_region.in_(states)
                )
        
        if city:
            cities = [c.strip() for c in city.split(',')]
            query = query.filter(
                Company.city != None,
                Company.city.in_(cities)
            )
        
        if revenue_range:
            revenue_ranges = [r.strip() for r in revenue_range.split(',')]
            revenue_conditions = []
            for rr in revenue_ranges:
                # First check for exact match in our mapping
                if rr in REVENUE_RANGE_CODES:
                    revenue_conditions.append(Company.revenue_range == REVENUE_RANGE_CODES[rr])
                else:
                    # Fallback to fuzzy matching for partial values
                    revenue_conditions.append(Company.revenue_range.ilike(f"%{rr}%"))
                    # Also check if this partial value matches any key
                    for readable, code in REVENUE_RANGE_CODES.items():
                        if rr in readable:
                            revenue_conditions.append(Company.revenue_range == code)
            query = query.filter(or_(*revenue_conditions))
        
        if employee_count:
            # Smart split: check for exact matches with commas first, then split
            employee_conditions = []
            remaining = employee_count
            matched_values = []
            
            # First, extract exact matches that contain commas (like "501-1,000")
            for key in EMPLOYEE_COUNT_CODES.keys():
                if ',' in key and key in remaining:
                    matched_values.append(key)
                    remaining = remaining.replace(key, '')
            
            # Now split the remaining by comma and add them
            if remaining.strip(','):
                for ec in remaining.split(','):
                    ec = ec.strip()
                    if ec:
                        matched_values.append(ec)
            
            # Build conditions for all matched values
            for ec in matched_values:
                # First check for exact match in our mapping
                if ec in EMPLOYEE_COUNT_CODES:
                    # Check both Crunchbase range and projected count fields
                    employee_conditions.append(Company.crunchbase_employee_count == EMPLOYEE_COUNT_CODES[ec])
                else:
                    # Fallback to fuzzy matching on Crunchbase field
                    employee_conditions.append(Company.crunchbase_employee_count.ilike(f"%{ec}%"))
                    # Also check if this partial value matches any key
                    for readable, code in EMPLOYEE_COUNT_CODES.items():
                        if ec in readable:
                            employee_conditions.append(Company.crunchbase_employee_count == code)
            
            if employee_conditions:
                query = query.filter(or_(*employee_conditions))
        
        # Revenue min/max filters
        if min_revenue is not None:
            query = query.filter(Company.current_revenue_usd >= min_revenue)
        
        if max_revenue is not None:
            query = query.filter(Company.current_revenue_usd <= max_revenue)
        
        # Employee count min/max filters
        if min_employees is not None:
            query = query.filter(
                or_(
                    Company.projected_employee_count >= min_employees,
                    Company.employee_count >= min_employees,
                    Company.crunchbase_employee_count.ilike(f"%{min_employees}%")
                )
            )
        
        if max_employees is not None:
            query = query.filter(
                or_(
                    Company.projected_employee_count <= max_employees,
                    Company.employee_count <= max_employees,
                    Company.crunchbase_employee_count.ilike(f"%{max_employees}%")
                )
            )
        
        if is_public is not None:
            query = query.filter(Company.is_public == is_public)
        
        if pe_firm:
            pe_firms = [f.strip() for f in pe_firm.split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))
        
        # Use distinct to avoid duplicates from the join, then add eager loading
        query = query.distinct().options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm)
        )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Add total count to response headers
        response.headers["X-Total-Count"] = str(total_count)
        
        # Order by name
        query = query.order_by(Company.name)
        
        # Apply pagination
        companies = query.offset(offset).limit(limit).all()
        
        # Format response with PE firms list
        result = []
        for company in companies:
            pe_firms = [inv.pe_firm.name for inv in company.investments]
            status = company.investments[0].computed_status if company.investments else 'Unknown'
            exit_type = company.investments[0].exit_type if company.investments else None
            investment_year = company.investments[0].investment_year if company.investments else None
            
            # Build headquarters from geographic fields (prioritize PitchBook data)
            hq_parts = []
            
            # Use PitchBook location first if available
            if company.hq_location:
                hq_parts.append(company.hq_location)
                if company.hq_country:
                    hq_parts.append(company.hq_country)
            # Fall back to city/state/country
            else:
                if company.city:
                    hq_parts.append(company.city)
                if company.state_region:
                    hq_parts.append(company.state_region)
                if company.country:
                    hq_parts.append(company.country)
            
            headquarters = ", ".join(hq_parts) if hq_parts else None
            
            # WORKAROUND: Get crunchbase_url via raw SQL if model cache issue on Railway
            crunchbase_url = None
            try:
                # Try direct attribute access first
                crunchbase_url = company.crunchbase_url
            except AttributeError:
                # Model cache issue - use raw SQL fallback
                try:
                    from sqlalchemy import text
                    cb_result = session.execute(
                        text("SELECT crunchbase_url FROM companies WHERE id = :id"),
                        {"id": company.id}
                    ).fetchone()
                    if cb_result:
                        crunchbase_url = cb_result[0]
                except Exception as e:
                    print(f"[ERROR] Failed to get crunchbase_url for company {company.id}: {e}")
                    crunchbase_url = None
            
            # Clean industry_category by removing "Other" and splitting into array
            industries_list = []
            if company.industry_category:
                # Split by comma and filter out "Other"
                industries_list = [
                    ind.strip() 
                    for ind in company.industry_category.split(',') 
                    if ind.strip().lower() != 'other'
                ]
            
            result.append(CompanyResponse(
                id=company.id,
                name=company.name,
                former_name=getattr(company, 'former_name', None),
                pe_firms=pe_firms,
                status=status,
                exit_type=exit_type,
                investment_year=investment_year,
                headquarters=headquarters,
                website=company.website,
                linkedin_url=company.linkedin_url,
                crunchbase_url=crunchbase_url,
                description=company.description,
                revenue_range=decode_revenue_range(company.revenue_range),
                employee_count=get_employee_count_display(company),
                crunchbase_employee_range=decode_employee_count(company.crunchbase_employee_count) if getattr(company, 'crunchbase_employee_count', None) else None,
                scraped_employee_count=getattr(company, 'projected_employee_count', None),
                industry_category=company.industry_category,
                industries=industries_list,
                # Funding data
                total_funding_usd=getattr(company, 'total_funding_usd', None),
                num_funding_rounds=getattr(company, 'num_funding_rounds', None),
                latest_funding_type=getattr(company, 'latest_funding_type', None),
                latest_funding_date=company.latest_funding_date.isoformat() if getattr(company, 'latest_funding_date', None) else None,
                funding_stage_encoded=getattr(company, 'funding_stage_encoded', None),
                avg_round_size_usd=getattr(company, 'avg_round_size_usd', None),
                total_investors=getattr(company, 'total_investors', None),
                # Predictions
                predicted_revenue=getattr(company, 'predicted_revenue', None),
                prediction_confidence=getattr(company, 'prediction_confidence', None),
                is_public=getattr(company, 'is_public', None),
                stock_exchange=getattr(company, 'ipo_exchange', None),
                # PitchBook data
                investor_name=getattr(company, 'investor_name', None),
                investor_status=getattr(company, 'investor_status', None),
                investor_holding=getattr(company, 'investor_holding', None),
                current_revenue_usd=float(company.current_revenue_usd) if getattr(company, 'current_revenue_usd', None) else None,
                last_known_valuation_usd=float(company.last_known_valuation_usd) if getattr(company, 'last_known_valuation_usd', None) else None,
                primary_industry_group=getattr(company, 'primary_industry_group', None),
                primary_industry_sector=getattr(company, 'primary_industry_sector', None),
                hq_location=getattr(company, 'hq_location', None),
                hq_country=getattr(company, 'hq_country', None),
                last_financing_date=company.last_financing_date.isoformat() if getattr(company, 'last_financing_date', None) else None,
                last_financing_size_usd=float(company.last_financing_size_usd) if getattr(company, 'last_financing_size_usd', None) else None,
                last_financing_deal_type=getattr(company, 'last_financing_deal_type', None),
                verticals=getattr(company, 'verticals', None)
            ))
        
        return result
    finally:
        session.close()


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int):
    """Get a specific company by ID"""
    session = get_session()
    
    try:
        company = session.query(Company).options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm)
        ).filter_by(id=company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Debug logging
        print(f"\n=== DEBUG get_company({company_id}) ===")
        print(f"Company name: {company.name}")
        print(f"Direct access - prediction_confidence: {company.prediction_confidence}")
        print(f"Direct access - total_funding_usd: {company.total_funding_usd}")
        print(f"getattr - prediction_confidence: {getattr(company, 'prediction_confidence', 'ATTR_NOT_FOUND')}")
        print(f"getattr - total_funding_usd: {getattr(company, 'total_funding_usd', 'ATTR_NOT_FOUND')}")
        
        pe_firms = [inv.pe_firm.name for inv in company.investments]
        status = company.investments[0].computed_status if company.investments else 'Unknown'
        exit_type = company.investments[0].exit_type if company.investments else None
        investment_year = company.investments[0].investment_year if company.investments else None
        
        # Build headquarters from geographic fields (prioritize PitchBook data)
        hq_parts = []
        
        # Use PitchBook location first if available
        if company.hq_location:
            hq_parts.append(company.hq_location)
            if company.hq_country:
                hq_parts.append(company.hq_country)
        # Fall back to city/state/country
        else:
            if company.city:
                hq_parts.append(company.city)
            if company.state_region:
                hq_parts.append(company.state_region)
            if company.country:
                hq_parts.append(company.country)
        
        headquarters = ", ".join(hq_parts) if hq_parts else None

        # Get crunchbase_url with fallback
        crunchbase_url = None
        try:
            crunchbase_url = company.crunchbase_url
        except AttributeError:
            # Fallback if attribute access fails
            try:
                from sqlalchemy import text
                cb_result = session.execute(
                    text("SELECT crunchbase_url FROM companies WHERE id = :id"),
                    {"id": company.id}
                ).fetchone()
                if cb_result:
                    crunchbase_url = cb_result[0]
            except Exception as e:
                print(f"[ERROR] Failed to get crunchbase_url for company {company.id}: {e}")

        # Get individual industry tags for this company (excluding "Other")
        from src.models.database_models_v2 import CompanyTag
        industry_tags = session.query(CompanyTag.tag_value).filter(
            CompanyTag.company_id == company.id,
            CompanyTag.tag_category == 'industry',
            CompanyTag.tag_value != 'Other'
        ).all()
        industries_list = [tag[0] for tag in industry_tags]

        return CompanyResponse(
            id=company.id,
            name=company.name,
            former_name=getattr(company, 'former_name', None),
            pe_firms=pe_firms,
            status=status,
            exit_type=exit_type,
            investment_year=investment_year,
            headquarters=headquarters,
            website=company.website,
            linkedin_url=company.linkedin_url,
            crunchbase_url=crunchbase_url,
            description=company.description,
            revenue_range=decode_revenue_range(company.revenue_range),
            employee_count=get_employee_count_display(company),
            crunchbase_employee_range=decode_employee_count(company.crunchbase_employee_count) if getattr(company, 'crunchbase_employee_count', None) else None,
            scraped_employee_count=getattr(company, 'projected_employee_count', None),
            industry_category=company.industry_category,
            industries=industries_list,
            # Funding data
            total_funding_usd=getattr(company, 'total_funding_usd', None),
            num_funding_rounds=getattr(company, 'num_funding_rounds', None),
            latest_funding_type=getattr(company, 'latest_funding_type', None),
            latest_funding_date=company.latest_funding_date.isoformat() if getattr(company, 'latest_funding_date', None) else None,
            funding_stage_encoded=getattr(company, 'funding_stage_encoded', None),
            avg_round_size_usd=getattr(company, 'avg_round_size_usd', None),
            total_investors=getattr(company, 'total_investors', None),
            # Predictions
            predicted_revenue=getattr(company, 'predicted_revenue', None),
            prediction_confidence=getattr(company, 'prediction_confidence', None),
            is_public=getattr(company, 'is_public', None),
            stock_exchange=getattr(company, 'ipo_exchange', None),
            # PitchBook data
            investor_name=getattr(company, 'investor_name', None),
            investor_status=getattr(company, 'investor_status', None),
            investor_holding=getattr(company, 'investor_holding', None),
            current_revenue_usd=float(company.current_revenue_usd) if getattr(company, 'current_revenue_usd', None) else None,
            last_known_valuation_usd=float(company.last_known_valuation_usd) if getattr(company, 'last_known_valuation_usd', None) else None,
            primary_industry_group=getattr(company, 'primary_industry_group', None),
            primary_industry_sector=getattr(company, 'primary_industry_sector', None),
            hq_location=getattr(company, 'hq_location', None),
            hq_country=getattr(company, 'hq_country', None),
            last_financing_date=company.last_financing_date.isoformat() if getattr(company, 'last_financing_date', None) else None,
            last_financing_size_usd=float(company.last_financing_size_usd) if getattr(company, 'last_financing_size_usd', None) else None,
            last_financing_deal_type=getattr(company, 'last_financing_deal_type', None),
            verticals=getattr(company, 'verticals', None)
        )
    finally:
        session.close()


@app.get("/api/companies/{company_id}/investments")
def get_company_investments(company_id: int):
    """Get all PE firm investments for a specific company"""
    session = get_session()
    
    try:
        company = session.query(Company).options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm)
        ).filter_by(id=company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        investments_list = []
        for inv in company.investments:
            investments_list.append({
                "investment_id": inv.id,
                "pe_firm_id": inv.pe_firm_id,
                "pe_firm_name": inv.pe_firm.name,
                "status": inv.computed_status or "Unknown",
                "raw_status": inv.raw_status,
                "exit_type": inv.exit_type,
                "exit_info": inv.exit_info,
                "exit_year": inv.exit_year,
                "investment_year": inv.investment_year
            })
        
        return investments_list
    finally:
        session.close()


@app.get("/api/companies/{company_id}/funding-rounds")
def get_company_funding_rounds(company_id: int):
    """Get all funding rounds for a specific company"""
    session = get_session()
    
    try:
        company = session.query(Company).filter_by(id=company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        funding_rounds = session.query(FundingRound).filter_by(company_id=company_id).order_by(FundingRound.announced_on).all()
        
        rounds_list = []
        for round in funding_rounds:
            rounds_list.append({
                "id": round.id,
                "announced_on": round.announced_on.isoformat() if round.announced_on else None,
                "investment_type": round.investment_type,
                "money_raised_usd": round.money_raised_usd,
                "investor_names": round.investor_names,
                "num_investors": round.num_investors
            })
        
        return rounds_list
    finally:
        session.close()


# Admin authentication
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "your-secret-admin-key-here")

def verify_admin(
    x_admin_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """
    Verify admin access via either:
    1. JWT token (Authorization: Bearer <token>) - NEW
    2. API key (X-Admin-Key: <key>) - LEGACY support
    """
    # Try JWT token first (preferred method)
    if authorization:
        try:
            payload = verify_admin_token(authorization)
            return payload
        except HTTPException:
            pass  # Fall through to API key check

    # Fall back to API key (legacy)
    if x_admin_key and x_admin_key == ADMIN_API_KEY:
        return True

    raise HTTPException(status_code=403, detail="Admin access required")


# Pydantic models for updates
class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    country: Optional[str] = None
    industry_category: Optional[str] = None
    revenue_range: Optional[str] = None  # Crunchbase code
    employee_count: Optional[str] = None  # Crunchbase code
    is_public: Optional[bool] = None
    ipo_exchange: Optional[str] = None
    ipo_date: Optional[str] = None
    # PitchBook fields
    primary_industry_group: Optional[str] = None
    primary_industry_sector: Optional[str] = None
    verticals: Optional[str] = None
    current_revenue_usd: Optional[float] = None
    last_known_valuation_usd: Optional[float] = None
    hq_location: Optional[str] = None
    hq_country: Optional[str] = None


@app.put("/api/companies/{company_id}")
async def update_company(company_id: int, company_update: CompanyUpdate):
    """
    Update company details
    """
    session = get_session()
    try:
        company = session.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Update fields that were provided
        update_data = company_update.dict(exclude_unset=True)
        updated_fields = []
        
        print(f"[DEBUG] Update data received: {update_data}")
        
        # Allowed fields that can be updated
        allowed_fields = {
            'name', 'website', 'linkedin_url', 'crunchbase_url', 'description',
            'city', 'state_region', 'country', 'industry_category', 
            'revenue_range', 'employee_count', 'is_public', 'ipo_exchange', 'ipo_date',
            # PitchBook fields
            'primary_industry_group', 'primary_industry_sector', 'verticals',
            'current_revenue_usd', 'last_known_valuation_usd', 'hq_location', 'hq_country'
        }
        
        for field, value in update_data.items():
            print(f"[DEBUG] Processing field '{field}' with value '{value}'")
            
            # Handle special mappings
            if field == "ipo_exchange":
                setattr(company, "ipo_exchange", value)
                updated_fields.append(field)
                print(f"[DEBUG] Updated ipo_exchange")
            elif field in allowed_fields:
                # Trust allowed_fields whitelist, bypass hasattr() which fails on Railway
                try:
                    setattr(company, field, value)
                    updated_fields.append(field)
                    print(f"[DEBUG] Updated {field} to '{value}'")
                except AttributeError as e:
                    print(f"[DEBUG] Failed to set {field}: {e}")
            else:
                print(f"[DEBUG] Field '{field}' not in allowed_fields")
        
        session.commit()
        session.refresh(company)
        
        return {
            "message": "Company updated successfully",
            "company_id": company_id,
            "updated_fields": updated_fields
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")
    finally:
        session.close()


@app.delete("/api/companies/{company_id}", dependencies=[Depends(verify_admin)])
async def delete_company(company_id: int):
    """
    Delete a company (Admin only)
    Requires X-Admin-Key header for authentication
    """
    session = get_session()
    try:
        company = session.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_name = company.name
        session.delete(company)
        session.commit()
        
        return {
            "message": f"Company '{company_name}' deleted successfully",
            "company_id": company_id
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
    finally:
        session.close()


class InvestmentUpdate(BaseModel):
    computed_status: Optional[str] = None
    raw_status: Optional[str] = None
    exit_type: Optional[str] = None
    exit_info: Optional[str] = None
    exit_year: Optional[str] = None
    investment_year: Optional[str] = None


@app.put("/api/investments/{investment_id}", dependencies=[Depends(verify_admin)])
async def update_investment(investment_id: int, investment_update: InvestmentUpdate):
    """
    Update investment details (Admin only)
    Requires admin authentication
    """
    session = get_session()
    try:
        investment = session.query(CompanyPEInvestment).filter(CompanyPEInvestment.id == investment_id).first()
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        
        # Update fields that were provided
        update_data = investment_update.dict(exclude_unset=True)
        updated_fields = []
        
        allowed_fields = {
            'computed_status', 'raw_status', 'exit_type', 'exit_info', 'exit_year', 'investment_year'
        }
        
        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(investment, field, value)
                updated_fields.append(field)
        
        session.commit()
        session.refresh(investment)
        
        return {
            "message": "Investment updated successfully",
            "investment_id": investment_id,
            "updated_fields": updated_fields
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating investment: {str(e)}")
    finally:
        session.close()


@app.post("/api/companies/merge")
async def merge_companies(
    source_id: int,
    target_id: int
):
    """
    Merge two companies: move all data from source to target, then delete source.
    
    Args:
        source_id: Company to merge FROM (will be deleted)
        target_id: Company to merge INTO (will be kept)
    """
    session = get_session()
    try:
        # Validate companies exist
        source = session.query(Company).filter_by(id=source_id).first()
        target = session.query(Company).filter_by(id=target_id).first()
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source company {source_id} not found")
        if not target:
            raise HTTPException(status_code=404, detail=f"Target company {target_id} not found")
        if source_id == target_id:
            raise HTTPException(status_code=400, detail="Cannot merge a company with itself")
        
        print(f"\n=== Merging Companies ===")
        print(f"Source: {source.name} (ID: {source_id})")
        print(f"Target: {target.name} (ID: {target_id})")
        
        # 1. Move all PE investments from source to target
        from src.models.database_models_v2 import CompanyPEInvestment
        investments = session.query(CompanyPEInvestment).filter_by(company_id=source_id).all()
        print(f"Moving {len(investments)} PE investments...")
        
        for inv in investments:
            # Check if target already has this PE firm
            existing = session.query(CompanyPEInvestment).filter_by(
                company_id=target_id,
                pe_firm_id=inv.pe_firm_id
            ).first()
            
            if existing:
                print(f"  Target already has {inv.pe_firm.name}, keeping target's record")
                session.delete(inv)
            else:
                print(f"  Moving {inv.pe_firm.name} investment to target")
                inv.company_id = target_id
        
        # 2. Move company tags from source to target
        from src.models.database_models_v2 import CompanyTag
        tags = session.query(CompanyTag).filter_by(company_id=source_id).all()
        print(f"Moving {len(tags)} tags...")
        
        for tag in tags:
            # Check if target already has this tag
            existing = session.query(CompanyTag).filter_by(
                company_id=target_id,
                tag_category=tag.tag_category,
                tag_value=tag.tag_value
            ).first()
            
            if existing:
                session.delete(tag)
            else:
                tag.company_id = target_id
        
        # 3. Merge data fields - keep best/most complete data
        def merge_field(field_name):
            """Helper to merge a field - prefer target, but use source if target is None"""
            source_val = getattr(source, field_name, None)
            target_val = getattr(target, field_name, None)
            
            if target_val is None and source_val is not None:
                print(f"  Copying {field_name}: {source_val}")
                setattr(target, field_name, source_val)
        
        print("Merging data fields...")
        fields_to_merge = [
            'description', 'website', 'linkedin_url', 'crunchbase_url',
            'headquarters', 'city', 'state_region', 'country',
            'revenue_range', 'predicted_revenue', 'prediction_confidence',
            'employee_count', 'scraped_employee_count', 'crunchbase_employee_range',
            'total_funding_usd', 'num_funding_rounds', 'latest_funding_type',
            'latest_funding_date', 'funding_stage_encoded', 'avg_round_size_usd',
            'total_investors', 'is_public', 'stock_exchange',
            'primary_industry_group', 'primary_industry_sector', 'verticals',
            'hq_location', 'hq_country', 'current_revenue_usd',
            'last_known_valuation_usd', 'last_financing_date',
            'last_financing_size_usd', 'last_financing_deal_type'
        ]
        
        for field in fields_to_merge:
            merge_field(field)
        
        # 4. Add former name tracking
        if target.former_name:
            target.former_name = f"{target.former_name}, {source.name}"
        else:
            target.former_name = source.name
        print(f"  Updated former_name: {target.former_name}")
        
        # 5. Delete source company
        print(f"Deleting source company: {source.name}")
        session.delete(source)
        
        # Commit transaction
        session.commit()
        print("✓ Merge completed successfully\n")
        
        return {
            "success": True,
            "message": f"Successfully merged '{source.name}' into '{target.name}'",
            "target_company_id": target_id,
            "deleted_company_id": source_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Merge failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error merging companies: {str(e)}")
    finally:
        session.close()


@app.get("/api/industries")
async def get_industries():
    """
    Get all unique industry tags with counts
    Returns list of industries sorted by company count
    """
    session = get_session()
    try:
        from sqlalchemy import func
        from src.models.database_models_v2 import CompanyTag
        
        # Get all industry tags with counts
        industries = session.query(
            CompanyTag.tag_value,
            func.count(CompanyTag.company_id).label('count')
        ).filter(
            CompanyTag.tag_category == 'industry'
        ).group_by(
            CompanyTag.tag_value
        ).order_by(
            func.count(CompanyTag.company_id).desc()
        ).all()
        
        return {
            "industries": [
                {
                    "name": industry[0],
                    "count": industry[1]
                }
                for industry in industries
            ],
            "total": len(industries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching industries: {str(e)}")
    finally:
        session.close()


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "PE Portfolio API V2",
        "version": "2.0.0",
        "endpoints": {
            "companies": "/api/companies",
            "investments": "/api/investments",
            "pe_firms": "/api/pe-firms",
            "industries": "/api/industries",
            "stats": "/api/stats"
        },
        "admin_endpoints": {
            "update_company": "PUT /api/companies/{id} (requires X-Admin-Key header)",
            "delete_company": "DELETE /api/companies/{id} (requires X-Admin-Key header)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

