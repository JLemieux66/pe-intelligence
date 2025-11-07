/**
 * PREDICTED REVENUE UI COMPONENT GUIDE
 * 
 * This is a reference for the new predicted revenue display with confidence indicators.
 * The UI automatically shows when a company has predicted_revenue data.
 */

// ============================================================================
// CONFIDENCE LEVELS - Color coding system
// ============================================================================

const CONFIDENCE_LEVELS = {
  HIGH: {
    threshold: 0.80,  // 80% and above
    color: 'green',
    gradient: 'from-green-400 to-green-600',
    icon: 'checkmark-circle',
    label: 'High Confidence',
    description: 'Model is very confident in this prediction'
  },
  
  MEDIUM: {
    threshold: 0.60,  // 60-79%
    color: 'yellow',
    gradient: 'from-yellow-400 to-yellow-600',
    icon: 'information-circle',
    label: 'Medium Confidence',
    description: 'Model has moderate confidence'
  },
  
  LOWER: {
    threshold: 0.00,  // Below 60%
    color: 'orange',
    gradient: 'from-orange-400 to-orange-600',
    icon: 'warning',
    label: 'Lower Confidence',
    description: 'Prediction has higher uncertainty'
  }
}

// ============================================================================
// UI COMPONENT STRUCTURE
// ============================================================================

/*
interface PredictedRevenueDisplay {
  // Main Components:
  components: {
    revenueAmount: {
      format: '$XXX.XM USD',
      style: 'text-2xl font-bold text-indigo-600',
      example: '$297.3M USD'
    },
    
    confidenceScore: {
      format: 'XX%',
      position: 'top-right',
      colorCoded: true,
      examples: {
        high: '92%',
        medium: '72%',
        lower: '51%'
      }
    },
    
    progressBar: {
      type: 'gradient',
      height: '8px (h-2)',
      animated: true,
      colors: {
        background: 'gray-200',
        fill: 'gradient based on confidence'
      }
    },
    
    statusLabel: {
      position: 'below-bar',
      includesIcon: true,
      examples: [
        '✓ High Confidence',
        'ℹ Medium Confidence',
        '⚠ Lower Confidence'
      ]
    },
    
    aiBadge: {
      text: 'AI-Predicted',
      style: 'indigo-50 background with indigo-700 text',
      icon: 'cpu-chip'
    }
  }
}
*/

// ============================================================================
// DATA FLOW
// ============================================================================

/*
1. DATABASE (PostgreSQL)
   └─ companies.predicted_revenue (FLOAT) - Revenue in USD
   └─ companies.prediction_confidence (FLOAT) - Score 0-1

2. BACKEND API (FastAPI)
   └─ GET /companies/{id}
   └─ Response includes:
      {
        "predicted_revenue": 297300000.0,
        "prediction_confidence": 0.92
      }

3. FRONTEND (React/TypeScript)
   └─ CompanyModal.tsx receives data
   └─ Calculates display values:
      - Revenue: $297.3M (predicted_revenue / 1M, fixed to 1 decimal)
      - Confidence: 92% (prediction_confidence * 100)
      - Color: Green (confidence >= 0.80)
   └─ Renders animated UI
*/

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

// Backend (Python) - When saving predictions:
// company.predicted_revenue = 297300000.0  // $297.3M
// company.prediction_confidence = 0.92     // 92%
// session.commit()

// Frontend (TypeScript) - Accessing in component:
/*
if (company.predicted_revenue && company.prediction_confidence) {
  const revenueInMillions = (company.predicted_revenue / 1000000).toFixed(1)
  const confidencePercent = (company.prediction_confidence * 100).toFixed(0)
  const confidenceLevel = 
    company.prediction_confidence >= 0.8 ? 'high' :
    company.prediction_confidence >= 0.6 ? 'medium' : 'lower'
  
  // UI renders automatically with proper styling
}
*/

// ============================================================================
// CONFIDENCE SCORE GUIDELINES
// ============================================================================

const confidenceGuidelines = {
  // When to use each confidence level:
  
  high: {
    range: '80-95%',
    when: [
      'Company has complete data (employees, industry, funding)',
      'Prediction falls within training data range',
      'Similar companies in training set',
      'Recent data (within 2 years)'
    ],
    example: 'SaaS company with 1000 employees, Series C, $50M funding'
  },
  
  medium: {
    range: '60-79%',
    when: [
      'Missing some data (no funding data)',
      'Prediction near edge of training range',
      'Industry has high variance',
      'Data is 2-3 years old'
    ],
    example: 'Manufacturing company, 500 employees, no funding data'
  },
  
  lower: {
    range: '40-59%',
    when: [
      'Missing critical data (no employee count)',
      'Extrapolating beyond training data',
      'Unusual business model',
      'Very old or estimated data'
    ],
    example: 'Niche industry, estimated employee count, no recent data'
  }
}

// ============================================================================
// TESTING
// ============================================================================

// View test companies with different confidence levels:
const testCompanies = [
  { name: 'Acquia', confidence: 0.92, expected: 'Green/High' },
  { name: 'Acumatica', confidence: 0.85, expected: 'Green/High' },
  { name: 'Aderant', confidence: 0.72, expected: 'Yellow/Medium' },
  { name: 'AGDATA', confidence: 0.65, expected: 'Yellow/Medium' },
  { name: 'Alegeus', confidence: 0.51, expected: 'Orange/Lower' }
]

// To test: Search for these companies in the frontend
// Each should display appropriate color coding and labels

// ============================================================================
// FUTURE ENHANCEMENTS
// ============================================================================

const futureFeatures = {
  confidenceTooltip: {
    description: 'Hover to see why confidence is X%',
    shows: [
      'Data completeness score',
      'Training set similarity',
      'Prediction range assessment',
      'Date recency'
    ]
  },
  
  confidenceRange: {
    description: 'Show prediction interval',
    example: '$250M - $350M (90% confidence interval)'
  },
  
  predictionExplanation: {
    description: 'SHAP values or feature importance',
    shows: 'Top 5 factors influencing this prediction'
  },
  
  historicalAccuracy: {
    description: 'For public companies or known exits',
    shows: 'Predicted: $300M, Actual: $325M (8% error)'
  }
}

export default {
  CONFIDENCE_LEVELS,
  confidenceGuidelines,
  testCompanies,
  futureFeatures
}
