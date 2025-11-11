#!/usr/bin/env python3
"""
Quick ML Test - Run this in your backend environment (Railway console, Docker, etc.)
"""
import sys
import os

# Ensure we're in the right directory
os.chdir('/app' if os.path.exists('/app') else '/home/user/pe-intelligence')
sys.path.insert(0, '.')
sys.path.insert(0, 'ml_pipeline')

print("=== Quick ML Prediction Test ===\n")

# Test 1: Check if models exist
print("1. Checking if model files exist...")
import os.path
models = ['ensemble.pkl', 'feature_engineer.pkl', 'xgboost.pkl']
for model in models:
    path = f'ml_pipeline/output/models/{model}'
    exists = "✅" if os.path.exists(path) else "❌"
    print(f"   {exists} {model}")
print()

# Test 2: Load models
print("2. Loading ML models...")
try:
    from backend.services.ml_enrichment_service import MLEnrichmentService
    service = MLEnrichmentService()
    service._load_models()
    print(f"   ✅ Models loaded successfully")
    print(f"   ✅ Feature engineer has {len(service._feature_engineer.feature_names) if service._feature_engineer else 0} features")
except Exception as e:
    print(f"   ❌ Failed to load models: {e}")
    sys.exit(1)
print()

# Test 3: Find and predict for 100ms
print("3. Finding 100ms company...")
try:
    from backend.database_pool import get_db
    from src.models.database_models_v2 import Company

    db = next(get_db())
    company = db.query(Company).filter(Company.name.ilike('%100ms%')).first()

    if not company:
        print("   ❌ Company not found")
        sys.exit(1)

    print(f"   ✅ Found: {company.name} (ID: {company.id})")
    print(f"      Current predicted_revenue: {company.predicted_revenue}")
    print(f"      Current prediction_confidence: {company.prediction_confidence}")
    print()

    # Test 4: Generate prediction
    print("4. Generating prediction...")
    prediction = service.predict_revenue(company)

    if prediction:
        print(f"   ✅ Prediction successful!")
        print(f"      Predicted Revenue: ${prediction['predicted_revenue']:.2f}M")
        print(f"      Confidence Level: {prediction['confidence_level']}")
        print(f"      Feature Completeness: {prediction['features_completeness']*100:.1f}%")
        print()

        # Test 5: Update database
        print("5. Updating database...")
        company.predicted_revenue = float(prediction['predicted_revenue'])
        company.prediction_confidence = float(prediction['features_completeness'])
        db.commit()
        print(f"   ✅ Database updated!")
        print()

        print("=== Test Successful! ===")
        print(f"Company '{company.name}' now has predicted_revenue = ${company.predicted_revenue:.2f}M")
        print("Check your frontend - it should now show this value!")
    else:
        print("   ❌ Prediction failed")
        print("      Check backend logs for errors")

    db.close()

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
