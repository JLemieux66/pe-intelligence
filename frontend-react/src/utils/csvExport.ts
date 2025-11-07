import type { Investment } from '../types/company'

export const exportToCSV = (investments: Investment[], filename: string = 'pe-portfolio') => {
  // Define CSV headers
  const headers = [
    'Company Name',
    'PE Firm',
    'Status',
    'Exit Type',
    'Industry',
    'Headquarters',
    'Employees',
    'Revenue Range',
    'Website',
    'LinkedIn'
  ]

  // Convert investments to CSV rows
  const rows = investments.map(inv => [
    inv.company_name || '',
    inv.pe_firm_name || '',
    inv.status || '',
    inv.exit_type || '',
    inv.industry_category || '',
    inv.headquarters || '',
    inv.employee_count?.toString() || '',
    inv.revenue_range || '',
    inv.website || '',
    inv.linkedin_url || ''
  ])

  // Escape CSV values (handle commas and quotes)
  const escapeCSV = (value: string) => {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`
    }
    return value
  }

  // Build CSV content
  const csvContent = [
    headers.map(escapeCSV).join(','),
    ...rows.map(row => row.map(escapeCSV).join(','))
  ].join('\n')

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}-${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}
