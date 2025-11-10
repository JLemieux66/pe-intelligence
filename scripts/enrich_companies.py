#!/usr/bin/env python3
"""
Script to enrich companies with ML revenue predictions

Usage:
  python scripts/enrich_companies.py [--force]

Options:
  --force  Re-predict for all companies (even those with existing predictions)
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database_pool import SessionLocal
from backend.services.ml_enrichment_service import MLEnrichmentService


def main():
    force_update = '--force' in sys.argv

    print("="*80)
    print("ML REVENUE PREDICTION ENRICHMENT")
    print("="*80)

    if force_update:
        print("⚠️  FORCE MODE: Re-predicting for ALL companies")
    else:
        print("📊 Enriching companies without predictions")

    db = SessionLocal()
    try:
        enrichment_service = MLEnrichmentService()

        # Count total companies
        from src.models.database_models_v2 import Company
        total = db.query(Company).count()
        with_prediction = db.query(Company).filter(Company.predicted_revenue.isnot(None)).count()

        print(f"\nDatabase status:")
        print(f"  Total companies: {total}")
        print(f"  With predictions: {with_prediction}")
        print(f"  Without predictions: {total - with_prediction}")

        if not force_update and with_prediction == total:
            print("\n✅ All companies already have predictions!")
            print("   Use --force to re-predict anyway")
            return

        print(f"\n🤖 Starting enrichment...")
        count = enrichment_service.enrich_all_companies(
            db,
            force_update=force_update,
            batch_size=50
        )

        print(f"\n{'='*80}")
        print(f"✅ SUCCESS!")
        print(f"{'='*80}")
        print(f"Enriched {count} companies with ML predictions")

        # Show updated stats
        with_prediction = db.query(Company).filter(Company.predicted_revenue.isnot(None)).count()
        print(f"\nFinal status:")
        print(f"  Total companies: {total}")
        print(f"  With predictions: {with_prediction}")
        print(f"  Coverage: {(with_prediction/total*100):.1f}%")

        # Show sample
        sample = db.query(Company).filter(Company.predicted_revenue.isnot(None)).first()
        if sample:
            print(f"\nSample prediction:")
            print(f"  Company: {sample.name}")
            print(f"  Predicted Revenue: ${sample.predicted_revenue:.2f}M")
            print(f"  Confidence: {sample.prediction_confidence}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
