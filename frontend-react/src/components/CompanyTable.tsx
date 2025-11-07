import { useState } from 'react'
import { ArrowUpDown, ExternalLink, Building2, MapPin, Users, DollarSign, Edit2, Download, GitMerge } from 'lucide-react'
import type { Investment } from '../types/company'
import CompanyEditModal from './CompanyEditModal'
import CompanyMergeModal from './CompanyMergeModal'

interface CompanyTableProps {
  investments: Investment[]
  loading: boolean
  onCompanyClick: (companyId: number) => void
  onExportCSV: () => void
  onRefresh?: () => void
}

type SortField = 'company_name' | 'pe_firm_name' | 'status' | 'industry_category' | 'headquarters' | 'employee_count' | 'revenue_range' | 'predicted_revenue' | 'prediction_confidence'
type SortDirection = 'asc' | 'desc'

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

// Company logo component
const CompanyLogo = ({ website, name }: { website: string | null | undefined; name: string }) => {
  const [logoError, setLogoError] = useState(false)
  const domain = extractDomain(website)
  const logoUrl = domain ? `https://logo.clearbit.com/${domain}` : null

  if (logoUrl && !logoError) {
    return (
      <img
        src={logoUrl}
        alt={`${name} logo`}
        onError={() => setLogoError(true)}
        className="w-6 h-6 object-contain rounded flex-shrink-0"
      />
    )
  }

  // Fallback to initials
  return (
    <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded flex items-center justify-center text-white font-bold text-xs flex-shrink-0">
      {getInitials(name)}
    </div>
  )
}

export default function CompanyTable({ investments, loading, onCompanyClick, onExportCSV, onRefresh }: CompanyTableProps) {
  const [sortField, setSortField] = useState<SortField>('company_name')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [editingInvestment, setEditingInvestment] = useState<Investment | null>(null)
  const [mergingCompany, setMergingCompany] = useState<Investment | null>(null)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedInvestments = [...investments].sort((a, b) => {
    // Handle numeric sorting for employee count
    if (sortField === 'employee_count') {
      const aNum = parseInt(a.employee_count || '0')
      const bNum = parseInt(b.employee_count || '0')
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum
    }
    
    // Handle numeric sorting for predicted revenue
    if (sortField === 'predicted_revenue') {
      const aNum = a.predicted_revenue || 0
      const bNum = b.predicted_revenue || 0
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum
    }
    
    // Handle numeric sorting for confidence
    if (sortField === 'prediction_confidence') {
      const aNum = a.prediction_confidence || 0
      const bNum = b.prediction_confidence || 0
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum
    }
    
    // String comparison
    const aValue = a[sortField] || ''
    const bValue = b[sortField] || ''
    const comparison = String(aValue).localeCompare(String(bValue))
    return sortDirection === 'asc' ? comparison : -comparison
  })

  const SortButton = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center space-x-1 hover:text-blue-600 transition-colors"
    >
      <span>{label}</span>
      <ArrowUpDown className={`w-4 h-4 ${sortField === field ? 'text-blue-600' : 'text-gray-400'}`} />
    </button>
  )

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="animate-pulse p-6">
          <div className="h-10 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (investments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">No companies found</p>
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                <SortButton field="company_name" label="Company" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-32">
                Industry Sector
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-32">
                Industry Group
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-32">
                Verticals
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                <SortButton field="employee_count" label="Employees" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-32">
                PitchBook Revenue
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                <SortButton field="revenue_range" label="Crunchbase Revenue" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                <SortButton field="predicted_revenue" label="Predicted Revenue" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                <SortButton field="prediction_confidence" label="Confidence" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">
                <SortButton field="headquarters" label="HQ" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 tracking-wider w-16">
                Links
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">
                <div className="flex items-center gap-2">
                  Actions
                  {onExportCSV && (
                    <div 
                      className="cursor-pointer"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation()
                        onExportCSV()
                      }}
                      title={`Export ${investments.length} companies to CSV`}
                    >
                      <Download className="w-4 h-4 text-emerald-600 hover:text-emerald-500 transition-colors" />
                    </div>
                  )}
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedInvestments.map((investment, index) => (
              <tr 
                key={`${investment.company_name}-${index}`} 
                className="hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => onCompanyClick?.(investment.company_id)}
              >
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    <CompanyLogo website={investment.website} name={investment.company_name} />
                    <span className="font-medium text-gray-900 text-sm break-words">{investment.company_name}</span>
                  </div>
                </td>
                {/* Industry Sector */}
                <td className="px-3 py-3">
                  {investment.primary_industry_sector ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-yellow-100 text-yellow-800">
                      {investment.primary_industry_sector}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400">N/A</span>
                  )}
                </td>
                
                {/* Industry Group */}
                <td className="px-3 py-3">
                  {investment.primary_industry_group ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-emerald-100 text-emerald-800">
                      {investment.primary_industry_group}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400">N/A</span>
                  )}
                </td>
                
                {/* Verticals */}
                <td className="px-3 py-3">
                  {investment.verticals ? (
                    <div className="flex flex-wrap gap-1">
                      {investment.verticals.split(',').slice(0, 2).map((vertical: string, idx: number) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                        >
                          {vertical.trim()}
                        </span>
                      ))}
                      {investment.verticals.split(',').length > 2 && (
                        <span
                          className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-50 text-gray-600 border border-gray-200 cursor-help"
                          title={investment.verticals}
                        >
                          +{investment.verticals.split(',').length - 2}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400">N/A</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center text-sm text-gray-700">
                    <Users className="w-3 h-3 text-gray-400 mr-1 flex-shrink-0" />
                    <span className="whitespace-nowrap">{investment.employee_count || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  {investment.current_revenue_usd ? (
                    <div className="flex items-center">
                      <DollarSign className="w-3 h-3 text-gray-400 mr-1 flex-shrink-0" />
                      <span className="text-sm font-semibold text-purple-600">
                        {investment.current_revenue_usd >= 1000
                          ? `$${(investment.current_revenue_usd / 1000).toFixed(1)}B`
                          : `$${investment.current_revenue_usd.toFixed(1)}M`
                        }
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">N/A</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-start text-sm text-gray-700">
                    <DollarSign className="w-3 h-3 text-gray-400 mr-1 mt-0.5 flex-shrink-0" />
                    <span className="break-words text-xs">{investment.revenue_range || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  {investment.predicted_revenue ? (
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center">
                        <span className="text-sm font-semibold text-indigo-600">
                          {investment.predicted_revenue >= 1000000000
                            ? `$${(investment.predicted_revenue / 1000000000).toFixed(1)}B`
                            : `$${(investment.predicted_revenue / 1000000).toFixed(1)}M`
                          }
                        </span>
                      </div>
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M13 7H7v6h6V7z" />
                          <path fillRule="evenodd" d="M7 2a1 1 0 012 0v1h2V2a1 1 0 112 0v1h2a2 2 0 012 2v2h1a1 1 0 110 2h-1v2h1a1 1 0 110 2h-1v2a2 2 0 01-2 2h-2v1a1 1 0 11-2 0v-1H9v1a1 1 0 11-2 0v-1H5a2 2 0 01-2-2v-2H2a1 1 0 110-2h1V9H2a1 1 0 010-2h1V5a2 2 0 012-2h2V2zM5 5h10v10H5V5z" clipRule="evenodd" />
                        </svg>
                        AI
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">N/A</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  {investment.prediction_confidence ? (
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${
                          investment.prediction_confidence >= 0.8 ? 'bg-green-500' :
                          investment.prediction_confidence >= 0.6 ? 'bg-yellow-500' :
                          'bg-orange-500'
                        }`} />
                        <span className={`text-sm font-medium ${
                          investment.prediction_confidence >= 0.8 ? 'text-green-700' :
                          investment.prediction_confidence >= 0.6 ? 'text-yellow-700' :
                          'text-orange-700'
                        }`}>
                          {(investment.prediction_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            investment.prediction_confidence >= 0.8 ? 'bg-green-500' :
                            investment.prediction_confidence >= 0.6 ? 'bg-yellow-500' :
                            'bg-orange-500'
                          }`}
                          style={{ width: `${investment.prediction_confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">N/A</span>
                  )}
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-start text-sm text-gray-700">
                    <MapPin className="w-3 h-3 text-gray-400 mr-1 mt-0.5 flex-shrink-0" />
                    <span className="break-words">{investment.headquarters || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex space-x-2">
                    {investment.website && (
                      <a
                        href={investment.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                        title="Website"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                    {investment.linkedin_url && (
                      <a
                        href={investment.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                        title="LinkedIn"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                        </svg>
                      </a>
                    )}
                    {investment.crunchbase_url && (
                      <a
                        href={investment.crunchbase_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center w-4 h-4 bg-[#0288D1] text-white text-[9px] font-bold rounded hover:bg-[#0277BD] transition-colors"
                        title="Crunchbase"
                        onClick={(e) => e.stopPropagation()}
                      >
                        CB
                      </a>
                    )}
                  </div>
                </td>

                {/* Actions Column */}
                <td className="px-3 py-2 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setEditingInvestment(investment)
                      }}
                      className="text-gray-600 hover:text-blue-600 transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setMergingCompany(investment)
                      }}
                      className="text-gray-600 hover:text-orange-600 transition-colors"
                      title="Merge Company"
                    >
                      <GitMerge className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {editingInvestment && (
        <CompanyEditModal
          company={{
            id: editingInvestment.company_id,
            name: editingInvestment.company_name,
            website: editingInvestment.website,
            linkedin_url: editingInvestment.linkedin_url,
            crunchbase_url: editingInvestment.crunchbase_url,
            headquarters: editingInvestment.headquarters,
            industry_category: editingInvestment.industry_category,
            revenue_range: editingInvestment.revenue_range,
            employee_count: editingInvestment.employee_count,
            status: editingInvestment.status,
            exit_type: editingInvestment.exit_type,
            pe_firms: [editingInvestment.pe_firm_name],
            // PitchBook data
            primary_industry_group: editingInvestment.primary_industry_group,
            primary_industry_sector: editingInvestment.primary_industry_sector,
            verticals: editingInvestment.verticals,
            current_revenue_usd: editingInvestment.current_revenue_usd,
            hq_location: (editingInvestment as any).hq_location,
            hq_country: (editingInvestment as any).hq_country,
            last_known_valuation_usd: (editingInvestment as any).last_known_valuation_usd,
            is_public: (editingInvestment as any).is_public,
            stock_exchange: (editingInvestment as any).stock_exchange,
            description: (editingInvestment as any).description,
          } as any}
          investment={editingInvestment.investment_id ? editingInvestment : undefined}
          onClose={() => setEditingInvestment(null)}
        />
      )}

      {/* Merge Modal */}
      {mergingCompany && (
        <CompanyMergeModal
          sourceCompany={mergingCompany}
          allCompanies={investments}
          onClose={() => setMergingCompany(null)}
          onMerge={async (sourceId: number, targetId: number) => {
            const response = await fetch(`/api/companies/merge?source_id=${sourceId}&target_id=${targetId}`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
            })
            
            if (!response.ok) {
              const error = await response.json()
              throw new Error(error.detail || 'Failed to merge companies')
            }
            
            // Refresh the data
            if (onRefresh) {
              onRefresh()
            }
          }}
        />
      )}
    </div>
    </>
  )
}
