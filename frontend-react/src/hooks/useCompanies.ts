import { useQuery } from '@tanstack/react-query'
import { fetchStats, fetchPEFirms, fetchCompanies, fetchIndustries, fetchLocations, fetchPitchBookMetadata } from '../api/client'
import type { CompanyFilters } from '../types/company'

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  })
}

export const usePEFirms = () => {
  return useQuery({
    queryKey: ['pe-firms'],
    queryFn: fetchPEFirms,
    staleTime: 10 * 60 * 1000, // 10 minutes - cache PE firms data
  })
}

export const useLocations = () => {
  return useQuery({
    queryKey: ['locations'],
    queryFn: fetchLocations,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const useCompanies = (filters: CompanyFilters = {}) => {
  return useQuery({
    queryKey: ['companies', JSON.stringify(filters)],
    queryFn: () => fetchCompanies(filters),
    placeholderData: (previousData) => previousData,
  })
}

export const useIndustries = () => {
  return useQuery({
    queryKey: ['industries'],
    queryFn: fetchIndustries,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const usePitchBookMetadata = () => {
  return useQuery({
    queryKey: ['pitchbook-metadata'],
    queryFn: fetchPitchBookMetadata,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}
