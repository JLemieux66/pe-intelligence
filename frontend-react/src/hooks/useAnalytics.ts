/**
 * Analytics hook for tracking user interactions
 */
import { useCallback } from 'react'

interface AnalyticsEvent {
  action: string
  category: string
  label?: string
  value?: number
  metadata?: Record<string, any>
}

export const useAnalytics = () => {
  const trackEvent = useCallback((event: AnalyticsEvent) => {
    // Simple console logging for now - replace with your analytics service
    console.log('Analytics Event:', event)
    
    // Example: Send to analytics service
    // analyticsService.track(event)
    
    // Example: Send to Google Analytics
    // gtag('event', event.action, {
    //   event_category: event.category,
    //   event_label: event.label,
    //   value: event.value,
    //   custom_parameters: event.metadata
    // })
  }, [])

  const trackSimilarCompaniesView = useCallback((companyId: number, resultCount: number) => {
    trackEvent({
      action: 'view_similar_companies',
      category: 'similar_companies',
      label: `company_${companyId}`,
      value: resultCount,
      metadata: { companyId, resultCount }
    })
  }, [trackEvent])

  const trackSimilarCompanyClick = useCallback((sourceId: number, targetId: number, score: number) => {
    trackEvent({
      action: 'click_similar_company',
      category: 'similar_companies',
      label: `${sourceId}_to_${targetId}`,
      value: Math.round(score),
      metadata: { sourceId, targetId, score }
    })
  }, [trackEvent])

  const trackFeedback = useCallback((sourceId: number, targetId: number, isSimilar: boolean) => {
    trackEvent({
      action: 'similarity_feedback',
      category: 'similar_companies',
      label: isSimilar ? 'positive' : 'negative',
      value: isSimilar ? 1 : 0,
      metadata: { sourceId, targetId, isSimilar }
    })
  }, [trackEvent])

  return {
    trackEvent,
    trackSimilarCompaniesView,
    trackSimilarCompanyClick,
    trackFeedback
  }
}