#!/usr/bin/env python3
"""
Mock test of Acquia similarity matching with new algorithm
Demonstrates scoring without requiring database connection
"""

# Mock Acquia data (based on typical Acquia profile)
acquia = {
    'name': 'Acquia',
    'current_revenue_usd': 150.0,  # ~$150M revenue
    'employee_count': 1200,
    'verticals': 'Digital Marketing Software, Content Management Systems, Cloud Computing',
    'industry_category': 'Software, SaaS, Enterprise Software, Marketing Technology',
    'description': 'Acquia provides cloud-based digital experience platform for building, delivering, and optimizing digital experiences',
    'pe_firms': ['Vista Equity Partners'],
    'hq_country': 'United States',
    'state_region': 'Massachusetts',
    'funding_stage_encoded': 6,  # Late stage
    'last_financing_deal_type': 'Buyout/LBO'
}

# Mock similar companies
candidates = [
    {
        'name': 'Sitecore',
        'current_revenue_usd': 180.0,
        'employee_count': 1400,
        'verticals': 'Content Management Systems, Digital Marketing Software, Cloud Computing',
        'industry_category': 'Software, SaaS, Enterprise Software, Marketing Technology',
        'description': 'Sitecore delivers digital experience management platform for personalized content',
        'pe_firms': ['EQT Partners'],
        'hq_country': 'United States',
        'state_region': 'California',
        'funding_stage_encoded': 6,
        'last_financing_deal_type': 'Buyout/LBO'
    },
    {
        'name': 'Adobe Experience Manager (Marketo)',
        'current_revenue_usd': 4500.0,  # Much larger
        'employee_count': 26000,
        'verticals': 'Digital Marketing Software, Content Management, Cloud Computing',
        'industry_category': 'Software, Enterprise Software, Marketing Technology',
        'description': 'Adobe provides digital marketing and experience management solutions',
        'pe_firms': [],  # Public company
        'hq_country': 'United States',
        'state_region': 'California',
        'funding_stage_encoded': 7,  # IPO
        'last_financing_deal_type': 'IPO'
    },
    {
        'name': 'Contentful',
        'current_revenue_usd': 90.0,
        'employee_count': 800,
        'verticals': 'Content Management Systems, API Platform, Cloud Computing',
        'industry_category': 'Software, SaaS, Enterprise Software',
        'description': 'Contentful provides headless CMS platform for digital content delivery',
        'pe_firms': [],
        'hq_country': 'Germany',
        'state_region': 'Berlin',
        'funding_stage_encoded': 5,  # Growth stage
        'last_financing_deal_type': 'Series E'
    },
    {
        'name': 'Optimizely',
        'current_revenue_usd': 140.0,
        'employee_count': 1100,
        'verticals': 'Digital Marketing Software, A/B Testing, Content Management',
        'industry_category': 'Software, SaaS, Enterprise Software, Marketing Technology',
        'description': 'Optimizely provides digital experience optimization platform for testing and personalization',
        'pe_firms': ['Vista Equity Partners'],  # Same PE firm!
        'hq_country': 'United States',
        'state_region': 'California',
        'funding_stage_encoded': 6,
        'last_financing_deal_type': 'Buyout/LBO'
    },
    {
        'name': 'MongoDB',
        'current_revenue_usd': 1280.0,
        'employee_count': 5000,
        'verticals': 'Database Software, Cloud Computing, NoSQL',
        'industry_category': 'Software, Database, Infrastructure',
        'description': 'MongoDB provides NoSQL database platform for modern applications',
        'pe_firms': [],  # Public
        'hq_country': 'United States',
        'state_region': 'New York',
        'funding_stage_encoded': 7,
        'last_financing_deal_type': 'IPO'
    }
]

def score_company(input_company, candidate):
    """Simulate the scoring algorithm"""
    total_score = 0.0
    breakdown = {}

    # 1. Revenue (30 pts)
    rev_a = input_company['current_revenue_usd']
    rev_b = candidate['current_revenue_usd']
    ratio = min(rev_a, rev_b) / max(rev_a, rev_b)

    if ratio >= 0.9:
        revenue_score = 30
    elif ratio >= 0.8:
        revenue_score = 27
    elif ratio >= 0.7:
        revenue_score = 24
    elif ratio >= 0.6:
        revenue_score = 21
    elif ratio >= 0.5:
        revenue_score = 18
    elif ratio >= 0.4:
        revenue_score = 13
    elif ratio >= 0.3:
        revenue_score = 8
    elif ratio >= 0.2:
        revenue_score = 4
    else:
        revenue_score = 0

    total_score += revenue_score
    breakdown['revenue'] = f"{revenue_score}/30 (ratio: {ratio:.2f})"

    # 2. Employee Count (25 pts)
    emp_a = input_company['employee_count']
    emp_b = candidate['employee_count']
    ratio = min(emp_a, emp_b) / max(emp_a, emp_b)

    if ratio >= 0.9:
        employee_score = 25
    elif ratio >= 0.8:
        employee_score = 22
    elif ratio >= 0.7:
        employee_score = 19
    elif ratio >= 0.6:
        employee_score = 16
    elif ratio >= 0.5:
        employee_score = 13
    elif ratio >= 0.4:
        employee_score = 10
    else:
        employee_score = 0

    total_score += employee_score
    breakdown['employees'] = f"{employee_score}/25 (ratio: {ratio:.2f})"

    # 3. Investor Overlap (12 pts)
    pe_a = set(input_company['pe_firms'])
    pe_b = set(candidate['pe_firms'])
    shared = pe_a.intersection(pe_b)

    if shared:
        union = pe_a.union(pe_b)
        jaccard = len(shared) / len(union)
        investor_score = jaccard * 12

        # Bonus for multiple shared
        if len(shared) >= 2:
            investor_score = min(12, investor_score * 1.1)

        total_score += investor_score
        breakdown['investors'] = f"{investor_score:.1f}/12 (shared: {list(shared)})"
    else:
        breakdown['investors'] = "0/12 (no overlap)"

    # 4. Verticals (12 pts)
    vert_a = set(v.strip().lower() for v in input_company['verticals'].split(','))
    vert_b = set(v.strip().lower() for v in candidate['verticals'].split(','))

    intersection = len(vert_a.intersection(vert_b))
    union = len(vert_a.union(vert_b))
    jaccard = intersection / union if union > 0 else 0

    verticals_score = jaccard * 12
    total_score += verticals_score
    breakdown['verticals'] = f"{verticals_score:.1f}/12 (jaccard: {jaccard:.2f})"

    # 5. Industry Category (8 pts)
    ind_a = set(i.strip().lower() for i in input_company['industry_category'].split(','))
    ind_b = set(i.strip().lower() for i in candidate['industry_category'].split(','))

    intersection = len(ind_a.intersection(ind_b))
    union = len(ind_a.union(ind_b))
    jaccard = intersection / union if union > 0 else 0

    industry_score = jaccard * 8
    total_score += industry_score
    breakdown['industry'] = f"{industry_score:.1f}/8 (jaccard: {jaccard:.2f})"

    # 6. Description Similarity (5 pts) - simplified
    desc_a = set(input_company['description'].lower().split())
    desc_b = set(candidate['description'].lower().split())

    shared = desc_a.intersection(desc_b)
    union = desc_a.union(desc_b)
    jaccard = len(shared) / len(union) if len(union) > 0 else 0

    description_score = jaccard * 5
    if description_score > 1:
        total_score += description_score
        breakdown['description'] = f"{description_score:.1f}/5"
    else:
        breakdown['description'] = "0/5"

    # 7. Business Model (3 pts) - inferred
    def infer_model(company):
        text = f"{company['verticals']} {company['industry_category']}".lower()
        models = set()
        if any(k in text for k in ['saas', 'software', 'cloud']):
            models.add('saas')
        if any(k in text for k in ['enterprise', 'b2b']):
            models.add('b2b')
        return models

    models_a = infer_model(input_company)
    models_b = infer_model(candidate)
    shared_models = models_a.intersection(models_b)

    if shared_models:
        business_model_score = 3 if len(shared_models) >= 2 else 2
        total_score += business_model_score
        breakdown['business_model'] = f"{business_model_score}/3 ({','.join(shared_models)})"
    else:
        breakdown['business_model'] = "0/3"

    # 8. Funding Stage (3 pts)
    stage_diff = abs(input_company['funding_stage_encoded'] - candidate['funding_stage_encoded'])
    if stage_diff == 0:
        funding_score = 3
    elif stage_diff == 1:
        funding_score = 2
    elif stage_diff == 2:
        funding_score = 1
    else:
        funding_score = 0

    total_score += funding_score
    breakdown['funding_stage'] = f"{funding_score}/3 (diff: {stage_diff})"

    # 9. Geography (1 pt)
    if input_company['hq_country'].lower() == candidate['hq_country'].lower():
        geo_score = 1
        total_score += geo_score
        breakdown['geography'] = "1/1 (same country)"
    else:
        breakdown['geography'] = "0/1"

    # 10. Funding Type (1 pt)
    if 'buyout' in input_company['last_financing_deal_type'].lower() and 'buyout' in candidate['last_financing_deal_type'].lower():
        funding_type_score = 1
        total_score += funding_type_score
        breakdown['funding_type'] = "1/1"
    else:
        breakdown['funding_type'] = "0/1"

    return total_score, breakdown

# Score all candidates
print("=" * 80)
print("ACQUIA SIMILARITY MATCHING - NEW ALGORITHM TEST")
print("=" * 80)
print(f"\nInput Company: {acquia['name']}")
print(f"Revenue: ${acquia['current_revenue_usd']:.0f}M")
print(f"Employees: {acquia['employee_count']:,}")
print(f"PE Firms: {acquia['pe_firms']}")
print(f"Verticals: {acquia['verticals'][:60]}...")
print("\n" + "=" * 80)

results = []
for candidate in candidates:
    score, breakdown = score_company(acquia, candidate)
    results.append((candidate['name'], score, breakdown))

# Sort by score
results.sort(key=lambda x: x[1], reverse=True)

# Display results
for rank, (name, score, breakdown) in enumerate(results, 1):
    print(f"\n#{rank}. {name} - SCORE: {score:.1f}/100")
    print("-" * 80)
    for category, value in breakdown.items():
        print(f"  {category:20s}: {value}")

print("\n" + "=" * 80)
print("KEY INSIGHTS:")
print("=" * 80)

# Insights
best_match = results[0]
print(f"\n🏆 BEST MATCH: {best_match[0]} ({best_match[1]:.1f} points)")
print(f"   - Revenue+Employees alone: ~{sum(float(v.split('/')[0]) for k,v in best_match[2].items() if k in ['revenue', 'employees']):.0f} points")

shared_investors = [r for r in results if 'Vista' in str(r[2].get('investors', ''))]
if shared_investors:
    print(f"\n🤝 INVESTOR OVERLAP BONUS:")
    for name, score, _ in shared_investors:
        print(f"   - {name}: +12 points for shared Vista Equity backing")

print(f"\n📊 ALGORITHM EFFECTIVENESS:")
print(f"   - Top match: {results[0][0]} (direct competitor)")
print(f"   - Score spread: {results[0][1]:.1f} to {results[-1][1]:.1f} points")
print(f"   - Revenue+Employees = {((float(results[0][2]['revenue'].split('/')[0]) + float(results[0][2]['employees'].split('/')[0])) / results[0][1] * 100):.0f}% of top score")
