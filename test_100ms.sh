#!/bin/bash
# Quick test for 100ms company ML prediction
# Run this from anywhere - just set your backend URL

BACKEND_URL="${1:-https://pe-intelligence-production.up.railway.app}"

echo "Testing ML prediction for 100ms"
echo "Backend: $BACKEND_URL"
echo ""

echo "Step 1: Finding 100ms company..."
RESPONSE=$(curl -s "${BACKEND_URL}/api/companies?search=100ms&limit=1")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

COMPANY_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['companies'][0]['id'] if data.get('companies') and len(data['companies']) > 0 else 'NOT_FOUND')" 2>/dev/null)

if [ "$COMPANY_ID" = "NOT_FOUND" ]; then
    echo "ERROR: 100ms company not found"
    exit 1
fi

echo ""
echo "Found company ID: $COMPANY_ID"
echo ""

echo "Step 2: Triggering ML prediction..."
curl -s -X POST "${BACKEND_URL}/api/ml/enrich/company/${COMPANY_ID}?force_update=true" | python3 -m json.tool
echo ""

echo "Step 3: Fetching result..."
curl -s "${BACKEND_URL}/api/companies/${COMPANY_ID}" | python3 -m json.tool | grep -A 3 "predicted_revenue"
echo ""

echo "Done! Check your frontend to see the updated prediction."
