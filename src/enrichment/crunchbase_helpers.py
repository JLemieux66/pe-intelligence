"""
Crunchbase API helper functions
"""
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

CRUNCHBASE_API_KEY = os.getenv('CRUNCHBASE_API_KEY')
CRUNCHBASE_BASE_URL = "https://api.crunchbase.com/v4/data"

# Rate limiting
CALL_DELAY = 2.0  # 2 second delay between calls to avoid hitting limits

# Revenue range mappings
REVENUE_RANGES = {
    "r_00000000": "Less than $1M",
    "r_00001000": "$1M - $10M",
    "r_00010000": "$10M - $50M",
    "r_00050000": "$50M - $100M",
    "r_00100000": "$100M - $500M",
    "r_00500000": "$500M - $1B",
    "r_01000000": "$1B - $10B",
    "r_10000000": "$10B+"
}

# Employee count mappings
EMPLOYEE_RANGES = {
    "c_00001_00010": "1-10",
    "c_00011_00050": "11-50",
    "c_00051_00100": "51-100",
    "c_00101_00250": "101-250",
    "c_00251_00500": "251-500",
    "c_00501_01000": "501-1,000",
    "c_01001_05000": "1,001-5,000",
    "c_05001_10000": "5,001-10,000",
    "c_10001_max": "10,001+"
}

def decode_revenue_range(code):
    """Convert Crunchbase revenue code to readable string"""
    return REVENUE_RANGES.get(code, code if code else "N/A")

def decode_employee_count(code):
    """Convert Crunchbase employee code to readable string"""
    return EMPLOYEE_RANGES.get(code, code if code else "N/A")

def search_company_crunchbase(company_name, retry=True):
    """Search for company in Crunchbase with retry logic"""
    try:
        url = f"{CRUNCHBASE_BASE_URL}/autocompletes"
        params = {
            "query": company_name,
            "collection_ids": "organizations",
            "user_key": CRUNCHBASE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Handle rate limiting
        if response.status_code == 429:
            if retry:
                print(f"      ⚠️  Rate limit hit, waiting 5 seconds...")
                time.sleep(5)
                return search_company_crunchbase(company_name, retry=False)
            return []
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        entities = data.get("entities", [])
        
        if entities:
            # Add small delay to avoid hitting rate limits
            time.sleep(CALL_DELAY)
            return entities[0].get("identifier", {}).get("permalink", "")
        
        return ""
    except Exception as e:
        # Log the error but don't crash
        # print(f"      Error searching Crunchbase: {e}")
        return []

def get_company_details_crunchbase(entity_id, retry=True):
    """Get company details from Crunchbase with retry logic"""
    try:
        url = f"{CRUNCHBASE_BASE_URL}/entities/organizations/{entity_id}"
        params = {
            "user_key": CRUNCHBASE_API_KEY,
            "field_ids": "location_identifiers,founded_on,short_description,revenue_range,num_employees_enum,linkedin,categories,category_groups"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        # Handle rate limiting
        if response.status_code == 429:
            if retry:
                print(f"      ⚠️  Rate limit hit, waiting 5 seconds...")
                time.sleep(5)
                return get_company_details_crunchbase(entity_id, retry=False)
            return {}
        
        if response.status_code != 200:
            return {}
        
        data = response.json()
        properties = data.get("properties", {})
        
        # Extract headquarters
        hq = ""
        location_ids = properties.get("location_identifiers", [])
        if location_ids and len(location_ids) > 0:
            city = next((loc.get("value") for loc in location_ids if loc.get("location_type") == "city"), "")
            region = next((loc.get("value") for loc in location_ids if loc.get("location_type") == "region"), "")
            
            if city and region:
                hq = f"{city}, {region}"
            elif city:
                hq = city
            elif region:
                hq = region
        
        # Extract founded year
        founded_on = properties.get("founded_on", {})
        founded_year = ""
        if founded_on and isinstance(founded_on, dict):
            value = founded_on.get("value", "")
            if value and len(value) >= 4:
                founded_year = value[:4]
        
        # Extract LinkedIn URL
        linkedin_url = ""
        linkedin_data = properties.get("linkedin", {})
        if linkedin_data and isinstance(linkedin_data, dict):
            linkedin_url = linkedin_data.get("value", "")
            # Convert to full URL if it's just the identifier
            if linkedin_url and not linkedin_url.startswith("http"):
                linkedin_url = f"https://www.linkedin.com/company/{linkedin_url}"
        
        # Extract categories and map to industry_category
        industry_category = map_crunchbase_category_to_industry(properties)
        
        # Add small delay to avoid hitting rate limits
        time.sleep(CALL_DELAY)
        
        return {
            "headquarters": hq,
            "founded_year": founded_year,
            "description": properties.get("short_description", ""),
            "revenue_range": properties.get("revenue_range", ""),
            "employee_count": properties.get("num_employees_enum", ""),
            "linkedin_url": linkedin_url,
            "industry_category": industry_category
        }
    except Exception as e:
        # Log the error but don't crash
        # print(f"      Error getting Crunchbase details: {e}")
        return {}

def map_crunchbase_category_to_industry(properties):
    """
    Map Crunchbase categories to our standardized industry_category values
    
    Our categories:
    - Technology & Software
    - Financial Services
    - Healthcare & Biotech
    - E-commerce & Retail
    - Media & Entertainment
    - Marketing & Advertising
    - Education & HR
    - Manufacturing & Industrial
    - Energy & Sustainability
    - Transportation & Automotive
    - Real Estate & Construction
    - Communication & Collaboration
    - Artificial Intelligence & Data
    - Blockchain & Crypto
    - Consulting & Services
    - Legal & Compliance
    - Government & Public Sector
    - Agriculture & Food
    - Other
    """
    categories = properties.get("categories", [])
    category_groups = properties.get("category_groups", [])
    
    # Extract category values (handle both string and dict formats)
    cat_values = []
    for cat in categories:
        if isinstance(cat, dict):
            cat_values.append(cat.get("value", "").lower())
        else:
            cat_values.append(str(cat).lower())
    
    for grp in category_groups:
        if isinstance(grp, dict):
            cat_values.append(grp.get("value", "").lower())
        else:
            cat_values.append(str(grp).lower())
    
    # Mapping rules (order matters - more specific first)
    
    # Financial Services
    if any(term in cat_values for term in ["financial services", "finance", "fintech", "banking", "payments", "insurance", "lending", "wealth management", "trading", "investment"]):
        return "Financial Services"
    
    # Healthcare & Biotech
    if any(term in cat_values for term in ["health care", "healthcare", "medical", "biotech", "biotechnology", "pharmaceuticals", "hospital", "clinical", "wellness", "therapeutics"]):
        return "Healthcare & Biotech"
    
    # Artificial Intelligence & Data
    if any(term in cat_values for term in ["artificial intelligence", "machine learning", "data", "analytics", "big data", "ai", "ml"]):
        return "Artificial Intelligence & Data"
    
    # Blockchain & Crypto
    if any(term in cat_values for term in ["blockchain", "cryptocurrency", "crypto", "web3", "nft", "defi"]):
        return "Blockchain & Crypto"
    
    # E-commerce & Retail
    if any(term in cat_values for term in ["e-commerce", "ecommerce", "retail", "shopping", "marketplace", "consumer goods"]):
        return "E-commerce & Retail"
    
    # Media & Entertainment
    if any(term in cat_values for term in ["media", "entertainment", "gaming", "video", "music", "publishing", "streaming", "content"]):
        return "Media & Entertainment"
    
    # Marketing & Advertising
    if any(term in cat_values for term in ["marketing", "advertising", "ad tech", "adtech", "social media marketing", "digital marketing"]):
        return "Marketing & Advertising"
    
    # Education & HR
    if any(term in cat_values for term in ["education", "edtech", "learning", "training", "human resources", "hr", "recruiting", "talent"]):
        return "Education & HR"
    
    # Communication & Collaboration
    if any(term in cat_values for term in ["communication", "collaboration", "messaging", "video conferencing", "productivity", "workflow"]):
        return "Communication & Collaboration"
    
    # Energy & Sustainability
    if any(term in cat_values for term in ["energy", "renewable", "sustainability", "clean tech", "cleantech", "solar", "environmental"]):
        return "Energy & Sustainability"
    
    # Transportation & Automotive
    if any(term in cat_values for term in ["transportation", "automotive", "mobility", "logistics", "delivery", "shipping", "fleet"]):
        return "Transportation & Automotive"
    
    # Real Estate & Construction
    if any(term in cat_values for term in ["real estate", "construction", "property", "housing"]):
        return "Real Estate & Construction"
    
    # Manufacturing & Industrial
    if any(term in cat_values for term in ["manufacturing", "industrial", "supply chain", "hardware", "machinery"]):
        return "Manufacturing & Industrial"
    
    # Legal & Compliance
    if any(term in cat_values for term in ["legal", "compliance", "regulatory", "legaltech"]):
        return "Legal & Compliance"
    
    # Government & Public Sector
    if any(term in cat_values for term in ["government", "public sector", "govtech", "civic"]):
        return "Government & Public Sector"
    
    # Agriculture & Food
    if any(term in cat_values for term in ["agriculture", "food", "farming", "agtech"]):
        return "Agriculture & Food"
    
    # Consulting & Services
    if any(term in cat_values for term in ["consulting", "professional services", "business services"]):
        return "Consulting & Services"
    
    # Technology & Software (broad fallback for tech)
    if any(term in cat_values for term in ["software", "saas", "technology", "internet", "mobile", "apps", "platform", "cloud", "api", "developer"]):
        return "Technology & Software"
    
    # Default
    return "Other"

def enrich_company_with_crunchbase(company_name: str) -> dict:
    """
    Main function to enrich a company with Crunchbase data
    
    Args:
        company_name: Name of the company to search for
    
    Returns:
        Dictionary with enriched data or empty dict if not found
    """
    # Search for company
    results = search_company_crunchbase(company_name)
    
    if not results or not results[0]:
        return {}
    
    entity_id = results[0]
    
    # Get detailed information (already processed)
    details = get_company_details_crunchbase(entity_id)
    
    if not details:
        return {}
    
    # The details are already processed, just return them
    # They already have the correct keys: linkedin_url, revenue_range, employee_count, etc.
    return details


