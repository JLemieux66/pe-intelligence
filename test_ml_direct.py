#!/usr/bin/env python3
"""
Direct ML Prediction Test Script
Tests ML prediction pipeline directly without going through API
"""
import sys
sys.path.insert(0, '/home/user/pe-intelligence')
sys.path.insert(0, '/home/user/pe-intelligence/ml_pipeline')

from sqlalchemy.orm import Session
from backend.database_pool import get_db
from backend.services.ml_enrichment_service import MLEnrichmentService
from src.models.database_models_v2 import Company
import json

def test_ml_prediction(company_name="100ms"):
    """Test ML prediction for a specific company"""

    print(f"=== Testing ML Prediction for '{company_name}' ===\n")

    # Get database session
    db = next(get_db())

    try:
        # Find company
        print(f"1. Searching for company '{company_name}'...")
        company = db.query(Company).filter(Company.name.ilike(f'%{company_name}%')).first()

        if not company:
            print(f"ERROR: Company '{company_name}' not found")
            return

        print(f"   Found: {company.name} (ID: {company.id})")
        print(f"   Employee Count: {company.employee_count}")
        print(f"   Total Funding: ${company.total_funding_usd:,}" if company.total_funding_usd else "   Total Funding: None")
        print(f"   Valuation: ${company.last_known_valuation_usd}M" if company.last_known_valuation_usd else "   Valuation: None")
        print()

        # Initialize ML service
        print("2. Initializing ML enrichment service...")
        enrichment_service = MLEnrichmentService()

        # Get prediction
        print("3. Generating revenue prediction...")
        prediction = enrichment_service.predict_revenue(company)

        if prediction:
            print("   ✅ Prediction successful!")
            print(f"   Predicted Revenue: ${prediction['predicted_revenue']:.2f}M")
            print(f"   Confidence Level: {prediction['confidence_level']}")
            print(f"   Confidence Interval: ${prediction['confidence_lower']:.2f}M - ${prediction['confidence_upper']:.2f}M")
            print(f"   Feature Completeness: {prediction['features_completeness']*100:.1f}%")
            print()

            # Update database
            print("4. Updating database...")
            company.predicted_revenue = float(prediction['predicted_revenue'])
            company.prediction_confidence = float(prediction['features_completeness'])
            db.commit()
            db.refresh(company)

            print("   ✅ Database updated successfully")
            print(f"   New predicted_revenue in DB: {company.predicted_revenue}")
            print(f"   New prediction_confidence in DB: {company.prediction_confidence}")

        else:
            print("   ❌ Prediction failed - check error logs above")

            # Show company features for debugging
            print("\n5. Company features (for debugging):")
            features = enrichment_service.prepare_company_features(company)
            for key, value in features.items():
                if value is not None and value != '' and value != 0:
                    print(f"   {key}: {value}")

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    company_name = sys.argv[1] if len(sys.argv) > 1 else "100ms"
    test_ml_prediction(company_name)
