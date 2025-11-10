"""
ML Admin API - Train models and manage ML system
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path
from backend.auth import verify_admin_token

router = APIRouter(prefix="/ml/admin", tags=["ML Admin"])


class TrainingStatus(BaseModel):
    """Training status response"""
    status: str
    message: str
    details: Optional[dict] = None


@router.post("/train", response_model=TrainingStatus, dependencies=[Depends(verify_admin_token)])
async def train_models(background_tasks: BackgroundTasks):
    """
    Train ML models in production

    This endpoint trains Random Forest, XGBoost, LightGBM, and Ensemble models
    using the latest data from the database.

    **IMPORTANT**: This operation:
    - Takes 5-15 minutes to complete
    - Runs in the background
    - Requires training data (companies with revenue)
    - Saves models to ml_pipeline/output/models/

    **Admin authentication required**
    """
    try:
        # Check if training data exists
        data_path = Path(__file__).parent.parent.parent / "ml_pipeline" / "data" / "companies_with_revenue.csv"

        if not data_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Training data not found at {data_path}. Please export data first using /api/companies/export/with-revenue"
            )

        # Import training function
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml_pipeline"))

        try:
            from train_models import main as train_main
        except ImportError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to import training module: {str(e)}"
            )

        # Run training in background
        def train_task():
            try:
                print("🤖 Starting ML model training...")
                train_main()
                print("✅ ML model training complete!")
            except Exception as e:
                print(f"❌ ML model training failed: {e}")

        background_tasks.add_task(train_task)

        return TrainingStatus(
            status="started",
            message="Model training started in background. Check logs for progress. This will take 5-15 minutes.",
            details={
                "training_data": str(data_path),
                "output_dir": "ml_pipeline/output/models/",
                "estimated_time": "5-15 minutes"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start training: {str(e)}"
        )


@router.get("/training-status", dependencies=[Depends(verify_admin_token)])
async def get_training_status():
    """
    Check if models are trained and ready

    Returns information about available models and their training status.

    **Admin authentication required**
    """
    models_dir = Path(__file__).parent.parent.parent / "ml_pipeline" / "output" / "models"
    results_dir = Path(__file__).parent.parent.parent / "ml_pipeline" / "output" / "results"

    models = {}
    for model_name in ["ensemble.pkl", "xgboost.pkl", "lightgbm.pkl", "random_forest.pkl", "feature_engineer.pkl"]:
        model_path = models_dir / model_name
        models[model_name] = {
            "exists": model_path.exists(),
            "path": str(model_path)
        }

    # Check for training results
    results_path = results_dir / "training_results.json"
    training_results = None
    if results_path.exists():
        import json
        with open(results_path, 'r') as f:
            training_results = json.load(f)

    # Determine overall status
    required_models = ["ensemble.pkl", "feature_engineer.pkl"]
    all_required_exist = all(models[m]["exists"] for m in required_models)

    return {
        "status": "ready" if all_required_exist else "not_trained",
        "message": "Models are ready for predictions" if all_required_exist else "Models need to be trained",
        "models": models,
        "training_results": training_results,
        "next_steps": [] if all_required_exist else [
            "1. Export training data: GET /api/companies/export/with-revenue > ml_pipeline/data/companies_with_revenue.csv",
            "2. Train models: POST /ml/admin/train",
            "3. Wait 5-15 minutes for training to complete",
            "4. Verify: GET /ml/admin/training-status"
        ]
    }


@router.post("/export-training-data", dependencies=[Depends(verify_admin_token)])
async def export_training_data():
    """
    Export training data from database to CSV

    Exports all companies with revenue data to ml_pipeline/data/companies_with_revenue.csv
    This file is then used to train the ML models.

    **Admin authentication required**
    """
    try:
        from backend.database_pool import SessionLocal
        from backend.services.company_service import CompanyService
        import pandas as pd

        db = SessionLocal()
        try:
            # Get all companies with revenue
            filters = {'min_revenue': 0}
            with CompanyService(db) as service:
                companies, total = service.get_companies(filters, limit=10000, offset=0)

            if total == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No companies with revenue data found in database"
                )

            # Convert to DataFrame
            data = []
            for company in companies:
                # Extract relevant fields for training
                data.append({
                    'revenue_usd_millions': company.current_revenue_usd,
                    'employee_count_pitchbook': company.employee_count,
                    # Add other fields as needed based on training script
                })

            df = pd.DataFrame(data)

            # Save to CSV
            output_path = Path(__file__).parent.parent.parent / "ml_pipeline" / "data" / "companies_with_revenue.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)

            return {
                "status": "success",
                "message": f"Exported {len(data)} companies to {output_path}",
                "total_companies": len(data),
                "output_file": str(output_path)
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export training data: {str(e)}"
        )
