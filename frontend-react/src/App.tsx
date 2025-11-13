import { useState, useEffect, useCallback } from 'react'
import { TrendingUp, LogIn, LogOut, Plus } from 'lucide-react'
import { useStats, usePEFirms, useCompanies } from './hooks/useCompanies'
import { fetchCompanies } from './api/client'
import DashboardWidgets from './components/DashboardWidgets'
import CompanyTable from './components/CompanyTable'
import CompanyModal from './components/CompanyModal'
import CompanyCreateModal from './components/CompanyCreateModal'
import LoginModal from './components/LoginModal'
import HorizontalFilters from './components/HorizontalFilters'
import Pagination from './components/Pagination'
import { exportToCSV } from './utils/csvExport'
import type { CompanyFilters, Investment } from './types/company'

function App() {
  const [filters, setFilters] = useState<CompanyFilters>({ limit: 25, offset: 0 })
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null)
  const [showLoginModal, setShowLoginModal] = useState(true) // Show login by default
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)
  const [adminEmail, setAdminEmail] = useState<string | null>(null)
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: peFirms, isLoading: peFirmsLoading } = usePEFirms()
  const { data: companiesData, isLoading: companiesLoading, refetch: refetchCompanies } = useCompanies(filters)

  const companies = companiesData?.companies || []
  const totalCount = companiesData?.totalCount || 0

  // Convert Company format to Investment format for backwards compatibility
  const investments: Investment[] = companies?.map(company => ({
    investment_id: company.id,  // Use company.id as investment_id for display
    company_id: company.id,
    company_name: company.name,
    pe_firm_name: company.pe_firms[0] || '', // Take first PE firm for display
    status: company.status,
    exit_type: company.exit_type,
    investment_year: company.investment_year,
    headquarters: company.headquarters,
    website: company.website,
    linkedin_url: company.linkedin_url,
    crunchbase_url: company.crunchbase_url,
    revenue_range: company.revenue_range,
    employee_count: company.employee_count,
    industry_category: company.industry_category,
    industries: company.industries || [],
    predicted_revenue: company.predicted_revenue,
    prediction_confidence: company.prediction_confidence,
    // Funding data
    total_funding_usd: company.total_funding_usd,
    num_funding_rounds: company.num_funding_rounds,
    latest_funding_type: company.latest_funding_type,
    latest_funding_date: company.latest_funding_date,
    funding_stage_encoded: company.funding_stage_encoded,
    avg_round_size_usd: company.avg_round_size_usd,
    total_investors: company.total_investors,
    // PitchBook data
    primary_industry_group: company.primary_industry_group,
    primary_industry_sector: company.primary_industry_sector,
    verticals: company.verticals,
    current_revenue_usd: company.current_revenue_usd,
  })) || []

  // Check for existing admin session on mount
  useEffect(() => {
    const token = localStorage.getItem('admin_token')
    const email = localStorage.getItem('admin_email')
    if (token && email) {
      setIsAdmin(true)
      setAdminEmail(email)
      setShowLoginModal(false) // Hide login modal if already logged in
    }
  }, [])

  const handleFilterChange = useCallback((newFilters: CompanyFilters) => {
    setFilters({ ...newFilters, limit: 25, offset: 0 })
    setCurrentPage(1)
  }, [])

  const handlePageChange = (newPage: number) => {
    const newOffset = (newPage - 1) * 25
    
    // Update both state values together
    setCurrentPage(newPage)
    const newFilters = { ...filters, limit: 25, offset: newOffset }
    setFilters(newFilters)
    
    // Instantly jump to top of page
    window.scrollTo(0, 0)
  }

  const handleExportCSV = async () => {
    try {
      // Create filters without pagination to get all results
      const exportFilters = { ...filters }
      delete exportFilters.limit
      delete exportFilters.offset
      
      // Fetch all filtered companies
      const { companies: allCompanies } = await fetchCompanies(exportFilters)
      
      // Convert to Investment format
      const allInvestments: Investment[] = allCompanies.map((company: any) => ({
        investment_id: company.id,
        company_id: company.id,
        company_name: company.name,
        pe_firm_name: company.pe_firms[0] || '',
        status: company.status,
        exit_type: company.exit_type,
        investment_year: company.investment_year,
        headquarters: company.headquarters,
        website: company.website,
        linkedin_url: company.linkedin_url,
        crunchbase_url: company.crunchbase_url,
        revenue_range: company.revenue_range,
        employee_count: company.employee_count,
        industry_category: company.industry_category,
        industries: company.industries || [],
        predicted_revenue: company.predicted_revenue,
        prediction_confidence: company.prediction_confidence,
        total_funding_usd: company.total_funding_usd,
        num_funding_rounds: company.num_funding_rounds,
        latest_funding_type: company.latest_funding_type,
        latest_funding_date: company.latest_funding_date,
        funding_stage_encoded: company.funding_stage_encoded,
        avg_round_size_usd: company.avg_round_size_usd,
        total_investors: company.total_investors,
        primary_industry_group: company.primary_industry_group,
        primary_industry_sector: company.primary_industry_sector,
        verticals: company.verticals,
        current_revenue_usd: company.current_revenue_usd,
      }))
      
      if (allInvestments.length > 0) {
        exportToCSV(allInvestments, 'pe-portfolio')
      }
    } catch (error) {
      console.error('Error exporting CSV:', error)
      alert('Failed to export data. Please try again.')
    }
  }

  const handleLoginSuccess = (_token: string, email: string) => {
    setIsAdmin(true)
    setAdminEmail(email)
    setShowLoginModal(false) // Close login modal on success
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_email')
    setIsAdmin(false)
    setAdminEmail(null)
    setShowLoginModal(true) // Show login modal after logout
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-slate-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 shadow-lg">
        <div className="px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="absolute inset-0 bg-blue-500 blur-lg opacity-50 rounded-full"></div>
                <TrendingUp className="relative w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  Portfolio<span className="text-blue-400">Intel</span>
                </h1>
                <p className="text-xs text-blue-300 font-medium">Private Equity Intelligence Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {isAdmin ? (
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium shadow-lg shadow-blue-500/30"
                  >
                    <Plus className="w-4 h-4" />
                    Add Company
                  </button>
                  <span className="text-sm text-blue-200">{adminEmail}</span>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-colors text-sm backdrop-blur-sm border border-white/20"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-400 transition-colors text-sm shadow-lg shadow-blue-500/50"
                >
                  <LogIn className="w-4 h-4" />
                  Admin Login
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Dashboard Content - Only show if logged in */}
      {isAdmin ? (
        <div className="px-4 sm:px-6 lg:px-8 py-8">
          {statsLoading ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                  <div className="h-12 bg-gray-200 rounded w-3/4 mb-4"></div>
                  <div className="h-24 bg-gray-200 rounded w-full"></div>
                </div>
              ))}
            </div>
          ) : stats && (
            <DashboardWidgets stats={stats} peFirms={peFirms || []} />
          )}

          {/* Horizontal Filters */}
          <HorizontalFilters
            peFirms={peFirms || []}
            peFirmsLoading={peFirmsLoading}
            onFilterChange={handleFilterChange}
          />

          {/* Company Table */}
          <CompanyTable
            investments={investments || []}
            loading={companiesLoading}
            onCompanyClick={setSelectedCompanyId}
            onExportCSV={handleExportCSV}
            onRefresh={refetchCompanies}
          />

          {/* Pagination Controls */}
          {companies && companies.length > 0 && (
            <Pagination
              currentPage={currentPage}
              totalItems={totalCount}
              itemsPerPage={25}
              onPageChange={handlePageChange}
              offset={filters.offset || 0}
            />
          )}
        </div>
      ) : (
        <div className="px-4 sm:px-6 lg:px-8 py-20">
          <div className="max-w-md mx-auto text-center">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <LogIn className="w-16 h-16 text-blue-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Login Required</h2>
              <p className="text-gray-600 mb-6">Please login to access the portfolio dashboard</p>
              <button
                onClick={() => setShowLoginModal(true)}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Login to Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Company Detail Modal */}
      {selectedCompanyId && (
        <CompanyModal
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
        />
      )}

      {/* Company Create Modal */}
      {showCreateModal && (
        <CompanyCreateModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            refetchCompanies()
          }}
        />
      )}

      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLoginSuccess={handleLoginSuccess}
          allowClose={isAdmin}  // Only allow closing if already logged in (re-login scenario)
        />
      )}
    </div>
  )
}

export default App
