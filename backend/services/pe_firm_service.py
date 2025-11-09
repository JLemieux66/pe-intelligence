"""
PE Firm service for business logic and data processing
"""
from typing import List, Dict, Any
from sqlalchemy import func, distinct
from backend.services.base import BaseService
from backend.schemas.responses import PEFirmResponse
from src.models.database_models_v2 import PEFirm, CompanyPEInvestment


class PEFirmService(BaseService):
    """Service for PE firm-related business logic"""
    
    def get_pe_firms(self) -> List[PEFirmResponse]:
        """Get all PE firms with investment counts"""
        
        # Query PE firms with investment counts
        pe_firms_data = self.session.query(
            PEFirm.id,
            PEFirm.name,
            func.count(CompanyPEInvestment.id).label('investment_count')
        ).outerjoin(CompanyPEInvestment).group_by(
            PEFirm.id, PEFirm.name
        ).order_by(PEFirm.name).all()
        
        result = []
        for firm_data in pe_firms_data:
            # Get active and exit investment counts
            active_count = self.session.query(CompanyPEInvestment).filter(
                CompanyPEInvestment.pe_firm_id == firm_data.id,
                CompanyPEInvestment.computed_status.ilike('%Active%')
            ).count()
            
            exit_count = self.session.query(CompanyPEInvestment).filter(
                CompanyPEInvestment.pe_firm_id == firm_data.id,
                CompanyPEInvestment.computed_status.ilike('%Exit%')
            ).count()
            
            result.append(PEFirmResponse(
                id=firm_data.id,
                name=firm_data.name,
                total_investments=firm_data.investment_count,
                active_count=active_count,
                exit_count=exit_count
            ))
        
        return result