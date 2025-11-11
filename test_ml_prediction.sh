#!/bin/bash
# Test ML Prediction for 100ms company
# This script will help diagnose why predictions show as 0

set -e

echo "=== ML Prediction Test for 100ms ==="
echo ""

# Get backend URL from environment or use default
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "1. Checking ML model status..."
curl -s "${BACKEND_URL}/api/ml/models/status" | python3 -m json.tool
echo ""

echo "2. Searching for 100ms company..."
COMPANY_DATA=$(curl -s "${BACKEND_URL}/api/companies?search=100ms&limit=1")
echo "$COMPANY_DATA" | python3 -m json.tool
echo ""

# Extract company ID
COMPANY_ID=$(echo "$COMPANY_DATA" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['companies'][0]['id'] if data.get('companies') else 'NOT_FOUND')" 2>/dev/null || echo "NOT_FOUND")

if [ "$COMPANY_ID" = "NOT_FOUND" ]; then
    echo "ERROR: Could not find 100ms company"
    exit 1
fi

echo "Found company ID: $COMPANY_ID"
echo ""

echo "3. Triggering ML enrichment for company $COMPANY_ID..."
curl -s -X POST "${BACKEND_URL}/api/ml/enrich/company/${COMPANY_ID}?force_update=true" | python3 -m json.tool
echo ""

echo "4. Fetching updated company data..."
curl -s "${BACKEND_URL}/api/companies/${COMPANY_ID}" | python3 -m json.tool
echo ""

echo "=== Test Complete ==="
echo "If predicted_revenue is still 0 or null, check the backend logs for errors"
