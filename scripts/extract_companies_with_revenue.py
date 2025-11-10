#!/usr/bin/env python3
"""
Extract all companies WITH PitchBook revenue data for ML model training.

This script connects to the PostgreSQL database and exports all companies
that have current_revenue_usd populated, along with all relevant features
for machine learning model training.
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_companies_with_revenue(database_url: str, output_file: str = None):
    """
    Extract all companies with PitchBook revenue data.

    Args:
        database_url: PostgreSQL connection string
        output_file: Output CSV file path (default: companies_with_revenue_TIMESTAMP.csv)

    Returns:
        DataFrame with all companies that have revenue data
    """
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'companies_with_revenue_{timestamp}.csv'

    logger.info(f"Connecting to database...")
    engine = create_engine(database_url)

    # Comprehensive SQL query to get all relevant features
    query = text("""
        SELECT DISTINCT
            -- Core identifiers
            c.id,
            c.name,
            c.website,
            c.description,

            -- TARGET VARIABLE: Revenue (in millions USD)
            c.current_revenue_usd,

            -- Financial data
            c.last_known_valuation_usd,
            c.last_financing_date,
            c.last_financing_size_usd,
            c.total_funding_usd,
            c.num_funding_rounds,

            -- Employee data (multiple sources)
            c.employee_count as pitchbook_employee_count,
            c.scraped_employee_count as linkedin_employee_count,
            c.crunchbase_employee_range,

            -- Industry classification
            c.primary_industry_group,
            c.primary_industry_sector,
            c.verticals,

            -- Location data
            c.hq_location,
            c.hq_country,
            c.headquarters,
            c.country,
            c.state_region,
            c.city,

            -- PE firm relationship
            c.investor_name,
            c.investor_status,
            c.investor_holding,

            -- Company stage & status
            c.funding_stage,
            c.is_public,
            c.ipo_date,
            c.ipo_exchange,
            c.ipo_valuation_usd,

            -- Dates
            c.founded_date,
            c.closed_date,
            c.created_at,
            c.updated_at,

            -- Social & web presence
            c.linkedin_url,
            c.crunchbase_url,
            c.twitter_url,

            -- ML predictions (if available)
            c.predicted_revenue,
            c.prediction_confidence,

            -- Aggregated PE firm data
            STRING_AGG(DISTINCT pf.name, ', ' ORDER BY pf.name) as all_pe_firms,
            COUNT(DISTINCT cpi.pe_firm_id) as num_pe_firms,

            -- Investment status
            STRING_AGG(DISTINCT cpi.status, ', ') as investment_statuses,
            STRING_AGG(DISTINCT cpi.exit_type, ', ') as exit_types

        FROM companies c
        LEFT JOIN company_pe_investments cpi ON c.id = cpi.company_id
        LEFT JOIN pe_firms pf ON cpi.pe_firm_id = pf.id

        WHERE c.current_revenue_usd IS NOT NULL

        GROUP BY
            c.id, c.name, c.website, c.description,
            c.current_revenue_usd, c.last_known_valuation_usd,
            c.last_financing_date, c.last_financing_size_usd,
            c.total_funding_usd, c.num_funding_rounds,
            c.employee_count, c.scraped_employee_count, c.crunchbase_employee_range,
            c.primary_industry_group, c.primary_industry_sector, c.verticals,
            c.hq_location, c.hq_country, c.headquarters, c.country, c.state_region, c.city,
            c.investor_name, c.investor_status, c.investor_holding,
            c.funding_stage, c.is_public, c.ipo_date, c.ipo_exchange, c.ipo_valuation_usd,
            c.founded_date, c.closed_date, c.created_at, c.updated_at,
            c.linkedin_url, c.crunchbase_url, c.twitter_url,
            c.predicted_revenue, c.prediction_confidence

        ORDER BY c.current_revenue_usd DESC
    """)

    logger.info("Executing query to extract companies with revenue data...")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    logger.info(f"Found {len(df)} companies with PitchBook revenue data")

    # Add derived features that might be useful for ML
    logger.info("Computing derived features...")

    # Revenue per employee (if employee data available)
    df['revenue_per_employee'] = None
    employee_mask = df['pitchbook_employee_count'].notna()
    if employee_mask.any():
        df.loc[employee_mask, 'revenue_per_employee'] = (
            df.loc[employee_mask, 'current_revenue_usd'] * 1_000_000 /
            df.loc[employee_mask, 'pitchbook_employee_count']
        )

    # Valuation to revenue ratio
    valuation_mask = df['last_known_valuation_usd'].notna()
    df['valuation_to_revenue_ratio'] = None
    if valuation_mask.any():
        df.loc[valuation_mask, 'valuation_to_revenue_ratio'] = (
            df.loc[valuation_mask, 'last_known_valuation_usd'] /
            df.loc[valuation_mask, 'current_revenue_usd']
        )

    # Company age (years since founding)
    df['company_age_years'] = None
    founded_mask = df['founded_date'].notna()
    if founded_mask.any():
        df.loc[founded_mask, 'company_age_years'] = (
            (datetime.now() - pd.to_datetime(df.loc[founded_mask, 'founded_date'])).dt.days / 365.25
        )

    # Years since last financing
    df['years_since_last_financing'] = None
    financing_mask = df['last_financing_date'].notna()
    if financing_mask.any():
        df.loc[financing_mask, 'years_since_last_financing'] = (
            (datetime.now() - pd.to_datetime(df.loc[financing_mask, 'last_financing_date'])).dt.days / 365.25
        )

    # Average funding per round
    df['avg_funding_per_round'] = None
    rounds_mask = (df['num_funding_rounds'].notna()) & (df['num_funding_rounds'] > 0)
    if rounds_mask.any():
        df.loc[rounds_mask, 'avg_funding_per_round'] = (
            df.loc[rounds_mask, 'total_funding_usd'] /
            df.loc[rounds_mask, 'num_funding_rounds']
        )

    # Has multiple PE firms (co-investment indicator)
    df['has_multiple_pe_firms'] = df['num_pe_firms'] > 1

    # Is exited
    df['is_exited'] = df['investment_statuses'].str.contains('Exit', na=False)

    # Export to CSV
    logger.info(f"Exporting to {output_file}...")
    df.to_csv(output_file, index=False)
    logger.info(f"Successfully exported {len(df)} companies to {output_file}")

    # Print summary statistics
    print("\n" + "="*80)
    print("DATA EXTRACTION SUMMARY")
    print("="*80)
    print(f"\nTotal companies with PitchBook revenue: {len(df)}")
    print(f"\nRevenue statistics (in millions USD):")
    print(df['current_revenue_usd'].describe())

    print(f"\nData completeness:")
    completeness = (df.notna().sum() / len(df) * 100).round(1)
    key_fields = [
        'current_revenue_usd',
        'pitchbook_employee_count',
        'last_known_valuation_usd',
        'total_funding_usd',
        'primary_industry_group',
        'hq_country',
        'founded_date'
    ]
    for field in key_fields:
        if field in completeness:
            print(f"  {field}: {completeness[field]}%")

    print(f"\nIndustry distribution (top 10):")
    if 'primary_industry_group' in df.columns:
        print(df['primary_industry_group'].value_counts().head(10))

    print(f"\nCountry distribution (top 10):")
    if 'hq_country' in df.columns:
        print(df['hq_country'].value_counts().head(10))

    print(f"\nOutput saved to: {output_file}")
    print("="*80 + "\n")

    return df


def main():
    """Main entry point for the script."""
    # Get database URL from environment or command line
    database_url = os.environ.get('DATABASE_URL')

    if len(sys.argv) > 1:
        database_url = sys.argv[1]

    if not database_url:
        print("Error: Database URL not provided.")
        print("\nUsage:")
        print("  python extract_companies_with_revenue.py <DATABASE_URL>")
        print("  or set DATABASE_URL environment variable")
        print("\nExample:")
        print("  python extract_companies_with_revenue.py 'postgresql://user:pass@host:port/db'")
        sys.exit(1)

    # Optional: output file path
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        df = extract_companies_with_revenue(database_url, output_file)
        return 0
    except Exception as e:
        logger.error(f"Error extracting data: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
