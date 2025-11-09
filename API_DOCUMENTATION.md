# 🔌 PE Intelligence API Documentation

## Authentication

All API endpoints require JWT authentication via the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 🤖 Similar Companies

Find companies similar to given input companies using AI-powered analysis.

**Endpoint:** `POST /api/similar-companies`

**Request Body:**
```json
{
  "company_ids": [14898, 15234],
  "min_score": 30.0,
  "limit": 10
}
```

**Response:**
```json
{
  "total_results": 5,
  "processing_time_ms": 2341,
  "matches": [
    {
      "company": {
        "id": 16789,
        "name": "TechCorp Inc",
        "industry": "Technology",
        "stage": "Series B",
        "location": "San Francisco, CA",
        "employee_count": 150,
        "revenue_range": "$10M-$50M",
        "description": "AI-powered analytics platform...",
        "tags": ["SaaS", "B2B", "Analytics"]
      },
      "similarity_score": 87.5,
      "score_breakdown": {
        "industry": 20.0,
        "stage": 15.0,
        "location": 8.5,
        "size": 12.0,
        "revenue": 10.0,
        "tags": 15.0,
        "description": 7.0
      },
      "ai_reasoning": "These companies are highly similar because they both operate in the B2B SaaS space..."
    }
  ]
}
```

**Parameters:**
- `company_ids` (required): Array of company IDs to find similarities for
- `min_score` (optional, default: 30.0): Minimum similarity score (0-100)
- `limit` (optional, default: 10): Maximum number of results to return

**Scoring Dimensions:**
1. **Industry Match** (0-20 points): Exact industry alignment
2. **Funding Stage** (0-15 points): Similar funding stages
3. **Geographic Location** (0-10 points): Location proximity
4. **Company Size** (0-12 points): Employee count similarity
5. **Revenue Range** (0-10 points): Revenue bracket alignment
6. **Tags/Categories** (0-15 points): Business model and category overlap
7. **Description Similarity** (0-8 points): AI-powered description analysis
8. **Market Focus** (0-5 points): Target market alignment
9. **Technology Stack** (0-5 points): Technical approach similarity

### 📊 Company Details

**Endpoint:** `GET /api/companies/{company_id}`

**Response:**
```json
{
  "id": 14898,
  "name": "Example Corp",
  "industry": "Technology",
  "stage": "Series A",
  "location": "New York, NY",
  "employee_count": 75,
  "revenue_range": "$1M-$10M",
  "description": "Innovative software solutions...",
  "tags": ["SaaS", "B2B"],
  "funding_rounds": [
    {
      "round_type": "Seed",
      "amount": 2000000,
      "date": "2022-03-15",
      "investors": ["VC Fund A", "Angel Investor B"]
    }
  ]
}
```

### 📈 Analytics

**Endpoint:** `GET /api/analytics/usage`

**Query Parameters:**
- `days` (optional, default: 7): Number of days to analyze

**Response:**
```json
{
  "total_requests": 1250,
  "avg_response_time": 1847.5,
  "endpoint_usage": {
    "similar_companies": 890,
    "companies": 360
  },
  "daily_usage": {
    "2024-11-09": 180,
    "2024-11-08": 165
  },
  "error_rate": 0.02
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "error_code": "INVALID_REQUEST",
  "timestamp": "2024-11-09T15:30:00Z"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found
- `429`: Rate Limited
- `500`: Internal Server Error

## Rate Limiting

- **Similar Companies**: 100 requests per hour per user
- **Other endpoints**: 1000 requests per hour per user

## Best Practices

1. **Caching**: Similar companies results are cached for 24 hours
2. **Batch Requests**: Include multiple company IDs in single request when possible
3. **Score Thresholds**: Use appropriate `min_score` values (30+ recommended)
4. **Error Handling**: Always handle rate limiting and server errors gracefully
5. **Authentication**: Store JWT tokens securely and refresh before expiration