#!/usr/bin/env python3
"""
Enrich ALL companies with ML predictions
Run this locally with database access, then the predictions will sync to production
"""
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')
sys.path.insert(0, 'ml_pipeline')

from sqlalchemy.orm import Session
from backend.database_pool import get_db
from backend.services.ml_enrichment_service import MLEnrichmentService
from src.models.database_models_v2 import Company
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enrich_all_companies(batch_size=100, force_update=False):
    """
    Enrich all companies in the database with ML predictions

    Args:
        batch_size: Number of companies to process at once
        force_update: If True, re-predict for companies that already have predictions
    """
    print("=" * 80)
    print("ML ENRICHMENT - BATCH PROCESSING")
    print("=" * 80)
    print()

    # Initialize ML service
    print("Loading ML models...")
    service = MLEnrichmentService()
    service._load_models()

    if not service._models_loaded or not service._ensemble_model:
        print("❌ ERROR: Failed to load ML models")
        print("   Make sure models exist in ml_pipeline/output/models/")
        return 0

    print(f"✅ Models loaded successfully")
    print(f"   Feature count: {len(service._feature_engineer.feature_names)}")
    print()

    # Get database session
    db = next(get_db())

    try:
        # Query companies
        if force_update:
            query = db.query(Company)
            print("Processing ALL companies (force update enabled)")
        else:
            query = db.query(Company).filter(Company.predicted_revenue.is_(None))
            print("Processing companies WITHOUT predictions")

        total = query.count()
        print(f"Total companies to process: {total}")
        print()

        if total == 0:
            print("✅ All companies already have predictions!")
            print("   Use force_update=True to re-process all companies")
            return 0

        # Process in batches with progress bar
        enriched = 0
        failed = 0

        with tqdm(total=total, desc="Enriching companies", unit="company") as pbar:
            for offset in range(0, total, batch_size):
                companies = query.offset(offset).limit(batch_size).all()

                for company in companies:
                    try:
                        prediction = service.predict_revenue(company)

                        if prediction:
                            # Update company
                            company.predicted_revenue = float(prediction['predicted_revenue'])
                            company.prediction_confidence = float(prediction['features_completeness'])
                            enriched += 1
                        else:
                            failed += 1
                            logger.debug(f"Prediction failed for company {company.id}: {company.name}")

                    except Exception as e:
                        failed += 1
                        logger.error(f"Error processing company {company.id} ({company.name}): {e}")

                    pbar.update(1)

                # Commit batch
                db.commit()

        print()
        print("=" * 80)
        print("ENRICHMENT COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully enriched: {enriched} companies")
        print(f"❌ Failed: {failed} companies")
        print(f"📊 Success rate: {enriched/total*100:.1f}%")
        print()

        # Show sample results
        if enriched > 0:
            print("Sample predictions:")
            samples = db.query(Company).filter(
                Company.predicted_revenue.isnot(None)
            ).limit(5).all()

            for company in samples:
                print(f"  • {company.name[:40]:40} → ${company.predicted_revenue:>8.2f}M (confidence: {company.prediction_confidence:.2%})")

        print()
        print("🚀 Predictions are now in the database!")
        print("   Commit and push to sync to production, or they should auto-sync if using the same DB.")

        return enriched

    except Exception as e:
        logger.error(f"Fatal error during enrichment: {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich all companies with ML predictions")
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    parser.add_argument('--force', action='store_true', help='Re-predict for companies that already have predictions')

    args = parser.parse_args()

    enriched = enrich_all_companies(
        batch_size=args.batch_size,
        force_update=args.force
    )

    sys.exit(0 if enriched > 0 else 1)
