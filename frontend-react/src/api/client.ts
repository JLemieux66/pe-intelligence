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
