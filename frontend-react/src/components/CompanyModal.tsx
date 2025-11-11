import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchCompanyById, fetchCompanyFundingRounds } from '../api/client'
import { useState } from 'react'
import CompanyEditModal from './CompanyEditModal'
import FundingTimeline from './FundingTimeline'
import SimilarCompaniesTab from './SimilarCompaniesTab'
import axios from 'axios'

interface CompanyModalProps {
  companyId: number
  onClose: () => void
  onNavigateToCompany?: (companyId: number) => void
}

// Check if admin is logged in
const isAdminLoggedIn = () => {
  return !!localStorage.getItem('admin_token')
}

// Helper function to get funding stage label
const getFundingStageLabel = (stage: number | undefined): string | null => {
  if (stage === undefined || stage === null) return null
  const stages: Record<number, string> = {
    0: 'Pre-Seed',
    1: 'Seed',
    2: 'Series A',
    3: 'Series B',
    4: 'Series C',
    5: 'Series D+',
    6: 'Late Stage / PE',
    7: 'IPO'
  }
  return stages[stage] || 'Unknown'
}

// Helper function to extract domain from URL
const extractDomain = (url: string | null | undefined): string | null => {
  if (!url) return null
  try {
    const domain = url.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0]
    return domain
  } catch {
    return null
  }
}

// Helper function to get company initials
const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export default function CompanyModal({ companyId, onClose, onNavigateToCompany }: CompanyModalProps) {
  const [logoError, setLogoError] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [fundingView, setFundingView] = useState<'timeline' | 'list'>('timeline')
  const [activeTab, setActiveTab] = useState<'overview' | 'funding' | 'pitchbook' | 'similar'>('overview')
  
  const queryClient = useQueryClient()
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

  // Mutation to re-run ML prediction
  const enrichMutation = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem('admin_token')
      const response = await axios.post(
        `${API_BASE_URL}/ml/enrich/company/${companyId}`,
        {},
        {
          headers: {
            Authorization: token ? `Bearer ${token}` : '',
          },
        }
      )
      return response.data
    },
    onSuccess: () => {
      // Refetch company data to show updated prediction
      queryClient.invalidateQueries({ queryKey: ['company', companyId] })
    },
  })
  
  const { data: company, isLoading, error } = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompanyById(companyId.toString()),
  })

  // Fetch funding rounds
  const { data: fundingRounds = [] } = useQuery({
    queryKey: ['fundingRounds', companyId],
    queryFn: () => fetchCompanyFundingRounds(companyId),
    enabled: !!company, // Only fetch when company data is loaded
  })

  // Debug logging
  if (company) {
    console.log('=== COMPANY MODAL DATA ===')
    console.log('Company ID:', companyId)
    console.log('Company Name:', company.name)
    console.log('prediction_confidence:', company.prediction_confidence)
    console.log('predicted_revenue:', company.predicted_revenue)
    console.log('total_funding_usd:', company.total_funding_usd)
    console.log('num_funding_rounds:', company.num_funding_rounds)
    console.log('latest_funding_type:', company.latest_funding_type)
    console.log('funding_stage_encoded:', company.funding_stage_encoded)
    console.log('Full company object:', company)
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading company details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Error</h2>
          <p className="text-gray-600 mb-4">Could not load company details.</p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  const domain = extractDomain(company.website)
  const logoUrl = domain ? `https://logo.clearbit.com/${domain}` : null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto shadow-2xl company-modal-scroll">
        {/* Header - Gradient */}
        <div className="sticky top-0 bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 px-6 py-5 flex items-center justify-between z-50">
          <div className="flex items-center gap-4">
            {/* Company Logo */}
            {logoUrl && !logoError ? (
              <div className="relative">
                <div className="absolute inset-0 bg-blue-400 blur-xl opacity-50 rounded-full"></div>
                <img
                  src={logoUrl}
                  alt={`${company.name} logo`}
                  onError={() => setLogoError(true)}
                  className="relative w-14 h-14 object-contain rounded-lg bg-white p-2"
                />
              </div>
            ) : (
              <div className="relative">
                <div className="absolute inset-0 bg-blue-400 blur-xl opacity-50 rounded-full"></div>
                <div className="relative w-14 h-14 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-lg">
                  {getInitials(company.name)}
                </div>
              </div>
            )}
            <div>
              <h2 className="text-2xl font-bold text-white">{company.name}</h2>
              {company.former_name && (
                <p className="text-sm text-blue-200/80 mt-0.5 italic">
                  Formerly: {company.former_name}
                </p>
              )}
              {company.headquarters && (
                <p className="text-sm text-blue-200 mt-0.5">{company.headquarters}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status and Industry Badges */}
          <div className="flex flex-wrap gap-2">
            {/* PE Firm tags */}
            {company.pe_firms && company.pe_firms.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {company.pe_firms.map((firm, idx) => (
                  <span key={idx} className="px-3 py-1 bg-slate-100 text-slate-800 rounded-full text-sm font-medium border border-slate-300">
                    {firm}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            {company.website && (
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-lg hover:from-blue-500 hover:to-blue-400 flex items-center text-sm font-medium shadow-lg shadow-blue-500/30 transition-all"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Website
              </a>
            )}
            
            {company.linkedin_url && (
              <a
                href={company.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-gradient-to-r from-[#0077B5] to-[#005582] text-white rounded-lg hover:from-[#006399] hover:to-[#004466] flex items-center text-sm font-medium shadow-lg shadow-blue-600/30 transition-all"
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
                LinkedIn
              </a>
            )}
            
            {company.crunchbase_url && (
              <a
                href={company.crunchbase_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-gradient-to-r from-[#0288D1] to-[#0277BD] text-white rounded-lg hover:from-[#0277BD] hover:to-[#0266AA] flex items-center text-sm font-medium shadow-lg shadow-cyan-500/30 transition-all"
              >
                <div className="w-4 h-4 mr-2 bg-white rounded flex items-center justify-center text-[9px] font-bold text-[#0288D1]">
                  CB
                </div>
                Crunchbase
              </a>
            )}
            
            {/* Admin Edit Button */}
            {isAdminLoggedIn() && (
              <button
                onClick={() => setShowEditModal(true)}
                className="px-4 py-2 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-lg hover:from-slate-500 hover:to-slate-600 flex items-center text-sm font-medium shadow-lg shadow-slate-500/30 transition-all"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit
              </button>
            )}
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 bg-white sticky top-[88px] z-40">
            <nav className="flex space-x-1" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-6 py-3 text-sm font-semibold transition-all relative ${
                  activeTab === 'overview'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Overview
                </div>
              </button>
              
              <button
                onClick={() => setActiveTab('funding')}
                className={`px-6 py-3 text-sm font-semibold transition-all relative ${
                  activeTab === 'funding'
                    ? 'text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Funding
                  {fundingRounds.length > 0 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
                      {fundingRounds.length}
                    </span>
                  )}
                </div>
              </button>
              
              {(company.current_revenue_usd || company.last_known_valuation_usd || company.investor_name ||
                company.primary_industry_group || company.last_financing_size_usd) && (
                <button
                  onClick={() => setActiveTab('pitchbook')}
                  className={`px-6 py-3 text-sm font-semibold transition-all relative ${
                    activeTab === 'pitchbook'
                      ? 'text-emerald-600 border-b-2 border-emerald-600'
                      : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    PitchBook
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                      Premium
                    </span>
                  </div>
                </button>
              )}

              <button
                onClick={() => setActiveTab('similar')}
                className={`px-6 py-3 text-sm font-semibold transition-all relative ${
                  activeTab === 'similar'
                    ? 'text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Similar Companies
                </div>
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Revenue Section - Show Actual or AI Prediction */}
              {(company.current_revenue_usd || company.predicted_revenue) && (
            <div className={`border-2 rounded-xl p-6 shadow-lg ${
              company.current_revenue_usd 
                ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-200'
                : 'bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 border-indigo-200'
            }`}>
              <div className="flex items-center gap-2 mb-4">
                <div className={`p-2.5 rounded-lg shadow-lg ${
                  company.current_revenue_usd
                    ? 'bg-gradient-to-br from-green-600 to-emerald-600 shadow-green-500/50'
                    : 'bg-gradient-to-br from-indigo-600 to-purple-600 shadow-indigo-500/50'
                }`}>
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    {company.current_revenue_usd ? (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    ) : (
                      <>
                        <path d="M13 7H7v6h6V7z" />
                        <path fillRule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clipRule="evenodd" />
                      </>
                    )}
                  </svg>
                </div>
                <h3 className={`text-lg font-bold bg-clip-text text-transparent ${
                  company.current_revenue_usd
                    ? 'bg-gradient-to-r from-green-900 via-emerald-900 to-teal-900'
                    : 'bg-gradient-to-r from-indigo-900 via-purple-900 to-pink-900'
                }`}>
                  {company.current_revenue_usd ? 'Actual Revenue' : 'AI Revenue Prediction'}
                </h3>
                <div className="ml-auto flex items-center gap-2">
                  {!company.current_revenue_usd && isAdminLoggedIn() && (
                    <button
                      onClick={() => enrichMutation.mutate()}
                      disabled={enrichMutation.isPending}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {enrichMutation.isPending ? 'Re-running...' : 'Re-run ML'}
                    </button>
                  )}
                  {company.current_revenue_usd ? (
                    <span className="text-xs px-3 py-1 rounded-full font-semibold shadow-md text-white bg-gradient-to-r from-green-600 to-emerald-600">
                      Verified
                    </span>
                  ) : (
                    <span className="text-xs px-3 py-1 rounded-full font-semibold shadow-md text-white bg-gradient-to-r from-indigo-600 to-purple-600">
                      ML-Powered
                    </span>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Revenue Amount */}
                <div>
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                    {company.current_revenue_usd ? 'Revenue' : 'Predicted Revenue'}
                  </p>
                  <p className={`text-3xl font-bold bg-gradient-to-r bg-clip-text text-transparent ${
                    company.current_revenue_usd
                      ? 'from-green-600 via-emerald-600 to-teal-600'
                      : 'from-indigo-600 via-purple-600 to-pink-600'
                  }`}>
                    {company.current_revenue_usd ? (
                      company.current_revenue_usd >= 1000 
                        ? `$${(company.current_revenue_usd / 1000).toFixed(1)}B`
                        : `$${company.current_revenue_usd.toFixed(1)}M`
                    ) : company.predicted_revenue ? (
                      company.predicted_revenue >= 1000 
                        ? `$${(company.predicted_revenue / 1000).toFixed(1)}B`
                        : `$${company.predicted_revenue.toFixed(1)}M`
                    ) : 'N/A'}
                  </p>
                </div>

                {/* Confidence Score - Only for AI predictions */}
                {!company.current_revenue_usd && company.prediction_confidence !== undefined && company.prediction_confidence !== null && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Confidence Score</p>
                    <div className="space-y-1.5">
                      <div className="relative h-2.5 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`absolute inset-y-0 left-0 rounded-full transition-all ${
                            company.prediction_confidence >= 0.8 
                              ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                              : company.prediction_confidence >= 0.6
                              ? 'bg-gradient-to-r from-yellow-500 to-amber-500'
                              : 'bg-gradient-to-r from-orange-500 to-red-500'
                          }`}
                          style={{ width: `${company.prediction_confidence * 100}%` }}
                        />
                      </div>
                      
                      {/* Confidence Label */}
                      <div className="flex items-center gap-1.5">
                        {company.prediction_confidence >= 0.8 ? (
                          <>
                            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-sm text-green-700 font-semibold">High</span>
                          </>
                        ) : company.prediction_confidence >= 0.6 ? (
                          <>
                            <svg className="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            <span className="text-sm text-yellow-700 font-semibold">Medium</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <span className="text-sm text-red-700 font-semibold">Low</span>
                          </>
                        )}
                        <span className="text-xs text-gray-600 ml-1">
                          ({(company.prediction_confidence * 100).toFixed(0)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Company Information */}
            <div className="bg-gradient-to-br from-slate-50 to-blue-50/30 border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg shadow-md">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">Company Info</h3>
              </div>
              <dl className="space-y-3">
                {company.description && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">About</dt>
                    <dd className="text-sm text-gray-700 leading-relaxed mt-1">{company.description}</dd>
                  </div>
                )}

                {company.headquarters && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Headquarters</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.headquarters}</dd>
                  </div>
                )}

                {company.investment_year && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Investment Year</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.investment_year}</dd>
                  </div>
                )}
                
                {company.exit_type && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Exit Type</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                        {company.exit_type}
                      </span>
                    </dd>
                  </div>
                )}

                {(company.pitchbook_employee_count || company.scraped_employee_count || company.crunchbase_employee_range) && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Employees</dt>
                    <dd className="text-sm text-gray-900 mt-1 space-y-1.5">
                      {company.pitchbook_employee_count && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600 font-medium">{company.pitchbook_employee_count.toLocaleString()}</span>
                          <span className="text-xs text-white bg-gradient-to-r from-orange-600 to-red-600 px-2 py-1 rounded-md font-semibold shadow-sm">PitchBook</span>
                        </div>
                      )}
                      {company.scraped_employee_count && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600 font-medium">{company.scraped_employee_count.toLocaleString()}</span>
                          {company.linkedin_url ? (
                            <a
                              href={company.linkedin_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-white bg-gradient-to-r from-[#0077B5] to-[#005582] hover:from-[#006399] hover:to-[#004466] px-2 py-1 rounded-md font-semibold shadow-sm transition-all"
                            >
                              LinkedIn
                            </a>
                          ) : (
                            <span className="text-xs text-white bg-gradient-to-r from-[#0077B5] to-[#005582] px-2 py-1 rounded-md font-semibold shadow-sm">LinkedIn</span>
                          )}
                        </div>
                      )}
                      {company.crunchbase_employee_range && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600 font-medium">{company.crunchbase_employee_range}</span>
                          <span className="text-xs text-white bg-gradient-to-r from-blue-600 to-cyan-600 px-2 py-1 rounded-md font-semibold shadow-sm">Crunchbase</span>
                        </div>
                      )}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Funding Information */}
            <div className="bg-gradient-to-br from-purple-50 to-indigo-50/30 border border-purple-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg shadow-md">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold bg-gradient-to-r from-purple-900 to-indigo-700 bg-clip-text text-transparent">Funding</h3>
              </div>
              <dl className="space-y-3">
                {/* Total Funding - Large Display */}
                {company.total_funding_usd && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Raised</dt>
                    <dd className="text-2xl font-bold text-purple-600 mt-1">
                      ${(company.total_funding_usd / 1000000).toFixed(1)}M
                    </dd>
                  </div>
                )}

                {/* 2-column grid for compact info */}
                <div className="grid grid-cols-2 gap-3 pt-2">
                  {company.funding_stage_encoded !== undefined && company.funding_stage_encoded !== null && (
                    <div>
                      <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Stage</dt>
                      <dd className="text-sm text-gray-900 font-medium mt-0.5">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-semibold text-xs">
                          {getFundingStageLabel(company.funding_stage_encoded)}
                        </span>
                      </dd>
                    </div>
                  )}

                  {company.num_funding_rounds && (
                    <div>
                      <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Rounds</dt>
                      <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.num_funding_rounds}</dd>
                    </div>
                  )}

                  {company.total_investors && (
                    <div>
                      <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Investors</dt>
                      <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.total_investors}</dd>
                    </div>
                  )}

                  {company.avg_round_size_usd && (
                    <div>
                      <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Avg Round</dt>
                      <dd className="text-sm text-gray-900 font-medium mt-0.5">
                        ${(company.avg_round_size_usd / 1000000).toFixed(1)}M
                      </dd>
                    </div>
                  )}
                </div>

                {/* Latest Round - Full Width */}
                {company.latest_funding_type && (
                  <div className="pt-2">
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Latest Round</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5 flex items-center gap-2 flex-wrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 font-semibold">
                        {company.latest_funding_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                      {company.latest_funding_date && (
                        <span className="text-xs text-gray-500">
                          {new Date(company.latest_funding_date).toLocaleDateString()}
                        </span>
                      )}
                    </dd>
                  </div>
                )}

                {/* Crunchbase Revenue Range */}
                {company.revenue_range && (
                  <div className="pt-2 border-t border-purple-200">
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Crunchbase Revenue Range</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.revenue_range}</dd>
                  </div>
                )}
                
              </dl>
            </div>
          </div>
            </div>
          )}

          {/* Funding Tab */}
          {activeTab === 'funding' && (
            <div className="space-y-6">
              {/* Funding Stats Summary */}
              {(company.total_funding_usd || company.num_funding_rounds || company.latest_funding_type) && (
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50/30 border border-purple-200 rounded-xl p-5 shadow-sm">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {company.total_funding_usd && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Total Raised</dt>
                        <dd className="text-2xl font-bold text-purple-600 mt-1">
                          ${(company.total_funding_usd / 1000000).toFixed(1)}M
                        </dd>
                      </div>
                    )}
                    
                    {company.num_funding_rounds && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Funding Rounds</dt>
                        <dd className="text-2xl font-bold text-indigo-600 mt-1">
                          {company.num_funding_rounds}
                        </dd>
                      </div>
                    )}
                    
                    {company.latest_funding_type && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Latest Round</dt>
                        <dd className="text-sm text-gray-900 font-medium mt-1">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 font-semibold">
                            {company.latest_funding_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                        </dd>
                      </div>
                    )}
                  </div>
                </div>
              )}

          {/* Funding Timeline - Full Width Section */}
          {fundingRounds.length > 0 && (
            <div className="bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50/30 border-2 border-blue-200 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg shadow-lg shadow-blue-500/50">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold bg-gradient-to-r from-blue-900 via-purple-900 to-pink-900 bg-clip-text text-transparent">Funding Timeline</h3>
                  <span className="ml-2 text-xs bg-gradient-to-r from-blue-600 to-purple-600 text-white px-3 py-1 rounded-full font-semibold shadow-md">
                    {fundingRounds.length} Round{fundingRounds.length > 1 ? 's' : ''}
                  </span>
                </div>

                {/* View Toggle */}
                <div className="flex items-center gap-2 bg-white rounded-lg p-1 shadow-md border border-gray-200">
                  <button
                    onClick={() => setFundingView('timeline')}
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 ${
                      fundingView === 'timeline'
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Timeline
                  </button>
                  <button
                    onClick={() => setFundingView('list')}
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 ${
                      fundingView === 'list'
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    List
                  </button>
                </div>
              </div>

              {/* Timeline View */}
              {fundingView === 'timeline' && (
                <FundingTimeline rounds={fundingRounds} />
              )}

              {/* List View */}
              {fundingView === 'list' && (
                <div className="space-y-3">
                  {[...fundingRounds].sort((a, b) => {
                    const dateA = a.announced_on ? new Date(a.announced_on).getTime() : 0
                    const dateB = b.announced_on ? new Date(b.announced_on).getTime() : 0
                    return dateB - dateA // Newest first
                  }).map((round) => (
                    <div key={round.id} className="bg-white rounded-lg p-4 border-2 border-purple-100 hover:border-purple-300 shadow-sm hover:shadow-md transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-purple-100 text-purple-800">
                          {round.investment_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown'}
                        </span>
                        {round.announced_on && (
                          <span className="text-sm text-gray-500 font-medium">
                            {new Date(round.announced_on).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-base mb-2">
                        <span className="font-bold text-gray-900">
                          {round.money_raised_usd 
                            ? `$${(round.money_raised_usd / 1000000).toFixed(1)}M`
                            : 'Undisclosed'}
                        </span>
                        {round.num_investors && round.num_investors > 0 && (
                          <span className="text-sm text-gray-500 font-medium">
                            {round.num_investors} investor{round.num_investors > 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                      {round.investor_names && (
                        <div className="text-sm text-gray-600 leading-relaxed">
                          <span className="font-semibold text-gray-700">Investors:</span> {round.investor_names}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
            </div>
          )}

          {/* PitchBook Tab */}
          {activeTab === 'pitchbook' && (
            <div className="space-y-6">
          {/* PitchBook Data Section */}
          {(company.current_revenue_usd || company.last_known_valuation_usd || company.investor_name || 
            company.primary_industry_group || company.last_financing_size_usd) && (
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50/30 border border-emerald-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-lg shadow-md">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold bg-gradient-to-r from-emerald-900 to-teal-700 bg-clip-text text-transparent">PitchBook Data</h3>
                <span className="ml-auto text-xs bg-gradient-to-r from-emerald-600 to-teal-600 text-white px-3 py-1 rounded-full font-semibold shadow-md">Premium</span>
              </div>
              
              <dl className="space-y-3">
                {/* Revenue & Valuation - Large Display */}
                {(company.current_revenue_usd || company.last_known_valuation_usd) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-3 border-b border-emerald-200">
                    {company.current_revenue_usd && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Current Revenue</dt>
                        <dd className="text-2xl font-bold text-emerald-600 mt-1">
                          ${company.current_revenue_usd >= 1000 
                            ? `${(company.current_revenue_usd / 1000).toFixed(1)}B`
                            : `${company.current_revenue_usd.toFixed(0)}M`
                          }
                        </dd>
                      </div>
                    )}
                    
                    {company.last_known_valuation_usd && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Valuation</dt>
                        <dd className="text-2xl font-bold text-teal-600 mt-1">
                          ${company.last_known_valuation_usd >= 1000 
                            ? `${(company.last_known_valuation_usd / 1000).toFixed(1)}B`
                            : `${company.last_known_valuation_usd.toFixed(0)}M`
                          }
                        </dd>
                      </div>
                    )}
                  </div>
                )}

                {/* Investor Information */}
                {(company.investor_name || company.investor_status || company.investor_holding) && (
                  <div className="space-y-2">
                    {company.investor_name && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Investor</dt>
                        <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.investor_name}</dd>
                      </div>
                    )}
                    <div className="flex gap-2 flex-wrap">
                      {company.investor_status && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold text-xs">
                          {company.investor_status}
                        </span>
                      )}
                      {company.investor_holding && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 font-semibold text-xs">
                          {company.investor_holding}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Industry Classifications */}
                {(company.primary_industry_group || company.primary_industry_sector) && (
                  <div className="space-y-2">
                    {company.primary_industry_group && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Industry Group</dt>
                        <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.primary_industry_group}</dd>
                      </div>
                    )}
                    {company.primary_industry_sector && (
                      <div>
                        <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Industry Sector</dt>
                        <dd className="text-sm text-gray-900 font-medium mt-0.5">{company.primary_industry_sector}</dd>
                      </div>
                    )}
                  </div>
                )}

                {/* Verticals */}
                {company.verticals && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Verticals</dt>
                    <dd className="text-sm text-gray-700 mt-0.5">{company.verticals}</dd>
                  </div>
                )}

                {/* Last Financing */}
                {(company.last_financing_size_usd || company.last_financing_deal_type || company.last_financing_date) && (
                  <div className="pt-2 border-t border-emerald-200">
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Last Financing</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5 flex items-center gap-2 flex-wrap">
                      {company.last_financing_size_usd && (
                        <span className="text-emerald-700 font-bold">
                          ${company.last_financing_size_usd >= 1000 
                            ? `${(company.last_financing_size_usd / 1000).toFixed(1)}B`
                            : `${company.last_financing_size_usd.toFixed(0)}M`
                          }
                        </span>
                      )}
                      {company.last_financing_deal_type && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold text-xs">
                          {company.last_financing_deal_type}
                        </span>
                      )}
                      {company.last_financing_date && (
                        <span className="text-xs text-gray-500">
                          {new Date(company.last_financing_date).toLocaleDateString()}
                        </span>
                      )}
                    </dd>
                  </div>
                )}

                {/* HQ Location (PitchBook version) */}
                {(company.hq_location || company.hq_country) && (
                  <div>
                    <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wide">PB Headquarters</dt>
                    <dd className="text-sm text-gray-900 font-medium mt-0.5">
                      {[company.hq_location, company.hq_country].filter(Boolean).join(', ')}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}
            </div>
          )}

          {/* Similar Companies Tab */}
          {activeTab === 'similar' && (
            <div className="space-y-6">
              <SimilarCompaniesTab companyId={companyId} onCompanyClick={(id) => {
                if (onNavigateToCompany) {
                  onNavigateToCompany(id);
                }
              }} />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full md:w-auto px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
      
      {/* Edit Modal - Opens on top of company modal */}
      {showEditModal && (
        <CompanyEditModal
          company={company}
          onClose={() => setShowEditModal(false)}
        />
      )}
    </div>
  )
}
