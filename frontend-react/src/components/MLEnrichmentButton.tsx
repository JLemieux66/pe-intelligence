import { useState } from 'react'
import { Brain, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

interface EnrichmentResult {
  successfully_enriched: number
  message: string
}

interface MLEnrichmentButtonProps {
  isAdmin: boolean
  onEnrichmentComplete?: () => void
}

export default function MLEnrichmentButton({ isAdmin, onEnrichmentComplete }: MLEnrichmentButtonProps) {
  const [isEnriching, setIsEnriching] = useState(false)
  const [showResult, setShowResult] = useState(false)
  const [result, setResult] = useState<EnrichmentResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleEnrich = async () => {
    if (!isAdmin) {
      setError('Admin access required')
      return
    }

    setIsEnriching(true)
    setError(null)
    setShowResult(false)

    try {
      const token = localStorage.getItem('admin_token')
      const response = await axios.post<EnrichmentResult>(
        `${API_BASE_URL}/ml/enrich/all`,
        {},
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: 300000, // 5 minute timeout for large databases
        }
      )

      setResult(response.data)
      setShowResult(true)

      // Call callback if provided
      if (onEnrichmentComplete) {
        setTimeout(() => onEnrichmentComplete(), 1000)
      }

      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setShowResult(false)
      }, 5000)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to enrich companies. Check if ML models are deployed.')
      } else {
        setError('An unexpected error occurred')
      }
      setShowResult(true)
    } finally {
      setIsEnriching(false)
    }
  }

  if (!isAdmin) {
    return null // Don't show button if not admin
  }

  return (
    <div className="relative">
      <button
        onClick={handleEnrich}
        disabled={isEnriching}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
          ${isEnriching
            ? 'bg-purple-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700'
          }
          text-white shadow-lg hover:shadow-xl
        `}
        title="Generate ML revenue predictions for all companies"
      >
        {isEnriching ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Enriching...</span>
          </>
        ) : (
          <>
            <Brain className="h-4 w-4" />
            <span>ML Enrich</span>
          </>
        )}
      </button>

      {/* Result Toast */}
      {showResult && (
        <div className={`
          absolute top-full right-0 mt-2 w-80 p-4 rounded-lg shadow-xl z-50
          ${error
            ? 'bg-red-50 border-2 border-red-200'
            : 'bg-green-50 border-2 border-green-200'
          }
        `}>
          <div className="flex items-start gap-3">
            {error ? (
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <h4 className={`font-semibold ${error ? 'text-red-900' : 'text-green-900'}`}>
                {error ? 'Enrichment Failed' : 'Success!'}
              </h4>
              <p className={`text-sm mt-1 ${error ? 'text-red-700' : 'text-green-700'}`}>
                {error || result?.message}
              </p>
              {result && !error && (
                <p className="text-xs text-green-600 mt-2">
                  ✓ {result.successfully_enriched} companies enriched with ML predictions
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
