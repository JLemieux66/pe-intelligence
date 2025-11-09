"""
Similar Companies Service
AI-powered company similarity analysis with weighted scoring algorithm
"""
import os
import math
from typing import List, Dict, Tuple, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc

from src.models.database_models_v2 import Company, CompanyPEInvestment, CompanyTag
from backend.schemas.requests import SimilarCompaniesRequest
from backend.schemas.responses import CompanyResponse, SimilarCompanyMatch, SimilarCompaniesResponse
from backend.services.base import BaseService


class SimilarCompaniesService(BaseService):
    """Service for finding similar companies using AI-powered analysis"""
    
    def __init__(self, session: Session):
        super().__init__(session)
        self.openai_client = None
        self._init_openai()
    
    def _init_openai(self):
        """Initialize OpenAI client if API key is available"""
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                print("[OK] OpenAI client initialized")
            else:
                print("[INFO] OpenAI API key not found - semantic similarity disabled")
        except ImportError:
            print("[WARNING] OpenAI package not installed - semantic similarity disabled")
    
    def find_similar_companies(self, request: SimilarCompaniesRequest) -> SimilarCompaniesResponse:
        """
        Find similar companies based on input company IDs.
        Uses weighted scoring algorithm across multiple dimensions.
        """
        print(f"\n=== Similar Companies Request ===")
        print(f"Company IDs: {request.company_ids}")
        print(f"Min Score: {request.min_score}")
        print(f"Limit: {request.limit}")
        
        # 1. Get input companies with eager loading
        print("[1/6] Fetching input companies...")
        input_companies = self.session.query(Company).options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm),
            joinedload(Company.tags)  # Load industry tags for similarity matching
        ).filter(
            Company.id.in_(request.company_ids)
        ).all()
        
        if not input_companies:
            raise ValueError("No companies found with provided IDs")
        
        print(f"   Found {len(input_companies)} input companies")
        
        # 2. Get all potential match candidates with eager loading
        print("[2/6] Fetching candidate companies...")
        query = self.session.query(Company).options(
            joinedload(Company.investments).joinedload(CompanyPEInvestment.pe_firm),
            joinedload(Company.tags)  # Load industry tags for similarity matching
        ).filter(
            ~Company.id.in_(request.company_ids)  # Exclude input companies
        )
        
        # Apply filters if provided
        if request.filters:
            if 'country' in request.filters:
                query = query.filter(Company.country == request.filters['country'])
            if 'sector' in request.filters:
                query = query.filter(Company.primary_industry_sector == request.filters['sector'])
        
        # Limit candidates for performance (top 2000 by revenue/valuation)
        candidates = query.order_by(
            desc(Company.current_revenue_usd),
            desc(Company.last_known_valuation_usd)
        ).limit(2000).all()
        
        print(f"   Found {len(candidates)} candidate companies")
        
        # 3. Calculate similarity scores for all candidates against all input companies
        print("[3/6] Calculating similarity scores...")
        all_matches = []
        
        for input_company in input_companies:
            print(f"   Processing {input_company.name}...")
            
            for candidate in candidates:
                # Calculate rule-based similarity score with detailed breakdown
                similarity_score, matching_attrs, score_breakdown, confidence, categories_with_score = self.calculate_similarity_score(input_company, candidate)
                
                # Skip semantic similarity (OpenAI embeddings) for performance
                # semantic_score, semantic_explanation = self.calculate_semantic_similarity(input_company, candidate)
                
                # Total score (cap at 100)
                total_score = similarity_score  # + semantic_score
                
                if total_score >= request.min_score:
                    # Generate AI reasoning
                    reasoning = self.generate_ai_reasoning(input_company, candidate, matching_attrs, total_score)
                    
                    all_matches.append({
                        'input_company_id': input_company.id,
                        'candidate': candidate,
                        'score': min(100.0, total_score),  # Cap at 100
                        'reasoning': reasoning,
                        'matching_attributes': matching_attrs,
                        'score_breakdown': score_breakdown,
                        'confidence': confidence
                    })
        
        # 4. Sort by similarity score (descending) and limit results
        print("[4/6] Sorting and filtering results...")
        all_matches.sort(key=lambda x: x['score'], reverse=True)
        top_matches = all_matches[:request.limit]
        
        print(f"   Found {len(all_matches)} total matches, returning top {len(top_matches)}")
        
        # 5. Convert to response format
        print("[5/6] Converting to response format...")
        input_company_responses = [self._company_to_response(comp) for comp in input_companies]
        
        match_responses = []
        for match in top_matches:
            company_response = self._company_to_response(match['candidate'])
            
            match_response = SimilarCompanyMatch(
                company=company_response,
                similarity_score=match['score'],
                reasoning=match['reasoning'],
                matching_attributes=match['matching_attributes']
            )
            match_responses.append(match_response)
        
        print(f"✓ Complete! Returning {len(match_responses)} similar companies\n")
        
        return SimilarCompaniesResponse(
            input_companies=input_company_responses,
            matches=match_responses,
            total_results=len(all_matches)
        )
    
    def calculate_similarity_score(self, company_a: Company, company_b: Company) -> Tuple[float, List[str], Dict[str, Dict[str, float]], float, int]:
        """
        Enhanced similarity score calculation between two companies (0-100).
        Returns: (similarity_score, matching_attributes, score_breakdown, confidence, categories_with_score)
        """
        matching_attributes = []
        score_breakdown = {}
        total_score = 0.0
        confidence_factors = []
        categories_with_score = 0
        
        # Helper function to safely get attribute
        def safe_get(obj, attr, default=None):
            return getattr(obj, attr, default) if obj else default
        
        # Helper function to safely split and clean strings
        def safe_split(text, delimiter=','):
            if not text:
                return set()
            return set(item.strip().lower() for item in text.split(delimiter) if item.strip())
        
        # 1. Verticals/Sub-industries similarity (18 points) - HIGH PRIORITY - PitchBook verticals
        verticals_a = safe_split(safe_get(company_a, 'verticals'))
        verticals_b = safe_split(safe_get(company_b, 'verticals'))
        
        if verticals_a and verticals_b:
            # Calculate Jaccard similarity (intersection over union)
            intersection = len(verticals_a.intersection(verticals_b))
            union = len(verticals_a.union(verticals_b))
            jaccard_similarity = intersection / union if union > 0 else 0
            
            verticals_score = jaccard_similarity * 18
            total_score += verticals_score
            categories_with_score += 1
            confidence_factors.append(0.9)  # High confidence for PitchBook data
            
            score_breakdown['verticals'] = {
                'score': verticals_score,
                'max_score': 18,
                'company_a_value': ', '.join(sorted(verticals_a)) if verticals_a else 'None',
                'company_b_value': ', '.join(sorted(verticals_b)) if verticals_b else 'None',
                'jaccard_similarity': jaccard_similarity
            }
            
            if intersection > 0:
                shared_verticals = verticals_a.intersection(verticals_b)
                matching_attributes.append(f"Shared verticals: {', '.join(sorted(shared_verticals))}")
        
        # 2. Crunchbase Industry Tags similarity (8 points) - HIGH PRIORITY - Granular industry matching
        tags_a = set()
        tags_b = set()
        
        if hasattr(company_a, 'tags') and company_a.tags:
            tags_a = set(tag.tag_value.lower() for tag in company_a.tags)
        if hasattr(company_b, 'tags') and company_b.tags:
            tags_b = set(tag.tag_value.lower() for tag in company_b.tags)
        
        if tags_a and tags_b:
            # Calculate Jaccard similarity
            intersection = len(tags_a.intersection(tags_b))
            union = len(tags_a.union(tags_b))
            jaccard_similarity = intersection / union if union > 0 else 0
            
            tags_score = jaccard_similarity * 8
            total_score += tags_score
            categories_with_score += 1
            confidence_factors.append(0.8)  # Good confidence for Crunchbase tags
            
            score_breakdown['industry_tags'] = {
                'score': tags_score,
                'max_score': 8,
                'company_a_value': ', '.join(sorted(tags_a)) if tags_a else 'None',
                'company_b_value': ', '.join(sorted(tags_b)) if tags_b else 'None',
                'jaccard_similarity': jaccard_similarity
            }
            
            if intersection > 0:
                shared_tags = tags_a.intersection(tags_b)
                matching_attributes.append(f"Shared industry tags: {', '.join(sorted(shared_tags))}")
        
        # 3. Industry/Sector similarity (6 points) - PitchBook sector
        sector_a = safe_get(company_a, 'primary_industry_sector')
        sector_b = safe_get(company_b, 'primary_industry_sector')
        
        if sector_a and sector_b:
            if sector_a.lower() == sector_b.lower():
                sector_score = 6
                matching_attributes.append(f"Same sector: {sector_a}")
            else:
                sector_score = 0
            
            total_score += sector_score
            categories_with_score += 1
            confidence_factors.append(0.9)  # High confidence for PitchBook sector
            
            score_breakdown['sector'] = {
                'score': sector_score,
                'max_score': 6,
                'company_a_value': sector_a,
                'company_b_value': sector_b
            }
        
        # 4. Revenue similarity (42 points) - EXTREMELY IMPORTANT - PitchBook exact revenue ONLY
        rev_a = safe_get(company_a, 'current_revenue_usd')
        rev_b = safe_get(company_b, 'current_revenue_usd')
        
        if rev_a and rev_b and rev_a > 0 and rev_b > 0:
            # Calculate ratio similarity - TIGHTER bands for better matching
            ratio = min(rev_a, rev_b) / max(rev_a, rev_b)
            
            if ratio >= 0.75:  # Within 25% (0.75+ ratio)
                revenue_score = 42
                matching_attributes.append(f"Very similar revenue: ${rev_a:.1f}M vs ${rev_b:.1f}M")
            elif ratio >= 0.5:  # Within 50% (0.5-0.75 ratio)
                revenue_score = 30
                matching_attributes.append(f"Similar revenue: ${rev_a:.1f}M vs ${rev_b:.1f}M")
            elif ratio >= 0.25:  # Within 4x (0.25-0.5 ratio)
                revenue_score = 15
                matching_attributes.append(f"Comparable revenue scale: ${rev_a:.1f}M vs ${rev_b:.1f}M")
            elif ratio >= 0.1:  # Within 10x (0.1-0.25 ratio)
                revenue_score = 5
            else:
                revenue_score = 0
            
            total_score += revenue_score
            categories_with_score += 1
            confidence_factors.append(0.95)  # Very high confidence for exact revenue
            
            score_breakdown['revenue'] = {
                'score': revenue_score,
                'max_score': 42,
                'company_a_value': f"${rev_a:.1f}M",
                'company_b_value': f"${rev_b:.1f}M",
                'ratio': ratio
            }
        
        # 5. Employee Count similarity (13 points) - IMPORTANT
        emp_a = safe_get(company_a, 'employee_count') or safe_get(company_a, 'projected_employee_count')
        emp_b = safe_get(company_b, 'employee_count') or safe_get(company_b, 'projected_employee_count')
        
        if emp_a and emp_b and emp_a > 0 and emp_b > 0:
            # Calculate ratio similarity
            ratio = min(emp_a, emp_b) / max(emp_a, emp_b)
            
            if ratio >= 0.7:  # Within 30%
                employee_score = 13
                matching_attributes.append(f"Similar employee count: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.5:  # Within 50%
                employee_score = 9
            elif ratio >= 0.25:  # Within 4x
                employee_score = 4
            else:
                employee_score = 0
            
            total_score += employee_score
            categories_with_score += 1
            confidence_factors.append(0.8)  # Good confidence for employee count
            
            score_breakdown['employee_count'] = {
                'score': employee_score,
                'max_score': 13,
                'company_a_value': f"{emp_a:,}",
                'company_b_value': f"{emp_b:,}",
                'ratio': ratio
            }
        
        # 6. Total Funding similarity (4 points) - Shows capital efficiency and growth stage
        funding_a = safe_get(company_a, 'total_funding_usd')
        funding_b = safe_get(company_b, 'total_funding_usd')
        
        if funding_a and funding_b and funding_a > 0 and funding_b > 0:
            # Calculate ratio similarity
            ratio = min(funding_a, funding_b) / max(funding_a, funding_b)
            
            if ratio >= 0.5:  # Within 2x
                funding_score = 4
                matching_attributes.append(f"Similar funding levels: ${funding_a/1e6:.1f}M vs ${funding_b/1e6:.1f}M")
            elif ratio >= 0.2:  # Within 5x
                funding_score = 2
            else:
                funding_score = 0
            
            total_score += funding_score
            categories_with_score += 1
            confidence_factors.append(0.7)  # Moderate confidence for funding data
            
            score_breakdown['total_funding'] = {
                'score': funding_score,
                'max_score': 4,
                'company_a_value': f"${funding_a/1e6:.1f}M",
                'company_b_value': f"${funding_b/1e6:.1f}M",
                'ratio': ratio
            }
        
        # 7. Public/Private Status similarity (4 points)
        public_a = safe_get(company_a, 'is_public', False)
        public_b = safe_get(company_b, 'is_public', False)
        
        if public_a == public_b:
            status_score = 4
            status_text = "public" if public_a else "private"
            matching_attributes.append(f"Both are {status_text} companies")
            
            total_score += status_score
            categories_with_score += 1
            confidence_factors.append(0.9)  # High confidence for public/private status
            
            score_breakdown['public_status'] = {
                'score': status_score,
                'max_score': 4,
                'company_a_value': "Public" if public_a else "Private",
                'company_b_value': "Public" if public_b else "Private"
            }
        
        # 8. Geography similarity (4 points) - Hierarchical: City > State > Country
        country_a = safe_get(company_a, 'hq_country') or safe_get(company_a, 'country')
        country_b = safe_get(company_b, 'hq_country') or safe_get(company_b, 'country')
        
        if country_a and country_b:
            if country_a.lower() == country_b.lower():
                geo_score = 4
                matching_attributes.append(f"Same country: {country_a}")
                
                # Bonus for same state/region (if available)
                state_a = safe_get(company_a, 'state_region')
                state_b = safe_get(company_b, 'state_region')
                if state_a and state_b and state_a.lower() == state_b.lower():
                    matching_attributes.append(f"Same state/region: {state_a}")
                
                # Bonus for same city (if available)
                city_a = safe_get(company_a, 'city')
                city_b = safe_get(company_b, 'city')
                if city_a and city_b and city_a.lower() == city_b.lower():
                    matching_attributes.append(f"Same city: {city_a}")
            else:
                # Regional clustering bonus
                na_countries = {'united states', 'canada', 'mexico'}
                eu_countries = {'united kingdom', 'germany', 'france', 'italy', 'spain', 'netherlands', 'sweden', 'norway', 'denmark'}
                
                if (country_a.lower() in na_countries and country_b.lower() in na_countries) or \
                   (country_a.lower() in eu_countries and country_b.lower() in eu_countries):
                    geo_score = 1
                    matching_attributes.append(f"Same region: {country_a} and {country_b}")
                else:
                    geo_score = 0
            
            total_score += geo_score
            categories_with_score += 1
            confidence_factors.append(0.9)  # High confidence for geography
            
            score_breakdown['geography'] = {
                'score': geo_score,
                'max_score': 4,
                'company_a_value': country_a,
                'company_b_value': country_b
            }
        
        # 9. Funding Stage similarity (1 point)
        stage_a = safe_get(company_a, 'funding_stage_encoded')
        stage_b = safe_get(company_b, 'funding_stage_encoded')
        
        if stage_a and stage_b:
            # Similar funding stages (within 1 stage)
            if abs(stage_a - stage_b) <= 1:
                stage_score = 1
                matching_attributes.append("Similar funding stage")
            else:
                stage_score = 0
            
            total_score += stage_score
            categories_with_score += 1
            confidence_factors.append(0.6)  # Moderate confidence for funding stage
            
            score_breakdown['funding_stage'] = {
                'score': stage_score,
                'max_score': 1,
                'company_a_value': stage_a,
                'company_b_value': stage_b
            }
        
        # Calculate overall confidence based on data availability and quality
        if confidence_factors:
            confidence = sum(confidence_factors) / len(confidence_factors) * 100
        else:
            confidence = 0.0
        
        return total_score, matching_attributes, score_breakdown, confidence, categories_with_score
    
    def calculate_semantic_similarity(self, company_a: Company, company_b: Company) -> Tuple[float, str]:
        """
        Calculate semantic similarity using OpenAI embeddings.
        This function now returns 0 to disable semantic similarity for performance.
        """
        return 0.0, "Semantic similarity disabled for performance"
    
    def generate_ai_reasoning(self, company_a: Company, company_b: Company, matching_attributes: List[str], similarity_score: float) -> str:
        """
        Generate enhanced AI-powered reasoning for why two companies are similar.
        Falls back to rule-based reasoning if OpenAI is not available.
        """
        if not self.openai_client:
            return self.generate_rule_based_reasoning(company_a, company_b, matching_attributes, similarity_score)
        
        # For now, use rule-based reasoning for performance
        return self.generate_rule_based_reasoning(company_a, company_b, matching_attributes, similarity_score)
    
    def generate_rule_based_reasoning(self, company_a: Company, company_b: Company, matching_attributes: List[str], similarity_score: float) -> str:
        """
        Generate rule-based reasoning for why two companies are similar.
        """
        reasoning_parts = []
        
        # Opening statement based on score
        if similarity_score >= 80:
            reasoning_parts.append(f"{company_b.name} is a highly similar company to {company_a.name}")
        elif similarity_score >= 60:
            reasoning_parts.append(f"{company_b.name} shows strong similarities to {company_a.name}")
        else:
            reasoning_parts.append(f"{company_b.name} has some similarities to {company_a.name}")
        
        # Add key matching attributes
        if matching_attributes:
            key_matches = matching_attributes[:3]  # Top 3 matches
            reasoning_parts.append(f"Key similarities include: {', '.join(key_matches).lower()}")
        
        # Add business context if available
        if hasattr(company_a, 'current_revenue_usd') and company_a.current_revenue_usd:
            reasoning_parts.append(f"Both operate at similar revenue scales")
        
        return ". ".join(reasoning_parts) + "."
    
    def _company_to_response(self, company: Company) -> CompanyResponse:
        """Convert Company model to CompanyResponse"""
        # Get PE firms
        pe_firms = []
        if hasattr(company, 'investments') and company.investments:
            pe_firms = [inv.pe_firm.name for inv in company.investments if inv.pe_firm]
        
        # Get employee count display
        employee_count = None
        if hasattr(company, 'employee_count') and company.employee_count:
            employee_count = f"{company.employee_count:,}"
        elif company.projected_employee_count:
            employee_count = f"{company.projected_employee_count:,}"
        elif company.crunchbase_employee_count:
            from src.enrichment.crunchbase_helpers import decode_employee_count
            employee_count = decode_employee_count(company.crunchbase_employee_count)
        
        # Get revenue range
        revenue_range = None
        if company.revenue_range:
            from src.enrichment.crunchbase_helpers import decode_revenue_range
            revenue_range = decode_revenue_range(company.revenue_range)
        
        # Get industries
        industries = []
        if hasattr(company, 'tags') and company.tags:
            industries = [tag.tag_value for tag in company.tags]
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            former_name=getattr(company, 'former_name', None),
            pe_firms=pe_firms,
            status=getattr(company, 'computed_status', 'Unknown'),
            headquarters=f"{company.city}, {company.state_region}" if company.city and company.state_region else company.city or company.state_region,
            website=company.website,
            linkedin_url=company.linkedin_url,
            crunchbase_url=company.crunchbase_url,
            description=company.description,
            revenue_range=revenue_range,
            employee_count=employee_count,
            industry_category=company.industry_category,
            industries=industries,
            is_public=getattr(company, 'is_public', False),
            # PitchBook data
            current_revenue_usd=getattr(company, 'current_revenue_usd', None),
            last_known_valuation_usd=getattr(company, 'last_known_valuation_usd', None),
            primary_industry_group=getattr(company, 'primary_industry_group', None),
            primary_industry_sector=getattr(company, 'primary_industry_sector', None),
            hq_location=getattr(company, 'hq_location', None),
            hq_country=getattr(company, 'hq_country', None),
            verticals=getattr(company, 'verticals', None)
        )