"""
Response schemas for PE Intelligence API
"""
from typing import Optional, List, Dict
from pydantic import BaseModel


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
    employee_count: Optional[str] = None  # Display value (prefer PitchBook, fallback to scraped, then Crunchbase)
    pitchbook_employee_count: Optional[int] = None  # PitchBook exact count
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
    predicted_revenue: Optional[float] = None  # ML-predicted revenue in USD (converted from millions in DB)
    prediction_confidence: Optional[float] = None  # Confidence score 0-1
    prediction_confidence_lower: Optional[float] = None  # Lower bound of confidence interval
    prediction_confidence_upper: Optional[float] = None  # Upper bound of confidence interval
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
    predicted_revenue: Optional[float] = None  # ML-predicted revenue in USD (converted from millions in DB)
    prediction_confidence: Optional[float] = None  # Confidence score 0-1
    prediction_confidence_lower: Optional[float] = None  # Lower bound of confidence interval
    prediction_confidence_upper: Optional[float] = None  # Upper bound of confidence interval
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


class SimilarCompanyMatch(BaseModel):
    company: CompanyResponse
    similarity_score: float  # 0-100 similarity score
    reasoning: str  # AI-generated reasoning
    matching_attributes: List[str]  # Key attributes that matched


class SimilarCompaniesResponse(BaseModel):
    input_companies: List[CompanyResponse]  # Companies user selected
    matches: List[SimilarCompanyMatch]
    total_results: int


class LocationData(BaseModel):
    """Location data with count"""
    name: str
    count: int
    country: Optional[str] = None  # For states/cities
    state: Optional[str] = None    # For cities


class LocationsResponse(BaseModel):
    countries: List[LocationData]
    states: List[LocationData]
    cities: List[LocationData]


class PitchBookMetadataResponse(BaseModel):
    industry_groups: List[str]
    industry_sectors: List[str]
    verticals: List[str]
    hq_locations: List[str]
    hq_countries: List[str]


class IndustriesResponse(BaseModel):
    industries: List[str]
    categories: List[str]