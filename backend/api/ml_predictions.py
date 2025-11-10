"""
ML Predictions API for Revenue Prediction
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import pickle
import sys
from sqlalchemy.orm import Session

# Add ml_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml_pipeline"))

from data_preprocessing import FeatureEngineer
from backend.database_pool import get_db
from backend.services.ml_enrichment_service import MLEnrichmentService

router = APIRouter(prefix="/ml", tags=["ML Predictions"])

# Global variables for loaded models
_feature_engineer: Optional[FeatureEngineer] = None
_ensemble_model: Optional[Any] = None
_best_model: Optional[Any] = None
_model_metadata: Optional[Dict[str, Any]] = None


class CompanyFeatures(BaseModel):
    """Input features for revenue prediction"""

    # Core numeric features
    pitchbook_valuation_usd_millions: Optional[float] = Field(None, description="Company valuation in millions USD")
    employee_count_pitchbook: Optional[float] = Field(None, description="Employee count from PitchBook")
    employee_count_linkedin_scraped: Optional[float] = Field(None, description="Employee count from LinkedIn")
    employee_count_crunchbase_range: Optional[str] = Field(None, description="Employee range from Crunchbase")
    pitchbook_last_financing_size_usd_millions: Optional[float] = Field(None, description="Last financing size")
    total_funding_usd: Optional[float] = Field(0, description="Total funding in USD")
    num_funding_rounds: Optional[int] = Field(0, description="Number of funding rounds")
    avg_round_size_usd: Optional[float] = Field(0, description="Average round size")
    total_investors: Optional[int] = Field(0, description="Total number of investors")
    months_since_last_funding: Optional[float] = Field(None, description="Months since last funding")
    funding_stage_encoded: Optional[float] = Field(None, description="Encoded funding stage")
    company_age_years: Optional[float] = Field(None, description="Company age in years")
    founded_year: Optional[float] = Field(None, description="Year founded")
    num_pe_investors: Optional[int] = Field(0, description="Number of PE investors")
    is_pe_backed: Optional[int] = Field(0, description="Is PE backed (0 or 1)")
    is_public: Optional[bool] = Field(False, description="Is publicly traded")

    # Categorical features
    pitchbook_primary_industry_sector: Optional[str] = Field(None, description="Primary industry sector")
    pitchbook_primary_industry_group: Optional[str] = Field(None, description="Primary industry group")
    pitchbook_verticals: Optional[str] = Field(None, description="Industry verticals")
    pitchbook_hq_country: Optional[str] = Field(None, description="Headquarters country")
    pitchbook_hq_location: Optional[str] = Field(None, description="Headquarters location")
    latest_funding_type: Optional[str] = Field(None, description="Latest funding type")
    latest_funding_date: Optional[str] = Field(None, description="Latest funding date")
    crunchbase_revenue_range: Optional[str] = Field(None, description="Revenue range from Crunchbase")
    company_size_category: Optional[str] = Field(None, description="Company size category")
    revenue_tier: Optional[str] = Field(None, description="Revenue tier")
    country: Optional[str] = Field(None, description="Country")
    state_region: Optional[str] = Field(None, description="State/Region")
    city: Optional[str] = Field(None, description="City")
    crunchbase_industry_tags: Optional[str] = Field(None, description="Industry tags")
    crunchbase_industry_category: Optional[str] = Field(None, description="Industry category")
    pitchbook_last_financing_date: Optional[str] = Field(None, description="Last financing date")
    pitchbook_last_financing_deal_type: Optional[str] = Field(None, description="Last financing deal type")
    ipo_date: Optional[float] = Field(None, description="IPO date")
    ipo_exchange: Optional[str] = Field(None, description="IPO exchange")
    ipo_ticker: Optional[str] = Field(None, description="IPO ticker")


class RevenuePrediction(BaseModel):
    """Revenue prediction response"""
    predicted_revenue_millions: float = Field(..., description="Predicted revenue in millions USD")
    confidence_interval_lower: float = Field(..., description="Lower bound of 80% confidence interval")
    confidence_interval_upper: float = Field(..., description="Upper bound of 80% confidence interval")
    model_used: str = Field(..., description="Model used for prediction")
    prediction_confidence: str = Field(..., description="Confidence level (High/Medium/Low)")
    features_used: int = Field(..., description="Number of features used")


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions"""
    companies: List[CompanyFeatures]


class BatchPredictionResponse(BaseModel):
    """Response for batch predictions"""
    predictions: List[RevenuePrediction]
    total_predictions: int


def load_models():
    """Load trained models and feature engineer"""
    global _feature_engineer, _ensemble_model, _best_model, _model_metadata

    if _feature_engineer is not None:
        return  # Already loaded

    models_dir = Path(__file__).parent.parent.parent / "ml_pipeline" / "output" / "models"

    # Load feature engineer
    fe_path = models_dir / "feature_engineer.pkl"
    if not fe_path.exists():
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Please train models first."
        )

    with open(fe_path, 'rb') as f:
        _feature_engineer = pickle.load(f)

    # Load ensemble model (preferred)
    ensemble_path = models_dir / "ensemble.pkl"
    if ensemble_path.exists():
        with open(ensemble_path, 'rb') as f:
            _ensemble_model = pickle.load(f)

    # Load best individual model as backup
    best_model_path = models_dir / "xgboost.pkl"
    if best_model_path.exists():
        with open(best_model_path, 'rb') as f:
            _best_model = pickle.load(f)

    # Load model metadata
    results_path = Path(__file__).parent.parent.parent / "ml_pipeline" / "output" / "results" / "training_results.json"
    if results_path.exists():
        import json
        with open(results_path, 'r') as f:
            _model_metadata = json.load(f)


def calculate_confidence(prediction: float, features_completeness: float) -> str:
    """
    Calculate prediction confidence based on completeness of features

    Args:
        prediction: Predicted revenue value (log scale)
        features_completeness: Percentage of features that are non-null (0-1)

    Returns:
        Confidence level: High, Medium, or Low
    """
    if features_completeness >= 0.7:
        return "High"
    elif features_completeness >= 0.5:
        return "Medium"
    else:
        return "Low"


def calculate_confidence_interval(prediction: float, confidence_level: str) -> tuple:
    """
    Calculate confidence interval for prediction

    Args:
        prediction: Predicted revenue (log scale)
        confidence_level: High, Medium, or Low

    Returns:
        Tuple of (lower_bound, upper_bound) in original scale
    """
    # Confidence intervals based on typical model performance
    # These are rough estimates - ideally would be calculated from validation set
    interval_widths = {
        "High": 0.2,    # ±20%
        "Medium": 0.35,  # ±35%
        "Low": 0.5       # ±50%
    }

    width = interval_widths.get(confidence_level, 0.5)

    # Convert to original scale
    pred_original = np.expm1(prediction)

    lower = pred_original * (1 - width)
    upper = pred_original * (1 + width)

    return max(0, lower), upper


@router.get("/models/status")
async def get_model_status():
    """Get status of loaded ML models"""
    try:
        load_models()

        return {
            "status": "ready",
            "feature_engineer_loaded": _feature_engineer is not None,
            "ensemble_model_loaded": _ensemble_model is not None,
            "best_model_loaded": _best_model is not None,
            "metadata_available": _model_metadata is not None,
            "best_model": _model_metadata.get("best_model") if _model_metadata else None,
            "training_samples": _model_metadata.get("training_samples") if _model_metadata else None,
            "feature_count": len(_feature_engineer.feature_names) if _feature_engineer else 0
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Models not available: {str(e)}")


@router.post("/predict/revenue", response_model=RevenuePrediction)
async def predict_revenue(features: CompanyFeatures):
    """
    Predict company revenue based on input features

    Returns predicted revenue in millions USD with confidence interval
    """
    try:
        load_models()

        # Convert input to DataFrame
        input_dict = features.dict()
        df = pd.DataFrame([input_dict])

        # Calculate features completeness
        non_null_count = df.notna().sum(axis=1).values[0]
        total_features = len(df.columns)
        features_completeness = non_null_count / total_features

        # Preprocess features using feature engineer
        # Note: We need to handle this carefully since the feature engineer
        # expects the same columns as training data
        df_processed = _feature_engineer.transform(df, target='revenue_usd_millions')

        # Make prediction (ensemble if available, otherwise best model)
        if _ensemble_model:
            prediction_log = _ensemble_model.predict(df_processed)[0]
            model_used = "Ensemble"
        elif _best_model:
            prediction_log = _best_model.predict(df_processed)[0]
            model_used = "XGBoost"
        else:
            raise HTTPException(status_code=503, detail="No trained models available")

        # Convert from log scale to original scale
        predicted_revenue = np.expm1(prediction_log)

        # Calculate confidence
        confidence = calculate_confidence(prediction_log, features_completeness)
        lower, upper = calculate_confidence_interval(prediction_log, confidence)

        return RevenuePrediction(
            predicted_revenue_millions=round(predicted_revenue, 2),
            confidence_interval_lower=round(lower, 2),
            confidence_interval_upper=round(upper, 2),
            model_used=model_used,
            prediction_confidence=confidence,
            features_used=int(non_null_count)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_revenue_batch(request: BatchPredictionRequest):
    """
    Predict revenue for multiple companies in batch

    More efficient than individual predictions
    """
    try:
        load_models()

        predictions = []

        for company_features in request.companies:
            # Convert to DataFrame
            input_dict = company_features.dict()
            df = pd.DataFrame([input_dict])

            # Calculate features completeness
            non_null_count = df.notna().sum(axis=1).values[0]
            features_completeness = non_null_count / len(df.columns)

            # Preprocess
            df_processed = _feature_engineer.transform(df, target='revenue_usd_millions')

            # Predict
            if _ensemble_model:
                prediction_log = _ensemble_model.predict(df_processed)[0]
                model_used = "Ensemble"
            elif _best_model:
                prediction_log = _best_model.predict(df_processed)[0]
                model_used = "XGBoost"
            else:
                raise HTTPException(status_code=503, detail="No trained models available")

            # Convert and calculate confidence
            predicted_revenue = np.expm1(prediction_log)
            confidence = calculate_confidence(prediction_log, features_completeness)
            lower, upper = calculate_confidence_interval(prediction_log, confidence)

            predictions.append(RevenuePrediction(
                predicted_revenue_millions=round(predicted_revenue, 2),
                confidence_interval_lower=round(lower, 2),
                confidence_interval_upper=round(upper, 2),
                model_used=model_used,
                prediction_confidence=confidence,
                features_used=int(non_null_count)
            ))

        return BatchPredictionResponse(
            predictions=predictions,
            total_predictions=len(predictions)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}"
        )


@router.get("/models/performance")
async def get_model_performance():
    """Get performance metrics of trained models"""
    try:
        load_models()

        if _model_metadata is None:
            raise HTTPException(
                status_code=404,
                detail="Model performance metrics not available"
            )

        return {
            "best_model": _model_metadata.get("best_model"),
            "metrics": _model_metadata.get("metrics"),
            "ensemble_weights": _model_metadata.get("ensemble_weights"),
            "training_samples": _model_metadata.get("training_samples"),
            "test_samples": _model_metadata.get("test_samples")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/features/importance")
async def get_feature_importance(top_n: int = 20):
    """Get feature importance from trained models"""
    try:
        results_dir = Path(__file__).parent.parent.parent / "ml_pipeline" / "output" / "results"
        importance_path = results_dir / "feature_importance_comparison.csv"

        if not importance_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Feature importance data not available"
            )

        # Read feature importance
        df = pd.read_csv(importance_path, index_col=0)
        top_features = df.head(top_n)

        return {
            "top_features": top_features.to_dict(orient="index"),
            "total_features": len(df)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feature importance: {str(e)}"
        )


@router.post("/enrich/company/{company_id}")
async def enrich_company_with_prediction(
    company_id: int,
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Enrich a single company with ML revenue prediction

    Args:
        company_id: Company ID to enrich
        force_update: Re-predict even if prediction already exists

    Returns:
        Updated company with prediction
    """
    try:
        enrichment_service = MLEnrichmentService()
        company = enrichment_service.enrich_company(db, company_id, force_update)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found"
            )

        # Get full prediction details
        prediction = enrichment_service.predict_revenue(company)

        # Format features completeness, handling NaN values
        features_completeness_display = None
        if prediction and prediction.get('features_completeness') is not None:
            import math
            completeness = prediction['features_completeness']
            if not math.isnan(completeness):
                features_completeness_display = f"{completeness * 100:.1f}%"

        return {
            "company_id": company.id,
            "company_name": company.name,
            "predicted_revenue_millions": prediction['predicted_revenue'] if prediction else None,
            "confidence_level": prediction['confidence_level'] if prediction else None,
            "confidence_interval": {
                "lower": prediction['confidence_lower'] if prediction else None,
                "upper": prediction['confidence_upper'] if prediction else None
            },
            "features_completeness": features_completeness_display,
            "updated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enrich company: {str(e)}"
        )


@router.post("/enrich/batch")
async def enrich_companies_batch(
    company_ids: List[int],
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Enrich multiple companies with ML predictions

    Args:
        company_ids: List of company IDs to enrich
        force_update: Re-predict even if predictions already exist

    Returns:
        Summary of enrichment results
    """
    try:
        enrichment_service = MLEnrichmentService()
        enriched_count = enrichment_service.enrich_companies_batch(
            db, company_ids, force_update
        )

        return {
            "total_requested": len(company_ids),
            "successfully_enriched": enriched_count,
            "message": f"Enriched {enriched_count} out of {len(company_ids)} companies"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch enrichment failed: {str(e)}"
        )


@router.post("/enrich/all")
async def enrich_all_companies(
    force_update: bool = False,
    batch_size: int = 100,
    db: Session = Depends(get_db)
):
    """
    Enrich ALL companies in database with ML predictions

    WARNING: This may take several minutes for large databases

    Args:
        force_update: Re-predict for all companies (even those with existing predictions)
        batch_size: Number of companies to process at once

    Returns:
        Summary of enrichment results
    """
    try:
        enrichment_service = MLEnrichmentService()
        enriched_count = enrichment_service.enrich_all_companies(
            db, force_update, batch_size
        )

        return {
            "successfully_enriched": enriched_count,
            "message": f"Successfully enriched {enriched_count} companies with ML predictions"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bulk enrichment failed: {str(e)}"
        )
