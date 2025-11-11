# Run ML Enrichment Locally

This guide walks you through running ML predictions on ALL companies in your database.

## Why Run Locally?

Your frontend shows 0 for predicted revenue because the `predicted_revenue` field is NULL in the database. This script will:

1. Load the trained ML models (already in `ml_pipeline/output/models/`)
2. Query all companies from your database
3. Generate revenue predictions for each company
4. Update the database with predictions
5. Show progress and results

Once done, your frontend will automatically display the predictions!

## Prerequisites

Make sure you have these Python packages installed:

```bash
pip install tqdm  # For progress bar (optional but recommended)
```

All other dependencies should already be installed.

## Step 1: Set Database Connection

Make sure your database connection is configured. Check that you have one of:

- `.env` file with `DATABASE_URL`
- Environment variable `DATABASE_URL`
- Railway CLI logged in (if using Railway)

Test connection:
```bash
python -c "from backend.database_pool import get_db; db = next(get_db()); print('✅ Database connected')"
```

## Step 2: Run the Enrichment

### Basic Usage (Recommended)

Process all companies that don't have predictions yet:

```bash
python enrich_all_companies.py
```

This will:
- Skip companies that already have predictions
- Process in batches of 100
- Show a progress bar
- Take about 1-2 minutes per 1000 companies

### Advanced Options

Force re-predict for ALL companies (even those with existing predictions):

```bash
python enrich_all_companies.py --force
```

Use a different batch size:

```bash
python enrich_all_companies.py --batch-size 50
```

## Step 3: Verify Results

After enrichment completes, you should see output like:

```
==================================================
ENRICHMENT COMPLETE
==================================================
✅ Successfully enriched: 1,523 companies
❌ Failed: 12 companies
📊 Success rate: 99.2%

Sample predictions:
  • 100ms                                  →   $45.23M (confidence: 75.00%)
  • Acme Corp                              →  $120.50M (confidence: 82.00%)
  • Beta Solutions                         →   $12.75M (confidence: 68.00%)
```

## Step 4: Check Frontend

Refresh your frontend - companies should now show predicted revenue values!

If using the same database for local and production, the changes are already live.

If using separate databases, you'll need to:
- Export the updated data
- Import to production DB
- Or run this script in your production environment

## Troubleshooting

### "Failed to load ML models"

Make sure models exist:
```bash
ls -lh ml_pipeline/output/models/
# Should show: ensemble.pkl, feature_engineer.pkl, xgboost.pkl
```

If missing, train models first:
```bash
cd ml_pipeline
python train_revenue_model.py
```

### "ModuleNotFoundError"

Install missing dependencies:
```bash
pip install sqlalchemy pandas numpy scikit-learn xgboost lightgbm
```

### "Database connection failed"

Check your DATABASE_URL:
```bash
echo $DATABASE_URL
```

If using Railway:
```bash
railway link
railway run python enrich_all_companies.py
```

### Many predictions fail

Check backend logs for specific errors. Common issues:
- Missing required fields (employees, funding, etc.)
- Type conversion errors (should be fixed in latest version)
- Companies with no data (expected - will show low confidence)

### Predictions show but still 0 in frontend

This means the frontend is reading from a different database. Check:
1. Is your frontend pointing to the same DATABASE_URL?
2. Try hard refresh (Ctrl+Shift+R)
3. Check browser console for errors

## Performance Notes

Processing speed depends on:
- **Database location**: Local DB is faster than remote
- **Number of companies**: ~0.5-1 second per company
- **Batch size**: Larger batches = faster but more memory

Expected times:
- 100 companies: ~30 seconds
- 1,000 companies: ~5 minutes
- 10,000 companies: ~1 hour

## What Gets Predicted?

The ML model predicts **annual revenue in millions USD** based on:

- Employee count
- Total funding raised
- Company valuation
- Funding stage and rounds
- Company age
- Industry and geography
- PE backing and investors
- 70+ derived features

Companies with more complete data get higher confidence scores.

## Next Steps

After enrichment:

1. ✅ Verify predictions in frontend
2. 📊 Check prediction accuracy for companies with known revenue
3. 🔄 Set up automatic enrichment on new companies
4. 📈 Use predictions for investment analysis

To enable automatic enrichment when backend starts:
```bash
export ML_ENRICH_ON_STARTUP=true
```

Add this to your Railway environment variables or `.env` file.
