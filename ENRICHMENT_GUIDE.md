# 🤖 ML Revenue Prediction Enrichment Guide

## Why You're Not Seeing Predicted Revenue

Your frontend is correctly configured, but the **database doesn't have predicted revenue values yet**. You need to run the enrichment process once to populate these values.

## ✅ Quick Solution

### For Production (Railway + Vercel)

**Option 1: Manual Trigger (Do this now)**
```bash
curl -X POST https://pe-intelligence-production.up.railway.app/api/ml/enrich/all
```

**Option 2: Auto-Enrich on Startup (Best for future)**
1. Go to Railway dashboard → Backend service
2. Add environment variable: `ML_ENRICH_ON_STARTUP=true`
3. Redeploy
4. Companies will auto-enrich on every restart

### For Local Development

**Using the script:**
```bash
# Install dependencies first
pip install sqlalchemy psycopg2-binary

# Run enrichment
python scripts/enrich_companies.py

# Force re-prediction for all companies
python scripts/enrich_companies.py --force
```

**Using the API:**
```bash
# Start your backend
cd backend && uvicorn main:app --reload

# In another terminal, trigger enrichment
curl -X POST http://localhost:8000/api/ml/enrich/all
```

## 📊 What Happens During Enrichment

1. **Loads ML models** - Uses the trained models from `ml_pipeline/output/models/`
2. **Processes companies** - Goes through all companies in batches of 50
3. **Makes predictions** - Predicts revenue for companies without actual revenue data
4. **Saves to database** - Updates `predicted_revenue` and `prediction_confidence` columns
5. **Shows in frontend** - Predicted revenue automatically appears in the UI

## 🎯 Expected Results

After enrichment completes:
- Companies without actual revenue will have predicted values
- Predicted revenue shows in the company table with a "Predicted" badge
- Company modals show confidence intervals
- You can sort/filter by predicted revenue

## 📈 Performance

| Companies | Time | Memory |
|-----------|------|--------|
| 100 | ~5 sec | ~100MB |
| 1,000 | ~30 sec | ~150MB |
| 10,000 | ~5 min | ~200MB |

## 🔍 Verify It Worked

Check the API:
```bash
curl https://pe-intelligence-production.up.railway.app/api/companies?limit=5
```

Look for `predicted_revenue` field in the response:
```json
{
  "id": 123,
  "name": "Example Corp",
  "predicted_revenue": 297300000.0,
  "prediction_confidence": "High"
}
```

## 🚨 Troubleshooting

**"Models not available" error**
- Solution: Make sure the ML models are deployed (they should be in the git repo)
- Check: `ml_pipeline/output/models/*.pkl` files exist

**"Database connection failed"**
- Solution: Check `DATABASE_URL` environment variable is set correctly
- Verify: Railway database is running

**Enrichment is slow**
- Solution: Normal for large databases
- Reduce batch size: `POST /api/ml/enrich/all?batch_size=25`

**Some companies missing predictions**
- Normal: Companies need at least 30% of features to get predictions
- Check: Employee count or funding data available

## 🔄 When to Re-Run Enrichment

- After adding new companies to the database
- After retraining models with new data
- Monthly/quarterly to refresh predictions
- Use `--force` flag to re-predict all companies

## 📚 API Endpoints

```bash
# Check model status
GET /api/ml/models/status

# Enrich single company
POST /api/ml/enrich/company/{company_id}

# Enrich multiple companies
POST /api/ml/enrich/batch
Body: {"company_ids": [1, 2, 3]}

# Enrich all companies
POST /api/ml/enrich/all?force_update=false&batch_size=50

# Get model performance metrics
GET /api/ml/models/performance

# Get feature importance
GET /api/ml/features/importance?top_n=20
```

## 🎓 Model Details

- **Best Model**: XGBoost ensemble
- **Accuracy**: 61.58% R² score
- **Within 50%**: 48.5% of predictions
- **Training Data**: 6,683 companies with actual revenue
- **Features**: 43 engineered features

## Need Help?

1. Check the logs: Railway dashboard → Backend service → Logs
2. Test the API: `/api/ml/models/status`
3. Review: `ML_DEPLOYMENT_GUIDE.md` for detailed setup
