import { Building2, TrendingUp, Target } from 'lucide-react'
import type { Stats, PEFirm } from '../types/company'

interface DashboardWidgetsProps {
  stats: Stats
  peFirms: PEFirm[]
}

export default function DashboardWidgets({ stats, peFirms }: DashboardWidgetsProps) {
  // Calculate percentages for visual bars
  const activePercentage = (stats.active_investments / stats.total_investments) * 100
  const exitedPercentage = (stats.exited_investments / stats.total_investments) * 100
  
  // Get top 5 PE firms by total investments
  const topPEFirms = [...peFirms]
    .sort((a, b) => b.total_investments - a.total_investments)
    .slice(0, 5)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      {/* Database Overview Widget */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Database Overview</h3>
          <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-md">
            <Building2 className="w-5 h-5 text-white" />
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Total Companies - Large */}
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-blue-500 bg-clip-text text-transparent">
                {stats.total_companies.toLocaleString()}
              </span>
              <span className="text-sm text-gray-500">companies</span>
            </div>
          </div>

          {/* PE Firms - Total */}
          <div className="pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-600">PE Firms</span>
              <span className="text-xl font-bold text-purple-600">{stats.total_pe_firms}</span>
            </div>
          </div>

          {/* Top PE Firms Breakdown */}
          <div className="space-y-2">
            <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Top 5 by Companies</div>
            {topPEFirms.map((firm, index) => {
              const percentage = (firm.total_investments / stats.total_investments) * 100
              return (
                <div key={firm.id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-700 font-medium truncate pr-2">{firm.name}</span>
                    <span className="text-gray-900 font-semibold">{firm.total_investments}</span>
                  </div>
                  <div className="relative h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${
                        index === 0 ? 'bg-gradient-to-r from-purple-500 to-indigo-500' :
                        index === 1 ? 'bg-gradient-to-r from-purple-400 to-indigo-400' :
                        index === 2 ? 'bg-gradient-to-r from-purple-300 to-indigo-300' :
                        index === 3 ? 'bg-gradient-to-r from-purple-200 to-indigo-200' :
                        'bg-gradient-to-r from-purple-100 to-indigo-100'
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Investment Status Widget */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Investment Status</h3>
          <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg shadow-md">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
        </div>

        <div className="space-y-4">
          {/* Active Investments */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Active</span>
              </div>
              <span className="text-2xl font-bold text-green-600">{stats.active_investments.toLocaleString()}</span>
            </div>
            <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-500 shadow-lg shadow-green-500/50"
                style={{ width: `${activePercentage}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1 text-right">{activePercentage.toFixed(1)}% of data</div>
          </div>

          {/* Exited Investments */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Exited</span>
              </div>
              <span className="text-2xl font-bold text-gray-600">{stats.exited_investments.toLocaleString()}</span>
            </div>
            <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-gray-400 to-gray-500 rounded-full transition-all duration-500"
                style={{ width: `${exitedPercentage}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1 text-right">{exitedPercentage.toFixed(1)}% of data</div>
          </div>

          {/* Total Investments Count */}
          <div className="pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Total Investments</span>
              <span className="text-lg font-bold text-gray-900">{stats.total_investments.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Data Quality Widget */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Data Enrichment</h3>
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-md">
            <Target className="w-5 h-5 text-white" />
          </div>
        </div>

        <div className="space-y-4">
          {/* Enrichment Rate - Large Display */}
          <div>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                {stats.enrichment_rate.toFixed(1)}%
              </span>
              <span className="text-sm text-gray-500">enriched</span>
            </div>
            
            {/* Circular Progress */}
            <div className="relative w-32 h-32 mx-auto mb-3">
              <svg className="transform -rotate-90 w-32 h-32">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  className="text-gray-200"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="url(#gradient)"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 56}`}
                  strokeDashoffset={`${2 * Math.PI * 56 * (1 - stats.enrichment_rate / 100)}`}
                  className="transition-all duration-1000 ease-out"
                  strokeLinecap="round"
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {Math.round((stats.total_companies * stats.enrichment_rate) / 100).toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500">companies</div>
                </div>
              </div>
            </div>
          </div>

          {/* Enrichment Stats */}
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">With LinkedIn</div>
              <div className="text-lg font-bold text-indigo-600">
                {Math.round((stats.total_companies * stats.enrichment_rate) / 100).toLocaleString()}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Missing Data</div>
              <div className="text-lg font-bold text-gray-400">
                {(stats.total_companies - Math.round((stats.total_companies * stats.enrichment_rate) / 100)).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
