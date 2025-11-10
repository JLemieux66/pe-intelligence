# ML Models Training - Quick Start Guide

Your ML models were trained locally but the `.pkl` files are gitignored and not deployed to production.

## ✅ Simple 3-Step Solution

### Step 1: Check Model Status
```bash
curl -X GET "https://your-production-url.com/ml/admin/training-status" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Expected Response (if not trained):**
```json
{
  "status": "not_trained",
  "message": "Models need to be trained",
  "next_steps": [
    "1. Export training data...",
    "2. Train models...",
    "..."
  ]
}
```

---

### Step 2: Export Training Data
Visit in your browser (or curl):
```bash
https://your-production-url.com/api/companies/export/with-revenue
```

Save the CSV file as: `ml_pipeline/data/companies_with_revenue.csv`

Or use the export endpoint (requires admin auth):
```bash
curl -X POST "https://your-production-url.com/ml/admin/export-training-data" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

### Step 3: Train Models (in Production)
```bash
curl -X POST "https://your-production-url.com/ml/admin/train" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
{
  "status": "started",
  "message": "Model training started in background. Check logs for progress. This will take 5-15 minutes.",
  "details": {
    "estimated_time": "5-15 minutes"
  }
}
```

**Monitor Progress:**
- Check your Railway/Vercel logs
- Look for: "🤖 Starting ML model training..."
- Completion: "✅ ML model training complete!"

---

### Step 4: Verify Training Complete
```bash
curl -X GET "https://your-production-url.com/ml/admin/training-status" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Expected Response (when ready):**
```json
{
  "status": "ready",
  "message": "Models are ready for predictions",
  "models": {
    "ensemble.pkl": {"exists": true},
    "feature_engineer.pkl": {"exists": true}
  }
}
```

---

### Step 5: Run Predictions
```bash
curl -X POST "https://your-production-url.com/ml/enrich/all?batch_size=100"
```

This will:
- Predict revenue for all companies without predictions
- Take ~30 seconds for 1,000 companies
- Can be run multiple times (only enriches missing predictions)

---

## Alternative: Train Locally & Upload

If training in production is slow or fails:

### Option A: Manual Upload (Railway)
```bash
# 1. Train locally
python ml_pipeline/train_models.py

# 2. SSH into Railway
railway shell

# 3. Upload models
scp ml_pipeline/output/models/*.pkl user@railway:/app/ml_pipeline/output/models/
```

### Option B: Use Railway Volumes
```bash
# In railway.toml
[volumes]
models = "/app/ml_pipeline/output/models"
```

---

## Automatic Predictions (Optional)

Once models are trained, enable auto-enrichment:

**In Railway/Vercel Environment Variables:**
```bash
ML_ENRICH_ON_STARTUP=true
```

This will automatically:
- Run predictions on startup
- Only enrich companies without predictions
- Take ~30 seconds on startup

---

## API Endpoints Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/ml/admin/training-status` | GET | Admin | Check if models exist |
| `/ml/admin/train` | POST | Admin | Train models (background) |
| `/ml/admin/export-training-data` | POST | Admin | Export data for training |
| `/ml/enrich/all` | POST | None | Run predictions on all companies |
| `/ml/enrich/company/{id}` | POST | None | Predict single company |
| `/ml/models/status` | GET | None | Check model availability |

---

## Troubleshooting

### "Models not available"
✅ **Solution:** Run Step 3 above to train models in production

### "Training data not found"
✅ **Solution:** Run Step 2 to export training data first

### Training takes too long
✅ **Solution:** Train locally and upload models manually

### Out of memory during training
✅ **Solution:**
- Reduce training data size
- Upgrade production instance
- Train locally and upload

---

## Expected Model Performance

Based on your training results:

| Metric | Value |
|--------|-------|
| **Best Model** | Ensemble |
| **R² Score** | 0.614 |
| **RMSE** | $207.6M |
| **MAE** | $116.4M |
| **Within 30% Accuracy** | 28.6% |

This means predictions will be within ±30% for about 1 in 3 companies - good for ballpark estimates!

---

## Need Help?

1. Check production logs for errors
2. Verify training data has companies with revenue
3. Ensure admin token is valid
4. Try training locally first to verify it works
