"""
Pytest configuration and shared fixtures
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database_models_v2 import Base, Company, PEFirm, CompanyPEInvestment, get_session
from fastapi.testclient import TestClient
from backend.main import app
from datetime import datetime


# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ADMIN_EMAIL"] = "test@admin.com"
os.environ["ADMIN_PASSWORD_HASH"] = "$2b$12$test.hash.for.testing.only"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:5173"


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine"""
    # Use file-based SQLite for tests to avoid threading issues
    engine = create_engine("sqlite:///test_pe_intelligence.db", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    # Clean up test database file
    import os
    if os.path.exists("test_pe_intelligence.db"):
        os.remove("test_pe_intelligence.db")


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a new database session for each test"""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def api_client(test_db_engine):
    """Create FastAPI test client with test database"""
    # Create a session factory for the test database
    TestSession = sessionmaker(bind=test_db_engine)
    
    # Override the database dependency
    def override_get_session():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pe_firm(db_session):
    """Create a sample PE firm"""
    firm = PEFirm(
        name="Test Capital Partners",
        total_companies=5,
        current_portfolio_count=3,
        exited_portfolio_count=2,
        last_scraped=datetime.utcnow(),
        extraction_time_minutes=15
    )
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    return firm


@pytest.fixture
def sample_company(db_session):
    """Create a sample company"""
    company = Company(
        name="Test Software Inc",
        website="https://testsoftware.com",
        country="United States",
        state_region="California",
        city="San Francisco",
        primary_industry_sector="Business Products and Services (B2B)",
        primary_industry_group="Software",
        employee_count=150,
        revenue_range="$10M-$50M",
        founded_year=2015,
        is_public=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def sample_company_b2c(db_session):
    """Create a sample B2C company for filtering tests"""
    company = Company(
        name="Consumer App Co",
        website="https://consumerapp.com",
        country="United States",
        state_region="New York",
        city="New York",
        primary_industry_sector="Consumer Products and Services (B2C)",
        primary_industry_group="Consumer Services",
        employee_count=75,
        revenue_range="$1M-$10M",
        founded_year=2018,
        is_public=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def sample_investment(db_session, sample_pe_firm, sample_company):
    """Create a sample investment"""
    investment = CompanyPEInvestment(
        company_id=sample_company.id,
        pe_firm_id=sample_pe_firm.id,
        computed_status="Active",
        investment_year=2020,
        exit_type=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(investment)
    db_session.commit()
    db_session.refresh(investment)
    return investment


@pytest.fixture
def sample_investment_b2c(db_session, sample_pe_firm, sample_company_b2c):
    """Create a sample B2C investment"""
    investment = CompanyPEInvestment(
        company_id=sample_company_b2c.id,
        pe_firm_id=sample_pe_firm.id,
        computed_status="Active",
        investment_year=2021,
        exit_type=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(investment)
    db_session.commit()
    db_session.refresh(investment)
    return investment


@pytest.fixture
def admin_token():
    """Create admin authentication token for testing"""
    from backend.auth import create_access_token
    return create_access_token({"email": "test@admin.com"})


@pytest.fixture
def auth_headers(admin_token):
    """Create authorization headers for admin requests"""
    return {"Authorization": f"Bearer {admin_token}"}
