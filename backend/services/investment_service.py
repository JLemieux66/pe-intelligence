"""
Investment service for business logic and data processing
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import or_, text
from sqlalchemy.orm import Session
from backend.services.base import BaseService
from backend.schemas.responses import InvestmentResponse
from backend.schemas.requests import InvestmentUpdate
from src.models.database_models_v2 import (
    Company, CompanyPEInvestment, PEFirm, CompanyTag
)
from src.enrichment.crunchbase_helpers import decode_revenue_range


class InvestmentService(BaseService):
    """Service for investment-related business logic"""
    
    def get_employee_count_display(self, company: Company) -> Optional[str]:
        """
        Get employee count for display - returns the best available value.
        Priority: PitchBook/exact count > projected LinkedIn count > Crunchbase range
        """
        # Check PitchBook employee_count first (from PitchBook ingestion)
        if hasattr(company, 'employee_count') and company.employee_count:
            return f"{company.employee_count:,}"  # e.g., "1,234"
        # If we have exact LinkedIn count, format it nicely
        elif company.projected_employee_count:
            return f"{company.projected_employee_count:,}"  # e.g., "1,234"
        # Fall back to Crunchbase range
        elif company.crunchbase_employee_count:
            from src.enrichment.crunchbase_helpers import decode_employee_count
            return decode_employee_count(company.crunchbase_employee_count)  # e.g., "501-1,000"
        return None
    
    def build_headquarters(self, company: Company) -> Optional[str]:
        """Build headquarters string from geographic fields (prioritize PitchBook data)"""
        hq_parts = []
        
        # Use PitchBook location first if available
        if company.hq_location:
            hq_parts.append(company.hq_location)
            if company.hq_country:
                hq_parts.append(company.hq_country)
        # Fall back to city/state/country
        else:
            if company.city:
                hq_parts.append(company.city)
            if company.state_region:
                hq_parts.append(company.state_region)
            if company.country:
                hq_parts.append(company.country)
        
        return ", ".join(hq_parts) if hq_parts else None
    
    def get_crunchbase_url_with_fallback(self, company: Company) -> Optional[str]:
        """Get crunchbase_url with raw SQL fallback for model cache issues"""
        try:
            # Try direct attribute access first
            return company.crunchbase_url
        except AttributeError:
            # Model cache issue - use raw SQL fallback
            try:
                cb_result = self.session.execute(
                    text("SELECT crunchbase_url FROM companies WHERE id = :id"),
                    {"id": company.id}
                ).fetchone()
                if cb_result:
                    return cb_result[0]
            except Exception as e:
                print(f"[ERROR] Failed to get crunchbase_url for company {company.id}: {e}")
                return None
        return None
    
    def get_company_industries(self, company_id: int) -> List[str]:
        """Get individual industry tags for a company (excluding 'Other')"""
        industry_tags = self.session.query(CompanyTag.tag_value).filter(
            CompanyTag.company_id == company_id,
            CompanyTag.tag_category == 'industry',
            CompanyTag.tag_value != 'Other'
        ).all()
        return [tag[0] for tag in industry_tags]

    def get_prediction_confidence_display(self, company: Company) -> Optional[str]:
        """Convert prediction confidence float (0-1) to display string (High/Medium/Low)"""
        if company.prediction_confidence is None:
            return None

        confidence = company.prediction_confidence
        if confidence >= 0.7:
            return "High"
        elif confidence >= 0.5:
            return "Medium"
        else:
            return "Low"

    def build_investment_response(self, investment: CompanyPEInvestment) -> InvestmentResponse:
        """Build a complete InvestmentResponse from a CompanyPEInvestment model"""
        headquarters = self.build_headquarters(investment.company)
        crunchbase_url = self.get_crunchbase_url_with_fallback(investment.company)
        industries_list = self.get_company_industries(investment.company.id)
        
        return InvestmentResponse(
            investment_id=investment.id,
            company_id=investment.company.id,
            company_name=investment.company.name,
            pe_firm_name=investment.pe_firm.name,
            status=investment.computed_status or 'Unknown',
            raw_status=investment.raw_status,
            exit_type=investment.exit_type,
            exit_info=investment.exit_info,
            investment_year=investment.investment_year,
            sector=investment.sector_page,
            revenue_range=decode_revenue_range(investment.company.revenue_range),
            employee_count=self.get_employee_count_display(investment.company),
            industry_category=investment.company.industry_category,
            industries=industries_list,
            predicted_revenue=investment.company.predicted_revenue,  # Already in millions in DB
            prediction_confidence=investment.company.prediction_confidence,  # Keep as float 0-1 for frontend
            headquarters=headquarters,
            website=investment.company.website,
            linkedin_url=investment.company.linkedin_url,
            crunchbase_url=crunchbase_url,
            # PitchBook data
            primary_industry_group=getattr(investment.company, 'primary_industry_group', None),
            primary_industry_sector=getattr(investment.company, 'primary_industry_sector', None),
            verticals=getattr(investment.company, 'verticals', None),
            current_revenue_usd=float(investment.company.current_revenue_usd) if getattr(investment.company, 'current_revenue_usd', None) else None,
            hq_location=getattr(investment.company, 'hq_location', None),
            hq_country=getattr(investment.company, 'hq_country', None),
            last_known_valuation_usd=float(investment.company.last_known_valuation_usd) if getattr(investment.company, 'last_known_valuation_usd', None) else None
        )
    
    def apply_filters(self, query, filters: Dict[str, Any]):
        """Apply all filters to an investment query"""
        
        # Company ID filter (for fetching investments by company)
        if filters.get('company_id'):
            query = query.filter(CompanyPEInvestment.company_id == filters['company_id'])
        
        # PE Firm filter
        if filters.get('pe_firm'):
            pe_firms = [f.strip() for f in filters['pe_firm'].split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))
        
        if filters.get('status'):
            query = query.filter(CompanyPEInvestment.computed_status.ilike(f"%{filters['status']}%"))
        
        if filters.get('exit_type'):
            query = query.filter(CompanyPEInvestment.exit_type.ilike(f"%{filters['exit_type']}%"))
        
        if filters.get('industry'):
            # Filter by individual industry tags instead of string matching
            industries = [i.strip() for i in filters['industry'].split(',')]
            # Join with company_tags table and filter by industry tags
            query = query.join(CompanyTag, Company.id == CompanyTag.company_id).filter(
                CompanyTag.tag_category == 'industry',
                CompanyTag.tag_value.in_(industries)
            ).distinct()
        
        # PitchBook filters
        if filters.get('industry_group'):
            groups = [g.strip() for g in filters['industry_group'].split(',')]
            query = query.filter(
                Company.primary_industry_group != None,
                Company.primary_industry_group.in_(groups)
            )
        
        if filters.get('industry_sector'):
            sectors = [s.strip() for s in filters['industry_sector'].split(',')]
            query = query.filter(
                Company.primary_industry_sector != None,
                Company.primary_industry_sector.in_(sectors)
            )
        
        if filters.get('verticals'):
            # Verticals are comma-separated in the database, so we need to check if any match
            vertical_list = [v.strip() for v in filters['verticals'].split(',')]
            vertical_conditions = [Company.verticals.ilike(f"%{v}%") for v in vertical_list]
            query = query.filter(
                Company.verticals != None,
                or_(*vertical_conditions)
            )
        
        # Location filters
        if filters.get('country'):
            countries = [c.strip() for c in filters['country'].split(',')]
            query = query.filter(
                Company.country != None,
                Company.country.in_(countries)
            )
        
        if filters.get('state_region'):
            states = [s.strip() for s in filters['state_region'].split(',')]
            query = query.filter(
                Company.state_region != None,
                Company.state_region.in_(states)
            )
        
        if filters.get('city'):
            cities = [c.strip() for c in filters['city'].split(',')]
            query = query.filter(
                Company.city != None,
                Company.city.in_(cities)
            )
        
        # Revenue filters
        if filters.get('min_revenue') is not None:
            query = query.filter(Company.current_revenue_usd >= filters['min_revenue'])
        
        if filters.get('max_revenue') is not None:
            query = query.filter(Company.current_revenue_usd <= filters['max_revenue'])
        
        # Employee count filters
        if filters.get('min_employees') is not None:
            # Try to parse employee_count field (which might be a range like "101-250")
            query = query.filter(
                or_(
                    Company.projected_employee_count >= filters['min_employees'],
                    Company.employee_count >= filters['min_employees'],
                    Company.crunchbase_employee_count.ilike(f"%{filters['min_employees']}%")
                )
            )
        
        if filters.get('max_employees') is not None:
            query = query.filter(
                or_(
                    Company.projected_employee_count <= filters['max_employees'],
                    Company.employee_count <= filters['max_employees'],
                    Company.crunchbase_employee_count.ilike(f"%{filters['max_employees']}%")
                )
            )
        
        if filters.get('search'):
            query = query.filter(Company.name.ilike(f"%{filters['search']}%"))
        
        return query
    
    def get_investments(self, filters: Dict[str, Any], limit: int = 10000, offset: int = 0) -> List[InvestmentResponse]:
        """Get investments with filters and pagination"""
        
        query = self.session.query(CompanyPEInvestment).join(Company).join(PEFirm)
        
        # Apply all filters
        query = self.apply_filters(query, filters)
        
        # Order by company name
        query = query.order_by(Company.name)
        
        # Apply pagination
        investments = query.offset(offset).limit(limit).all()
        
        # Build response objects
        result = [self.build_investment_response(inv) for inv in investments]
        
        return result
    
    def update_investment(self, investment_id: int, investment_update: InvestmentUpdate) -> bool:
        """Update investment details"""
        investment = self.session.query(CompanyPEInvestment).filter(CompanyPEInvestment.id == investment_id).first()
        if not investment:
            return False
        
        try:
            # Update fields if provided
            if investment_update.computed_status is not None:
                investment.computed_status = investment_update.computed_status
            if investment_update.raw_status is not None:
                investment.raw_status = investment_update.raw_status
            if investment_update.exit_type is not None:
                investment.exit_type = investment_update.exit_type
            if investment_update.exit_info is not None:
                investment.exit_info = investment_update.exit_info
            if investment_update.exit_year is not None:
                investment.exit_year = investment_update.exit_year
            if investment_update.investment_year is not None:
                investment.investment_year = investment_update.investment_year
            
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False