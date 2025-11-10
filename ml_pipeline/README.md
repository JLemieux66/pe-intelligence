# ML Revenue Prediction Pipeline

A comprehensive machine learning pipeline for predicting company revenue using ensemble methods.

## Overview

This ML pipeline uses multiple state-of-the-art algorithms to predict company revenue with high accuracy:
- **Random Forest**: Robust ensemble method with 300 trees
- **XGBoost**: Gradient boosting with optimized hyperparameters
- **LightGBM**: Fast gradient boosting framework
- **Hist Gradient Boosting**: Scikit-learn's histogram-based boosting
- **Ensemble Model**: Weighted combination of all models

## Performance Metrics

Based on test set evaluation:

| Model | R² Score | RMSE ($M) | MAE ($M) | Within 30% Accuracy |
|-------|----------|-----------|----------|---------------------|
| Random Forest | 0.592 | $213.38M | $120.06M | 28.6% |
| XGBoost | 0.616 | $207.08M | $116.88M | 28.5% |
| LightGBM | 0.608 | $209.17M | $117.26M | 29.7% |
| Ensemble | TBD | TBD | TBD | TBD |

## Features (43 total)

### Key Predictive Features
1. **funding_stage_encoded** - Most important predictor
2. **pitchbook_valuation_usd_millions** - Company valuation
3. **employee_count_pitchbook** - Employee count
4. **pitchbook_last_financing_size_usd_millions** - Last financing amount
5. **company_age_years** - Age of company

### Engineered Features
- Log-transformed numeric features
- Funding efficiency metrics
- Geographic indicators
- Industry encoding
- PE backing indicators
- Growth stage classifications

## Project Structure

```
ml_pipeline/
├── __init__.py                    # Package initialization
├── data_preprocessing.py          # Feature engineering pipeline
├── models.py                      # Model implementations
├── train_models.py                # Training script
├── README.md                      # This file
└── output/
    ├── models/                    # Saved models
    │   ├── feature_engineer.pkl
    │   ├── random_forest.pkl
    │   ├── xgboost.pkl
    │   ├── lightgbm.pkl
    │   ├── gradient_boosting.pkl
    │   └── ensemble.pkl
    ├── plots/                     # Visualizations
    │   ├── rf_predictions.png
    │   ├── xgb_predictions.png
    │   ├── lgb_predictions.png
    │   ├── feature_importance_comparison.png
    │   └── model_comparison.png
    └── results/                   # Training results
        ├── training_results.json
        ├── model_comparison.csv
        └── feature_importance_comparison.csv
```

## Installation

### Requirements

```bash
pip install pandas numpy scikit-learn xgboost lightgbm matplotlib seaborn scipy
```

### Training Models

```bash
# Train all models
python ml_pipeline/train_models.py
```

This will:
1. Load and preprocess the data
2. Train all 5 models
3. Generate evaluation metrics
4. Create visualizations
5. Save models and results

## Usage

### 1. Preprocessing Pipeline

```python
from ml_pipeline import prepare_data

# Load and prepare data
data = prepare_data('ml_features_combined_cleaned.csv', test_size=0.2)

X_train = data['X_train']
X_test = data['X_test']
y_train = data['y_train']
y_test = data['y_test']
feature_engineer = data['feature_engineer']
```

### 2. Training Individual Models

```python
from ml_pipeline import RandomForestModel, XGBoostModel, LightGBMModel

# Train Random Forest
rf_model = RandomForestModel(n_estimators=300, max_depth=25)
rf_model.train(X_train, y_train)
predictions = rf_model.predict(X_test)

# Train XGBoost
xgb_model = XGBoostModel(n_estimators=300, learning_rate=0.05)
xgb_model.train(X_train, y_train)
predictions = xgb_model.predict(X_test)

# Train LightGBM
lgb_model = LightGBMModel(n_estimators=300, learning_rate=0.05)
lgb_model.train(X_train, y_train)
predictions = lgb_model.predict(X_test)
```

### 3. Using the Ensemble

```python
from ml_pipeline import EnsembleModel

# Create ensemble
ensemble = EnsembleModel([rf_model, xgb_model, lgb_model])
ensemble_predictions = ensemble.predict(X_test)
```

### 4. Loading Pre-trained Models

```python
import pickle

# Load feature engineer
with open('ml_pipeline/output/models/feature_engineer.pkl', 'rb') as f:
    feature_engineer = pickle.load(f)

# Load ensemble model
with open('ml_pipeline/output/models/ensemble.pkl', 'rb') as f:
    ensemble = pickle.load(f)

# Make predictions on new data
new_data_processed = feature_engineer.transform(new_data)
predictions = ensemble.predict(new_data_processed)

# Convert from log scale to original
revenue_predictions = np.expm1(predictions)
```

### 5. Evaluation

```python
from ml_pipeline import ModelEvaluator

# Evaluate model
metrics = ModelEvaluator.evaluate_model(y_true, y_pred, model_name="My Model")

# Metrics include:
# - R² Score (log and original scale)
# - RMSE ($ millions)
# - MAE ($ millions)
# - MAPE (%)
# - Within 20%, 30%, 50% accuracy
```

## API Integration

The models are integrated with the FastAPI backend:

### Endpoints

```python
# Check model status
GET /api/ml/models/status

# Predict revenue for single company
POST /api/ml/predict/revenue
{
    "employee_count_pitchbook": 500,
    "total_funding_usd": 50000000,
    "pitchbook_valuation_usd_millions": 200,
    ...
}

# Batch predictions
POST /api/ml/predict/batch
{
    "companies": [
        { "employee_count_pitchbook": 500, ... },
        { "employee_count_pitchbook": 1000, ... }
    ]
}

# Get model performance metrics
GET /api/ml/models/performance

# Get feature importance
GET /api/ml/features/importance?top_n=20
```

### Example API Usage

```python
import requests

# Predict revenue
response = requests.post(
    "http://localhost:8000/api/ml/predict/revenue",
    json={
        "employee_count_pitchbook": 500,
        "total_funding_usd": 50000000,
        "pitchbook_valuation_usd_millions": 200,
        "company_age_years": 10,
        "funding_stage_encoded": 5,
        "num_pe_investors": 2,
        "pitchbook_primary_industry_sector": "Information Technology"
    }
)

result = response.json()
print(f"Predicted Revenue: ${result['predicted_revenue_millions']:.2f}M")
print(f"Confidence: {result['prediction_confidence']}")
print(f"Range: ${result['confidence_interval_lower']:.2f}M - ${result['confidence_interval_upper']:.2f}M")
```

## Data Requirements

### Minimum Required Features
- `employee_count_pitchbook` or `employee_count_linkedin_scraped`
- `total_funding_usd`
- `num_funding_rounds`
- `pitchbook_primary_industry_sector`

### Recommended Features for Best Accuracy
- Company valuation
- Last financing size
- Company age
- PE investor information
- Geographic information
- Industry classifications

## Model Training Details

### Data Split
- Training: 80% (5,346 companies)
- Test: 20% (1,337 companies)

### Feature Engineering
1. **Missing Value Imputation**
   - Zero fill for counts
   - Median fill for continuous variables
   - Category encoding for missing categorical

2. **Derived Features**
   - Log transformations
   - Ratio features (e.g., funding efficiency)
   - Interaction terms
   - Geographic indicators
   - Industry flags

3. **Scaling**
   - RobustScaler for outlier resistance

### Hyperparameters

**Random Forest:**
- n_estimators: 300
- max_depth: 25
- min_samples_split: 5
- min_samples_leaf: 2

**XGBoost:**
- n_estimators: 300
- max_depth: 8
- learning_rate: 0.05
- subsample: 0.8
- colsample_bytree: 0.8

**LightGBM:**
- n_estimators: 300
- max_depth: 8
- learning_rate: 0.05
- num_leaves: 31
- subsample: 0.8

## Model Interpretation

### Feature Importance
Check `output/results/feature_importance_comparison.csv` for detailed feature importance across all models.

Top features typically include:
1. Funding stage
2. Company valuation
3. Employee count
4. Last financing size
5. Company age

### Prediction Confidence
Predictions include confidence levels based on feature completeness:
- **High**: ≥70% features present
- **Medium**: 50-70% features present
- **Low**: <50% features present

## Performance Considerations

### Training Time
- Random Forest: ~0.5 seconds
- XGBoost: ~1 second
- LightGBM: ~1 second
- Total pipeline: ~5 seconds

### Prediction Time
- Single prediction: <10ms
- Batch (100 companies): <100ms

### Memory Usage
- Trained models: ~50MB total
- Feature engineer: ~5MB

## Troubleshooting

### Issue: High prediction errors
**Solution**: Check feature completeness. Predictions work best with ≥70% features populated.

### Issue: NaN in predictions
**Solution**: Ensure all required features are provided. Use the feature_engineer to handle missing values.

### Issue: Slow predictions
**Solution**: Use batch prediction endpoint for multiple companies instead of individual requests.

## Future Improvements

1. **Hyperparameter Optimization**: Implement systematic grid/random search
2. **Deep Learning**: Add neural network models
3. **Feature Selection**: Automated feature importance-based selection
4. **Online Learning**: Incremental model updates
5. **Explainability**: SHAP values for individual predictions
6. **Calibration**: Improve confidence interval accuracy

## License

This project is private and proprietary.

## Authors

- JLemieux66

## Contact

For issues or questions, please open a GitHub issue.
