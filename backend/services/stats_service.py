"""
Stats service for business logic and data processing
"""
from typing import Dict, Any
from sqlalchemy import func, distinct
from backend.services.base import BaseService
from backend.schemas.responses import StatsResponse
from src.models.database_models_v2 import Company, CompanyPEInvestment, PEFirm


class StatsService(BaseService):
    """Service for statistics-related business logic"""
    
    def get_stats(self) -> StatsResponse:
        """Get comprehensive statistics for the dashboard"""
        
        # Total companies
        total_companies = self.session.query(Company).count()
        
        # Total PE firms
        total_pe_firms = self.session.query(PEFirm).count()
        
        # Total investments
        total_investments = self.session.query(CompanyPEInvestment).count()
        
        # Active vs Exit investments
        active_investments = self.session.query(CompanyPEInvestment).filter_by(computed_status='Active').count()
        exit_investments = self.session.query(CompanyPEInvestment).filter_by(computed_status='Exit').count()
        
        # Co-investments: companies with multiple PE firms
        co_investments = self.session.query(Company.id).join(CompanyPEInvestment).group_by(Company.id).having(
            func.count(CompanyPEInvestment.pe_firm_id) > 1
        ).count()
        
        # Enrichment rate: companies with LinkedIn URLs
        enriched = self.session.query(Company).filter(Company.linkedin_url != None).count()
        enrichment_rate = (enriched / total_companies * 100) if total_companies > 0 else 0
        
        return StatsResponse(
            total_companies=total_companies,
            total_investments=total_investments,
            total_pe_firms=total_pe_firms,
            active_investments=active_investments,
            exited_investments=exit_investments,
            co_investments=co_investments,
            enrichment_rate=round(enrichment_rate, 1)
        )