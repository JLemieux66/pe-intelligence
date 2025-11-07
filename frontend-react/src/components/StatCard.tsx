import { ReactNode } from 'react'

interface StatCardProps {
  title: string
  value: string
  icon: ReactNode
  color: 'blue' | 'green' | 'gray' | 'purple'
  subtitle?: string
}

const colorClasses = {
  blue: 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/50',
  green: 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/50',
  gray: 'bg-gradient-to-br from-slate-500 to-slate-600 text-white shadow-lg shadow-slate-500/50',
  purple: 'bg-gradient-to-br from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/50',
}

export default function StatCard({ title, value, icon, color, subtitle }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow border border-gray-100 overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">{title}</h3>
          <div className={`p-2.5 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        </div>
        <p className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">{value}</p>
        {subtitle && <p className="text-sm text-gray-500 mt-2 font-medium">{subtitle}</p>}
      </div>
      <div className={`h-1 ${colorClasses[color].split(' ')[0]}`}></div>
    </div>
  )
}
