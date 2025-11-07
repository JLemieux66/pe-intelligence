import { useState, useMemo } from 'react'
import { X, AlertTriangle, ArrowRight, Search } from 'lucide-react'
import type { Investment } from '../types/company'

interface CompanyMergeModalProps {
  sourceCompany: Investment
  allCompanies: Investment[]
  onClose: () => void
  onMerge: (sourceId: number, targetId: number) => Promise<void>
}

export default function CompanyMergeModal({ 
  sourceCompany, 
  allCompanies,
  onClose,
  onMerge 
}: CompanyMergeModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTargetId, setSelectedTargetId] = useState<number | null>(null)
  const [isConfirming, setIsConfirming] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Filter companies for search (exclude source company)
  const filteredCompanies = useMemo(() => {
    return allCompanies
      .filter(company => 
        company.company_id !== sourceCompany.company_id &&
        company.company_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
      .sort((a, b) => a.company_name.localeCompare(b.company_name))
      .slice(0, 50) // Limit to 50 results
  }, [allCompanies, sourceCompany.company_id, searchQuery])

  const selectedTarget = allCompanies.find(c => c.company_id === selectedTargetId)

  const handleMerge = async () => {
    if (!selectedTargetId) return
    
    setIsSubmitting(true)
    try {
      await onMerge(sourceCompany.company_id, selectedTargetId)
      onClose()
    } catch (error) {
      console.error('Merge failed:', error)
      alert('Failed to merge companies. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Merge Company</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!isConfirming ? (
            <>
              {/* Source Company */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Merge FROM (will be deleted):
                </label>
                <div className="p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                  <div className="font-semibold text-gray-900">{sourceCompany.company_name}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {sourceCompany.headquarters && `📍 ${sourceCompany.headquarters}`}
                    {sourceCompany.primary_industry_group && ` • ${sourceCompany.primary_industry_group}`}
                  </div>
                </div>
              </div>

              <div className="flex justify-center mb-6">
                <ArrowRight className="w-8 h-8 text-gray-400" />
              </div>

              {/* Target Company Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Merge INTO (will keep this company):
                </label>
                
                {/* Search */}
                <div className="relative mb-3">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search companies..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    autoFocus
                  />
                </div>

                {/* Company List */}
                <div className="border border-gray-200 rounded-lg max-h-96 overflow-y-auto">
                  {filteredCompanies.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                      {searchQuery ? 'No companies found' : 'Start typing to search...'}
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-200">
                      {filteredCompanies.map((company) => (
                        <button
                          key={company.company_id}
                          onClick={() => setSelectedTargetId(company.company_id)}
                          className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                            selectedTargetId === company.company_id 
                              ? 'bg-blue-50 border-l-4 border-blue-500' 
                              : ''
                          }`}
                        >
                          <div className="font-medium text-gray-900">{company.company_name}</div>
                          <div className="text-sm text-gray-600 mt-1">
                            {company.headquarters && `📍 ${company.headquarters}`}
                            {company.primary_industry_group && ` • ${company.primary_industry_group}`}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {selectedTarget && (
                  <div className="mt-4 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                    <div className="font-semibold text-gray-900">{selectedTarget.company_name}</div>
                    <div className="text-sm text-gray-600 mt-1">
                      {selectedTarget.headquarters && `📍 ${selectedTarget.headquarters}`}
                      {selectedTarget.primary_industry_group && ` • ${selectedTarget.primary_industry_group}`}
                    </div>
                  </div>
                )}
              </div>

              {/* Warning */}
              <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                <div className="flex">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="ml-3 text-sm text-yellow-800">
                    <p className="font-semibold">Warning: This action cannot be undone</p>
                    <p className="mt-1">
                      All PE investments, tags, and data from "{sourceCompany.company_name}" will be moved to the target company,
                      and the source company will be permanently deleted.
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* Confirmation Screen */
            <div className="space-y-6">
              <div className="text-center">
                <AlertTriangle className="w-16 h-16 text-orange-500 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  Confirm Company Merge
                </h3>
                <p className="text-gray-600">
                  Are you absolutely sure you want to proceed?
                </p>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="text-sm font-medium text-red-800 mb-1">DELETE:</div>
                  <div className="font-semibold text-gray-900">{sourceCompany.company_name}</div>
                </div>

                <div className="flex justify-center">
                  <ArrowRight className="w-8 h-8 text-gray-400" />
                </div>

                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="text-sm font-medium text-green-800 mb-1">KEEP:</div>
                  <div className="font-semibold text-gray-900">{selectedTarget?.company_name}</div>
                </div>
              </div>

              <div className="p-4 bg-gray-100 rounded-lg">
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-2">What will happen:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>All PE investments will be moved to {selectedTarget?.company_name}</li>
                    <li>All tags will be merged</li>
                    <li>Missing data will be copied over</li>
                    <li>{sourceCompany.company_name} will be added as a former name</li>
                    <li>{sourceCompany.company_name} will be permanently deleted</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          
          {!isConfirming ? (
            <button
              onClick={() => setIsConfirming(true)}
              disabled={!selectedTargetId}
              className="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
            </button>
          ) : (
            <button
              onClick={handleMerge}
              disabled={isSubmitting}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                  Merging...
                </>
              ) : (
                'Confirm Merge'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
