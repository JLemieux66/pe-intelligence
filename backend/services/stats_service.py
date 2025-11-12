"""
Stats service for business logic and data processing
OPTIMIZED: Uses batched queries to reduce database round trips + caching
"""
from typing import Dict, Any
from sqlalchemy import func, distinct, case
from backend.services.base import BaseService
from backend.schemas.responses import StatsResponse
from src.models.database_models_v2 import Company, CompanyPEInvestment, PEFirm
from backend.middleware.query_cache import cache_result


class StatsService(BaseService):
    """Service for statistics-related business logic"""

    @cache_result(ttl_seconds=300, key_prefix="dashboard_stats")
    def get_stats(self) -> StatsResponse:
        """
        Get comprehensive statistics for the dashboard.
        OPTIMIZED: Batches multiple COUNT queries into 1-2 queries instead of 7.
        """

        # OPTIMIZATION: Single query for most stats using aggregations
        stats = self.session.query(
            func.count(distinct(Company.id)).label('total_companies'),
            func.count(distinct(PEFirm.id)).label('total_pe_firms'),
            func.count(CompanyPEInvestment.id).label('total_investments'),
            func.sum(case((CompanyPEInvestment.computed_status == 'Active', 1), else_=0)).label('active'),
            func.sum(case((CompanyPEInvestment.computed_status == 'Exit', 1), else_=0)).label('exit'),
            func.sum(case((Company.linkedin_url != None, 1), else_=0)).label('enriched')
        ).select_from(Company).join(CompanyPEInvestment).join(PEFirm).first()

        # Co-investments requires a separate query (more complex aggregation)
        co_investments = self.session.query(Company.id).join(CompanyPEInvestment).group_by(Company.id).having(
            func.count(CompanyPEInvestment.pe_firm_id) > 1
        ).count()

        enrichment_rate = (stats.enriched / stats.total_companies * 100) if stats.total_companies > 0 else 0

        return StatsResponse(
            total_companies=stats.total_companies,
            total_investments=stats.total_investments,
            total_pe_firms=stats.total_pe_firms,
            active_investments=stats.active,
            exited_investments=stats.exit,
            co_investments=co_investments,
            enrichment_rate=round(enrichment_rate, 1)
        )