# ML Revenue Prediction - Deployment Guide

This guide explains how to deploy and use the ML revenue prediction system in production.

## Quick Start

The ML models are **already trained and saved** in the repository. You just need to choose when to run predictions.

## Deployment Options

### Option 1: Manual Enrichment (Safest)

Deploy normally, then manually trigger enrichment via API:

```bash
# After deployment, run once:
curl -X POST https://your-api-url.com/api/ml/enrich/all
```

**Pros:**
- Full control over when predictions run
- Can monitor the process
- No startup delay

**Cons:**
- Must remember to run manually
- Need to run again for new companies

---

### Option 2: Automatic on Startup (Recommended)

Enable automatic enrichment when the backend starts.

#### Setup

Add to your `.env` file (or environment variables in Railway/Vercel):

```bash
ML_ENRICH_ON_STARTUP=true
```

**What happens:**
- On every backend startup/restart, checks for companies without predictions
- Only enriches companies that don't have predictions yet
- Runs in batches of 50 companies
- Takes ~1-2 seconds per batch
- Backend still starts if enrichment fails

**Pros:**
- Automatic - no manual intervention needed
- New companies get predictions automatically
- Safe - only enriches missing predictions

**Cons:**
- Slight startup delay (usually <30 seconds for first run)
- Runs on every deployment/restart

---

### Option 3: Scheduled Job (For Large Databases)

For databases with thousands of companies, use a scheduled job:

**Using Railway:**
```bash
# Add a cron service to railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python -m scripts.enrich_companies_cron"
  }
}
```

**Create the script:**
```python
# scripts/enrich_companies_cron.py
from backend.database_pool import SessionLocal
from backend.services.ml_enrichment_service import MLEnrichmentService

def main():
    db = SessionLocal()
    try:
        service = MLEnrichmentService()
        count = service.enrich_all_companies(db, force_update=False)
        print(f"Enriched {count} companies")
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

Run daily at midnight:
- Railway: Add cron schedule
- Vercel: Use Vercel Cron
- Heroku: Use Heroku Scheduler

---

## Environment Variables

### Required (Already Set)
```bash
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
```

### Optional ML Settings
```bash
# Enable automatic enrichment on startup
ML_ENRICH_ON_STARTUP=true

# Batch size for enrichment (default: 50)
ML_BATCH_SIZE=100
```

---

## API Endpoints for Manual Control

### Check Model Status
```bash
GET /api/ml/models/status
```

Response:
```json
{
  "status": "ready",
  "ensemble_model_loaded": true,
  "feature_count": 43
}
```

### Enrich Single Company
```bash
POST /api/ml/enrich/company/{company_id}
```

### Enrich Multiple Companies
```bash
POST /api/ml/enrich/batch
{
  "company_ids": [1, 2, 3, 100]
}
```

### Enrich All Companies
```bash
POST /api/ml/enrich/all?batch_size=100
```

---

## What Gets Predicted?

The system automatically predicts revenue for companies that:
- ✅ Have employee count or funding data
- ✅ Don't already have actual revenue data
- ✅ Have at least 30% of required features

Companies with **actual known revenue** are skipped (we use the real value).

---

## Performance Expectations

| Database Size | Enrichment Time | Memory Usage |
|---------------|-----------------|--------------|
| 100 companies | ~5 seconds | ~100MB |
| 1,000 companies | ~30 seconds | ~150MB |
| 10,000 companies | ~5 minutes | ~200MB |

**Note:** These are estimates. First run is slower, subsequent runs are faster as only new companies are enriched.

---

## Monitoring & Troubleshooting

### Check Logs

The backend logs will show:
```
🤖 ML enrichment enabled - enriching companies...
Progress: 50/100 companies processed
Progress: 100/100 companies processed
✅ Successfully enriched 45 companies with ML predictions
```

### Common Issues

**Issue: "Models not available"**
- Solution: Ensure `ml_pipeline/output/models/` directory is deployed
- Models are committed to git (except `.pkl` files in .gitignore)
- You need to run `python ml_pipeline/train_models.py` once on server

**Issue: Slow startup**
- Solution: Reduce `ML_BATCH_SIZE` or disable `ML_ENRICH_ON_STARTUP`
- Use manual enrichment via API instead

**Issue: Out of memory**
- Solution: Process in smaller batches
- Use scheduled job instead of startup enrichment

---

## Best Practices

### For Development
```bash
# Disable auto-enrichment in development
ML_ENRICH_ON_STARTUP=false
```

### For Staging/Production
```bash
# Enable auto-enrichment
ML_ENRICH_ON_STARTUP=true
ML_BATCH_SIZE=50
```

### For Very Large Databases (>10,000 companies)
- Use scheduled job instead of startup
- Run enrichment during off-peak hours
- Monitor database load

---

## Updating Predictions

### Force Re-prediction for All Companies
```bash
POST /api/ml/enrich/all?force_update=true
```

**When to do this:**
- After retraining models with new data
- After significant feature additions
- Monthly/quarterly refresh

### Re-train Models (Advanced)

If you have new revenue data:

```bash
# SSH into your server
python ml_pipeline/train_models.py

# Models are saved to ml_pipeline/output/models/
# They'll be used automatically on next prediction
```

---

## Frontend Integration

Predictions are automatically included in all company responses:

```json
{
  "id": 123,
  "name": "Acme Corp",
  "predicted_revenue": 207.5,
  "prediction_confidence": "High",
  "prediction_confidence_lower": 166.0,
  "prediction_confidence_upper": 249.0
}
```

Display in your React frontend:
```tsx
{company.predicted_revenue && (
  <div>
    <span className="font-bold">
      Predicted Revenue: ${company.predicted_revenue}M
    </span>
    <span className="text-gray-600">
      (${company.prediction_confidence_lower}M -
       ${company.prediction_confidence_upper}M)
    </span>
    <Badge variant={getConfidenceColor(company.prediction_confidence)}>
      {company.prediction_confidence} Confidence
    </Badge>
  </div>
)}
```

---

## Recommended Setup

For most users:

1. **On initial deployment:**
   - Set `ML_ENRICH_ON_STARTUP=false`
   - Deploy and verify everything works
   - Run manual enrichment: `POST /api/ml/enrich/all`

2. **After verification:**
   - Set `ML_ENRICH_ON_STARTUP=true`
   - Redeploy
   - New companies auto-get predictions

3. **Monitor:**
   - Check logs during startup
   - Verify predictions in frontend
   - Re-enrich monthly if needed

---

## Support

If enrichment fails, the application will continue to work. Predictions are optional enhancements, not required for core functionality.

For issues, check:
1. Backend logs
2. Model files exist in `ml_pipeline/output/models/`
3. Database connectivity
4. Required Python packages installed
