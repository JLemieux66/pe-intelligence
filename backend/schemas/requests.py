"""
Request schemas for PE Intelligence API
"""
from typing import Optional, List, Dict
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    email: str


class SimilarCompaniesRequest(BaseModel):
    company_ids: List[int]  # Input company IDs to find similar companies to
    limit: int = 20  # Max number of similar companies to return
    min_score: float = 60.0  # Minimum similarity score (0-100)
    filters: Optional[Dict[str, str]] = None  # Optional filters (country, sector, etc.)


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
    employee_count: Optional[int] = None  # PitchBook exact count
    crunchbase_employee_count: Optional[str] = None  # Crunchbase range code
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


class InvestmentUpdate(BaseModel):
    computed_status: Optional[str] = None
    raw_status: Optional[str] = None
    exit_type: Optional[str] = None
    exit_info: Optional[str] = None
    exit_year: Optional[str] = None
    investment_year: Optional[str] = None


class CompanyTagCreate(BaseModel):
    tag_category: str
    tag_value: str


class FundingRoundCreate(BaseModel):
    announced_on: Optional[str] = None  # Date in YYYY-MM-DD format
    investment_type: Optional[str] = None  # seed, series_a, series_b, etc.
    money_raised_usd: Optional[float] = None
    investor_names: Optional[str] = None  # Comma-separated
    num_investors: Optional[int] = None


class PEInvestmentCreate(BaseModel):
    pe_firm_name: str  # Name of PE firm (will be looked up or created)
    raw_status: Optional[str] = None
    computed_status: Optional[str] = None
    investment_year: Optional[str] = None
    investment_stage: Optional[str] = None
    exit_type: Optional[str] = None
    exit_info: Optional[str] = None
    exit_year: Optional[str] = None


class CompanyCreate(BaseModel):
    # Required fields
    name: str

    # Basic information
    former_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None

    # Geographic data
    country: Optional[str] = None
    state_region: Optional[str] = None
    city: Optional[str] = None
    hq_location: Optional[str] = None
    hq_country: Optional[str] = None

    # Categorization
    industry_category: Optional[str] = None
    primary_industry_group: Optional[str] = None
    primary_industry_sector: Optional[str] = None
    verticals: Optional[str] = None
    founded_year: Optional[int] = None

    # Employee data
    employee_count: Optional[int] = None  # PitchBook exact count
    projected_employee_count: Optional[int] = None  # LinkedIn scraped count
    crunchbase_employee_count: Optional[str] = None  # Range code like "c_00501_01000"

    # Revenue data
    revenue_range: Optional[str] = None  # Crunchbase code
    current_revenue_usd: Optional[float] = None  # In millions USD
    predicted_revenue: Optional[float] = None  # In millions USD
    prediction_confidence: Optional[float] = None  # 0-1 confidence score

    # Funding data
    total_funding_usd: Optional[int] = None
    num_funding_rounds: Optional[int] = None
    latest_funding_type: Optional[str] = None
    latest_funding_date: Optional[str] = None  # Date in YYYY-MM-DD format
    months_since_last_funding: Optional[int] = None
    funding_stage_encoded: Optional[int] = None  # 0=preseed, 7=IPO
    avg_round_size_usd: Optional[int] = None
    total_investors: Optional[int] = None

    # IPO/Exit information
    is_public: Optional[bool] = False
    ipo_ticker: Optional[str] = None
    ipo_date: Optional[str] = None  # Date in YYYY-MM-DD format
    ipo_exchange: Optional[str] = None  # NYSE, NASDAQ, LON, etc.

    # PitchBook data
    investor_name: Optional[str] = None
    investor_status: Optional[str] = None
    investor_holding: Optional[str] = None
    last_known_valuation_usd: Optional[float] = None  # In millions USD
    last_financing_date: Optional[str] = None  # Date in YYYY-MM-DD format
    last_financing_size_usd: Optional[float] = None  # In millions USD
    last_financing_deal_type: Optional[str] = None
    financing_status_note: Optional[str] = None

    # Categorization fields
    company_size_category: Optional[str] = None
    revenue_tier: Optional[str] = None

    # Associated data (nested creates)
    tags: Optional[List[CompanyTagCreate]] = []
    funding_rounds: Optional[List[FundingRoundCreate]] = []
    pe_investments: Optional[List[PEInvestmentCreate]] = []