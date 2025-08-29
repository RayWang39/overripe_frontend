# Quick Start Guide

## 🚀 Start the API

From the project root:
```bash
# Option 1: Use the helper script
./api/scripts/run_api.sh

# Option 2: Manual start
cd api
PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Option 3: Docker
cd api
docker-compose up
```

## 🧪 Test the API

```bash
# Run the demo script
cd api
python demos/method_chain_demo.py

# Or test manually
curl -X POST "http://localhost:8001/api/v1/translate/method-chain" \
  -H "Content-Type: application/json" \
  -d '{"method_chain": ".find.with_organizations", "parameters": {"asn": 15169}}'
```

## 🔗 Key URLs

- **API Docs**: http://localhost:8001/docs
- **Test Interface**: http://localhost:8001/
- **Health Check**: http://localhost:8001/api/v1/health

## 📂 File Organization

```
api/
├── README.md                    # Main API documentation
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Dependencies
│
├── docs/                        # Documentation
│   ├── API_README.md           # Detailed API docs
│   └── QUICK_START.md          # This file
│
├── demos/                       # Example scripts
│   └── method_chain_demo.py    # Interactive demo
│
├── scripts/                     # Utility scripts
│   └── run_api.sh              # Server startup script
│
├── models/                      # Data models
├── routers/                     # API endpoints
├── services/                    # Business logic
├── middleware/                  # Custom middleware
└── static/                      # Web interface
```

## 💡 Common Method Chains

```bash
# Basic AS lookup
.find

# AS with organization
.find.with_organizations

# Find upstream providers
.find.upstream

# Complex chain
.find.with_organizations.upstream.limit
```

## 🛠️ Integration Example

```javascript
// Your colleague's web server integration
async function translateQuery(methodChain, params) {
    const response = await fetch('http://your-api:8001/api/v1/translate/method-chain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method_chain: methodChain,
            parameters: params
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        // Use result.cypher and result.parameters with Neo4j
        return runCypherQuery(result.cypher, result.parameters);
    } else {
        throw new Error(result.error);
    }
}
```