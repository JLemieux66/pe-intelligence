"""
Database Models v2 - Many-to-Many Relationship with IPO Validation
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Date,
    Float,
    create_engine,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import re

Base = declarative_base()


class PEFirm(Base):
    """Private Equity Firm"""

    __tablename__ = "pe_firms"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    total_companies = Column(Integer)
    current_portfolio_count = Column(Integer)
    exited_portfolio_count = Column(Integer)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    extraction_time_minutes = Column(Integer)

    # Relationship
    investments = relationship("CompanyPEInvestment", back_populates="pe_firm")

    def __repr__(self):
        return f"<PEFirm(name='{self.name}', total={self.total_companies})>"


class Company(Base):
    """Unique Portfolio Company (deduplicated across PE firms)"""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    former_name = Column(String(255))  # Former/previous company name (fka/formerly)
    description = Column(Text)
    website = Column(String(500), index=True)
    linkedin_url = Column(String(500))
    crunchbase_url = Column(String(500))  # Crunchbase profile URL (2025-10-31)
    
    # Crunchbase enrichment fields
    revenue_range = Column(String(50), index=True)
    crunchbase_employee_count = Column(String(50), index=True)  # Crunchbase range (e.g., "501-1,000")

    # ML prediction fields
    predicted_revenue = Column(Float, index=True)  # ML-predicted revenue in USD
    prediction_confidence = Column(Float)  # Confidence score 0-1 for revenue prediction
    employee_count = Column(Integer, index=True)  # PitchBook exact employee count
    projected_employee_count = Column(Integer, index=True)  # Scraped exact count from LinkedIn
    
    # Funding features (calculated from funding_rounds)
    total_funding_usd = Column(Integer, index=True)  # Total funding raised across all rounds
    num_funding_rounds = Column(Integer)  # Number of funding rounds
    latest_funding_type = Column(String(100))  # Type of most recent round
    latest_funding_date = Column(Date)  # Date of most recent funding
    months_since_last_funding = Column(Integer)  # Months since last funding
    funding_stage_encoded = Column(Integer, index=True)  # Encoded funding stage (0=preseed, 7=IPO)
    avg_round_size_usd = Column(Integer)  # Average funding per round
    total_investors = Column(Integer)  # Total unique investors
    
    # Geographic fields
    country = Column(String(100), index=True)
    state_region = Column(String(100), index=True)
    city = Column(String(200), index=True)
    
    # Categorization fields
    company_size_category = Column(String(50), index=True)
    revenue_tier = Column(String(50), index=True)
    industry_category = Column(String(500), index=True)  # Expanded for comprehensive Crunchbase categories
    founded_year = Column(Integer, index=True)  # Year company was founded
    
    # Exit information (if applicable)
    is_public = Column(Boolean, default=False, index=True)
    ipo_ticker = Column(String(20))  # Stock ticker if IPO'd
    ipo_date = Column(Date)
    ipo_exchange = Column(String(50))  # NYSE, NASDAQ, LON, etc.

    # PitchBook enrichment fields
    investor_name = Column(String(255))  # PE firm name from PitchBook
    investor_status = Column(String(50))  # Active, Former, etc.
    investor_holding = Column(String(50))  # Minority, Majority, etc.
    current_revenue_usd = Column(Float)  # Revenue in millions USD
    last_known_valuation_usd = Column(Float)  # Valuation in millions USD
    primary_industry_group = Column(String(255))
    primary_industry_sector = Column(String(255))
    hq_location = Column(String(255))
    hq_country = Column(String(100))
    last_financing_date = Column(Date)
    last_financing_size_usd = Column(Float)  # Financing size in millions USD
    last_financing_deal_type = Column(String(100))
    company_last_updated = Column(DateTime)
    verticals = Column(Text)
    financing_status_note = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    investments = relationship("CompanyPEInvestment", back_populates="company", cascade="all, delete-orphan")
    tags = relationship("CompanyTag", back_populates="company", cascade="all, delete-orphan")
    funding_rounds = relationship("FundingRound", backref="company", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_name_website", "name", "website"),
        Index("idx_industry_public", "industry_category", "is_public"),
    )

    def __repr__(self):
        return f"<Company(name='{self.name}', is_public={self.is_public})>"
    
    @property
    def computed_status(self):
        """Compute overall company status based on investments"""
        if self.is_public:
            return "Public (IPO)"
        
        # Check if any PE firm still has active investment
        active_count = sum(1 for inv in self.investments if inv.computed_status == "Active")
        if active_count > 0:
            return f"Active ({active_count} firms)"
        
        return "Exited (All firms)"


class CompanyPEInvestment(Base):
    """Junction table: Relationship between Company and PE Firm"""

    __tablename__ = "company_pe_investments"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    pe_firm_id = Column(Integer, ForeignKey("pe_firms.id"), nullable=False)
    
    # Status information
    raw_status = Column(String(50), index=True)  # What PE firm's website said: 'Active', 'Current', 'Exit', etc.
    computed_status = Column(String(50), index=True)  # Normalized status: 'Active' or 'Exit'
    
    # Investment details
    investment_year = Column(String(50), index=True)
    investment_stage = Column(String(50))  # Recent/Mature/Legacy
    
    # Exit information (if applicable for this relationship)
    exit_type = Column(String(50))  # 'IPO', 'Acquisition', 'Secondary Sale', 'Buyout', etc.
    exit_info = Column(Text)  # Original exit info from scraper
    exit_year = Column(String(50))
    
    # Scraper metadata
    source_url = Column(String(500))  # URL where this relationship was found
    sector_page = Column(String(255))  # PE-firm specific sector classification
    data_area = Column(String(255))  # Vista specific
    data_fund = Column(String(255))  # Vista specific
    
    last_scraped = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="investments")
    pe_firm = relationship("PEFirm", back_populates="investments")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("company_id", "pe_firm_id", name="uq_company_pe_firm"),
        Index("idx_pe_firm_status", "pe_firm_id", "computed_status"),
        Index("idx_company_status", "company_id", "computed_status"),
        Index("idx_investment_year", "investment_year"),
    )

    def __repr__(self):
        return f"<CompanyPEInvestment(company_id={self.company_id}, pe_firm_id={self.pe_firm_id}, status='{self.computed_status}')>"
    
    def normalize_status(self):
        """
        Normalize raw_status to computed_status with validation rules:
        1. If company IPO'd → always 'Exit'
        2. If exit_type is set → 'Exit'
        3. If raw_status contains 'active', 'current', 'portfolio' → 'Active'
        4. Otherwise → 'Exit'
        """
        # Rule 1: IPO overrides everything
        if self.company and self.company.is_public:
            self.computed_status = "Exit"
            if not self.exit_type:
                self.exit_type = "IPO"
            return
        
        # Rule 2: Exit type set
        if self.exit_type and self.exit_type != "None":
            self.computed_status = "Exit"
            return
        
        # Rule 3: Check raw status
        if self.raw_status:
            status_lower = self.raw_status.lower()
            if any(word in status_lower for word in ['active', 'current', 'portfolio']):
                self.computed_status = "Active"
                return
        
        # Rule 4: Default to Exit
        self.computed_status = "Exit"
    
    @staticmethod
    def extract_ipo_info(exit_info_text):
        """
        Extract IPO ticker and exchange from exit_info text
        Returns: (ticker, exchange) tuple or (None, None)
        
        Examples:
        - "IPO: FB" → ("FB", None)
        - "IPO: LON: WPS" → ("WPS", "LON")
        - "IPO: WORK" → ("WORK", None)
        """
        if not exit_info_text or 'IPO' not in exit_info_text:
            return None, None
        
        # Pattern: IPO: <EXCHANGE>: <TICKER> or IPO: <TICKER>
        match = re.search(r'IPO:\s*(?:([A-Z]+):\s*)?([A-Z]+)', exit_info_text)
        if match:
            exchange = match.group(1)  # May be None
            ticker = match.group(2)
            return ticker, exchange
        
        return None, None


class CompanyTag(Base):
    """Flexible tagging system for companies"""
    
    __tablename__ = "company_tags"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    tag_category = Column(String(100), nullable=False, index=True)
    tag_value = Column(String(200), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    company = relationship("Company", back_populates="tags")
    
    # Indexes
    __table_args__ = (
        Index("idx_company_category", "company_id", "tag_category"),
        Index("idx_category_value", "tag_category", "tag_value"),
    )
    
    def __repr__(self):
        return f"<CompanyTag(company_id={self.company_id}, category='{self.tag_category}', value='{self.tag_value}')>"


class FundingRound(Base):
    """Funding rounds for companies from Crunchbase"""
    
    __tablename__ = "funding_rounds"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    
    # Round details
    announced_on = Column(Date, index=True)  # Date of funding round
    investment_type = Column(String(50), index=True)  # seed, series_a, series_b, etc.
    money_raised_usd = Column(Float)  # Amount raised in USD
    
    # Investor information (stored as comma-separated string for simplicity)
    investor_names = Column(Text)  # Comma-separated list of investor names
    num_investors = Column(Integer)  # Number of investors in this round
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_company_date", "company_id", "announced_on"),
        Index("idx_type_amount", "investment_type", "money_raised_usd"),
        Index("idx_date_amount", "announced_on", "money_raised_usd"),
    )
    
    def __repr__(self):
        return f"<FundingRound(company_id={self.company_id}, type='{self.investment_type}', amount=${self.money_raised_usd})>"


# Database connection functions
def get_database_url():
    """Get database URL from environment or use default."""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    return os.getenv("DATABASE_URL", "sqlite:///pe_portfolio_v2.db")


def create_database_engine():
    """Create and return database engine with connection pooling"""
    database_url = get_database_url()
    
    # Configure connection pooling for production reliability
    engine = create_engine(
        database_url,
        echo=False,
        pool_size=10,           # Maximum number of permanent connections
        max_overflow=20,        # Maximum number of temporary connections
        pool_pre_ping=True,     # Verify connections are alive before using
        pool_recycle=3600,      # Recycle connections after 1 hour
    )
    return engine


def init_database():
    """Initialize database - create all tables"""
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully!")
    return engine


def get_session():
    """Get database session"""
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    print("Creating new database schema v2...")
    init_database()
