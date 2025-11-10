# ML Model Files

This directory contains trained ML model files for revenue prediction.

## Required Model Files

The following files are needed for ML predictions to work:

- **ensemble.pkl** - Ensemble model (combination of RF, XGB, LGB)
- **xgboost.pkl** - XGBoost model (backup if ensemble fails)
- **lightgbm.pkl** - LightGBM model
- **random_forest.pkl** - Random Forest model
- **feature_engineer.pkl** - Feature engineering pipeline (REQUIRED)

## Training Models Locally

If the model files don't exist, train them locally:

```bash
# From project root
cd ml_pipeline
python train_models.py
```

This will:
- Use `ml_features_combined_cleaned.csv` as training data
- Take ~5-10 minutes
- Generate all model .pkl files in this directory
- Create performance metrics and plots

## After Training

Once trained, the `.pkl` files will be in this directory. They are now tracked by git (no longer gitignored), so:

```bash
git add ml_pipeline/output/models/*.pkl
git commit -m "Add trained ML models for deployment"
git push
```

The models will then deploy automatically with your application!

## Model Size Guidelines

- **Small models** (<50MB total): Commit directly to git ✅
- **Medium models** (50-100MB): Still okay for git, but watch size
- **Large models** (>100MB): Consider Git LFS or training in production

Current training results show models should be <50MB total.

## Deployment

Once committed, models are automatically available in production:
- No training needed in production
- Instant availability on startup
- Can run predictions immediately with: `POST /ml/enrich/all`
