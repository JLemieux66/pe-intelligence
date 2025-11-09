import { useState } from 'react'
import { useSimilarCompanies } from '../hooks/useCompanies'
import { TrendingUp, Building2, DollarSign, Users, MapPin, Target, X, ChevronDown, ChevronUp } from 'lucide-react'
import type { SimilarCompanyMatch } from '../api/client'
import { submitSimilarityFeedback } from '../api/client'

interface SimilarCompaniesTabProps {
  companyId: number
  onCompanyClick?: (companyId: number) => void
}

export default function SimilarCompaniesTab({ companyId, onCompanyClick }: SimilarCompaniesTabProps) {
  const [minScore, setMinScore] = useState(30)
  const [limit, setLimit] = useState(10)

  const { data, isLoading, error } = useSimilarCompanies([companyId], minScore, limit)

  // Debug logging
  console.log('[SimilarCompaniesTab] Component rendered', {
    companyId,
    minScore,
    limit,
    isLoading,
    error: error?.message,
    data
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-600 font-medium">Failed to load similar companies</p>
        <p className="text-red-500 text-sm mt-1">{error instanceof Error ? error.message : 'Unknown error'}</p>
        <p className="text-sm text-gray-600 mt-2">Make sure you're logged in and the API is running</p>
      </div>
    )
  }

  const matches = data?.matches || []
  const totalResults = data?.total_results || 0

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50/30 border border-purple-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg shadow-md">
              <Target className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                Similar Companies
              </h3>
              <p className="text-sm text-gray-600 mt-0.5">
                Comparable company analysis
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="font-semibold text-gray-900">{totalResults} matches found</span>
          </div>
        </div>

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-purple-200 shadow-sm">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Minimum Similarity Score
            </label>
            <select
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-lg text-base font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all cursor-pointer hover:border-purple-400"
            >
              <option value={20} className="text-base font-semibold text-gray-900">20% - Show More Results</option>
              <option value={30} className="text-base font-semibold text-gray-900">30% - Balanced (Default)</option>
              <option value={40} className="text-base font-semibold text-gray-900">40% - Higher Quality</option>
              <option value={50} className="text-base font-semibold text-gray-900">50% - Very Similar Only</option>
              <option value={60} className="text-base font-semibold text-gray-900">60% - Strict Matching</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Number of Results
            </label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-lg text-base font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all cursor-pointer hover:border-purple-400"
            >
              <option value={5} className="text-base font-semibold text-gray-900">Top 5 Companies</option>
              <option value={10} className="text-base font-semibold text-gray-900">Top 10 Companies</option>
              <option value={20} className="text-base font-semibold text-gray-900">Top 20 Companies</option>
              <option value={50} className="text-base font-semibold text-gray-900">Top 50 Companies</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results List */}
      {matches.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
          <Target className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">No similar companies found</p>
          <p className="text-sm text-gray-500 mt-1">Try lowering the minimum score threshold</p>
        </div>
      ) : (
        <div className="space-y-4">
          {matches.map((match: SimilarCompanyMatch, index: number) => (
            <SimilarCompanyCard
              key={match.company.id}
              match={match}
              rank={index + 1}
              inputCompanyId={companyId}
              onCompanyClick={onCompanyClick}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface SimilarCompanyCardProps {
  match: SimilarCompanyMatch
  rank: number
  inputCompanyId: number
  onCompanyClick?: (companyId: number) => void
}

function SimilarCompanyCard({ match, rank, inputCompanyId, onCompanyClick }: SimilarCompanyCardProps) {
  const { company, similarity_score, matching_attributes, score_breakdown, confidence } = match
  const [showQuickView, setShowQuickView] = useState(false)
  const [showScoreBreakdown, setShowScoreBreakdown] = useState(false)
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const handleNotAMatch = async () => {
    setIsSubmittingFeedback(true)
    try {
      await submitSimilarityFeedback({
        input_company_id: inputCompanyId,
        match_company_id: company.id,
        feedback_type: 'not_a_match'
      })
      setFeedbackSubmitted(true)
      // Show success state for a moment, then the card will be filtered out on next refresh
      setTimeout(() => {
        // In a production app, you might want to refetch similar companies here
        // or remove this card from the UI immediately
      }, 1000)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      alert('Failed to submit feedback. Please try again.')
    } finally {
      setIsSubmittingFeedback(false)
    }
  }

  // Determine score color
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'from-green-600 to-emerald-600'
    if (score >= 50) return 'from-blue-600 to-cyan-600'
    if (score >= 30) return 'from-amber-600 to-orange-600'
    return 'from-gray-600 to-slate-600'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 70) return 'bg-green-100 text-green-800 border-green-200'
    if (score >= 50) return 'bg-blue-100 text-blue-800 border-blue-200'
    if (score >= 30) return 'bg-amber-100 text-amber-800 border-amber-200'
    return 'bg-gray-100 text-gray-800 border-gray-200'
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden relative">
      {/* Quick View Card - Pops up on button click */}
      {showQuickView && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/20 z-40"
            onClick={() => setShowQuickView(false)}
          />
          
          {/* Quick View Modal */}
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-white rounded-2xl shadow-2xl border border-gray-300">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{company.name}</h3>
                  <div className="flex items-center gap-3">
                    {company.linkedin_url && (
                      <a
                        href={company.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                        </svg>
                        LinkedIn
                      </a>
                    )}
                    {company.website && (
                      <a
                        href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-gray-600 hover:underline flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        Website
                      </a>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setShowQuickView(false)}
                  className="text-gray-400 hover:text-gray-600 p-2"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Key Stats Grid */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                {(company.is_public || company.ipo_ticker) && (
                  <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                    <div className="text-xs text-green-600 mb-1 font-semibold">Public Company</div>
                    <div className="font-bold text-green-700">
                      {company.ipo_ticker || 'Publicly Traded'}
                      {company.stock_exchange && (
                        <span className="text-sm font-normal text-green-600 ml-1">
                          ({company.stock_exchange})
                        </span>
                      )}
                    </div>
                  </div>
                )}
                {company.primary_industry_group && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">Industry Group</div>
                    <div className="font-semibold text-gray-900">{company.primary_industry_group}</div>
                  </div>
                )}
                {company.headquarters && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">Location</div>
                    <div className="font-semibold text-gray-900">{company.headquarters}</div>
                  </div>
                )}
                {company.current_revenue_usd && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">Revenue (PitchBook)</div>
                    <div className="font-semibold text-gray-900">${company.current_revenue_usd.toFixed(1)}M</div>
                  </div>
                )}
                {company.employee_count && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">Employees</div>
                    <div className="font-semibold text-gray-900">{company.employee_count}</div>
                  </div>
                )}
              </div>

              {/* Description */}
              {company.description && (
                <div className="mb-6">
                  <div className="text-sm font-semibold text-gray-700 mb-2">About</div>
                  <p className="text-sm text-gray-600 leading-relaxed">{company.description}</p>
                </div>
              )}

              {/* Verticals */}
              {company.verticals && (
                <div className="mb-6">
                  <div className="text-sm font-semibold text-gray-700 mb-2">Verticals</div>
                  <div className="flex flex-wrap gap-2">
                    {company.verticals.split(',').map((vertical, idx) => (
                      <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-xs font-medium">
                        {vertical.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* PE Firms */}
              {company.pe_firms && company.pe_firms.length > 0 && (
                <div className="mb-6">
                  <div className="text-sm font-semibold text-gray-700 mb-2">PE Investors</div>
                  <div className="flex flex-wrap gap-2">
                    {company.pe_firms.map((firm, idx) => (
                      <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                        {firm}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowQuickView(false)
                    onCompanyClick?.(company.id)
                  }}
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition-colors"
                >
                  View Full Profile
                </button>
                <button
                  onClick={() => setShowQuickView(false)}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Main Card Content */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-4 flex-1">
            {/* Rank Badge */}
            <div className={`flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br ${getScoreColor(similarity_score)} flex items-center justify-center shadow-md`}>
              <span className="text-white font-bold text-lg">#{rank}</span>
            </div>

            {/* Company Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <h4
                  className="font-bold text-lg text-gray-900 hover:text-purple-600 cursor-pointer truncate transition-colors"
                  onClick={() => onCompanyClick?.(company.id)}
                  title="Click to view company details"
                >
                  {company.name}
                </h4>
                
                {/* LinkedIn Link */}
                {company.linkedin_url && (
                  <a
                    href={company.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 p-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
                    title="View on LinkedIn"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                  </a>
                )}
                
                {/* Website Link */}
                {company.website && (
                  <a
                    href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 p-1.5 text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                    title="Visit website"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>

              {/* Quick Stats */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600">
                {(company.is_public || company.ipo_ticker) && (
                  <div className="flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-green-600" />
                    <span className="font-semibold text-green-700">
                      {company.ipo_ticker || 'Public'}
                      {company.stock_exchange && ` (${company.stock_exchange})`}
                    </span>
                  </div>
                )}
                {company.primary_industry_group && (
                  <div className="flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5" />
                    <span>{company.primary_industry_group}</span>
                  </div>
                )}
                {company.headquarters && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{company.headquarters}</span>
                  </div>
                )}
                {company.employee_count && (
                  <div className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5" />
                    <span>{company.employee_count.toLocaleString()} employees</span>
                  </div>
                )}
                {company.current_revenue_usd && (
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-3.5 h-3.5" />
                    <span>${company.current_revenue_usd.toFixed(1)}M revenue</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Similarity Score */}
          <div className="flex-shrink-0 ml-4">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border ${getScoreBgColor(similarity_score)} font-bold`}>
              <TrendingUp className="w-4 h-4" />
              <span>{Math.round(similarity_score)}%</span>
            </div>
          </div>
        </div>

        {/* Matching Attributes - Show all */}
        {matching_attributes.length > 0 && (
          <div className="mb-3">
            <h6 className="text-xs font-semibold text-gray-700 mb-2">Matching Criteria:</h6>
            <div className="flex flex-wrap gap-2">
              {matching_attributes.map((attr, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-purple-50 text-purple-700 rounded-lg text-xs font-medium border border-purple-100"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                  {attr}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Score Breakdown */}
        {score_breakdown && (
          <div className="mb-3 border-t border-gray-100 pt-3">
            <button
              onClick={() => setShowScoreBreakdown(!showScoreBreakdown)}
              className="flex items-center gap-2 text-xs font-semibold text-gray-700 hover:text-purple-600 transition-colors"
            >
              {showScoreBreakdown ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              Score Breakdown
              {confidence !== undefined && (
                <span className="ml-1 px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                  {Math.round(confidence)}% data available
                </span>
              )}
            </button>
            
            {showScoreBreakdown && (
              <div className="mt-3 space-y-3">
                {Object.entries(score_breakdown).map(([category, details]) => {
                  const percentage = details.max_score > 0 ? (details.score / details.max_score) * 100 : 0
                  return (
                    <div key={category} className="space-y-1.5 p-3 bg-gray-50 rounded-lg border border-gray-100">
                      {/* Category Header */}
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-gray-800 capitalize">
                          {category.replace(/_/g, ' ')}
                        </span>
                        <span className={`font-bold ${details.available ? 'text-gray-900' : 'text-gray-400'}`}>
                          {details.score.toFixed(1)} / {details.max_score.toFixed(0)}
                          {!details.available && ' (N/A)'}
                        </span>
                      </div>
                      
                      {/* Progress Bar */}
                      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            !details.available
                              ? 'bg-gray-400'
                              : percentage >= 70
                              ? 'bg-green-500'
                              : percentage >= 40
                              ? 'bg-blue-500'
                              : 'bg-amber-500'
                          }`}
                          style={{ width: `${Math.min(100, percentage)}%` }}
                        />
                      </div>
                      
                      {/* Side-by-Side Comparison */}
                      {details.input_value !== undefined && details.match_value !== undefined && (
                        <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                          <div className="flex flex-col">
                            <span className="text-gray-500 font-medium mb-0.5">
                              {details.input_label || 'Input Company'}
                            </span>
                            <span className="text-gray-900 font-semibold truncate" title={String(details.input_value || 'N/A')}>
                              {details.input_value || 'N/A'}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-gray-500 font-medium mb-0.5">
                              {details.match_label || 'This Match'}
                            </span>
                            <span className="text-gray-900 font-semibold truncate" title={String(details.match_value || 'N/A')}>
                              {details.match_value || 'N/A'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowQuickView(true)}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            Quick Preview
          </button>
          
          {feedbackSubmitted ? (
            <div className="px-4 py-2 bg-green-100 text-green-700 text-sm font-semibold rounded-lg flex items-center gap-2 border border-green-200">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Feedback Sent
            </div>
          ) : (
            <button
              onClick={handleNotAMatch}
              disabled={isSubmittingFeedback}
              className="px-4 py-2 bg-gray-100 hover:bg-red-50 text-gray-700 hover:text-red-700 text-sm font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-2 border border-gray-200 hover:border-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Mark as not a match to improve future results"
            >
              <X className="w-4 h-4" />
              {isSubmittingFeedback ? 'Submitting...' : 'Not a Match'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
