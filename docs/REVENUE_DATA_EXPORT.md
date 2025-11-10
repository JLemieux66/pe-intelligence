# Exporting Companies with PitchBook Revenue Data for ML Training

This guide explains how to extract all companies **WITH** PitchBook revenue data from your database for machine learning model training.

## Overview

The system provides two methods to extract comprehensive company data:

1. **API Endpoint** (Recommended) - Use the built-in API endpoint
2. **Standalone Script** - Run a Python script locally

---

## Method 1: API Endpoint (Recommended)

### Endpoint Details

```
GET /api/companies/export/with-revenue
```

This endpoint automatically:
- Filters companies with `current_revenue_usd IS NOT NULL`
- Exports all relevant features for ML training
- Returns a CSV file with timestamped filename
- Includes derived features calculated on-the-fly

### Usage

#### Option A: Using cURL

```bash
curl -o companies_with_revenue.csv \
  "http://localhost:8000/api/companies/export/with-revenue"
```

#### Option B: Using Python requests

```python
import requests

response = requests.get('http://localhost:8000/api/companies/export/with-revenue')

# Save to file
with open('companies_with_revenue.csv', 'wb') as f:
    f.write(response.content)

# Get total count from header
total_count = response.headers.get('X-Total-Count')
print(f"Exported {total_count} companies with revenue data")
```

#### Option C: Using your browser

Simply navigate to:
```
http://localhost:8000/api/companies/export/with-revenue
```

The CSV file will automatically download.

---

## Method 2: Standalone Python Script

### Prerequisites

```bash
pip install pandas sqlalchemy psycopg2-binary
```

### Running the Script

```bash
# From the project root directory
python scripts/extract_companies_with_revenue.py "postgresql://postgres:XkwZYjArIufZzXBdSpUDPNwzMLDolHdS@interchange.proxy.rlwy.net:23887/railway"

# Or set as environment variable
export DATABASE_URL="postgresql://postgres:XkwZYjArIufZzXBdSpUDPNwzMLDolHdS@interchange.proxy.rlwy.net:23887/railway"
python scripts/extract_companies_with_revenue.py

# Specify custom output file
python scripts/extract_companies_with_revenue.py "$DATABASE_URL" "my_data.csv"
```

### Script Features

The standalone script:
- Connects directly to PostgreSQL
- Extracts all companies with revenue data
- Computes derived features
- Provides detailed statistics
- Exports to timestamped CSV file

---

## Data Schema

The exported CSV includes the following fields:

### Core Identifiers
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique company ID |
| `name` | string | Company name |
| `website` | string | Company website URL |

### Target Variable
| Field | Type | Description |
|-------|------|-------------|
| `current_revenue_usd` | float | **Revenue in millions USD** (TARGET) |

### Financial Data
| Field | Type | Description |
|-------|------|-------------|
| `last_known_valuation_usd` | float | Valuation in millions USD |
| `last_financing_date` | date | Most recent financing date |
| `last_financing_size_usd` | float | Latest financing amount (millions USD) |
| `total_funding_usd` | int | Total funding raised (USD) |
| `num_funding_rounds` | int | Number of funding rounds |

### Employee Data (Multiple Sources)
| Field | Type | Description |
|-------|------|-------------|
| `employee_count` | string | Best available employee count (PitchBook > LinkedIn > Crunchbase) |
| `scraped_employee_count` | int | LinkedIn employee count |
| `crunchbase_employee_range` | string | Crunchbase employee range |

### Industry Classification
| Field | Type | Description |
|-------|------|-------------|
| `primary_industry_group` | string | PitchBook industry group |
| `primary_industry_sector` | string | PitchBook industry sector |
| `verticals` | string | Comma-separated vertical markets |

### Location Data
| Field | Type | Description |
|-------|------|-------------|
| `hq_location` | string | PitchBook HQ location |
| `hq_country` | string | HQ country from PitchBook |
| `headquarters` | string | Full headquarters string |
| `country` | string | Country (from Crunchbase/scraped) |
| `state_region` | string | State or region |
| `city` | string | City |

### PE Firm Relationships
| Field | Type | Description |
|-------|------|-------------|
| `pe_firms` | string | Comma-separated list of all PE firms |
| `investor_name` | string | Primary PE firm name from PitchBook |
| `investor_status` | string | Active, Former, etc. |
| `investor_holding` | string | Minority, Majority, etc. |

### Company Stage & Status
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Active or Exit |
| `funding_stage` | string | Funding stage |
| `is_public` | boolean | Public company status |
| `ipo_date` | date | IPO date if applicable |
| `ipo_exchange` | string | Stock exchange |
| `ipo_valuation_usd` | float | IPO valuation (millions USD) |

### Dates
| Field | Type | Description |
|-------|------|-------------|
| `founded_date` | date | Company founding date |
| `closed_date` | date | Closure date (if applicable) |

### Social & Web Presence
| Field | Type | Description |
|-------|------|-------------|
| `linkedin_url` | string | LinkedIn company page |
| `crunchbase_url` | string | Crunchbase profile |
| `twitter_url` | string | Twitter/X profile |

### ML Predictions (if available)
| Field | Type | Description |
|-------|------|-------------|
| `predicted_revenue` | float | ML-predicted revenue |
| `prediction_confidence` | float | Confidence score (0-1) |

### Derived Features
| Field | Type | Description |
|-------|------|-------------|
| `valuation_to_revenue_ratio` | float | Valuation / Revenue multiple |
| `avg_funding_per_round` | float | Total funding / Number of rounds |
| `has_multiple_pe_firms` | boolean | Co-investment indicator |
| `is_exited` | boolean | Exit status flag |

---

## Example ML Usage

### Loading the Data

```python
import pandas as pd
import numpy as np

# Load the exported data
df = pd.read_csv('companies_with_revenue.csv')

print(f"Total companies: {len(df)}")
print(f"Revenue range: ${df['current_revenue_usd'].min():.2f}M - ${df['current_revenue_usd'].max():.2f}M")

# Check data completeness
print("\nData completeness:")
print((df.notna().sum() / len(df) * 100).round(1))
```

### Basic Feature Engineering

```python
# Convert employee count to numeric
df['employee_count_numeric'] = pd.to_numeric(
    df['employee_count'].str.replace(',', ''),
    errors='coerce'
)

# Log transform revenue (target)
df['log_revenue'] = np.log1p(df['current_revenue_usd'])

# One-hot encode categorical variables
df = pd.get_dummies(df, columns=['primary_industry_group', 'hq_country'])

# Handle missing values
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
```

### Train-Test Split

```python
from sklearn.model_selection import train_test_split

# Define features and target
feature_cols = [
    'employee_count_numeric',
    'total_funding_usd',
    'num_funding_rounds',
    'valuation_to_revenue_ratio',
    'avg_funding_per_round',
    'has_multiple_pe_firms',
    'is_exited'
    # Add one-hot encoded columns
]

X = df[feature_cols]
y = df['current_revenue_usd']  # or 'log_revenue' for log-transformed target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set: {len(X_train)} samples")
print(f"Test set: {len(X_test)} samples")
```

---

## Data Quality Notes

### Revenue Data
- **Units**: All revenue values are in **millions USD**
- **Source**: PitchBook
- **Filter**: Only companies with `current_revenue_usd IS NOT NULL` are included

### Employee Counts
- **Priority**: PitchBook > LinkedIn > Crunchbase
- **Formats**: May be exact numbers or ranges (e.g., "100-500")
- **Field**: `employee_count` contains the best available value

### Industry Data
- **Source**: PitchBook taxonomy
- **Hierarchy**: Group > Sector > Verticals
- **Multiple Values**: `verticals` may contain comma-separated values

### Location Data
- Multiple location fields from different sources
- Use `hq_country` for PitchBook data (most reliable)
- `country` field may differ (from Crunchbase/scraped)

### Missing Values
- Financial data may have gaps
- Not all companies have funding information
- Dates may be null for older companies

---

## Statistics & Validation

After extraction, the system provides:

1. **Total count** of companies with revenue
2. **Revenue statistics** (min, max, mean, median, quartiles)
3. **Data completeness** percentage for key fields
4. **Industry distribution** (top 10)
5. **Country distribution** (top 10)

Example output:
```
================================================================================
DATA EXTRACTION SUMMARY
================================================================================

Total companies with PitchBook revenue: 1,234

Revenue statistics (in millions USD):
count    1234.000000
mean       125.456789
std        234.567890
min          0.100000
25%         15.000000
50%         45.000000
75%        150.000000
max       2500.000000

Data completeness:
  current_revenue_usd: 100.0%
  pitchbook_employee_count: 78.3%
  last_known_valuation_usd: 45.6%
  total_funding_usd: 62.1%
  primary_industry_group: 89.2%
  hq_country: 95.4%
  founded_date: 67.8%

Industry distribution (top 10):
B2B Software & Services    234
Healthcare                 156
Financial Services         123
...

Country distribution (top 10):
United States             856
United Kingdom            112
Canada                     89
...

Output saved to: companies_with_revenue_20250110_143022.csv
================================================================================
```

---

## Troubleshooting

### Issue: No data returned

**Cause**: No companies with revenue in database

**Solution**: Check if companies have been enriched with PitchBook data:
```sql
SELECT COUNT(*) FROM companies WHERE current_revenue_usd IS NOT NULL;
```

### Issue: Script connection error

**Cause**: Network/firewall blocking database access

**Solution**: Use the API endpoint method instead (Method 1)

### Issue: Incomplete data

**Cause**: Not all companies fully enriched

**Solution**:
- Check enrichment process logs
- Use derived features to fill gaps
- Consider imputation strategies for ML

### Issue: Large file size

**Cause**: Many companies with extensive data

**Solution**:
- Use chunking for very large datasets
- Export in batches using pagination
- Consider Parquet format for compression

---

## API Endpoint Configuration

The endpoint is automatically available when you run the backend server:

```bash
# Start the backend
cd backend
uvicorn main:app --reload --port 8000
```

Endpoint will be accessible at:
```
http://localhost:8000/api/companies/export/with-revenue
```

For production deployments, replace `localhost:8000` with your domain.

---

## Next Steps

1. **Export the data** using Method 1 or 2
2. **Validate data quality** by reviewing statistics
3. **Explore the data** using pandas/jupyter notebooks
4. **Build your ML model** using the comprehensive features
5. **Iterate** on feature engineering based on model performance

---

## Support

For issues or questions:
- Check the `/api/docs` endpoint for API documentation
- Review the script source code: `scripts/extract_companies_with_revenue.py`
- Examine the API implementation: `backend/api/companies.py:107-286`

---

## Related Files

- **API Endpoint**: `backend/api/companies.py:107-286`
- **Python Script**: `scripts/extract_companies_with_revenue.py`
- **Database Models**: `src/models/database_models_v2.py`
- **Company Service**: `backend/services/company_service.py`
