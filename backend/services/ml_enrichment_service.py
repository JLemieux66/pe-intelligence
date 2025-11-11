"""
ML Enrichment Service - Add ML predictions to company data
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add ml_pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml_pipeline"))

from src.models.database_models_v2 import Company
import pandas as pd
import numpy as np
import pickle


class MLEnrichmentService:
    """Service for enriching company data with ML predictions"""

    def __init__(self):
        self._feature_engineer = None
        self._ensemble_model = None
        self._models_loaded = False

    def _load_models(self):
        """Load ML models if not already loaded"""
        if self._models_loaded:
            return

        models_dir = Path(__file__).parent.parent.parent / "ml_pipeline" / "output" / "models"

        # Load feature engineer
        fe_path = models_dir / "feature_engineer.pkl"
        if fe_path.exists():
            with open(fe_path, 'rb') as f:
                self._feature_engineer = pickle.load(f)

        # Load ensemble model
        ensemble_path = models_dir / "ensemble.pkl"
        if ensemble_path.exists():
            with open(ensemble_path, 'rb') as f:
                self._ensemble_model = pickle.load(f)

        self._models_loaded = True

    def prepare_company_features(self, company: Company) -> Dict[str, Any]:
        """Extract features from company for ML prediction"""
        return {
            # Valuation is already in millions USD according to schema
            'pitchbook_valuation_usd_millions': company.last_known_valuation_usd,
            'employee_count_pitchbook': company.employee_count,
            'employee_count_linkedin_scraped': company.projected_employee_count,
            'pitchbook_last_financing_size_usd_millions': company.last_financing_size_usd,
            'total_funding_usd': float(company.total_funding_usd) if company.total_funding_usd else 0,
            'num_funding_rounds': company.num_funding_rounds or 0,
            'avg_round_size_usd': float(company.avg_round_size_usd) if company.avg_round_size_usd else 0,
            'total_investors': company.total_investors or 0,
            'months_since_last_funding': company.months_since_last_funding,
            'funding_stage_encoded': float(company.funding_stage_encoded) if company.funding_stage_encoded else None,
            'company_age_years': (2025 - company.founded_year) if company.founded_year else None,
            'founded_year': float(company.founded_year) if company.founded_year else None,
            'num_pe_investors': 1,  # Since it's in PE portfolio
            'is_pe_backed': 1,
            'is_public': company.is_public or False,
            'pitchbook_primary_industry_sector': company.primary_industry_sector,
            'pitchbook_primary_industry_group': company.primary_industry_group,
            'pitchbook_hq_country': company.hq_country,
            'latest_funding_type': company.latest_funding_type,
            'crunchbase_revenue_range': company.revenue_range,
            'company_size_category': company.company_size_category,
            'country': company.country,
            'state_region': company.state_region,
            'city': company.city,
            'pitchbook_last_financing_date': str(company.last_financing_date) if company.last_financing_date else None,
            'pitchbook_last_financing_deal_type': company.last_financing_deal_type,
            'pitchbook_verticals': company.verticals
        }

    def predict_revenue(self, company: Company) -> Optional[Dict[str, Any]]:
        """
        Predict revenue for a company

        Returns:
            Dict with predicted_revenue, confidence_level, confidence_lower, confidence_upper
            or None if prediction fails
        """
        try:
            self._load_models()

            if not self._models_loaded or not self._ensemble_model or not self._feature_engineer:
                return None

            # Prepare features
            features = self.prepare_company_features(company)
            df = pd.DataFrame([features])

            # Calculate feature completeness
            non_null_count = df.notna().sum(axis=1).values[0]
            total_features = len(df.columns)
            features_completeness = non_null_count / total_features

            # Transform features
            try:
                df_processed = self._feature_engineer.transform(df, target='revenue_usd_millions')
            except Exception as e:
                # Only log errors, not every transformation attempt
                import logging
                logging.error(f"Feature transformation error for company {company.id}: {e}")
                return None

            # Make prediction
            prediction_log = self._ensemble_model.predict(df_processed)[0]
            predicted_revenue = np.expm1(prediction_log)

            # Calculate confidence level
            if features_completeness >= 0.7:
                confidence = "High"
                interval_width = 0.2
            elif features_completeness >= 0.5:
                confidence = "Medium"
                interval_width = 0.35
            else:
                confidence = "Low"
                interval_width = 0.5

            # Calculate confidence intervals
            lower = max(0, predicted_revenue * (1 - interval_width))
            upper = predicted_revenue * (1 + interval_width)

            return {
                'predicted_revenue': round(predicted_revenue, 2),
                'confidence_level': confidence,
                'confidence_lower': round(lower, 2),
                'confidence_upper': round(upper, 2),
                'features_completeness': features_completeness
            }

        except Exception as e:
            # Only log errors, don't print for every prediction
            import logging
            logging.error(f"Prediction error for company {company.id}: {e}")
            return None

    def enrich_company(self, db: Session, company_id: int, force_update: bool = False) -> Optional[Company]:
        """
        Enrich a company with ML predictions and save to database

        Args:
            db: Database session
            company_id: Company ID to enrich
            force_update: Force re-prediction even if already exists

        Returns:
            Updated company object or None if failed
        """
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None

        # Skip if already has prediction and not forcing update
        if company.predicted_revenue and not force_update:
            return company

        # Get prediction
        prediction = self.predict_revenue(company)
        if not prediction:
            return company

        # Update company with prediction - convert numpy types to Python floats for PostgreSQL
        # Store predicted revenue in millions USD (consistent with current_revenue_usd field)
        company.predicted_revenue = float(prediction['predicted_revenue'])
        company.prediction_confidence = float(prediction['features_completeness'])  # Store as float for now

        # Note: We'll need to add confidence interval fields to the database model
        # For now, we'll return them in the API response

        db.commit()
        db.refresh(company)

        return company

    def enrich_companies_batch(self, db: Session, company_ids: list, force_update: bool = False) -> int:
        """
        Enrich multiple companies with ML predictions

        Returns:
            Number of companies successfully enriched
        """
        count = 0
        for company_id in company_ids:
            if self.enrich_company(db, company_id, force_update):
                count += 1
        return count

    def enrich_all_companies(self, db: Session, force_update: bool = False, batch_size: int = 100) -> int:
        """
        Enrich all companies in database with ML predictions

        Args:
            db: Database session
            force_update: Force re-prediction for all companies
            batch_size: Number of companies to process at once

        Returns:
            Total number of companies enriched
        """
        self._load_models()

        if not self._models_loaded:
            return 0

        # Query companies
        if force_update:
            query = db.query(Company)
        else:
            query = db.query(Company).filter(Company.predicted_revenue.is_(None))

        total = query.count()
        enriched = 0

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Enriching {total} companies with ML predictions")

        # Process in batches
        for offset in range(0, total, batch_size):
            companies = query.offset(offset).limit(batch_size).all()

            for company in companies:
                prediction = self.predict_revenue(company)
                if prediction:
                    # Convert numpy types to Python floats for PostgreSQL
                    # Store predicted revenue in millions USD (consistent with current_revenue_usd field)
                    company.predicted_revenue = float(prediction['predicted_revenue'])
                    company.prediction_confidence = float(prediction['features_completeness'])
                    enriched += 1

            db.commit()
            # Only log every 10 batches to reduce log spam
            if offset % (batch_size * 10) == 0:
                logger.info(f"Progress: {min(offset + batch_size, total)}/{total} companies processed")

        logger.info(f"Enrichment complete! {enriched} companies enriched with ML predictions")
        return enriched
