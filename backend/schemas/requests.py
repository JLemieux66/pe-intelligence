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


class InvestmentUpdate(BaseModel):
    computed_status: Optional[str] = None
    raw_status: Optional[str] = None
    exit_type: Optional[str] = None
    exit_info: Optional[str] = None
    exit_year: Optional[str] = None
    investment_year: Optional[str] = None