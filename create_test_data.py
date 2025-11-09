#!/usr/bin/env python3
"""
Create test data for similar companies algorithm testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.database_models_v2 import get_direct_session, Company, PEFirm, CompanyPEInvestment
from datetime import datetime

def create_test_data():
    session = get_direct_session()
    
    try:
        # Create PE Firms
        pe_firms = [
            PEFirm(name="Accel Partners", total_companies=50),
            PEFirm(name="Sequoia Capital", total_companies=75),
            PEFirm(name="Andreessen Horowitz", total_companies=60),
        ]
        
        for firm in pe_firms:
            session.add(firm)
        session.commit()
        
        # Create test companies with diverse characteristics
        companies = [
            # Tech/SaaS companies
            Company(
                name="TechCorp Solutions",
                description="Enterprise software solutions for data analytics",
                website="https://techcorp.com",
                revenue_range="$10M-$50M",
                employee_count=150,
                country="United States",
                state_region="California",
                city="San Francisco",
                industry_category="Software",
                primary_industry_group="Technology",
                primary_industry_sector="Enterprise Software",
                founded_year=2018,
                total_funding_usd=25000000,
                latest_funding_type="Series B",
                current_revenue_usd=30000000,
                verticals="Analytics, Enterprise Software"
            ),
            Company(
                name="DataFlow Analytics",
                description="AI-powered business intelligence platform",
                website="https://dataflow.com",
                revenue_range="$10M-$50M",
                employee_count=120,
                country="United States",
                state_region="California",
                city="Palo Alto",
                industry_category="Software",
                primary_industry_group="Technology",
                primary_industry_sector="Enterprise Software",
                founded_year=2019,
                total_funding_usd=20000000,
                latest_funding_type="Series A",
                current_revenue_usd=25000000,
                verticals="Analytics, AI, Business Intelligence"
            ),
            Company(
                name="CloudSync Pro",
                description="Cloud infrastructure management platform",
                website="https://cloudsync.com",
                revenue_range="$50M-$100M",
                employee_count=200,
                country="United States",
                state_region="Washington",
                city="Seattle",
                industry_category="Software",
                primary_industry_group="Technology",
                primary_industry_sector="Cloud Services",
                founded_year=2017,
                total_funding_usd=45000000,
                latest_funding_type="Series C",
                current_revenue_usd=75000000,
                verticals="Cloud, Infrastructure, DevOps"
            ),
            # Healthcare companies
            Company(
                name="MedTech Innovations",
                description="Medical device manufacturing for diagnostics",
                website="https://medtech.com",
                revenue_range="$50M-$100M",
                employee_count=300,
                country="United States",
                state_region="Massachusetts",
                city="Boston",
                industry_category="Healthcare",
                primary_industry_group="Healthcare",
                primary_industry_sector="Medical Devices",
                founded_year=2015,
                total_funding_usd=60000000,
                latest_funding_type="Series D",
                current_revenue_usd=80000000,
                verticals="Medical Devices, Diagnostics"
            ),
            Company(
                name="HealthData Systems",
                description="Healthcare data analytics and patient management",
                website="https://healthdata.com",
                revenue_range="$10M-$50M",
                employee_count=180,
                country="United States",
                state_region="Texas",
                city="Austin",
                industry_category="Healthcare",
                primary_industry_group="Healthcare",
                primary_industry_sector="Health IT",
                founded_year=2020,
                total_funding_usd=35000000,
                latest_funding_type="Series B",
                current_revenue_usd=40000000,
                verticals="Healthcare, Analytics, Patient Management"
            ),
            # Fintech companies
            Company(
                name="PayFlow Solutions",
                description="Digital payment processing platform",
                website="https://payflow.com",
                revenue_range="$100M+",
                employee_count=400,
                country="United States",
                state_region="New York",
                city="New York",
                industry_category="Financial Services",
                primary_industry_group="Financial Technology",
                primary_industry_sector="Payments",
                founded_year=2016,
                total_funding_usd=120000000,
                latest_funding_type="Series E",
                current_revenue_usd=150000000,
                verticals="Payments, Fintech, Digital Banking"
            ),
            Company(
                name="CryptoTrade Pro",
                description="Cryptocurrency trading and wallet services",
                website="https://cryptotrade.com",
                revenue_range="$50M-$100M",
                employee_count=250,
                country="United States",
                state_region="Florida",
                city="Miami",
                industry_category="Financial Services",
                primary_industry_group="Financial Technology",
                primary_industry_sector="Cryptocurrency",
                founded_year=2018,
                total_funding_usd=80000000,
                latest_funding_type="Series C",
                current_revenue_usd=90000000,
                verticals="Cryptocurrency, Trading, Blockchain"
            ),
            # E-commerce companies
            Company(
                name="ShopEasy Platform",
                description="E-commerce platform for small businesses",
                website="https://shopeasy.com",
                revenue_range="$10M-$50M",
                employee_count=160,
                country="United States",
                state_region="Illinois",
                city="Chicago",
                industry_category="Retail",
                primary_industry_group="E-commerce",
                primary_industry_sector="E-commerce Platform",
                founded_year=2019,
                total_funding_usd=30000000,
                latest_funding_type="Series B",
                current_revenue_usd=35000000,
                verticals="E-commerce, Retail, Small Business"
            ),
        ]
        
        for company in companies:
            session.add(company)
        session.commit()
        
        # Create some investments to link companies with PE firms
        investments = [
            CompanyPEInvestment(company_id=1, pe_firm_id=1, investment_date=datetime(2020, 6, 15), investment_type="Series B", is_current=True),
            CompanyPEInvestment(company_id=2, pe_firm_id=2, investment_date=datetime(2021, 3, 10), investment_type="Series A", is_current=True),
            CompanyPEInvestment(company_id=3, pe_firm_id=3, investment_date=datetime(2019, 9, 20), investment_type="Series C", is_current=True),
            CompanyPEInvestment(company_id=4, pe_firm_id=1, investment_date=datetime(2018, 12, 5), investment_type="Series D", is_current=True),
            CompanyPEInvestment(company_id=5, pe_firm_id=2, investment_date=datetime(2022, 1, 25), investment_type="Series B", is_current=True),
            CompanyPEInvestment(company_id=6, pe_firm_id=3, investment_date=datetime(2020, 8, 30), investment_type="Series E", is_current=True),
            CompanyPEInvestment(company_id=7, pe_firm_id=1, investment_date=datetime(2021, 11, 12), investment_type="Series C", is_current=True),
            CompanyPEInvestment(company_id=8, pe_firm_id=2, investment_date=datetime(2022, 4, 18), investment_type="Series B", is_current=True),
        ]
        
        for investment in investments:
            session.add(investment)
        session.commit()
        
        print("✅ Test data created successfully!")
        print(f"Created {len(pe_firms)} PE firms")
        print(f"Created {len(companies)} companies")
        print(f"Created {len(investments)} investments")
        
        # Print company details for reference
        print("\n📊 Created Companies:")
        for i, company in enumerate(companies, 1):
            print(f"{i}. {company.name} - {company.industry_category} - {company.revenue_range}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating test data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_test_data()