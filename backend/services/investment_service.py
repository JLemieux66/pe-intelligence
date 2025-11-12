"""
Investment service for business logic and data processing
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import or_, and_, text
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
        """
        Apply all filters to an investment query.
        ENHANCED: Supports AND/OR/EXACT operators for advanced filtering.
        """
        # Get operator settings (default to backward-compatible behavior)
        filter_operator = filters.get('filter_operator', 'AND').upper()
        search_exact = filters.get('search_exact', False)

        # Collect all filter conditions if using global OR operator
        all_conditions = []

        # Company ID filter (for fetching investments by company) - always AND
        if filters.get('company_id'):
            query = query.filter(CompanyPEInvestment.company_id == filters['company_id'])

        # Search filter
        if filters.get('search'):
            search_term = filters['search'].strip()
            if search_exact:
                search_condition = Company.name == search_term
            else:
                search_condition = Company.name.ilike(f"%{search_term}%")

            if filter_operator == 'OR':
                all_conditions.append(search_condition)
            else:
                query = query.filter(search_condition)

        # PE Firm filter with operator support
        if filters.get('pe_firm'):
            pe_firms = [f.strip() for f in filters['pe_firm'].split(',')]
            pe_firm_operator = filters.get('pe_firm_operator', 'OR').upper()

            if search_exact:
                firm_conditions = [PEFirm.name == firm for firm in pe_firms]
            else:
                firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]

            if pe_firm_operator == 'AND':
                # For AND: investment company must have ALL specified firms
                for firm_cond in firm_conditions:
                    query = query.filter(
                        Company.id.in_(
                            self.session.query(Company.id)
                            .join(CompanyPEInvestment)
                            .join(PEFirm)
                            .filter(firm_cond)
                        )
                    )
            else:
                # For OR: investment company must have ANY specified firm
                pe_firm_condition = or_(*firm_conditions)
                if filter_operator == 'OR':
                    all_conditions.append(pe_firm_condition)
                else:
                    query = query.filter(pe_firm_condition)

        # Status filter
        if filters.get('status'):
            status_condition = CompanyPEInvestment.computed_status.ilike(f"%{filters['status']}%")
            if filter_operator == 'OR':
                all_conditions.append(status_condition)
            else:
                query = query.filter(status_condition)

        # Exit type filter
        if filters.get('exit_type'):
            exit_condition = CompanyPEInvestment.exit_type.ilike(f"%{filters['exit_type']}%")
            if filter_operator == 'OR':
                all_conditions.append(exit_condition)
            else:
                query = query.filter(exit_condition)

        # Industry filter with operator support
        if filters.get('industry'):
            industries = [i.strip() for i in filters['industry'].split(',')]
            industry_operator = filters.get('industry_operator', 'OR').upper()

            if industry_operator == 'AND':
                # For AND: company must have ALL specified industry tags
                for industry in industries:
                    query = query.filter(
                        Company.id.in_(
                            self.session.query(CompanyTag.company_id)
                            .filter(
                                CompanyTag.tag_category == 'industry',
                                CompanyTag.tag_value == industry
                            )
                        )
                    )
            else:
                # For OR: company must have ANY specified industry tag
                industry_condition = Company.id.in_(
                    self.session.query(CompanyTag.company_id)
                    .filter(
                        CompanyTag.tag_category == 'industry',
                        CompanyTag.tag_value.in_(industries)
                    )
                )
                if filter_operator == 'OR':
                    all_conditions.append(industry_condition)
                else:
                    query = query.filter(industry_condition)

        # PitchBook filters with operator support
        if filters.get('industry_group'):
            groups = [g.strip() for g in filters['industry_group'].split(',')]
            industry_group_operator = filters.get('industry_group_operator', 'OR').upper()

            if industry_group_operator == 'AND':
                group_conditions = [Company.primary_industry_group == g for g in groups]
                group_condition = and_(
                    Company.primary_industry_group != None,
                    and_(*group_conditions)
                )
            else:
                group_condition = and_(
                    Company.primary_industry_group != None,
                    Company.primary_industry_group.in_(groups)
                )

            if filter_operator == 'OR':
                all_conditions.append(group_condition)
            else:
                query = query.filter(group_condition)

        if filters.get('industry_sector'):
            sectors = [s.strip() for s in filters['industry_sector'].split(',')]
            industry_sector_operator = filters.get('industry_sector_operator', 'OR').upper()

            if industry_sector_operator == 'AND':
                sector_conditions = [Company.primary_industry_sector == s for s in sectors]
                sector_condition = and_(
                    Company.primary_industry_sector != None,
                    and_(*sector_conditions)
                )
            else:
                sector_condition = and_(
                    Company.primary_industry_sector != None,
                    Company.primary_industry_sector.in_(sectors)
                )

            if filter_operator == 'OR':
                all_conditions.append(sector_condition)
            else:
                query = query.filter(sector_condition)

        if filters.get('verticals'):
            vertical_list = [v.strip() for v in filters['verticals'].split(',')]
            verticals_operator = filters.get('verticals_operator', 'OR').upper()

            if search_exact:
                vertical_conditions = [Company.verticals == v for v in vertical_list]
            else:
                vertical_conditions = [Company.verticals.ilike(f"%{v}%") for v in vertical_list]

            if verticals_operator == 'AND':
                verticals_condition = and_(
                    Company.verticals != None,
                    and_(*vertical_conditions)
                )
            else:
                verticals_condition = and_(
                    Company.verticals != None,
                    or_(*vertical_conditions)
                )

            if filter_operator == 'OR':
                all_conditions.append(verticals_condition)
            else:
                query = query.filter(verticals_condition)

        # Location filters with operator support
        if filters.get('country'):
            countries = [c.strip() for c in filters['country'].split(',')]
            country_operator = filters.get('country_operator', 'OR').upper()

            if country_operator == 'AND':
                country_conditions = [Company.country == c for c in countries]
                country_condition = and_(
                    Company.country != None,
                    and_(*country_conditions)
                )
            else:
                country_condition = and_(
                    Company.country != None,
                    Company.country.in_(countries)
                )

            if filter_operator == 'OR':
                all_conditions.append(country_condition)
            else:
                query = query.filter(country_condition)

        if filters.get('state_region'):
            states = [s.strip() for s in filters['state_region'].split(',')]
            state_region_operator = filters.get('state_region_operator', 'OR').upper()

            if state_region_operator == 'AND':
                state_conditions = [Company.state_region == s for s in states]
                state_condition = and_(
                    Company.state_region != None,
                    and_(*state_conditions)
                )
            else:
                state_condition = and_(
                    Company.state_region != None,
                    Company.state_region.in_(states)
                )

            if filter_operator == 'OR':
                all_conditions.append(state_condition)
            else:
                query = query.filter(state_condition)

        if filters.get('city'):
            cities = [c.strip() for c in filters['city'].split(',')]
            city_operator = filters.get('city_operator', 'OR').upper()

            if city_operator == 'AND':
                city_conditions = [Company.city == c for c in cities]
                city_condition = and_(
                    Company.city != None,
                    and_(*city_conditions)
                )
            else:
                city_condition = and_(
                    Company.city != None,
                    Company.city.in_(cities)
                )

            if filter_operator == 'OR':
                all_conditions.append(city_condition)
            else:
                query = query.filter(city_condition)

        # Revenue filters
        if filters.get('min_revenue') is not None:
            min_revenue_condition = Company.current_revenue_usd >= filters['min_revenue']
            if filter_operator == 'OR':
                all_conditions.append(min_revenue_condition)
            else:
                query = query.filter(min_revenue_condition)

        if filters.get('max_revenue') is not None:
            max_revenue_condition = Company.current_revenue_usd <= filters['max_revenue']
            if filter_operator == 'OR':
                all_conditions.append(max_revenue_condition)
            else:
                query = query.filter(max_revenue_condition)

        # Employee count filters
        if filters.get('min_employees') is not None:
            min_emp_condition = or_(
                Company.projected_employee_count >= filters['min_employees'],
                Company.employee_count >= filters['min_employees'],
                Company.crunchbase_employee_count.ilike(f"%{filters['min_employees']}%")
            )
            if filter_operator == 'OR':
                all_conditions.append(min_emp_condition)
            else:
                query = query.filter(min_emp_condition)

        if filters.get('max_employees') is not None:
            max_emp_condition = or_(
                Company.projected_employee_count <= filters['max_employees'],
                Company.employee_count <= filters['max_employees'],
                Company.crunchbase_employee_count.ilike(f"%{filters['max_employees']}%")
            )
            if filter_operator == 'OR':
                all_conditions.append(max_emp_condition)
            else:
                query = query.filter(max_emp_condition)

        # Apply global OR operator if specified
        if filter_operator == 'OR' and all_conditions:
            query = query.filter(or_(*all_conditions))

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