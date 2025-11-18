#!/bin/bash
# Test script for NLP translation API

echo "🧪 Testing NLP Translation API"
echo "================================"
echo ""

# Test 1: Health Check
echo "1. Health Check:"
curl -s http://localhost:8001/api/v1/nlp/health | python3 -m json.tool
echo ""
echo ""

# Test 2: Simple Translation
echo "2. Simple Natural Language Translation:"
curl -X POST http://localhost:8001/api/v1/nlp/translate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all upstream providers of Google"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 3: Translation with Context
echo "3. Translation with ASN Context:"
curl -X POST http://localhost:8001/api/v1/nlp/translate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the upstream providers",
    "context": {"asn": 15169}
  }' | python3 -m json.tool
echo ""
echo ""

echo "✅ Test complete!"
