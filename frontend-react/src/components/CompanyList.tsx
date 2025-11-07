import { ExternalLink, Building, TrendingUp, TrendingDown } from 'lucide-react'
import type { Investment } from '../types/company'

interface CompanyListProps {
  investments: Investment[]
  isLoading: boolean
  onCompanyClick?: (companyId: number) => void
}

export default function CompanyList({ investments, isLoading, onCompanyClick }: CompanyListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(9)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!investments || investments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <Building className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No companies found matching your filters.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          {investments.length} {investments.length === 1 ? 'Company' : 'Companies'}
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {investments.map((investment) => (
          <div 
            key={`${investment.company_id}-${investment.pe_firm_name}`} 
            className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 cursor-pointer"
            onClick={() => onCompanyClick?.(investment.company_id)}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {investment.company_name}
                </h3>
                <p className="text-sm text-gray-600">{investment.pe_firm_name}</p>
              </div>
              <div className="flex items-center">
                {investment.status === 'Active' ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    <TrendingDown className="w-3 h-3 mr-1" />
                    Exit
                  </span>
                )}
              </div>
            </div>

            {/* Exit Info */}
            {investment.exit_type && (
              <div className="mb-4">
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  {investment.exit_type}
                </span>
                {investment.exit_info && (
                  <p className="text-xs text-gray-500 mt-1">{investment.exit_info}</p>
                )}
              </div>
            )}

            {/* Details */}
            <div className="space-y-2 text-sm">
              {investment.industry_category && (
                <div className="flex items-center text-gray-600">
                  <span className="font-medium mr-2">Industry:</span>
                  <span>{investment.industry_category}</span>
                </div>
              )}
              {investment.headquarters && (
                <div className="flex items-center text-gray-600">
                  <span className="font-medium mr-2">HQ:</span>
                  <span>{investment.headquarters}</span>
                </div>
              )}
              {investment.employee_count && (
                <div className="flex items-center text-gray-600">
                  <span className="font-medium mr-2">Employees:</span>
                  <span>{investment.employee_count}</span>
                </div>
              )}
              {(investment.revenue_range || investment.predicted_revenue) && (
                <div className="space-y-1">
                  {investment.revenue_range && (
                    <div className="flex items-center text-gray-600">
                      <span className="font-medium mr-2">Revenue (CB):</span>
                      <span>{investment.revenue_range}</span>
                    </div>
                  )}
                  {investment.predicted_revenue && (
                    <div className="flex items-center text-gray-600">
                      <span className="font-medium mr-2">Revenue (ML):</span>
                      <span className="text-blue-600 font-medium">
                        {investment.predicted_revenue >= 1_000_000_000
                          ? `$${(investment.predicted_revenue / 1_000_000_000).toFixed(1)}B`
                          : investment.predicted_revenue >= 1_000_000
                          ? `$${(investment.predicted_revenue / 1_000_000).toFixed(0)}M`
                          : `$${(investment.predicted_revenue / 1_000).toFixed(0)}K`
                        }
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Links */}
            <div className="mt-4 pt-4 border-t border-gray-200 flex space-x-3">
              {investment.linkedin_url && (
                <a
                  href={investment.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  LinkedIn
                </a>
              )}
              {investment.website && (
                <a
                  href={investment.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <ExternalLink className="w-3 h-3 mr-1" />
                  Website
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
