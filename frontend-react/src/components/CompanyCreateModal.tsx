import { useState } from 'react'
import { X, Plus, Building2 } from 'lucide-react'
import axios from 'axios'

interface CompanyCreateModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function CompanyCreateModal({ onClose, onSuccess }: CompanyCreateModalProps) {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

  const [formData, setFormData] = useState({
    name: '',
    website: '',
    description: '',
    country: '',
    state_region: '',
    city: '',
    industry_category: '',
    primary_industry_group: '',
    primary_industry_sector: '',
    verticals: '',
    employee_count: '',
    current_revenue_usd: '',
    founded_year: '',
    is_public: false,
    pe_firm_name: '',
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const token = localStorage.getItem('admin_token')
      if (!token) {
        setError('You must be logged in as an admin to create companies')
        setIsSubmitting(false)
        return
      }

      // Build the request body
      const requestBody: any = {
        name: formData.name,
      }

      // Add optional fields only if they have values
      if (formData.website) requestBody.website = formData.website
      if (formData.description) requestBody.description = formData.description
      if (formData.country) requestBody.country = formData.country
      if (formData.state_region) requestBody.state_region = formData.state_region
      if (formData.city) requestBody.city = formData.city
      if (formData.industry_category) requestBody.industry_category = formData.industry_category
      if (formData.primary_industry_group) requestBody.primary_industry_group = formData.primary_industry_group
      if (formData.primary_industry_sector) requestBody.primary_industry_sector = formData.primary_industry_sector
      if (formData.verticals) requestBody.verticals = formData.verticals
      if (formData.employee_count) requestBody.employee_count = parseInt(formData.employee_count)
      if (formData.current_revenue_usd) requestBody.current_revenue_usd = parseFloat(formData.current_revenue_usd)
      if (formData.founded_year) requestBody.founded_year = parseInt(formData.founded_year)
      requestBody.is_public = formData.is_public

      // Add PE investment if firm name is provided
      if (formData.pe_firm_name) {
        requestBody.pe_investments = [
          {
            pe_firm_name: formData.pe_firm_name,
            computed_status: 'Active',
          },
        ]
      }

      await axios.post(`${API_BASE_URL}/companies`, requestBody, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      onSuccess()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create company')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }))
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Plus className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Add New Company</h2>
              <p className="text-sm text-gray-600">Create a new portfolio company</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/50 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600" />
              Basic Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Acme Corporation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
                <input
                  type="url"
                  name="website"
                  value={formData.website}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://acme.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">PE Firm</label>
                <input
                  type="text"
                  name="pe_firm_name"
                  value={formData.pe_firm_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Vista Equity Partners"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Brief description of the company..."
                />
              </div>
            </div>
          </div>

          {/* Location */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Location</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                <input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="United States"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State/Region</label>
                <input
                  type="text"
                  name="state_region"
                  value={formData.state_region}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="California"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="San Francisco"
                />
              </div>
            </div>
          </div>

          {/* Industry */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Industry</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry Category</label>
                <input
                  type="text"
                  name="industry_category"
                  value={formData.industry_category}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Software"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry Group</label>
                <input
                  type="text"
                  name="primary_industry_group"
                  value={formData.primary_industry_group}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="B2B"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Industry Sector</label>
                <input
                  type="text"
                  name="primary_industry_sector"
                  value={formData.primary_industry_sector}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enterprise Software"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Verticals</label>
                <input
                  type="text"
                  name="verticals"
                  value={formData.verticals}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="SaaS, Analytics"
                />
              </div>
            </div>
          </div>

          {/* Company Data */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Company Data</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employees</label>
                <input
                  type="number"
                  name="employee_count"
                  value={formData.employee_count}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="250"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Revenue ($M USD)</label>
                <input
                  type="number"
                  step="0.1"
                  name="current_revenue_usd"
                  value={formData.current_revenue_usd}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="50.5"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Founded Year</label>
                <input
                  type="number"
                  name="founded_year"
                  value={formData.founded_year}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="2015"
                />
              </div>
            </div>
          </div>

          {/* Public Status */}
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                name="is_public"
                checked={formData.is_public}
                onChange={handleChange}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Public Company (IPO)</span>
            </label>
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !formData.name}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Creating...' : 'Create Company'}
          </button>
        </div>
      </div>
    </div>
  )
}
