"""
Pytest configuration and shared fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database_models_v2 import Base, Company, PEFirm, CompanyPEInvestment
from fastapi.testclient import TestClient
from backend.api_v2 import app
import os


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for fast tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a new database session for each test"""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_pe_firm(db_session):
    """Create a sample PE firm"""
    firm = PEFirm(name="Test Capital Partners")
    db_session.add(firm)
    db_session.commit()
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
        revenue_range="$10M-$50M"
    )
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def sample_investment(db_session, sample_pe_firm, sample_company):
    """Create a sample investment"""
    investment = CompanyPEInvestment(
        company_id=sample_company.id,
        pe_firm_id=sample_pe_firm.id,
        computed_status="Active",
        investment_year=2020
    )
    db_session.add(investment)
    db_session.commit()
    return investment


@pytest.fixture
def api_client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create admin authentication token for testing"""
    from backend.auth import create_access_token
    return create_access_token({"email": "test@admin.com"})
