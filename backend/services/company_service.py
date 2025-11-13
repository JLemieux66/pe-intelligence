"""
Company service for business logic and data processing
OPTIMIZED: Uses eager loading to prevent N+1 query problems
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Session, joinedload, selectinload
from backend.services.base import BaseService
from backend.schemas.responses import CompanyResponse
from backend.schemas.requests import (
    CompanyUpdate, CompanyCreate, CompanyTagCreate,
    FundingRoundCreate, PEInvestmentCreate
)
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
        """
        Build a complete CompanyResponse from a Company model.
        OPTIMIZED: Uses eager-loaded relationships instead of separate queries.
        """
        # Use loaded relationships instead of separate queries (prevents N+1)
        pe_firms = [inv.pe_firm.name for inv in company.investments if inv.pe_firm] if hasattr(company, 'investments') else []

        # Compute status from loaded investments
        if hasattr(company, 'investments') and company.investments:
            status_list = [inv.computed_status for inv in company.investments if inv.computed_status]
            if 'Active' in status_list:
                status = 'Active'
            elif 'Exit' in status_list:
                status = 'Exit'
            else:
                status = status_list[0] if status_list else 'Unknown'
        else:
            status = 'Unknown'

        # Get investment year from loaded investments
        if hasattr(company, 'investments') and company.investments:
            investment_years = [inv.investment_year for inv in company.investments if inv.investment_year]
            investment_year = min(investment_years) if investment_years else None
        else:
            investment_year = None

        # Get exit type from loaded investments
        if hasattr(company, 'investments') and company.investments:
            exit_types = [inv.exit_type for inv in company.investments if inv.exit_type]
            exit_type = exit_types[0] if exit_types else None
        else:
            exit_type = None

        headquarters = self.build_headquarters(company)

        # Get industries from loaded tags
        if hasattr(company, 'tags') and company.tags:
            industries = [tag.tag_value for tag in company.tags if tag.tag_category == 'industry' and tag.tag_value != 'Other']
        else:
            industries = []

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
    
    def _is_postgresql(self) -> bool:
        """Check if we're using PostgreSQL"""
        return 'postgresql' in str(self.session.bind.url).lower()

    def apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply all filters to a company query.
        OPTIMIZED: Uses full-text search for PostgreSQL.
        ENHANCED: Supports AND/OR/EXACT operators for advanced filtering.
        """
        # Get operator settings (default to backward-compatible behavior)
        filter_operator = filters.get('filter_operator', 'AND').upper()
        search_exact = filters.get('search_exact', False)

        # Collect all filter conditions if using global OR operator
        all_conditions = []

        # Search filter - OPTIMIZED with full-text search for PostgreSQL
        if filters.get('search'):
            search_term = filters['search'].strip()

            if search_exact:
                # Exact match
                search_condition = Company.name == search_term
            else:
                # Partial match - Try full-text search for PostgreSQL
                if self._is_postgresql():
                    try:
                        # Use PostgreSQL full-text search (10-50x faster than ILIKE)
                        from sqlalchemy import func as sql_func
                        from sqlalchemy.dialects.postgresql import TSVECTOR

                        # Convert search term to tsquery format
                        # Replace spaces with '&' for AND search
                        tsquery_term = ' & '.join(search_term.split())

                        # Check if search_vector column exists
                        if hasattr(Company, 'search_vector'):
                            search_condition = sql_func.to_tsvector('english', Company.name).op('@@')(
                                sql_func.to_tsquery('english', tsquery_term)
                            )
                        else:
                            # Fallback to ILIKE if search_vector not available
                            search_condition = Company.name.ilike(f"%{search_term}%")
                    except Exception:
                        # Fallback to ILIKE on error
                        search_condition = Company.name.ilike(f"%{search_term}%")
                else:
                    # Use ILIKE for SQLite or other databases
                    search_condition = Company.name.ilike(f"%{search_term}%")

            if filter_operator == 'OR':
                all_conditions.append(search_condition)
            else:
                query = query.filter(search_condition)

        # PE Firm filter with operator support
        if filters.get('pe_firm'):
            pe_firms = [f.strip() for f in filters['pe_firm'].split(',')]
            pe_firm_operator = filters.get('pe_firm_operator', 'OR').upper()
            pe_firm_not = filters.get('pe_firm_not', False)

            if search_exact:
                firm_conditions = [PEFirm.name == firm for firm in pe_firms]
            else:
                firm_conditions = [PEFirm.name.ilike(f"%{firm}%") for firm in pe_firms]

            if pe_firm_operator == 'AND' and not pe_firm_not:
                # For AND: company must have investments from ALL specified firms
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
                # For OR: company must have investment from ANY specified firm
                pe_firm_condition = or_(*firm_conditions)

                # Build the final condition
                firm_subquery_condition = Company.id.in_(
                    self.session.query(Company.id)
                    .join(CompanyPEInvestment)
                    .join(PEFirm)
                    .filter(pe_firm_condition)
                )

                # Apply NOT logic if enabled
                if pe_firm_not:
                    firm_subquery_condition = ~firm_subquery_condition

                if filter_operator == 'OR':
                    all_conditions.append(firm_subquery_condition)
                else:
                    query = query.filter(firm_subquery_condition)

        # Status filter
        if filters.get('status'):
            status_condition = CompanyPEInvestment.computed_status.ilike(f"%{filters['status']}%")
            if filter_operator == 'OR':
                all_conditions.append(status_condition)
            else:
                query = query.filter(status_condition)

        # Industry filter with operator support
        if filters.get('industry'):
            industries = [i.strip() for i in filters['industry'].split(',')]
            industry_operator = filters.get('industry_operator', 'OR').upper()
            industry_not = filters.get('industry_not', False)

            if industry_operator == 'AND' and not industry_not:
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

                # Apply NOT logic if enabled
                if industry_not:
                    industry_condition = ~industry_condition

                if filter_operator == 'OR':
                    all_conditions.append(industry_condition)
                else:
                    query = query.filter(industry_condition)

        # PitchBook filters with operator support
        if filters.get('industry_group'):
            groups = [g.strip() for g in filters['industry_group'].split(',')]
            industry_group_operator = filters.get('industry_group_operator', 'OR').upper()
            industry_group_not = filters.get('industry_group_not', False)

            if industry_group_operator == 'AND':
                # For AND: must match ALL groups (unusual case, but supported)
                group_conditions = [Company.primary_industry_group == g for g in groups]
                group_condition = and_(
                    Company.primary_industry_group != None,
                    and_(*group_conditions)
                )
            else:
                # For OR: must match ANY group
                group_condition = and_(
                    Company.primary_industry_group != None,
                    Company.primary_industry_group.in_(groups)
                )

            # Apply NOT logic if enabled
            if industry_group_not:
                group_condition = ~group_condition

            if filter_operator == 'OR':
                all_conditions.append(group_condition)
            else:
                query = query.filter(group_condition)

        if filters.get('industry_sector'):
            sectors = [s.strip() for s in filters['industry_sector'].split(',')]
            industry_sector_operator = filters.get('industry_sector_operator', 'OR').upper()
            industry_sector_not = filters.get('industry_sector_not', False)

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

            # Apply NOT logic if enabled
            if industry_sector_not:
                sector_condition = ~sector_condition

            if filter_operator == 'OR':
                all_conditions.append(sector_condition)
            else:
                query = query.filter(sector_condition)

        if filters.get('verticals'):
            vertical_list = [v.strip() for v in filters['verticals'].split(',')]
            verticals_operator = filters.get('verticals_operator', 'OR').upper()
            verticals_not = filters.get('verticals_not', False)
            verticals_exact = filters.get('verticals_exact', False)

            if verticals_exact:
                # EXACT mode: Company must have ONLY these verticals, no more, no less
                # Generate all possible orderings of the selected verticals (since order in CSV may vary)
                from itertools import permutations
                vertical_permutations = list(permutations(vertical_list))
                exact_match_conditions = [
                    Company.verticals == ', '.join(perm) for perm in vertical_permutations
                ]
                verticals_condition = and_(
                    Company.verticals != None,
                    or_(*exact_match_conditions)
                )
            elif search_exact:
                vertical_conditions = [Company.verticals == v for v in vertical_list]
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

            # Apply NOT logic if enabled
            if verticals_not:
                verticals_condition = ~verticals_condition

            if filter_operator == 'OR':
                all_conditions.append(verticals_condition)
            else:
                query = query.filter(verticals_condition)

        # Location filters with operator support
        if filters.get('country'):
            countries = [c.strip() for c in filters['country'].split(',')]
            country_operator = filters.get('country_operator', 'OR').upper()
            country_not = filters.get('country_not', False)

            if country_operator == 'AND':
                # For AND on countries (unusual), must match all
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

            # Apply NOT logic if enabled
            if country_not:
                country_condition = ~country_condition

            if filter_operator == 'OR':
                all_conditions.append(country_condition)
            else:
                query = query.filter(country_condition)

        if filters.get('state_region'):
            states = [s.strip() for s in filters['state_region'].split(',')]
            state_region_operator = filters.get('state_region_operator', 'OR').upper()
            state_region_not = filters.get('state_region_not', False)

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

            # Apply NOT logic if enabled
            if state_region_not:
                state_condition = ~state_condition

            if filter_operator == 'OR':
                all_conditions.append(state_condition)
            else:
                query = query.filter(state_condition)

        if filters.get('city'):
            cities = [c.strip() for c in filters['city'].split(',')]
            city_operator = filters.get('city_operator', 'OR').upper()
            city_not = filters.get('city_not', False)

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

            # Apply NOT logic if enabled
            if city_not:
                city_condition = ~city_condition

            if filter_operator == 'OR':
                all_conditions.append(city_condition)
            else:
                query = query.filter(city_condition)

        # Revenue filters
        if filters.get('revenue_range'):
            ranges = [r.strip() for r in filters['revenue_range'].split(',')]
            range_codes = [self.REVENUE_RANGE_CODES.get(r) for r in ranges if self.REVENUE_RANGE_CODES.get(r)]
            if range_codes:
                revenue_condition = Company.revenue_range.in_(range_codes)
                if filter_operator == 'OR':
                    all_conditions.append(revenue_condition)
                else:
                    query = query.filter(revenue_condition)

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
        if filters.get('employee_count'):
            ranges = [e.strip() for e in filters['employee_count'].split(',')]
            range_codes = [self.EMPLOYEE_COUNT_CODES.get(r) for r in ranges if self.EMPLOYEE_COUNT_CODES.get(r)]
            if range_codes:
                employee_condition = Company.crunchbase_employee_count.in_(range_codes)
                if filter_operator == 'OR':
                    all_conditions.append(employee_condition)
                else:
                    query = query.filter(employee_condition)

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

        # Public status filter
        if filters.get('is_public') is not None:
            public_condition = Company.is_public == filters['is_public']
            if filter_operator == 'OR':
                all_conditions.append(public_condition)
            else:
                query = query.filter(public_condition)

        # Data quality filters (IS EMPTY / IS NOT EMPTY)
        if filters.get('has_linkedin_url') is not None:
            if filters['has_linkedin_url']:
                # Has LinkedIn URL
                linkedin_condition = Company.linkedin_url != None
            else:
                # Missing LinkedIn URL
                linkedin_condition = Company.linkedin_url == None
            if filter_operator == 'OR':
                all_conditions.append(linkedin_condition)
            else:
                query = query.filter(linkedin_condition)

        if filters.get('has_website') is not None:
            if filters['has_website']:
                website_condition = Company.website != None
            else:
                website_condition = Company.website == None
            if filter_operator == 'OR':
                all_conditions.append(website_condition)
            else:
                query = query.filter(website_condition)

        if filters.get('has_revenue') is not None:
            if filters['has_revenue']:
                # Has revenue data (either current_revenue_usd or revenue_range)
                revenue_condition = or_(
                    Company.current_revenue_usd != None,
                    Company.revenue_range != None
                )
            else:
                # Missing revenue data
                revenue_condition = and_(
                    Company.current_revenue_usd == None,
                    Company.revenue_range == None
                )
            if filter_operator == 'OR':
                all_conditions.append(revenue_condition)
            else:
                query = query.filter(revenue_condition)

        if filters.get('has_employees') is not None:
            if filters['has_employees']:
                # Has employee data (any of the employee fields)
                employee_condition = or_(
                    Company.projected_employee_count != None,
                    Company.employee_count != None,
                    Company.crunchbase_employee_count != None
                )
            else:
                # Missing employee data
                employee_condition = and_(
                    Company.projected_employee_count == None,
                    Company.employee_count == None,
                    Company.crunchbase_employee_count == None
                )
            if filter_operator == 'OR':
                all_conditions.append(employee_condition)
            else:
                query = query.filter(employee_condition)

        if filters.get('has_description') is not None:
            if filters['has_description']:
                description_condition = Company.description != None
            else:
                description_condition = Company.description == None
            if filter_operator == 'OR':
                all_conditions.append(description_condition)
            else:
                query = query.filter(description_condition)

        # Date range filters
        if filters.get('founded_year_min') is not None:
            founded_min_condition = Company.founded_year >= filters['founded_year_min']
            if filter_operator == 'OR':
                all_conditions.append(founded_min_condition)
            else:
                query = query.filter(founded_min_condition)

        if filters.get('founded_year_max') is not None:
            founded_max_condition = Company.founded_year <= filters['founded_year_max']
            if filter_operator == 'OR':
                all_conditions.append(founded_max_condition)
            else:
                query = query.filter(founded_max_condition)

        if filters.get('investment_year_min') is not None:
            # Filter companies with investments in or after this year
            inv_year_min_condition = Company.id.in_(
                self.session.query(CompanyPEInvestment.company_id)
                .filter(CompanyPEInvestment.investment_year >= str(filters['investment_year_min']))
            )
            if filter_operator == 'OR':
                all_conditions.append(inv_year_min_condition)
            else:
                query = query.filter(inv_year_min_condition)

        if filters.get('investment_year_max') is not None:
            # Filter companies with investments in or before this year
            inv_year_max_condition = Company.id.in_(
                self.session.query(CompanyPEInvestment.company_id)
                .filter(CompanyPEInvestment.investment_year <= str(filters['investment_year_max']))
            )
            if filter_operator == 'OR':
                all_conditions.append(inv_year_max_condition)
            else:
                query = query.filter(inv_year_max_condition)

        # Apply global OR operator if specified
        if filter_operator == 'OR' and all_conditions:
            query = query.filter(or_(*all_conditions))

        return query
    
    def get_companies(self, filters: Dict[str, Any], limit: int = 10000, offset: int = 0) -> Tuple[List[CompanyResponse], int]:
        """
        Get companies with filters and pagination.
        OPTIMIZED: Uses eager loading to prevent N+1 queries.
        """

        # Start with base query - always join to get PE firm data
        query = self.session.query(Company).join(Company.investments).join(CompanyPEInvestment.pe_firm)

        # Apply all filters
        query = self.apply_filters(query, filters)

        # Deduplicate companies (since we joined with investments)
        query = query.distinct()

        # Get total count for pagination
        total_count = query.count()

        # OPTIMIZATION: Add eager loading to prevent N+1 queries
        # Use selectinload for one-to-many relationships (more efficient than joinedload for collections)
        query = query.options(
            selectinload(Company.investments).joinedload(CompanyPEInvestment.pe_firm),
            selectinload(Company.tags)
        )

        # Apply pagination and ordering
        companies = query.order_by(Company.name).offset(offset).limit(limit).all()

        # Build response objects (now uses loaded data, no additional queries)
        result = [self.build_company_response(company) for company in companies]

        return result, total_count
    
    def get_company_by_id(self, company_id: int) -> Optional[CompanyResponse]:
        """
        Get a single company by ID.
        OPTIMIZED: Uses eager loading to prevent N+1 queries.
        """
        company = self.session.query(Company).options(
            selectinload(Company.investments).joinedload(CompanyPEInvestment.pe_firm),
            selectinload(Company.tags)
        ).filter(Company.id == company_id).first()

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

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string in YYYY-MM-DD format to date object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    def _get_or_create_pe_firm(self, firm_name: str) -> Optional[PEFirm]:
        """Get existing PE firm or create a new one"""
        pe_firm = self.session.query(PEFirm).filter(PEFirm.name == firm_name).first()
        if not pe_firm:
            pe_firm = PEFirm(
                name=firm_name,
                total_companies=0,
                current_portfolio_count=0,
                exited_portfolio_count=0,
                last_scraped=datetime.utcnow()
            )
            self.session.add(pe_firm)
            self.session.flush()  # Get the ID without committing
        return pe_firm

    def create_company(self, company_create: CompanyCreate) -> Optional[CompanyResponse]:
        """
        Create a new company with all associated data.

        Args:
            company_create: Company creation request with all fields

        Returns:
            CompanyResponse if successful, None if company already exists or error occurs
        """
        try:
            # Check if company already exists (by name and website)
            existing_query = self.session.query(Company).filter(Company.name == company_create.name)
            if company_create.website:
                existing_query = existing_query.filter(Company.website == company_create.website)
            existing = existing_query.first()

            if existing:
                return None  # Company already exists

            # Create new company
            new_company = Company(
                # Required fields
                name=company_create.name,

                # Basic information
                former_name=company_create.former_name,
                description=company_create.description,
                website=company_create.website,
                linkedin_url=company_create.linkedin_url,
                crunchbase_url=company_create.crunchbase_url,

                # Geographic data
                country=company_create.country,
                state_region=company_create.state_region,
                city=company_create.city,
                hq_location=company_create.hq_location,
                hq_country=company_create.hq_country,

                # Categorization
                industry_category=company_create.industry_category,
                primary_industry_group=company_create.primary_industry_group,
                primary_industry_sector=company_create.primary_industry_sector,
                verticals=company_create.verticals,
                founded_year=company_create.founded_year,

                # Employee data
                employee_count=company_create.employee_count,
                projected_employee_count=company_create.projected_employee_count,
                crunchbase_employee_count=company_create.crunchbase_employee_count,

                # Revenue data
                revenue_range=company_create.revenue_range,
                current_revenue_usd=company_create.current_revenue_usd,
                predicted_revenue=company_create.predicted_revenue,
                prediction_confidence=company_create.prediction_confidence,

                # Funding data
                total_funding_usd=company_create.total_funding_usd,
                num_funding_rounds=company_create.num_funding_rounds,
                latest_funding_type=company_create.latest_funding_type,
                latest_funding_date=self._parse_date(company_create.latest_funding_date),
                months_since_last_funding=company_create.months_since_last_funding,
                funding_stage_encoded=company_create.funding_stage_encoded,
                avg_round_size_usd=company_create.avg_round_size_usd,
                total_investors=company_create.total_investors,

                # IPO/Exit information
                is_public=company_create.is_public,
                ipo_ticker=company_create.ipo_ticker,
                ipo_date=self._parse_date(company_create.ipo_date),
                ipo_exchange=company_create.ipo_exchange,

                # PitchBook data
                investor_name=company_create.investor_name,
                investor_status=company_create.investor_status,
                investor_holding=company_create.investor_holding,
                last_known_valuation_usd=company_create.last_known_valuation_usd,
                last_financing_date=self._parse_date(company_create.last_financing_date),
                last_financing_size_usd=company_create.last_financing_size_usd,
                last_financing_deal_type=company_create.last_financing_deal_type,
                financing_status_note=company_create.financing_status_note,

                # Categorization fields
                company_size_category=company_create.company_size_category,
                revenue_tier=company_create.revenue_tier,

                # Timestamps
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(new_company)
            self.session.flush()  # Get the company ID

            # Create associated tags
            if company_create.tags:
                for tag_data in company_create.tags:
                    tag = CompanyTag(
                        company_id=new_company.id,
                        tag_category=tag_data.tag_category,
                        tag_value=tag_data.tag_value,
                        created_at=datetime.utcnow()
                    )
                    self.session.add(tag)

            # Create funding rounds
            if company_create.funding_rounds:
                for round_data in company_create.funding_rounds:
                    funding_round = FundingRound(
                        company_id=new_company.id,
                        announced_on=self._parse_date(round_data.announced_on),
                        investment_type=round_data.investment_type,
                        money_raised_usd=round_data.money_raised_usd,
                        investor_names=round_data.investor_names,
                        num_investors=round_data.num_investors,
                        created_at=datetime.utcnow()
                    )
                    self.session.add(funding_round)

            # Create PE investments
            if company_create.pe_investments:
                for investment_data in company_create.pe_investments:
                    # Get or create PE firm
                    pe_firm = self._get_or_create_pe_firm(investment_data.pe_firm_name)
                    if not pe_firm:
                        continue

                    # Create investment relationship
                    investment = CompanyPEInvestment(
                        company_id=new_company.id,
                        pe_firm_id=pe_firm.id,
                        raw_status=investment_data.raw_status,
                        computed_status=investment_data.computed_status or 'Active',  # Default to Active
                        investment_year=investment_data.investment_year,
                        investment_stage=investment_data.investment_stage,
                        exit_type=investment_data.exit_type,
                        exit_info=investment_data.exit_info,
                        exit_year=investment_data.exit_year,
                        last_scraped=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.session.add(investment)

            # Commit all changes
            self.session.commit()

            # Return the created company
            return self.get_company_by_id(new_company.id)

        except Exception as e:
            self.session.rollback()
            print(f"Error creating company: {e}")
            import traceback
            traceback.print_exc()
            return None