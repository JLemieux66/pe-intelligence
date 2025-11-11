# ML Prediction Testing Guide

## Quick Test for 100ms Company

### Option 1: Via API (Recommended)

If your backend is running, use the shell script:

```bash
./test_ml_prediction.sh
```

Or manually via curl:

```bash
# 1. Check ML model status
curl http://localhost:8000/api/ml/models/status

# 2. Find 100ms company
curl "http://localhost:8000/api/companies?search=100ms&limit=1"

# 3. Trigger prediction (replace COMPANY_ID with actual ID from step 2)
curl -X POST "http://localhost:8000/api/ml/enrich/company/COMPANY_ID?force_update=true"

# 4. Check result
curl "http://localhost:8000/api/companies/COMPANY_ID"
```

### Option 2: Direct Python Test

If you have access to the backend environment with database access:

```bash
# In your backend environment (Railway, Docker, etc.)
python test_ml_direct.py 100ms
```

Or for a different company:
```bash
python test_ml_direct.py "Company Name"
```

## Troubleshooting: Why Revenue Shows as 0

### Check 1: ML Models Loaded?

```bash
curl http://localhost:8000/api/ml/models/status
```

Expected response:
```json
{
  "status": "ready",
  "feature_engineer_loaded": true,
  "ensemble_model_loaded": true,
  "best_model_loaded": true,
  "feature_count": 70+
}
```

If models aren't loaded, check:
- Do model files exist in `ml_pipeline/output/models/`?
- Are there any import errors in backend logs?

### Check 2: Has Enrichment Been Triggered?

Companies only get predictions after enrichment runs. Check if:

1. **Automatic enrichment on startup** - Set this environment variable:
   ```bash
   ML_ENRICH_ON_STARTUP=true
   ```
   Then restart the backend.

2. **Manual enrichment** - Trigger via API:
   ```bash
   # Enrich specific company
   curl -X POST "http://localhost:8000/api/ml/enrich/company/123?force_update=true"

   # Or enrich ALL companies
   curl -X POST "http://localhost:8000/api/ml/enrich/all"
   ```

### Check 3: Backend Errors?

Look for these errors in backend logs:

1. **Type conversion errors** (should be fixed now):
   ```
   ERROR:root:Feature transformation error for company X: loop of ufunc does not support argument 0 of type int
   ```

2. **Missing features**:
   ```
   ERROR:root:Feature transformation error: KeyError: 'column_name'
   ```

3. **Model loading failures**:
   ```
   ML models not available
   ```

### Check 4: Database Values

Query the database directly:

```sql
SELECT
    id,
    name,
    predicted_revenue,
    prediction_confidence,
    employee_count,
    total_funding_usd,
    last_known_valuation_usd
FROM companies
WHERE name ILIKE '%100ms%';
```

If `predicted_revenue` is NULL, enrichment hasn't run for that company yet.

If `predicted_revenue` is 0, check:
- Does the company have any input features? (employees, funding, etc.)
- Are backend logs showing prediction errors for this company?

## Common Issues and Solutions

### Issue 1: "ML models not available"

**Solution**: Ensure model files exist:
```bash
ls -lh ml_pipeline/output/models/
# Should show: ensemble.pkl, feature_engineer.pkl, xgboost.pkl, etc.
```

If missing, retrain models:
```bash
cd ml_pipeline
python train_revenue_model.py
```

### Issue 2: All predictions are 0

**Likely cause**: Enrichment hasn't run yet.

**Solution**: Trigger enrichment:
```bash
curl -X POST "http://localhost:8000/api/ml/enrich/all"
```

### Issue 3: Predictions work but frontend shows 0

**Likely causes**:
1. Frontend caching - hard refresh (Ctrl+Shift+R)
2. API returning wrong units (millions vs USD)
3. Frontend displaying wrong field

**Solution**: Check API response directly:
```bash
curl http://localhost:8000/api/companies/COMPANY_ID
```

Look for `predicted_revenue` field. If it's non-zero in API but zero in frontend, it's a frontend display issue.

### Issue 4: "Feature transformation error"

**Should be fixed** as of latest commit. If still occurring:

1. Check backend logs for specific column name causing error
2. Ensure database fields are correct types (not strings for numeric fields)
3. Check if company has NULL values for all features

## Manual Database Update (Last Resort)

If all else fails, you can manually trigger enrichment from database console:

```python
from backend.services.ml_enrichment_service import MLEnrichmentService
from backend.database_pool import get_db
from src.models.database_models_v2 import Company

db = next(get_db())
service = MLEnrichmentService()

# Enrich specific company
company = db.query(Company).filter(Company.id == YOUR_COMPANY_ID).first()
prediction = service.predict_revenue(company)
print(f"Prediction: {prediction}")

# Update database
if prediction:
    company.predicted_revenue = float(prediction['predicted_revenue'])
    company.prediction_confidence = float(prediction['features_completeness'])
    db.commit()
```

## Expected Timeline

After triggering enrichment:
- **Single company**: < 1 second
- **100 companies**: 5-10 seconds
- **1000+ companies**: 1-2 minutes
- **10,000+ companies**: 10-20 minutes

Progress is logged every 1000 companies.
