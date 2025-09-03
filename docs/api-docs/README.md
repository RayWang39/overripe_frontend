# IYP Method Chain Translation API

A FastAPI service that translates method chains into Cypher queries for the Internet Yellow Pages (IYP) Neo4j database.

## Overview

This API focuses on **translation-only** - it converts method chains like `.find.with_organizations.upstream` into Cypher queries without executing them. Perfect for integration into web servers that need programmatic Cypher generation.

## Quick Start

```bash
# Start the API server
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Or use Docker
docker-compose up
```

## Directory Structure

```
api/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Docker orchestration
│
├── models/              # Pydantic data models
│   ├── translation.py   # Translation request/response models
│   ├── requests.py      # General request models
│   └── responses.py     # General response models
│
├── routers/             # API route handlers
│   ├── translation.py   # Method chain translation endpoints
│   ├── query.py         # Legacy query endpoints
│   ├── search.py        # Search endpoints
│   └── admin.py         # Admin endpoints
│
├── services/            # Business logic
│   ├── translation_service.py  # Core translation logic
│   └── query_service.py        # Legacy query service
│
├── middleware/          # Custom middleware
│   └── auth.py          # Authentication middleware
│
├── static/             # Web interface files
│   └── index.html      # Interactive test interface
│
├── docs/               # Documentation
│   └── API_README.md   # Detailed API documentation
│
├── demos/              # Example scripts
│   └── method_chain_demo.py  # Demo script for testing
│
└── scripts/            # Utility scripts
    └── run_api.sh      # Server startup script
```

## Key Features

### 🔄 Method Chain Translation
Convert method chains to Cypher queries:
```python
# Input: ".find.with_organizations.upstream.limit"
# Output: Optimized Cypher query with parameters
```

### 🛡️ Security
- Parameter injection prevention
- API key authentication
- Input validation with Pydantic

### 🔗 Integration Ready
- RESTful JSON API
- Detailed error messages
- Query explanations
- CORS support

## API Endpoints

### Core Translation
- `POST /api/v1/translate/method-chain` - Main translation endpoint
- `GET /api/v1/translate/help` - Available methods documentation
- `GET /api/v1/translate/examples` - Working example translations

### Utility
- `GET /api/v1/health` - Service health check
- `GET /docs` - Interactive API documentation
- `GET /` - Web interface for testing

## Usage Examples

### Basic Method Chain
```bash
curl -X POST "http://localhost:8001/api/v1/translate/method-chain" \
  -H "Content-Type: application/json" \
  -d '{
    "method_chain": ".find.with_organizations",
    "parameters": {"asn": 15169}
  }'
```

### Complex Chain with Multiple Methods
```bash
curl -X POST "http://localhost:8001/api/v1/translate/method-chain" \
  -H "Content-Type: application/json" \
  -d '{
    "method_chain": ".find.upstream.limit",
    "parameters": {"asn": 15169, "hops": 2, "limit": 10}
  }'
```

### JavaScript Integration
```javascript
async function translateMethodChain(chain, params) {
    const response = await fetch('/api/v1/translate/method-chain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method_chain: chain,
            parameters: params
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        // Use result.cypher and result.parameters with Neo4j
        return result;
    } else {
        throw new Error(result.error);
    }
}
```

## Available Methods

- `.find` - Find nodes by type and properties
- `.with_organizations` - Include organization details
- `.upstream` - Find upstream providers
- `.downstream` - Find downstream customers
- `.peers` - Find peering partners
- `.with_relationship` - Custom relationship traversal
- `.where` - Add filtering conditions
- `.limit` - Limit number of results
- `.return_fields` - Specify fields to return

## Running Demos

```bash
# Test the translation API
cd api
python demos/method_chain_demo.py
```

## Configuration

Environment variables:
- `NEO4J_URI` - Neo4j database URI
- `NEO4J_USER` - Database username
- `NEO4J_PASSWORD` - Database password
- `API_KEY` - Optional API key for authentication

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
python -m uvicorn main:app --reload --port 8001

# Run tests
pytest

# Format code
black .
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t iyp-api .
docker run -p 8001:8001 iyp-api
```

## Benefits

✅ **No Cypher Knowledge Required** - Users work with simple method chains  
✅ **Injection Safe** - Parameters properly escaped  
✅ **Optimized Queries** - Generated Cypher is efficient  
✅ **Easy Integration** - Standard REST API  
✅ **Self-Documenting** - Built-in help and examples  
✅ **Query Explanations** - Understand what each query does