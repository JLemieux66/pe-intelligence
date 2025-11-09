import axios from 'axios'
import type { Company, PEFirm, Stats, CompanyFilters, LocationsResponse } from '../types/company'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const fetchStats = async (): Promise<Stats> => {
  const { data } = await api.get<Stats>('/stats')
  return data
}

export const fetchPEFirms = async (): Promise<PEFirm[]> => {
  const { data } = await api.get<PEFirm[]>('/pe-firms')
  return data
}

export const fetchLocations = async (): Promise<LocationsResponse> => {
  const { data } = await api.get<LocationsResponse>('/locations')
  return data
}

export const fetchCompanies = async (filters: CompanyFilters = {}): Promise<{ companies: Company[], totalCount: number }> => {
  const response = await api.get<Company[]>('/companies', { params: filters })
  const totalCount = parseInt(response.headers['x-total-count'] || '0', 10)
  return { companies: response.data, totalCount }
}

export const fetchCompanyById = async (id: string): Promise<Company> => {
  const { data } = await api.get<Company>(`/companies/${id}`)
  return data
}

export interface FundingRound {
  id: number
  announced_on: string | null
  investment_type: string | null
  money_raised_usd: number | null
  investor_names: string | null
  num_investors: number | null
}

export const fetchCompanyFundingRounds = async (companyId: number): Promise<FundingRound[]> => {
  const { data } = await api.get<FundingRound[]>(`/companies/${companyId}/funding-rounds`)
  return data
}

export const fetchIndustries = async (): Promise<string[]> => {
  // Fetch from new /api/industries endpoint which returns individual tags
  const response = await fetch(`${API_BASE_URL}/industries`)
  if (!response.ok) {
    throw new Error('Failed to fetch industries')
  }
  const data = await response.json()
  // Return array of industry names sorted alphabetically
  return data.industries.map((ind: { name: string; count: number }) => ind.name).sort()
}

export const fetchPitchBookMetadata = async (): Promise<{
  industry_groups: string[];
  industry_sectors: string[];
  verticals: string[];
}> => {
  const response = await fetch(`${API_BASE_URL}/pitchbook-metadata`)
  if (!response.ok) {
    throw new Error('Failed to fetch PitchBook metadata')
  }
  return await response.json()
}

export interface SimilarCompanyMatch {
  company: Company
  similarity_score: number
  reasoning: string
  matching_attributes: string[]
  score_breakdown?: {
    [category: string]: {
      score: number
      max_score: number
      available: boolean
      input_value?: string | number | null
      match_value?: string | number | null
      input_label?: string
      match_label?: string
    }
  }
  confidence?: number
}

export interface SimilarCompaniesResponse {
  input_companies: Company[]
  matches: SimilarCompanyMatch[]
  total_results: number
}

export const fetchSimilarCompanies = async (
  companyIds: number[],
  minScore: number = 30,
  limit: number = 10
): Promise<SimilarCompaniesResponse> => {
  const token = localStorage.getItem('admin_token')
  
  console.log('[fetchSimilarCompanies] Starting request', {
    companyIds,
    minScore,
    limit,
    hasToken: !!token,
    tokenPreview: token ? `${token.substring(0, 20)}...` : 'none',
    apiUrl: `${API_BASE_URL}/similar-companies`
  })

  try {
    console.log('[fetchSimilarCompanies] Making POST request...')
    
    const response = await api.post<SimilarCompaniesResponse>(
      '/similar-companies',
      {
        company_ids: companyIds,
        min_score: minScore,
        limit: limit,
      },
      {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
        timeout: 60000, // 60 second timeout (increased from 30s)
      }
    )
    
    console.log('[fetchSimilarCompanies] Response received', response.data)
    
    return response.data
  } catch (error: any) {
    console.error('[fetchSimilarCompanies] Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText,
      isTimeout: error.code === 'ECONNABORTED'
    })
    throw error
  }
}

export interface SimilarityFeedbackRequest {
  input_company_id: number
  match_company_id: number
  feedback_type: 'not_a_match' | 'good_match'
}

export const submitSimilarityFeedback = async (
  request: SimilarityFeedbackRequest
): Promise<{ success: boolean; message: string }> => {
  const token = localStorage.getItem('admin_token')
  
  console.log('[submitSimilarityFeedback] Submitting feedback', request)

  try {
    const response = await api.post(
      '/similar-companies/feedback',
      request,
      {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      }
    )
    
    console.log('[submitSimilarityFeedback] Success', response.data)
    return response.data
  } catch (error: any) {
    console.error('[submitSimilarityFeedback] Error:', error.response?.data || error.message)
    throw error
  }
}
