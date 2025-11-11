"""
Company service for business logic and data processing
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import or_, func, desc
from sqlalchemy.orm import Session
from backend.services.base import BaseService
from backend.schemas.responses import CompanyResponse
from backend.schemas.requests import CompanyUpdate
from src.models.database_models_v2 import (
    Company, CompanyPEInvestment, PEFirm, CompanyTag, FundingRound
)
from src.enrichment.crunchbase_helpers import decode_revenue_range, decode_employee_count


class CompanyService(BaseService):
    """Service for company-related business logic"""
    
    # Reverse mappings for filtering
    REVENUE_RANGE_CODES = {
        "Less than $1M": "r_00000000",
        "$1M - $10M": "r_00001000",
        "$10M - $50M": "r_00010000",
        "$50M - $100M": "r_00050000",
        "$100M - $500M": "r_00100000",
        "$500M - $1B": "r_00500000",
        "$1B - $10B": "r_01000000",
        "$10B+": "r_10000000",
        # Partial matches for convenience
        "$1M": "r_00001000",
        "$10M": "r_00010000",
        "$50M": "r_00050000",
        "$100M": "r_00100000",
        "$500M": "r_00500000",
        "$1B": "r_01000000",
        "$10B": "r_10000000"
    }

    EMPLOYEE_COUNT_CODES = {
        "1-10": "c_00001_00010",
        "11-50": "c_00011_00050",
        "51-100": "c_00051_00100",
        "101-250": "c_00101_00250",
        "251-500": "c_00251_00500",
        "501-1,000": "c_00501_01000",
        "1,001-5,000": "c_01001_05000",
        "5,001-10,000": "c_05001_10000",
        "10,001+": "c_10001_max"
    }
    
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
    
    def get_company_pe_firms(self, company_id: int) -> List[str]:
        """Get all PE firms for a company"""
        pe_firms = self.session.query(PEFirm.name).join(CompanyPEInvestment).filter(
            CompanyPEInvestment.company_id == company_id
        ).distinct().all()
        return [firm[0] for firm in pe_firms]
    
    def get_company_status(self, company_id: int) -> str:
        """Get overall investment status for a company (prioritize Active over Exit)"""
        investment_statuses = self.session.query(CompanyPEInvestment.computed_status).filter(
            CompanyPEInvestment.company_id == company_id
        ).distinct().all()
        status_list = [s[0] for s in investment_statuses if s[0]]
        
        # Determine overall status
        if 'Active' in status_list:
            return 'Active'
        elif 'Exit' in status_list:
            return 'Exit'
        else:
            return status_list[0] if status_list else 'Unknown'
    
    def get_company_investment_year(self, company_id: int) -> Optional[str]:
        """Get earliest investment year for a company"""
        investment_year = self.session.query(CompanyPEInvestment.investment_year).filter(
            CompanyPEInvestment.company_id == company_id,
            CompanyPEInvestment.investment_year != None
        ).order_by(CompanyPEInvestment.investment_year).first()
        return investment_year[0] if investment_year else None
    
    def get_company_exit_type(self, company_id: int) -> Optional[str]:
        """Get exit type for a company if any"""
        exit_type = self.session.query(CompanyPEInvestment.exit_type).filter(
            CompanyPEInvestment.company_id == company_id,
            CompanyPEInvestment.exit_type != None
        ).first()
        return exit_type[0] if exit_type else None
    
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

    def build_company_response(self, company: Company) -> CompanyResponse:
        """Build a complete CompanyResponse from a Company model"""
        pe_firms = self.get_company_pe_firms(company.id)
        status = self.get_company_status(company.id)
        investment_year = self.get_company_investment_year(company.id)
        exit_type = self.get_company_exit_type(company.id)
        headquarters = self.build_headquarters(company)
        industries = self.get_company_industries(company.id)

        return CompanyResponse(
            id=company.id,
            name=company.name,
            former_name=company.former_name,
            pe_firms=pe_firms,
            status=status,
            exit_type=exit_type,
            investment_year=investment_year,
            headquarters=headquarters,
            website=company.website,
            linkedin_url=company.linkedin_url,
            crunchbase_url=company.crunchbase_url,
            description=company.description,
            revenue_range=decode_revenue_range(company.revenue_range),
            employee_count=self.get_employee_count_display(company),
            pitchbook_employee_count=company.employee_count,
            crunchbase_employee_range=decode_employee_count(company.crunchbase_employee_count) if company.crunchbase_employee_count else None,
            scraped_employee_count=company.projected_employee_count,
            industry_category=company.industry_category,
            industries=industries,
            total_funding_usd=company.total_funding_usd,
            num_funding_rounds=company.num_funding_rounds,
            latest_funding_type=company.latest_funding_type,
            latest_funding_date=company.latest_funding_date.isoformat() if company.latest_funding_date else None,
            funding_stage_encoded=company.funding_stage_encoded,
            avg_round_size_usd=company.avg_round_size_usd,
            total_investors=company.total_investors,
            predicted_revenue=company.predicted_revenue,  # Already in millions in DB
            prediction_confidence=company.prediction_confidence,  # Keep as float 0-1 for frontend
            is_public=company.is_public,
            stock_exchange=company.ipo_exchange,
            investor_name=getattr(company, 'investor_name', None),
            investor_status=getattr(company, 'investor_status', None),
            investor_holding=getattr(company, 'investor_holding', None),
            current_revenue_usd=float(company.current_revenue_usd) if getattr(company, 'current_revenue_usd', None) else None,
            last_known_valuation_usd=float(company.last_known_valuation_usd) if getattr(company, 'last_known_valuation_usd', None) else None,
            primary_industry_group=getattr(company, 'primary_industry_group', None),
            primary_industry_sector=getattr(company, 'primary_industry_sector', None),
            hq_location=getattr(company, 'hq_location', None),
            hq_country=getattr(company, 'hq_country', None),
            last_financing_date=getattr(company, 'last_financing_date', None).isoformat() if getattr(company, 'last_financing_date', None) else None,
            last_financing_size_usd=float(company.last_financing_size_usd) if getattr(company, 'last_financing_size_usd', None) else None,
            last_financing_deal_type=getattr(company, 'last_financing_deal_type', None),
            verticals=getattr(company, 'verticals', None)
        )
    
    def apply_filters(self, query, filters: Dict[str, Any]):
        """Apply all filters to a company query"""
        
        # Search filter
        if filters.get('search'):
            query = query.filter(Company.name.ilike(f"%{filters['search']}%"))

        # PE Firm filter
        if filters.get('pe_firm'):
            pe_firms = [f.strip() for f in filters['pe_firm'].split(',')]
            firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]
            query = query.filter(or_(*firm_conditions))

        # Status filter
        if filters.get('status'):
            query = query.filter(CompanyPEInvestment.computed_status.ilike(f"%{filters['status']}%"))

        # Industry filter (supports AND/OR/EXACT modes)
        if filters.get('industry'):
            industries = [i.strip() for i in filters['industry'].split(',')]
            filter_mode = filters.get('industry_filter_mode', 'or').lower()

            if filter_mode == 'and':
                # Companies must have ALL selected industries
                for industry in industries:
                    subquery = self.session.query(CompanyTag.company_id).filter(
                        CompanyTag.tag_category == 'industry',
                        CompanyTag.tag_value == industry
                    ).subquery()
                    query = query.filter(Company.id.in_(subquery))
            elif filter_mode == 'exact':
                # Companies must have EXACTLY these industries (no more, no less)
                # First, get companies that have all required industries
                for industry in industries:
                    subquery = self.session.query(CompanyTag.company_id).filter(
                        CompanyTag.tag_category == 'industry',
                        CompanyTag.tag_value == industry
                    ).subquery()
                    query = query.filter(Company.id.in_(subquery))

                # Then, ensure they don't have any additional industries
                # Count of industries for each company should equal the number requested
                industry_count_subquery = (
                    self.session.query(CompanyTag.company_id)
                    .filter(CompanyTag.tag_category == 'industry')
                    .group_by(CompanyTag.company_id)
                    .having(func.count(CompanyTag.tag_value) == len(industries))
                    .subquery()
                )
                query = query.filter(Company.id.in_(industry_count_subquery))
            else:
                # Default 'or' mode - companies with ANY of the selected industries
                query = query.join(CompanyTag, Company.id == CompanyTag.company_id).filter(
                    CompanyTag.tag_category == 'industry',
                    CompanyTag.tag_value.in_(industries)
                ).distinct()

        # PitchBook filters with AND/OR/EXACT support
        if filters.get('industry_group'):
            groups = [g.strip() for g in filters['industry_group'].split(',')]
            filter_mode = filters.get('industry_group_filter_mode', 'or').lower()

            if filter_mode == 'and' or filter_mode == 'exact':
                # For single-value fields like primary_industry_group, AND/EXACT only makes sense
                # if there's exactly one group selected, otherwise no results
                if len(groups) == 1:
                    query = query.filter(
                        Company.primary_industry_group != None,
                        Company.primary_industry_group.in_(groups)
                    )
                # If multiple groups with AND/EXACT, return no results (impossible to satisfy)
            else:
                # Default OR mode
                query = query.filter(
                    Company.primary_industry_group != None,
                    Company.primary_industry_group.in_(groups)
                )

        if filters.get('industry_sector'):
            sectors = [s.strip() for s in filters['industry_sector'].split(',')]
            filter_mode = filters.get('industry_sector_filter_mode', 'or').lower()

            if filter_mode == 'and' or filter_mode == 'exact':
                # Same logic as industry_group
                if len(sectors) == 1:
                    query = query.filter(
                        Company.primary_industry_sector != None,
                        Company.primary_industry_sector.in_(sectors)
                    )
            else:
                # Default OR mode
                query = query.filter(
                    Company.primary_industry_sector != None,
                    Company.primary_industry_sector.in_(sectors)
                )

        if filters.get('verticals'):
            vertical_list = [v.strip() for v in filters['verticals'].split(',')]
            filter_mode = filters.get('verticals_filter_mode', 'or').lower()

            if filter_mode == 'and':
                # Companies must have ALL selected verticals
                for vertical in vertical_list:
                    query = query.filter(
                        Company.verticals != None,
                        Company.verticals.ilike(f"%{vertical}%")
                    )
            elif filter_mode == 'exact':
                # Companies must have EXACTLY these verticals (comma-separated)
                # Build expected string patterns for exact match (order-independent)
                for vertical in vertical_list:
                    query = query.filter(
                        Company.verticals != None,
                        Company.verticals.ilike(f"%{vertical}%")
                    )
                # Count commas to ensure exact count match
                expected_comma_count = len(vertical_list) - 1
                query = query.filter(
                    func.char_length(Company.verticals) - func.char_length(func.replace(Company.verticals, ',', '')) == expected_comma_count
                )
            else:
                # Default OR mode
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
        if filters.get('revenue_range'):
            ranges = [r.strip() for r in filters['revenue_range'].split(',')]
            range_codes = [self.REVENUE_RANGE_CODES.get(r) for r in ranges if self.REVENUE_RANGE_CODES.get(r)]
            if range_codes:
                query = query.filter(Company.revenue_range.in_(range_codes))

        # Min/Max revenue filters - check both current_revenue_usd and predicted_revenue
        if filters.get('min_revenue') is not None:
            min_rev = filters['min_revenue']
            query = query.filter(
                or_(
                    Company.current_revenue_usd >= min_rev,
                    Company.predicted_revenue >= min_rev
                )
            )

        if filters.get('max_revenue') is not None:
            max_rev = filters['max_revenue']
            query = query.filter(
                or_(
                    Company.current_revenue_usd <= max_rev,
                    Company.predicted_revenue <= max_rev
                )
            )

        # Employee count filters
        if filters.get('employee_count'):
            ranges = [e.strip() for e in filters['employee_count'].split(',')]
            range_codes = [self.EMPLOYEE_COUNT_CODES.get(r) for r in ranges if self.EMPLOYEE_COUNT_CODES.get(r)]
            if range_codes:
                query = query.filter(Company.crunchbase_employee_count.in_(range_codes))

        if filters.get('min_employees') is not None:
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

        # Public status filter
        if filters.get('is_public') is not None:
            query = query.filter(Company.is_public == filters['is_public'])

        return query
    
    def get_companies(self, filters: Dict[str, Any], limit: int = 10000, offset: int = 0) -> Tuple[List[CompanyResponse], int]:
        """Get companies with filters and pagination"""
        
        # Start with base query - always join to get PE firm data
        query = self.session.query(Company).join(Company.investments).join(CompanyPEInvestment.pe_firm)
        
        # Apply all filters
        query = self.apply_filters(query, filters)
        
        # Deduplicate companies (since we joined with investments)
        query = query.distinct()
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        companies = query.order_by(Company.name).offset(offset).limit(limit).all()
        
        # Build response objects
        result = [self.build_company_response(company) for company in companies]
        
        return result, total_count
    
    def get_company_by_id(self, company_id: int) -> Optional[CompanyResponse]:
        """Get a single company by ID"""
        company = self.session.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        
        return self.build_company_response(company)
    
    def update_company(self, company_id: int, company_update: CompanyUpdate) -> bool:
        """Update company details"""
        company = self.session.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
        
        # Update fields if provided
        if company_update.name is not None:
            company.name = company_update.name
        if company_update.website is not None:
            company.website = company_update.website
        if company_update.linkedin_url is not None:
            company.linkedin_url = company_update.linkedin_url
        if company_update.crunchbase_url is not None:
            company.crunchbase_url = company_update.crunchbase_url
        if company_update.description is not None:
            company.description = company_update.description
        if company_update.city is not None:
            company.city = company_update.city
        if company_update.state_region is not None:
            company.state_region = company_update.state_region
        if company_update.country is not None:
            company.country = company_update.country
        if company_update.industry_category is not None:
            company.industry_category = company_update.industry_category
        if company_update.revenue_range is not None:
            company.revenue_range = company_update.revenue_range
        if company_update.employee_count is not None:
            company.employee_count = company_update.employee_count
        if company_update.crunchbase_employee_count is not None:
            company.crunchbase_employee_count = company_update.crunchbase_employee_count
        if company_update.is_public is not None:
            company.is_public = company_update.is_public
        if company_update.ipo_exchange is not None:
            company.ipo_exchange = company_update.ipo_exchange
        if company_update.ipo_date is not None:
            company.ipo_date = company_update.ipo_date
        
        # PitchBook fields
        if company_update.primary_industry_group is not None:
            company.primary_industry_group = company_update.primary_industry_group
        if company_update.primary_industry_sector is not None:
            company.primary_industry_sector = company_update.primary_industry_sector
        if company_update.verticals is not None:
            company.verticals = company_update.verticals
        if company_update.current_revenue_usd is not None:
            company.current_revenue_usd = company_update.current_revenue_usd
        if company_update.last_known_valuation_usd is not None:
            company.last_known_valuation_usd = company_update.last_known_valuation_usd
        if company_update.hq_location is not None:
            company.hq_location = company_update.hq_location
        if company_update.hq_country is not None:
            company.hq_country = company_update.hq_country
        
        self.session.commit()
        return True
    
    def delete_company(self, company_id: int) -> bool:
        """Delete a company and all related data"""
        company = self.session.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
        
        try:
            # Delete related investments first
            self.session.query(CompanyPEInvestment).filter(CompanyPEInvestment.company_id == company_id).delete()
            
            # Delete company tags
            self.session.query(CompanyTag).filter(CompanyTag.company_id == company_id).delete()
            
            # Delete funding rounds
            self.session.query(FundingRound).filter(FundingRound.company_id == company_id).delete()
            
            # Delete the company
            self.session.delete(company)
            self.session.commit()
            
            return True
        except Exception:
            self.session.rollback()
            return False