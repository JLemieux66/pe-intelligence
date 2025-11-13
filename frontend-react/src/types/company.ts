export interface Investment {
  investment_id: number  // Made required for proper indexing
  company_id: number
  company_name: string
  pe_firm_name: string
  status: string
  raw_status?: string
  exit_type?: string
  exit_info?: string
  exit_year?: string  // Year company exited (from edit modal)
  investment_year?: string
  sector?: string
  revenue_range?: string
  predicted_revenue?: number  // ML-predicted revenue in millions USD
  prediction_confidence?: number  // Confidence score 0-1
  employee_count?: string
  industry_category?: string  // Comma-separated string (legacy)
  industries?: string[]  // Array of individual industry tags (new)
  headquarters?: string
  website?: string
  linkedin_url?: string
  crunchbase_url?: string
  // Funding data
  total_funding_usd?: number
  num_funding_rounds?: number
  latest_funding_type?: string
  latest_funding_date?: string
  funding_stage_encoded?: number
  avg_round_size_usd?: number
  total_investors?: number
  // PitchBook data
  primary_industry_group?: string
  primary_industry_sector?: string
  verticals?: string
  current_revenue_usd?: number  // Revenue in millions USD
  hq_location?: string
  hq_country?: string
  last_known_valuation_usd?: number  // Valuation in millions USD
}

export interface Company {
  id: number
  name: string
  former_name?: string  // Former/previous company name (fka/formerly)
  pe_firms: string[]
  status: string
  exit_type?: string
  investment_year?: string
  headquarters?: string
  website?: string
  linkedin_url?: string
  crunchbase_url?: string
  description?: string
  revenue_range?: string
  predicted_revenue?: number  // ML-predicted revenue in millions USD
  prediction_confidence?: number  // Confidence score 0-1
  employee_count?: string  // Display value (best available)
  pitchbook_employee_count?: number  // PitchBook exact count
  crunchbase_employee_range?: string  // Crunchbase range (e.g., "501-1,000")
  scraped_employee_count?: number  // LinkedIn exact count
  industry_category?: string  // Comma-separated string (legacy)
  industries?: string[]  // Array of individual industry tags (new)
  // Funding data
  total_funding_usd?: number
  num_funding_rounds?: number
  latest_funding_type?: string
  latest_funding_date?: string
  funding_stage_encoded?: number
  avg_round_size_usd?: number
  total_investors?: number
  // Public company data
  is_public?: boolean
  stock_exchange?: string
  ipo_ticker?: string
  // PitchBook enrichment data
  investor_name?: string  // PE firm name from PitchBook
  investor_status?: string  // Active, Former, etc.
  investor_holding?: string  // Minority, Majority, etc.
  current_revenue_usd?: number  // Revenue in millions USD
  last_known_valuation_usd?: number  // Valuation in millions USD
  primary_industry_group?: string
  primary_industry_sector?: string
  hq_location?: string
  hq_country?: string
  last_financing_date?: string
  last_financing_size_usd?: number  // Financing size in millions USD
  last_financing_deal_type?: string
  verticals?: string
}

export interface PEFirm {
  id: number
  name: string
  total_investments: number
  active_count: number
  exit_count: number
}

export interface Stats {
  total_companies: number
  total_investments: number
  total_pe_firms: number
  active_investments: number
  exited_investments: number
  co_investments: number
  enrichment_rate: number
}

export type FilterOperator = 'AND' | 'OR'

export interface CompanyFilters {
  pe_firm?: string
  status?: string
  exit_type?: string
  industry?: string
  search?: string
  limit?: number
  offset?: number
  // PitchBook filters
  industry_group?: string
  industry_sector?: string
  verticals?: string
  // Location filters
  country?: string
  state_region?: string
  city?: string
  // Range filters
  min_revenue?: number
  max_revenue?: number
  min_employees?: number
  max_employees?: number
  min_confidence?: number
  is_public?: boolean  // Filter by public/private status
  // Data quality filters (IS EMPTY / IS NOT EMPTY)
  has_linkedin_url?: boolean  // true = has LinkedIn, false = missing LinkedIn
  has_website?: boolean  // true = has website, false = missing website
  has_revenue?: boolean  // true = has revenue data, false = missing revenue
  has_employees?: boolean  // true = has employee data, false = missing employee count
  has_description?: boolean  // true = has description, false = missing description
  // Date range filters
  founded_year_min?: number  // Minimum founded year
  founded_year_max?: number  // Maximum founded year
  investment_year_min?: number  // Minimum investment year
  investment_year_max?: number  // Maximum investment year
  // Filter operators
  filter_operator?: FilterOperator  // Global AND/OR for combining different filter types
  search_exact?: boolean  // Exact match for search text
  pe_firm_operator?: FilterOperator  // AND/OR for multiple PE firms
  industry_operator?: FilterOperator  // AND/OR for multiple industries
  industry_group_operator?: FilterOperator  // AND/OR for multiple industry groups
  industry_sector_operator?: FilterOperator  // AND/OR for multiple industry sectors
  verticals_operator?: FilterOperator  // AND/OR for multiple verticals
  country_operator?: FilterOperator  // AND/OR for multiple countries
  state_region_operator?: FilterOperator  // AND/OR for multiple states
  city_operator?: FilterOperator  // AND/OR for multiple cities
  // NOT operators (negation filters)
  pe_firm_not?: boolean  // Exclude companies with these PE firms
  industry_not?: boolean  // Exclude companies with these industries
  industry_group_not?: boolean  // Exclude companies with these industry groups
  industry_sector_not?: boolean  // Exclude companies with these industry sectors
  verticals_not?: boolean  // Exclude companies with these verticals
  country_not?: boolean  // Exclude companies in these countries
  state_region_not?: boolean  // Exclude companies in these states
  city_not?: boolean  // Exclude companies in these cities
}

export interface LocationData {
  name: string
  count: number
  country?: string  // For states/cities
  state?: string    // For cities
}

export interface LocationsResponse {
  countries: LocationData[]
  states: LocationData[]
  cities: LocationData[]
}
