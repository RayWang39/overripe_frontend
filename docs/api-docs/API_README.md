# IYP Query API

A FastAPI wrapper for the Internet Yellow Pages Graph Database Query Library, enabling RESTful access to network infrastructure data.

## 🚀 Quick Start

### Option 1: Direct Python (Recommended for Development)

```bash
# Install dependencies
pip install -r api/requirements.txt

# Start the API server
./run_api.sh

# Or manually:
cd api && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t iyp-api ./api
docker run -p 8000:8000 iyp-api
```

## 📱 Access Points

Once running, access these URLs:

- **Test Interface**: http://localhost:8000 - Interactive web UI for testing queries
- **API Documentation**: http://localhost:8000/docs - Swagger UI with interactive API docs
- **ReDoc**: http://localhost:8000/redoc - Alternative API documentation
- **Health Check**: http://localhost:8000/api/v1/health - API status check

## 🔍 API Endpoints

### Core Query Endpoints

- `POST /api/v1/query/execute` - Execute builder-pattern queries
- `POST /api/v1/query/cypher` - Execute raw Cypher queries (read-only)
- `POST /api/v1/query/validate` - Validate Cypher queries

### High-Level Search Endpoints

- `GET /api/v1/as/{asn}` - Get AS details
- `GET /api/v1/as/{asn}/upstream` - Get upstream providers
- `GET /api/v1/as/{asn}/peers` - Get peering partners
- `GET /api/v1/country/{country_code}/as` - Get ASes by country
- `GET /api/v1/search/as` - Search ASes with filters

### Admin Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/stats` - Usage statistics
- `GET /api/v1/info` - API information

## 💡 Example Usage

### Using the Test Interface

1. Open http://localhost:8000
2. Try the example queries:
   - **Google AS**: Get details for AS15169
   - **UK ASes**: List ASes in Great Britain
   - **Upstream Providers**: Find provider hierarchy
   - **AS Peers**: Get peering relationships

### Using cURL

```bash
# Get AS details
curl "http://localhost:8000/api/v1/as/15169?include_organizations=true"

# Find upstream providers
curl "http://localhost:8000/api/v1/as/216139/upstream?max_hops=2"

# Search UK ASes
curl "http://localhost:8000/api/v1/country/GB/as?limit=10"

# Execute builder query
curl -X POST "http://localhost:8000/api/v1/query/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "builder",
    "operations": [
      {"method": "find", "params": {"node_type": "AS", "asn": 15169}},
      {"method": "with_organizations", "params": {}}
    ],
    "return_format": "json"
  }'
```

### Using Python Requests

```python
import requests

# API base URL
api_base = "http://localhost:8000"

# Get AS details
response = requests.get(f"{api_base}/api/v1/as/15169")
print(response.json())

# Execute a builder query
query = {
    "query_type": "builder",
    "operations": [
        {"method": "find", "params": {"node_type": "AS", "asn": 15169}},
        {"method": "upstream", "params": {"hops": 2}}
    ]
}
response = requests.post(f"{api_base}/api/v1/query/execute", json=query)
print(response.json())
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `api/` directory:

```env
# Database Configuration
NEO4J_URI=bolt+s://iyp.christyquinn.com:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# API Security (optional)
API_KEY_ENABLED=false
API_KEYS=your-api-key-1,your-api-key-2
SECRET_KEY=your-secret-key

# CORS (adjust for production)
CORS_ORIGINS=*

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### API Authentication (Optional)

To enable API key authentication:

1. Set `API_KEY_ENABLED=true` in your environment
2. Set `API_KEYS=key1,key2,key3` with your desired keys
3. Include `X-API-Key: your-key` header in requests

## 📊 Query Types

### 1. Simple Queries (High-Level API)

Use the search endpoints for common queries:

```bash
# AS details with organization info
GET /api/v1/as/15169?include_organizations=true&include_peers=false

# All ASes in United States
GET /api/v1/country/US/as?limit=100
```

### 2. Builder Queries (Medium Complexity)

Chain operations to build complex queries:

```json
{
  "query_type": "builder",
  "operations": [
    {"method": "find", "params": {"node_type": "AS", "asn": 15169}},
    {"method": "with_relationship", "params": {"rel_type": "DEPENDS_ON", "to": "AS", "alias": "upstream"}},
    {"method": "where", "params": {"conditions": "upstream.asn IN [174, 3356, 1299]"}},
    {"method": "return_fields", "params": {"fields": ["upstream.asn", "upstream.name"]}}
  ]
}
```

### 3. Raw Cypher (Full Power)

Execute native Neo4j Cypher queries:

```json
{
  "query": "MATCH (a:AS {asn: 15169})-[:PEERS_WITH]->(peer:AS) RETURN peer.asn, peer.name LIMIT 10",
  "parameters": {},
  "return_format": "json"
}
```

## 🔒 Security Features

- **Read-only**: Only SELECT/MATCH operations allowed
- **Query validation**: Prevents destructive operations
- **Rate limiting**: Configurable request limits
- **API key auth**: Optional authentication layer
- **CORS**: Configurable cross-origin access
- **Input validation**: All inputs validated with Pydantic

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Neo4j credentials in config
   - Verify network connectivity to database

2. **Module Import Errors**
   - Ensure you're running from the project root directory
   - Check that `iyp_query/` directory exists

3. **Port Already in Use**
   - Change port with: `--port 8001`
   - Or kill existing process: `lsof -ti:8000 | xargs kill`

### Debugging

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# View detailed logs
cd api && python -m uvicorn main:app --log-level debug

# Test database connection
python -c "from iyp_query import connect; print(connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'password'))"
```

## 🚀 Deployment

### Production Deployment

1. **Set environment variables** for production
2. **Enable API key authentication**
3. **Configure CORS origins** appropriately
4. **Use a reverse proxy** (nginx, Apache)
5. **Set up monitoring** and logging
6. **Use Docker** for consistent deployment

### Example Production Docker Command

```bash
docker run -d \
  --name iyp-api \
  -p 8000:8000 \
  -e NEO4J_PASSWORD=your-prod-password \
  -e API_KEY_ENABLED=true \
  -e API_KEYS=your-secure-api-key \
  -e CORS_ORIGINS=https://yourdomain.com \
  --restart unless-stopped \
  iyp-api
```

## 📈 Performance Tips

- Use **simple endpoints** for common queries (faster)
- **Limit result sets** to avoid large responses
- **Cache results** on your client side when possible
- Use **specific return fields** to reduce data transfer
- Monitor **query execution times** in responses

## 🤝 Integration Examples

### Web Application Integration

```javascript
// JavaScript/React example
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'X-API-Key': 'your-api-key' }
});

// Get AS details
const asDetails = await api.get(`/api/v1/as/${asn}`);

// Execute complex query
const queryResult = await api.post('/api/v1/query/execute', {
  query_type: 'builder',
  operations: [/*...*/]
});
```

### Backend Service Integration

```python
# Python service integration
import requests

class IYPClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.headers = {'X-API-Key': api_key} if api_key else {}
    
    def get_as_details(self, asn):
        response = requests.get(
            f"{self.base_url}/api/v1/as/{asn}",
            headers=self.headers
        )
        return response.json()
    
    def find_upstream_providers(self, asn, max_hops=1):
        response = requests.get(
            f"{self.base_url}/api/v1/as/{asn}/upstream",
            params={'max_hops': max_hops},
            headers=self.headers
        )
        return response.json()

# Usage
client = IYPClient('http://localhost:8000', 'your-api-key')
as_info = client.get_as_details(15169)
```

## 📋 API Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": [...],
  "count": 10,
  "query_time_ms": 45.2,
  "cached": false
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error description",
  "error_type": "ValidationError",
  "details": {...}
}
```