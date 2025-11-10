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
        
        # Get all candidates first for advanced filtering
        candidates = query.order_by(
            desc(Company.current_revenue_usd),
            desc(Company.last_known_valuation_usd)
        ).all()
        
        print(f"   Found {len(candidates)} candidate companies (before exit filter)")
        
        # EXCLUDE ALL EXITED COMPANIES EXCEPT IPO - Never show acquired, merged, LBO, buyout, etc.
        excluded_count = 0
        def has_non_ipo_exit(company):
            """Check if company has any non-IPO exits in its investments"""
            nonlocal excluded_count
            for inv in company.investments:
                # Check computed_status - if it's "Exit", verify it was an IPO
                computed_status = getattr(inv, 'computed_status', None)
                investor_status = getattr(inv, 'investor_status', None)

                # If investor is "Former", check the exit type
                if investor_status and 'former' in investor_status.lower():
                    exit_type = getattr(inv, 'exit_type', None)

                    # Former investor with no exit_type or non-IPO exit = exclude
                    if not exit_type or not exit_type.strip():
                        excluded_count += 1
                        return True

                    exit_lower = exit_type.lower().strip()
                    if exit_lower != 'ipo':
                        excluded_count += 1
                        return True

                # Also check computed_status = Exit
                if computed_status and 'exit' in computed_status.lower():
                    exit_type = getattr(inv, 'exit_type', None)

                    # If status is Exit but no exit_type specified, exclude it (safer default)
                    if not exit_type or not exit_type.strip():
                        excluded_count += 1
                        return True

                    exit_lower = exit_type.lower().strip()

                    # Only allow IPO exits
                    if exit_lower != 'ipo':
                        # Check for common non-IPO exit patterns
                        non_ipo_keywords = ['acquisition', 'acquired', 'buyout', 'lbo', 'secondary',
                                           'merger', 'merge', 'private equity', 'going private',
                                           'management buyout', 'mbo', 'sale', 'sold']

                        # Either matches a keyword OR is an exit that's not IPO
                        is_non_ipo = any(keyword in exit_lower for keyword in non_ipo_keywords)
                        if is_non_ipo or exit_lower not in ['none', 'null', 'unknown']:
                            excluded_count += 1
                            return True
            return False
        
        candidates = [c for c in candidates if not has_non_ipo_exit(c)]
        print(f"   Filtered to {len(candidates)} companies (excluded {excluded_count} non-IPO exits)")
        
        # USER FEEDBACK FILTERING: Exclude companies marked as "not a match"
        from src.models.database_models_v2 import CompanySimilarityFeedback
        
        # Get all negative feedback for input companies
        negative_feedback_query = self.session.query(CompanySimilarityFeedback).filter(
            CompanySimilarityFeedback.input_company_id.in_([c.id for c in input_companies]),
            CompanySimilarityFeedback.feedback_type == 'not_a_match'
        )
        
        excluded_company_ids = set()
        for feedback in negative_feedback_query.all():
            excluded_company_ids.add(feedback.match_company_id)
        
        if excluded_company_ids:
            before_feedback_filter = len(candidates)
            candidates = [c for c in candidates if c.id not in excluded_company_ids]
            print(f"   Feedback filter: Excluded {before_feedback_filter - len(candidates)} companies marked as 'not a match'")
        
        # REVENUE-BASED PRE-FILTERING: Only compare companies in reasonable revenue range
        # This dramatically improves result quality and speed
        if input_companies[0].current_revenue_usd:
            input_revenue = input_companies[0].current_revenue_usd
            # Keep companies within 0.1x to 10x revenue range (covers 100x total range)
            # More generous range to capture edge cases while still filtering outliers
            min_revenue = input_revenue * 0.1
            max_revenue = input_revenue * 10.0

            before_revenue_filter = len(candidates)
            candidates = [
                c for c in candidates
                if c.current_revenue_usd and min_revenue <= c.current_revenue_usd <= max_revenue
            ]
            print(f"   Revenue filter: ${input_revenue:.1f}M (10% to 10x) = {len(candidates)} companies (was {before_revenue_filter})")
        
        # AGGRESSIVE FILTERING: Limit to max 100 candidates to prevent timeout
        max_candidates = 100
        
        if len(candidates) > max_candidates:
            print(f"   WARNING: Too many candidates ({len(candidates)}), applying aggressive filtering...")
            
            # Strategy 1: Filter by same sector first
            if input_companies[0].primary_industry_sector:
                same_sector = [c for c in candidates 
                             if c.primary_industry_sector == input_companies[0].primary_industry_sector]
                
                if len(same_sector) >= 20:
                    # Take top N from same sector
                    candidates = same_sector[:max_candidates]
                    print(f"   Filtered to {len(candidates)} companies in same sector")
                else:
                    # Mix same sector + others
                    other_companies = [c for c in candidates 
                                     if c.primary_industry_sector != input_companies[0].primary_industry_sector]
                    candidates = same_sector + other_companies[:max_candidates - len(same_sector)]
                    print(f"   Mixed filter: {len(same_sector)} same sector + {len(candidates) - len(same_sector)} others")
            else:
                # No sector info, just take first N
                candidates = candidates[:max_candidates]
                print(f"   Limited to first {len(candidates)} companies")
        
        print(f"   Found {len(candidates)} candidate companies")
        
        # 3. Calculate similarity scores for all candidates against all input companies
        print("[3/6] Calculating similarity scores...")
        all_matches = []
        seen_company_ids = set()
        
        total_comparisons = len(input_companies) * len(candidates)
        print(f"   Total comparisons to make: {total_comparisons}")
        
        comparison_count = 0
        for idx, input_company in enumerate(input_companies):
            # Only log for multiple input companies to reduce noise
            if len(input_companies) > 1:
                print(f"   Processing input company {idx+1}/{len(input_companies)}: {input_company.name}")

            for candidate in candidates:
                comparison_count += 1

                # Skip if already processed (when multiple input companies)
                if candidate.id in seen_company_ids:
                    continue
                
                # Calculate rule-based similarity score with detailed breakdown
                similarity_score, matching_attrs, score_breakdown, confidence, categories_with_score = self.calculate_similarity_score(input_company, candidate)
                
                # Skip semantic similarity (OpenAI embeddings) for performance
                # semantic_score, semantic_explanation = self.calculate_semantic_similarity(input_company, candidate)
                
                # Multi-requirement filter: require scores in at least 2 categories
                # This prevents weak matches that only score high in one dimension
                if categories_with_score < 2:
                    continue
                
                # Total score (cap at 100)
                total_score = similarity_score  # + semantic_score
                
                if total_score >= request.min_score:
                    # Generate rule-based reasoning (no AI/API calls)
                    reasoning = self.generate_rule_based_reasoning(input_company, candidate, matching_attrs, total_score)
                    
                    all_matches.append({
                        'input_company_id': input_company.id,
                        'candidate': candidate,
                        'score': min(100.0, total_score),  # Cap at 100
                        'reasoning': reasoning,
                        'matching_attributes': matching_attrs,
                        'score_breakdown': score_breakdown,
                        'confidence': confidence
                    })
                    
                    seen_company_ids.add(candidate.id)
        
        print(f"   Found {len(all_matches)} matches above threshold")
        
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
        COMPREHENSIVE REVENUE & EMPLOYEE-FIRST WEIGHTING SYSTEM

        Scoring Distribution (100 points):
        - Revenue (PitchBook exact): 30 pts OR Crunchbase bands: 15 pts (30%)
        - Employee Count (enhanced): 25 points (25%)
        - Investor Overlap (PE firms): 12 points (12%)
        - Verticals: 12 points (12%)
        - Industry Category: 8 points (8%)
        - Description Similarity: 5 points (5%)
        - Business Model: 3 points (3%)
        - Funding Stage: 3 points (3%)
        - Geography: 1 point (1%)
        - Funding Type: 1 point (1%)

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

        # Helper function to convert Crunchbase revenue range to midpoint (in millions USD)
        def get_revenue_midpoint(revenue_code):
            """Convert Crunchbase revenue code to approximate midpoint in millions USD"""
            revenue_map = {
                "r_00000000": 0.5,      # Less than $1M -> 0.5M
                "r_00001000": 5.5,      # $1M - $10M -> 5.5M
                "r_00010000": 30,       # $10M - $50M -> 30M
                "r_00050000": 75,       # $50M - $100M -> 75M
                "r_00100000": 300,      # $100M - $500M -> 300M
                "r_00500000": 750,      # $500M - $1B -> 750M
                "r_01000000": 5500,     # $1B - $10B -> 5.5B
                "r_10000000": 15000,    # $10B+ -> 15B
            }
            return revenue_map.get(revenue_code, None)

        # 1. REVENUE SIMILARITY (30 points PitchBook OR 15 points Crunchbase) - HIGHEST PRIORITY
        revenue_a = safe_get(company_a, 'current_revenue_usd')
        revenue_b = safe_get(company_b, 'current_revenue_usd')

        # Try PitchBook exact revenue first (30 points possible)
        if revenue_a and revenue_b and revenue_a > 0 and revenue_b > 0:
            ratio = min(revenue_a, revenue_b) / max(revenue_a, revenue_b)

            # Granular scoring bands - reward close matches heavily
            if ratio >= 0.9:  # Within 10%
                revenue_score = 30
                matching_attributes.append(f"Nearly identical revenue: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.8:  # Within 20%
                revenue_score = 27
                matching_attributes.append(f"Very similar revenue: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.7:  # Within 30%
                revenue_score = 24
                matching_attributes.append(f"Highly similar revenue: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.6:  # Within 40%
                revenue_score = 21
                matching_attributes.append(f"Very similar revenue: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.5:  # Within 50%
                revenue_score = 18
                matching_attributes.append(f"Similar revenue: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.4:  # Within 60%
                revenue_score = 13
                matching_attributes.append(f"Comparable revenue: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.3:  # Within 70%
                revenue_score = 8
                matching_attributes.append(f"Similar revenue scale: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            elif ratio >= 0.2:  # Within 80%
                revenue_score = 4
                matching_attributes.append(f"Same revenue tier: ${revenue_a:.1f}M vs ${revenue_b:.1f}M")
            else:
                revenue_score = 0

            total_score += revenue_score
            categories_with_score += 1
            confidence_factors.append(0.95)  # Very high confidence for PitchBook data

            score_breakdown['revenue_pitchbook'] = {
                'score': revenue_score,
                'max_score': 30,
                'company_a_value': revenue_a,
                'company_b_value': revenue_b,
                'ratio': ratio,
                'source': 'PitchBook'
            }

        # Fallback to Crunchbase revenue bands if PitchBook unavailable (15 points possible)
        elif not (revenue_a and revenue_b):
            rev_code_a = safe_get(company_a, 'revenue_range')
            rev_code_b = safe_get(company_b, 'revenue_range')

            if rev_code_a and rev_code_b:
                rev_mid_a = get_revenue_midpoint(rev_code_a)
                rev_mid_b = get_revenue_midpoint(rev_code_b)

                if rev_mid_a and rev_mid_b:
                    # Same scoring logic but max 15 points
                    ratio = min(rev_mid_a, rev_mid_b) / max(rev_mid_a, rev_mid_b)

                    if ratio >= 0.9:
                        revenue_score = 15
                        matching_attributes.append(f"Similar revenue band (Crunchbase)")
                    elif ratio >= 0.8:
                        revenue_score = 13
                        matching_attributes.append(f"Similar revenue band (Crunchbase)")
                    elif ratio >= 0.7:
                        revenue_score = 11
                        matching_attributes.append(f"Similar revenue band (Crunchbase)")
                    elif ratio >= 0.6:
                        revenue_score = 9
                        matching_attributes.append(f"Comparable revenue band (Crunchbase)")
                    elif ratio >= 0.5:
                        revenue_score = 7
                        matching_attributes.append(f"Comparable revenue band (Crunchbase)")
                    elif ratio >= 0.4:
                        revenue_score = 5
                        matching_attributes.append(f"Same revenue tier (Crunchbase)")
                    elif ratio >= 0.3:
                        revenue_score = 3
                        matching_attributes.append(f"Same revenue tier (Crunchbase)")
                    else:
                        revenue_score = 0

                    total_score += revenue_score
                    categories_with_score += 1
                    confidence_factors.append(0.7)  # Lower confidence for band data

                    score_breakdown['revenue_crunchbase'] = {
                        'score': revenue_score,
                        'max_score': 15,
                        'company_a_value': rev_code_a,
                        'company_b_value': rev_code_b,
                        'ratio': ratio,
                        'source': 'Crunchbase'
                    }

        # 2. EMPLOYEE COUNT SIMILARITY (25 points) - SECOND HIGHEST PRIORITY
        # Enhanced with more granular bands
        emp_a = safe_get(company_a, 'employee_count')
        emp_b = safe_get(company_b, 'employee_count')

        if emp_a and emp_b and emp_a > 0 and emp_b > 0:
            # Calculate ratio (smaller/larger)
            ratio = min(emp_a, emp_b) / max(emp_a, emp_b)

            # Granular scoring bands - reward close matches
            if ratio >= 0.9:  # Within 10%
                employee_score = 25
                matching_attributes.append(f"Nearly identical employee count: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.8:  # Within 20%
                employee_score = 22
                matching_attributes.append(f"Very similar employee count: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.7:  # Within 30%
                employee_score = 19
                matching_attributes.append(f"Highly similar team size: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.6:  # Within 40%
                employee_score = 16
                matching_attributes.append(f"Similar employee count: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.5:  # Within 50%
                employee_score = 13
                matching_attributes.append(f"Comparable team size: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.4:  # Within 60%
                employee_score = 10
                matching_attributes.append(f"Similar company size: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.3:  # Within 70%
                employee_score = 7
                matching_attributes.append(f"Similar scale: {emp_a:,} vs {emp_b:,}")
            elif ratio >= 0.2:  # Within 80%
                employee_score = 4
                matching_attributes.append(f"Same size category: {emp_a:,} vs {emp_b:,}")
            else:
                employee_score = 0

            total_score += employee_score
            categories_with_score += 1
            confidence_factors.append(0.95)  # Very high confidence for employee data

            score_breakdown['employee_count'] = {
                'score': employee_score,
                'max_score': 25,
                'company_a_value': emp_a,
                'company_b_value': emp_b,
                'ratio': ratio
            }

        # 3. INVESTOR OVERLAP (12 points) - HIGH IMPACT - Shared PE firms
        pe_firms_a = set()
        pe_firms_b = set()

        if hasattr(company_a, 'investments') and company_a.investments:
            pe_firms_a = {inv.pe_firm.name for inv in company_a.investments if inv.pe_firm}

        if hasattr(company_b, 'investments') and company_b.investments:
            pe_firms_b = {inv.pe_firm.name for inv in company_b.investments if inv.pe_firm}

        if pe_firms_a and pe_firms_b:
            shared_investors = pe_firms_a.intersection(pe_firms_b)
            union_investors = pe_firms_a.union(pe_firms_b)

            if shared_investors:
                # Jaccard similarity with bonus for multiple shared investors
                jaccard = len(shared_investors) / len(union_investors) if union_investors else 0
                investor_score = jaccard * 12

                # Bonus: Multiple shared investors = stronger signal
                if len(shared_investors) >= 3:
                    investor_score = min(12, investor_score * 1.2)  # 20% bonus
                elif len(shared_investors) >= 2:
                    investor_score = min(12, investor_score * 1.1)  # 10% bonus

                total_score += investor_score
                categories_with_score += 1
                confidence_factors.append(0.95)  # Very high confidence

                investor_names = ', '.join(sorted(shared_investors)[:3])
                if len(shared_investors) > 3:
                    investor_names += f" +{len(shared_investors) - 3} more"

                matching_attributes.append(f"Shared investors: {investor_names}")

                score_breakdown['investor_overlap'] = {
                    'score': investor_score,
                    'max_score': 12,
                    'shared_count': len(shared_investors),
                    'shared_investors': list(shared_investors),
                    'jaccard_similarity': jaccard
                }

        # 4. Verticals similarity (12 points) - PitchBook verticals
        verticals_a = safe_split(safe_get(company_a, 'verticals'))
        verticals_b = safe_split(safe_get(company_b, 'verticals'))

        if verticals_a and verticals_b:
            # Calculate Jaccard similarity (intersection over union)
            intersection = len(verticals_a.intersection(verticals_b))
            union = len(verticals_a.union(verticals_b))
            jaccard_similarity = intersection / union if union > 0 else 0

            verticals_score = jaccard_similarity * 12
            total_score += verticals_score
            categories_with_score += 1
            confidence_factors.append(0.9)  # High confidence for PitchBook data

            score_breakdown['verticals'] = {
                'score': verticals_score,
                'max_score': 12,
                'company_a_value': ', '.join(sorted(verticals_a)) if verticals_a else 'None',
                'company_b_value': ', '.join(sorted(verticals_b)) if verticals_b else 'None',
                'jaccard_similarity': jaccard_similarity
            }

            if intersection > 0:
                shared_verticals = verticals_a.intersection(verticals_b)
                matching_attributes.append(f"Shared verticals: {', '.join(sorted(shared_verticals))}")

        # 5. Industry Category similarity (8 points) - More detailed than sector
        industry_cat_a = safe_split(safe_get(company_a, 'industry_category'))
        industry_cat_b = safe_split(safe_get(company_b, 'industry_category'))

        if industry_cat_a and industry_cat_b:
            # Calculate Jaccard similarity
            intersection = len(industry_cat_a.intersection(industry_cat_b))
            union = len(industry_cat_a.union(industry_cat_b))
            jaccard_similarity = intersection / union if union > 0 else 0

            industry_score = jaccard_similarity * 8
            total_score += industry_score
            categories_with_score += 1
            confidence_factors.append(0.85)  # Good confidence for detailed industry data

            score_breakdown['industry_category'] = {
                'score': industry_score,
                'max_score': 8,
                'company_a_value': ', '.join(sorted(industry_cat_a)) if industry_cat_a else 'None',
                'company_b_value': ', '.join(sorted(industry_cat_b)) if industry_cat_b else 'None',
                'jaccard_similarity': jaccard_similarity
            }

            if intersection > 0:
                shared_industries = industry_cat_a.intersection(industry_cat_b)
                matching_attributes.append(f"Shared industry categories: {', '.join(sorted(shared_industries))}")

        # 6. DESCRIPTION SIMILARITY (5 points) - Keyword-based matching
        desc_a = safe_get(company_a, 'description', '')
        desc_b = safe_get(company_b, 'description', '')

        if desc_a and desc_b:
            # Extract meaningful keywords (exclude common words)
            def extract_keywords(text):
                if not text:
                    return set()
                # Convert to lowercase and split
                words = text.lower().split()
                # Filter out common words and short words
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                             'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                             'this', 'that', 'these', 'those', 'it', 'its', 'they', 'their'}
                keywords = {w.strip('.,!?;:') for w in words if len(w) > 3 and w not in stop_words}
                return keywords

            keywords_a = extract_keywords(desc_a)
            keywords_b = extract_keywords(desc_b)

            if keywords_a and keywords_b:
                shared_keywords = keywords_a.intersection(keywords_b)
                union_keywords = keywords_a.union(keywords_b)

                if shared_keywords and union_keywords:
                    jaccard = len(shared_keywords) / len(union_keywords)
                    description_score = jaccard * 5

                    if description_score > 1:  # Only count if meaningful overlap
                        total_score += description_score
                        categories_with_score += 1
                        confidence_factors.append(0.6)  # Moderate confidence

                        top_keywords = list(sorted(shared_keywords))[:5]
                        matching_attributes.append(f"Similar business description")

                        score_breakdown['description'] = {
                            'score': description_score,
                            'max_score': 5,
                            'shared_keywords': top_keywords,
                            'jaccard_similarity': jaccard
                        }

        # 7. BUSINESS MODEL SIMILARITY (3 points) - Inferred from verticals/industry
        def infer_business_model(company):
            """Infer business model from verticals and industry"""
            models = set()

            verticals_lower = (safe_get(company, 'verticals') or '').lower()
            industry_lower = (safe_get(company, 'industry_category') or '').lower()
            combined = f"{verticals_lower} {industry_lower}"

            # SaaS indicators
            if any(keyword in combined for keyword in ['saas', 'software', 'cloud', 'platform', 'application']):
                models.add('saas')

            # B2B indicators
            if any(keyword in combined for keyword in ['enterprise', 'b2b', 'business', 'corporate', 'industrial']):
                models.add('b2b')

            # B2C indicators
            if any(keyword in combined for keyword in ['consumer', 'retail', 'b2c', 'ecommerce', 'marketplace']):
                models.add('b2c')

            # Marketplace indicators
            if any(keyword in combined for keyword in ['marketplace', 'platform', 'network']):
                models.add('marketplace')

            # Hardware indicators
            if any(keyword in combined for keyword in ['hardware', 'device', 'equipment', 'manufacturing']):
                models.add('hardware')

            # Services indicators
            if any(keyword in combined for keyword in ['service', 'consulting', 'professional']):
                models.add('services')

            return models

        models_a = infer_business_model(company_a)
        models_b = infer_business_model(company_b)

        if models_a and models_b:
            shared_models = models_a.intersection(models_b)

            if shared_models:
                # Full points if multiple shared models, partial for one
                if len(shared_models) >= 2:
                    business_model_score = 3
                else:
                    business_model_score = 2

                total_score += business_model_score
                categories_with_score += 1
                confidence_factors.append(0.7)

                matching_attributes.append(f"Similar business model: {', '.join(sorted(shared_models))}")

                score_breakdown['business_model'] = {
                    'score': business_model_score,
                    'max_score': 3,
                    'shared_models': list(shared_models),
                    'company_a_models': list(models_a),
                    'company_b_models': list(models_b)
                }

        # 8. Funding Stage similarity (3 points) - Company maturity
        funding_stage_a = safe_get(company_a, 'funding_stage_encoded')
        funding_stage_b = safe_get(company_b, 'funding_stage_encoded')

        if funding_stage_a and funding_stage_b:
            # Similar funding stages (within 1-2 stages)
            stage_diff = abs(funding_stage_a - funding_stage_b)
            if stage_diff == 0:
                funding_score = 3
                matching_attributes.append(f"Same funding stage")
            elif stage_diff == 1:
                funding_score = 2
                matching_attributes.append(f"Adjacent funding stages")
            elif stage_diff == 2:
                funding_score = 1
                matching_attributes.append(f"Similar funding maturity")
            else:
                funding_score = 0

            total_score += funding_score
            categories_with_score += 1
            confidence_factors.append(0.8)

            score_breakdown['funding_stage'] = {
                'score': funding_score,
                'max_score': 3,
                'company_a_value': funding_stage_a,
                'company_b_value': funding_stage_b,
                'stage_difference': stage_diff
            }

        # 9. Geographic proximity (1 point) - Lower priority
        country_a = safe_get(company_a, 'hq_country')
        country_b = safe_get(company_b, 'hq_country')
        state_a = safe_get(company_a, 'state_region')
        state_b = safe_get(company_b, 'state_region')

        geo_score = 0
        if country_a and country_b:
            if country_a.lower() == country_b.lower():
                geo_score = 1  # Same country
                if state_a and state_b and state_a.lower() == state_b.lower():
                    matching_attributes.append(f"Same state/region: {state_a}")
                else:
                    matching_attributes.append(f"Same country: {country_a}")

        total_score += geo_score
        if geo_score > 0:
            categories_with_score += 1
            confidence_factors.append(0.9)

            score_breakdown['geography'] = {
                'score': geo_score,
                'max_score': 1,
                'company_a_country': country_a,
                'company_b_country': country_b,
                'company_a_state': state_a,
                'company_b_state': state_b
            }

        # 10. Funding Type similarity (1 point) - Lowest priority
        funding_type_a = safe_get(company_a, 'last_financing_deal_type')
        funding_type_b = safe_get(company_b, 'last_financing_deal_type')

        if funding_type_a and funding_type_b:
            # Group similar funding types
            growth_types = {'series_a', 'series_b', 'series_c', 'series_d', 'series_e'}
            late_types = {'series_f', 'series_g', 'growth_equity', 'late_stage_vc'}
            buyout_types = {'buyout/lbo', 'management_buyout', 'leveraged_buyout'}
            debt_types = {'debt', 'debt_financing', 'debt - general'}

            def get_funding_category(funding_type):
                ft_lower = funding_type.lower().replace(' ', '_').replace('-', '_')
                if any(t in ft_lower for t in growth_types):
                    return 'growth'
                elif any(t in ft_lower for t in late_types):
                    return 'late_stage'
                elif any(t in ft_lower for t in buyout_types):
                    return 'buyout'
                elif any(t in ft_lower for t in debt_types):
                    return 'debt'
                elif 'ipo' in ft_lower or 'public' in ft_lower:
                    return 'public'
                else:
                    return 'other'

            cat_a = get_funding_category(funding_type_a)
            cat_b = get_funding_category(funding_type_b)

            if cat_a == cat_b:
                funding_type_score = 1
                matching_attributes.append(f"Similar funding type: {cat_a}")
            else:
                funding_type_score = 0

            total_score += funding_type_score
            categories_with_score += 1
            confidence_factors.append(0.7)

            score_breakdown['funding_type'] = {
                'score': funding_type_score,
                'max_score': 1,
                'company_a_value': funding_type_a,
                'company_b_value': funding_type_b,
                'company_a_category': cat_a,
                'company_b_category': cat_b
            }
        
        # Calculate overall confidence score
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
    
    def generate_rule_based_reasoning(self, company_a: Company, company_b: Company, matching_attributes: List[str], similarity_score: float) -> str:
        """Generate rule-based reasoning without AI/API calls for better performance"""
        if not matching_attributes:
            return f"Limited similarity to {company_a.name} (score: {similarity_score:.1f}%)"
        
        # Categorize the matching attributes
        revenue_matches = [attr for attr in matching_attributes if 'revenue' in attr.lower()]
        industry_matches = [attr for attr in matching_attributes if any(word in attr.lower() for word in ['industry', 'sector', 'vertical'])]
        size_matches = [attr for attr in matching_attributes if 'employee' in attr.lower()]
        geo_matches = [attr for attr in matching_attributes if any(word in attr.lower() for word in ['country', 'state', 'city', 'region'])]
        funding_matches = [attr for attr in matching_attributes if any(word in attr.lower() for word in ['funding', 'stage', 'public', 'private'])]
        
        reasoning_parts = []
        
        # Start with overall assessment
        if similarity_score >= 70:
            reasoning_parts.append(f"Strong match with {company_a.name} ({similarity_score:.1f}% similarity).")
        elif similarity_score >= 50:
            reasoning_parts.append(f"Good match with {company_a.name} ({similarity_score:.1f}% similarity).")
        elif similarity_score >= 30:
            reasoning_parts.append(f"Moderate match with {company_a.name} ({similarity_score:.1f}% similarity).")
        else:
            reasoning_parts.append(f"Limited match with {company_a.name} ({similarity_score:.1f}% similarity).")
        
        # Add specific matching details
        if revenue_matches:
            reasoning_parts.append(f"Revenue alignment: {revenue_matches[0]}.")
        
        if industry_matches:
            reasoning_parts.append(f"Industry similarity: {industry_matches[0]}.")
        
        if size_matches:
            reasoning_parts.append(f"Company size: {size_matches[0]}.")
        
        if geo_matches:
            reasoning_parts.append(f"Geographic proximity: {geo_matches[0]}.")
        
        if funding_matches:
            reasoning_parts.append(f"Funding characteristics: {funding_matches[0]}.")
        
        # Add context about comparison quality
        total_matches = len(matching_attributes)
        if total_matches >= 4:
            reasoning_parts.append("Multiple strong alignment factors.")
        elif total_matches >= 2:
            reasoning_parts.append("Several alignment factors.")
        else:
            reasoning_parts.append("Limited alignment factors.")
        
        return " ".join(reasoning_parts)

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