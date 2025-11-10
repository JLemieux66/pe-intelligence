# Data Extraction Scripts

This directory contains scripts for extracting and exporting data from the PE Intelligence database.

## Available Scripts

### extract_companies_with_revenue.py

Extracts all companies WITH PitchBook revenue data for machine learning model training.

**Usage:**
```bash
# Basic usage
python scripts/extract_companies_with_revenue.py "postgresql://user:pass@host:port/database"

# With custom output file
python scripts/extract_companies_with_revenue.py "postgresql://..." "output.csv"

# Using environment variable
export DATABASE_URL="postgresql://..."
python scripts/extract_companies_with_revenue.py
```

**Features:**
- Comprehensive feature extraction (40+ fields)
- Automatic derived feature calculation
- Data quality statistics
- Industry and location distributions
- Timestamped output files

**Requirements:**
```bash
pip install pandas sqlalchemy psycopg2-binary
```

**Output:**
- CSV file with all companies that have `current_revenue_usd IS NOT NULL`
- Includes: revenue, employees, funding, industry, location, PE firms, and derived features
- Suitable for direct use in ML pipelines

## Documentation

For complete documentation, see:
- [Revenue Data Export Guide](../docs/REVENUE_DATA_EXPORT.md)

## Database Connection

The scripts support both SQLite and PostgreSQL databases:

**PostgreSQL (Production):**
```
postgresql://user:password@host:port/database
```

**SQLite (Local Development):**
```
sqlite:///pe_portfolio_v2.db
```

Connection string can be provided via:
1. Command-line argument
2. `DATABASE_URL` environment variable
3. Default: Uses local SQLite database

## Notes

- All scripts log progress and errors to stdout
- Large datasets may take several minutes to export
- CSV files are UTF-8 encoded
- Timestamp format: `YYYYMMDD_HHMMSS`
