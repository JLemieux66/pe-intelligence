import { format } from 'date-fns'

interface FundingRound {
  id: number
  announced_on: string | null
  investment_type: string | null
  money_raised_usd: number | null
  investor_names: string | null
  num_investors: number | null
}

interface FundingTimelineProps {
  rounds: FundingRound[]
}

// Map investment types to colors with full Tailwind classes
const getTypeColors = (type: string | null): {
  dot: string
  dotPing: string
  border: string
  borderHover: string
  badge: string
  text: string
  investor: string
  investorBadge: string
  bgNumber: string
} => {
  if (!type) {
    return {
      dot: 'bg-gradient-to-br from-gray-400 to-gray-600',
      dotPing: 'bg-gray-400',
      border: 'border-gray-100',
      borderHover: 'hover:border-gray-300',
      badge: 'bg-gradient-to-r from-gray-500 to-gray-600',
      text: 'from-gray-600 to-gray-700',
      investor: 'text-gray-500',
      investorBadge: 'bg-gray-100 text-gray-800',
      bgNumber: 'text-gray-600'
    }
  }
  
  const typeLower = type.toLowerCase()
  
  if (typeLower.includes('seed') || typeLower.includes('angel')) {
    return {
      dot: 'bg-gradient-to-br from-emerald-400 to-emerald-600',
      dotPing: 'bg-emerald-400',
      border: 'border-emerald-100',
      borderHover: 'hover:border-emerald-300',
      badge: 'bg-gradient-to-r from-emerald-500 to-emerald-600',
      text: 'from-emerald-600 to-emerald-700',
      investor: 'text-emerald-500',
      investorBadge: 'bg-emerald-100 text-emerald-800',
      bgNumber: 'text-emerald-600'
    }
  }
  
  if (typeLower.includes('series_a')) {
    return {
      dot: 'bg-gradient-to-br from-blue-400 to-blue-600',
      dotPing: 'bg-blue-400',
      border: 'border-blue-100',
      borderHover: 'hover:border-blue-300',
      badge: 'bg-gradient-to-r from-blue-500 to-blue-600',
      text: 'from-blue-600 to-blue-700',
      investor: 'text-blue-500',
      investorBadge: 'bg-blue-100 text-blue-800',
      bgNumber: 'text-blue-600'
    }
  }
  
  if (typeLower.includes('series_b')) {
    return {
      dot: 'bg-gradient-to-br from-indigo-400 to-indigo-600',
      dotPing: 'bg-indigo-400',
      border: 'border-indigo-100',
      borderHover: 'hover:border-indigo-300',
      badge: 'bg-gradient-to-r from-indigo-500 to-indigo-600',
      text: 'from-indigo-600 to-indigo-700',
      investor: 'text-indigo-500',
      investorBadge: 'bg-indigo-100 text-indigo-800',
      bgNumber: 'text-indigo-600'
    }
  }
  
  if (typeLower.includes('series_c')) {
    return {
      dot: 'bg-gradient-to-br from-purple-400 to-purple-600',
      dotPing: 'bg-purple-400',
      border: 'border-purple-100',
      borderHover: 'hover:border-purple-300',
      badge: 'bg-gradient-to-r from-purple-500 to-purple-600',
      text: 'from-purple-600 to-purple-700',
      investor: 'text-purple-500',
      investorBadge: 'bg-purple-100 text-purple-800',
      bgNumber: 'text-purple-600'
    }
  }
  
  if (typeLower.includes('series_d') || typeLower.includes('series_e') || typeLower.includes('series_f')) {
    return {
      dot: 'bg-gradient-to-br from-violet-400 to-violet-600',
      dotPing: 'bg-violet-400',
      border: 'border-violet-100',
      borderHover: 'hover:border-violet-300',
      badge: 'bg-gradient-to-r from-violet-500 to-violet-600',
      text: 'from-violet-600 to-violet-700',
      investor: 'text-violet-500',
      investorBadge: 'bg-violet-100 text-violet-800',
      bgNumber: 'text-violet-600'
    }
  }
  
  if (typeLower.includes('private_equity')) {
    return {
      dot: 'bg-gradient-to-br from-rose-400 to-rose-600',
      dotPing: 'bg-rose-400',
      border: 'border-rose-100',
      borderHover: 'hover:border-rose-300',
      badge: 'bg-gradient-to-r from-rose-500 to-rose-600',
      text: 'from-rose-600 to-rose-700',
      investor: 'text-rose-500',
      investorBadge: 'bg-rose-100 text-rose-800',
      bgNumber: 'text-rose-600'
    }
  }
  
  if (typeLower.includes('ipo') || typeLower.includes('post_ipo')) {
    return {
      dot: 'bg-gradient-to-br from-amber-400 to-amber-600',
      dotPing: 'bg-amber-400',
      border: 'border-amber-100',
      borderHover: 'hover:border-amber-300',
      badge: 'bg-gradient-to-r from-amber-500 to-amber-600',
      text: 'from-amber-600 to-amber-700',
      investor: 'text-amber-500',
      investorBadge: 'bg-amber-100 text-amber-800',
      bgNumber: 'text-amber-600'
    }
  }
  
  if (typeLower.includes('debt')) {
    return {
      dot: 'bg-gradient-to-br from-slate-400 to-slate-600',
      dotPing: 'bg-slate-400',
      border: 'border-slate-100',
      borderHover: 'hover:border-slate-300',
      badge: 'bg-gradient-to-r from-slate-500 to-slate-600',
      text: 'from-slate-600 to-slate-700',
      investor: 'text-slate-500',
      investorBadge: 'bg-slate-100 text-slate-800',
      bgNumber: 'text-slate-600'
    }
  }
  
  if (typeLower.includes('grant')) {
    return {
      dot: 'bg-gradient-to-br from-teal-400 to-teal-600',
      dotPing: 'bg-teal-400',
      border: 'border-teal-100',
      borderHover: 'hover:border-teal-300',
      badge: 'bg-gradient-to-r from-teal-500 to-teal-600',
      text: 'from-teal-600 to-teal-700',
      investor: 'text-teal-500',
      investorBadge: 'bg-teal-100 text-teal-800',
      bgNumber: 'text-teal-600'
    }
  }
  
  return {
    dot: 'bg-gradient-to-br from-gray-400 to-gray-600',
    dotPing: 'bg-gray-400',
    border: 'border-gray-100',
    borderHover: 'hover:border-gray-300',
    badge: 'bg-gradient-to-r from-gray-500 to-gray-600',
    text: 'from-gray-600 to-gray-700',
    investor: 'text-gray-500',
    investorBadge: 'bg-gray-100 text-gray-800',
    bgNumber: 'text-gray-600'
  }
}

// Format investment type for display
const formatInvestmentType = (type: string | null): string => {
  if (!type) return 'Unknown'
  return type
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

// Format money amount
const formatMoney = (amount: number | null): string => {
  if (!amount) return 'Undisclosed'
  
  if (amount >= 1000000000) {
    return `$${(amount / 1000000000).toFixed(2)}B`
  } else if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`
  } else if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`
  }
  return `$${amount.toLocaleString()}`
}

export default function FundingTimeline({ rounds }: FundingTimelineProps) {
  // Sort rounds by date (newest first)
  const sortedRounds = [...rounds].sort((a, b) => {
    const dateA = a.announced_on ? new Date(a.announced_on).getTime() : 0
    const dateB = b.announced_on ? new Date(b.announced_on).getTime() : 0
    return dateB - dateA
  })

  if (rounds.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-sm font-medium">No funding rounds available</p>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-200 via-purple-200 to-pink-200"></div>
      
      {/* Funding rounds */}
      <div className="space-y-6">
        {sortedRounds.map((round) => {
          const colors = getTypeColors(round.investment_type)
          
          return (
            <div key={round.id} className="relative pl-20 group">
              {/* Timeline dot */}
              <div className={`absolute left-5 top-3 w-6 h-6 rounded-full border-4 border-white shadow-lg group-hover:scale-125 transition-transform z-0 ${colors.dot}`}>
                <div className={`absolute inset-0 rounded-full animate-ping opacity-75 ${colors.dotPing}`}></div>
              </div>
              
              {/* Card */}
              <div className={`bg-white rounded-xl border-2 shadow-md hover:shadow-xl transition-all p-5 group-hover:translate-x-1 ${colors.border} ${colors.borderHover}`}>
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-white font-bold text-sm shadow-md ${colors.badge}`}>
                        {formatInvestmentType(round.investment_type)}
                      </span>
                      {round.announced_on && (
                        <span className="text-sm text-gray-500 font-medium">
                          {format(new Date(round.announced_on), 'MMM d, yyyy')}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Amount - Large and prominent */}
                  <div className="text-right">
                    <div className={`text-2xl font-bold bg-gradient-to-r bg-clip-text text-transparent ${colors.text}`}>
                      {formatMoney(round.money_raised_usd)}
                    </div>
                  </div>
                </div>

                {/* Investors */}
                {(round.investor_names || round.num_investors) && (
                  <div className="space-y-2">
                    {/* All Investors */}
                    {round.investor_names && (
                      <div className="flex items-start gap-2">
                        <svg className={`w-4 h-4 mt-0.5 flex-shrink-0 ${colors.investor}`} fill="currentColor" viewBox="0 0 20 20">
                          <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                        </svg>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Investors</span>
                            {round.num_investors && round.num_investors > 0 && (
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${colors.investorBadge}`}>
                                {round.num_investors}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {round.investor_names}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary Stats at the bottom */}
      <div className="mt-8 pt-6 border-t-2 border-dashed border-gray-300">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{rounds.length}</div>
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mt-1">Total Rounds</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {formatMoney(rounds.reduce((sum, r) => sum + (r.money_raised_usd || 0), 0))}
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mt-1">Total Raised</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {formatMoney(
                rounds.filter(r => r.money_raised_usd).reduce((sum, r, _, arr) => 
                  sum + (r.money_raised_usd || 0) / arr.length, 0
                )
              )}
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mt-1">Avg Round</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-600">
              {rounds.reduce((sum, r) => sum + (r.num_investors || 0), 0)}
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mt-1">Total Investors</div>
          </div>
        </div>
      </div>
    </div>
  )
}
