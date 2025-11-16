# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IYP Query System - A multi-layer Python application that translates user-friendly queries into Neo4j Cypher for querying internet infrastructure data (ASNs, IP prefixes, organizations, IXPs).

### Core Components

1. **IYP Query Library** (`iyp_query/`) - Python library with SQL-like query builder interface
2. **Translation API** (`api/`) - FastAPI service for method chain to Cypher translation
3. **Streamlit Frontend** (`frontend/app.py`) - Interactive UI for query execution and graph visualization
4. **Companies House Dashboard** (`frontend/pages/2_Companies_House_Dashboard.py`) - UK corporate data analytics dashboard
5. **Authentication System** (`frontend/auth.py`) - Username/password authentication with bcrypt password hashing

### Active Development Branch

**Note:** The `overripe_frontend_fresh/` directory contains the latest development version with additional features:
- Natural Language to Cypher translation via LLM (DeepSeek R1)
- Enhanced API with `/api/v1/nlp/translate` endpoint
- Improved security with API key authentication

## Architecture

### Three-Layer Translation Pipeline

1. **Core Library** (`iyp_query/`): Query builder with three interfaces:
   - High-level domain methods (e.g., `find_upstream_providers()`)
   - SQL-like builder with Q objects (`.find().where(Q('asn') == 15169)`)
   - Raw Cypher escape hatch

2. **Translation API** (`api/`): FastAPI service with three translation modes:
   - **Method Chain Translation**: `.find.with_organizations.upstream` → Cypher
   - **Natural Language Translation** (NEW in `overripe_frontend_fresh/`): "Find Google's upstream providers" → Cypher
   - Direct query execution endpoints
   - Port 8001 (default)

3. **Frontend** (`frontend/`): Streamlit UIs:
   - **IYP Query Interface** (`app.py`): Method chain translator + query visualizer with PyVis graphs
   - **Companies House Dashboard** (`pages/2_Companies_House_Dashboard.py`): Address-based clustering and risk metrics
   - Port 8501 for main app, 8502 for dashboard

### Key Architectural Patterns

**Translation Flow:**
```
Natural Language → LLM (DeepSeek R1) → Cypher Query
Method Chain → IYPQueryBuilder → Cypher Query
Streamlit UI → Neo4j Driver → PyVis Visualization
```

**Critical Implementation Details:**
- API requires `PYTHONPATH=..` to import `iyp_query` library
- Streamlit uses `neo4j+s://` protocol, API uses `bolt+s://`
- NLP translation includes safety validation (no write operations)
- Method name: `with_organizations` (plural), not singular

## Database Schema (Neo4j IYP)

**Key Node Types:** AS, Organization, Prefix (BGPPrefix, GeoPrefix, etc.), IXP, Country, IP, HostName, DomainName, Facility, Tag

**Critical Relationships:**
- `DEPENDS_ON`: Upstream/downstream AS relationships (key for network analysis)
- `MANAGED_BY`: Organization ownership
- `PEERS_WITH`: AS peering at IXPs
- `MEMBER_OF`: IXP membership
- `COUNTRY`: Geographic location
- `EXTERNAL_ID`: Loosely identified entities (Organizations, IXPs)
- `SIBLING_OF`: Same entity with different identifiers

**Schema Location:** `data/schemas/yellow_page_info/`

## Key File Structure

```
iyp_query/                    # Core library - SQL-like query builder
├── builder.py                # IYPQueryBuilder (main interface)
├── conditions.py             # Q, And, Or, Not boolean logic
├── executors.py              # Neo4j connection layer
└── types.py                  # NodeType/RelationshipType enums

api/                          # FastAPI translation service
├── main.py                   # Entry point
├── config.py                 # Settings (env var based)
├── routers/
│   ├── translation.py        # Method chain translation
│   └── nlp_translation.py    # Natural language translation (NEW)
├── services/
│   └── nlp_translation_service.py  # LLM integration (DeepSeek R1)
└── middleware/auth.py        # API key verification

frontend/
├── app.py                    # Main IYP query interface
└── pages/
    ├── 2_Companies_House_Dashboard.py  # UK corporate analytics
    ├── tuesday_mvp.csv       # Companies House data
    └── baselines_final.csv   # National statistics

overripe_frontend_fresh/      # Latest development branch (newer features)
```

## Development Commands

### Environment Setup
```bash
pyenv virtualenv 3.12.9 overripe && pyenv activate overripe
pip install -r requirements.txt        # Core + Streamlit
pip install -r api/requirements.txt    # API service
```

### Running Services

**Full Stack (two terminals):**
```bash
# Terminal 1: Start API
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start Streamlit
streamlit run frontend/app.py
# Access at http://localhost:8501 (IYP Query) and http://localhost:8502 (Companies House Dashboard)
```

**API Only:**
```bash
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# Docs: http://localhost:8001/docs
```

**Streamlit Only (without API - limited functionality):**
```bash
streamlit run frontend/app.py  # Main IYP interface
streamlit run frontend/pages/2_Companies_House_Dashboard.py --server.port 8502  # Dashboard
```

### Testing & Validation

```bash
# Core library validation
python -m iyp_query.examples

# API method chain translation
cd api && python demos/method_chain_demo.py

# API health check
curl http://localhost:8001/api/v1/health

# NLP translation test (requires OPENROUTER_API_KEY)
curl -X POST "http://localhost:8001/api/v1/nlp/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "Find Google'\''s upstream providers"}'

# Code quality
black iyp_query/ api/ && flake8 iyp_query/ api/ && mypy iyp_query/ api/
```

## Data Flow Patterns

### Method Chain Translation
```
User Input: ".find.with_organizations.upstream"
    ↓
Streamlit → API (translation.py) → IYPQueryBuilder → Cypher Query
    ↓
Streamlit → Neo4j Driver → PyVis Visualization
```

### Natural Language Translation (NEW)
```
User Input: "Find Google's upstream providers"
    ↓
Streamlit → API (nlp_translation.py) → DeepSeek R1 LLM → Cypher Query
    ↓
Safety Validation (no CREATE/DELETE/SET) → Streamlit → Neo4j → Results
```

### Key Implementation Details

**Neo4j Connection Differences:**
- Streamlit frontend: `neo4j+s://iyp.christyquinn.com:7687` (SSL)
- API/Library: `bolt+s://iyp.christyquinn.com:7687` (SSL Bolt)

**Common Pitfalls:**
- API import error: Must use `PYTHONPATH=..` when running from `api/` directory
- Method naming: Use `with_organizations()` (plural), not `with_organization()`
- Query safety: NLP translation auto-validates against write operations
- Large result sets: Always use `.limit()` to prevent performance issues

## Configuration

### Environment Variables

**Core Variables:**
```bash
NEO4J_URI=neo4j+s://iyp.christyquinn.com:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=lewagon25omgbbq
API_BASE_URL=http://localhost:8001
```

**NLP Translation (NEW):**
```bash
OPENROUTER_API_KEY=your-key-here  # For natural language translation
VALID_API_KEYS=key1,key2,key3     # Comma-separated API keys for auth
```

**Setup:**
```bash
cp .env.example .env && cp api/.env.example api/.env
# Edit .env files with your credentials
```

**Deployment Notes:**
- Never commit `.env` files to version control
- Use Streamlit Cloud secrets management for production
- Change default credentials in production
- Heroku: `heroku config:set VAR=value`
- Railway: Set in dashboard

### Database-Specific Notes

**Critical Relationships for Network Analysis:**
- `DEPENDS_ON`: Upstream/downstream provider chains
- `EXTERNAL_ID`: Resolves loosely identified entities (Organizations, IXPs)
- `SIBLING_OF`: Links same entity with different identifiers

**Query Best Practices:**
- Always use `.to_cypher()` for debugging generated queries
- Validate queries before execution (built into IYPQueryBuilder)
- Use parameterized queries to prevent Cypher injection
- Apply `.limit()` for exploratory queries

## Usage Examples

### Python Library (Direct)
```python
from iyp_query import connect, Q, And

iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'password')

# SQL-like query building
results = (iyp.builder()
    .find('AS', asn=15169)  # Google
    .with_organizations()
    .upstream(hops=2)
    .where(Q('upstream.asn').in_([174, 3356, 1299]))  # Tier-1 providers
    .limit(10)
    .execute())

# High-level domain methods
providers = iyp.find_upstream_providers(asn=216139)
peers = iyp.find_peers_at_ixp('DE-CIX Frankfurt')

# Debug: View generated Cypher
cypher, params = iyp.builder().find('AS', asn=15169).to_cypher()
```

### API (Method Chain Translation)
```bash
curl -X POST "http://localhost:8001/api/v1/translate/method-chain" \
  -H "Content-Type: application/json" \
  -d '{"method_chain": ".find.with_organizations.upstream", "parameters": {"asn": 15169}}'
```

### API (Natural Language Translation - NEW)
```bash
curl -X POST "http://localhost:8001/api/v1/nlp/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "Find all ASes operated by Cloudflare"}'
```

### Available Method Chains
`.find` | `.with_organizations` | `.upstream` | `.downstream` | `.peers` | `.in_country` | `.with_relationship` | `.limit`

## Troubleshooting

**Connection Issues:**
- Verify protocol: `bolt+s://` for API/library, `neo4j+s://` for Streamlit
- Check credentials and network access to `iyp.christyquinn.com:7687`

**API Import Errors:**
- Must run API with `PYTHONPATH=..` from `api/` directory
- Example: `cd api && PYTHONPATH=.. python -m uvicorn main:app`

**Query Errors:**
- Use `.to_cypher()` to debug generated queries
- Check node/relationship types in `iyp_query/types.py`
- Verify method names (plural: `with_organizations`, not singular)

**NLP Translation Issues:**
- Requires `OPENROUTER_API_KEY` environment variable
- Only generates safe read-only queries (MATCH, WHERE, RETURN)
- Test connection: `curl http://localhost:8001/api/v1/nlp/test`

## Streamlit Frontend Features

### IYP Query Interface (`frontend/app.py`)
- **Method Chain Translator**: Converts `.find.upstream` syntax to Cypher via API
- **Query Visualizer**: Executes Cypher and renders interactive PyVis network graphs
  - Auto-color by node type (AS=red, Organization=teal, Country=blue)
  - Hover tooltips with properties
  - Force-directed layout
- **Python Interpreter**: Run pandas/numpy code on query results in real-time
- **Tabular Display**: DataFrames alongside visualizations

### Companies House Dashboard (`frontend/pages/2_Companies_House_Dashboard.py`)
- **Address-Based Clustering**: Identifies company concentration hubs
- **Risk Metrics**: Compares local patterns to UK national baselines
  - Dormant company rates (national: 12.4%)
  - No accounts filed (national: 25.9%)
  - Micro entity % (national: 29.5%)
- **Data Files**:
  - `tuesday_mvp.csv`: 4.5MB Companies House data
  - `baselines_final.csv`: UK national statistics
- **Default Analysis**: "71-75 SHELTON STREET", postcode "WC2H 9JQ"
- **Session State**: Smart reset (preserves defaults on refresh, clears on explicit reset)

### Service Ports
- API Documentation: http://localhost:8001/docs
- IYP Query UI: http://localhost:8501
- Companies House Dashboard: http://localhost:8502

## Authentication System

### Overview

The Streamlit frontend includes a simple, secure authentication system with username/password login.

**Features:**
- ✅ Simple login page with username + password
- ✅ Secure bcrypt password hashing (12 rounds)
- ✅ Session-based authentication across all pages
- ✅ Logout functionality
- ✅ Role-based access control (admin, analyst, viewer)
- ✅ User management via CLI utilities

### Quick Start

**Default Test Credentials (CHANGE IN PRODUCTION!):**
- Username: `admin`, Password: `admin123` (admin role)
- Username: `demo`, Password: `demo123` (viewer role)
- Username: `analyst`, Password: `demo123` (analyst role)

**Login:**
```bash
streamlit run frontend/app.py
# Navigate to http://localhost:8501
# Login page will appear automatically
```

### File Structure

```
frontend/
├── auth.py                    # Authentication module
├── users.json                 # User database (GITIGNORED - contains real passwords)
├── users.example.json         # Template file (safe to commit)
├── scripts/
│   └── hash_password.py       # Password hashing utility
├── AUTH_README.md            # Complete user guide
└── QUICK_START_AUTH.md       # Quick reference
```

### User Management

**Add New User:**
```bash
# 1. Generate password hash
cd frontend/scripts
python hash_password.py
# Enter password when prompted, copy the hash

# 2. Edit frontend/users.json
{
  "users": {
    "newuser": {
      "password_hash": "$2b$12$PASTE_HASH_HERE",
      "full_name": "User Full Name",
      "role": "admin",
      "enabled": true
    }
  }
}
```

**Change Password:**
1. Generate new hash: `python frontend/scripts/hash_password.py`
2. Replace `password_hash` in `users.json`

**Disable User:** Set `"enabled": false` in their entry

### User Roles

- **admin**: Full access (queries, translator, Python code, dashboards, user management)
- **analyst**: Queries, translator, dashboards (no Python code execution)
- **viewer**: Dashboards only (read-only access)

### Security Features

- **Password Security**: Bcrypt hashing (12 rounds), passwords never in plaintext
- **File Security**: `users.json` gitignored, won't be committed to repository
- **Session Management**: Session-based auth via Streamlit session state
- **Protected Files**:
  - ✅ `frontend/users.json` (real passwords) - GITIGNORED
  - ✅ `.streamlit/secrets.toml` - GITIGNORED
  - ✅ `.env` files - GITIGNORED

### Documentation

- **Quick Start**: `frontend/QUICK_START_AUTH.md`
- **User Guide**: `frontend/AUTH_README.md`
- **Implementation Details**: `AUTHENTICATION_SETUP.md`

### Important Notes

⚠️ **SECURITY WARNINGS:**
- Change all default passwords before production deployment!
- `users.json` is gitignored - never commit real passwords
- Use strong passwords (12+ characters, mixed case, numbers, symbols)
- Backup `users.json` securely (not in git)

## Deployment

### Streamlit Cloud
```bash
# 1. Push to GitHub
git add . && git commit -m "Deploy" && git push origin main

# 2. Streamlit Cloud dashboard:
# - Main file: frontend/app.py (IYP Query)
# - Main file: frontend/pages/2_Companies_House_Dashboard.py (Dashboard)

# 3. Add secrets (IYP Query only):
[database]
NEO4J_URI = "neo4j+s://iyp.christyquinn.com:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lewagon25omgbbq"

[api]
API_BASE_URL = "https://your-api.herokuapp.com"
```

### Heroku (API Service)
```bash
heroku create your-api
heroku config:set NEO4J_URI=bolt+s://iyp.christyquinn.com:7687
heroku config:set NEO4J_USERNAME=neo4j
heroku config:set NEO4J_PASSWORD=lewagon25omgbbq
heroku config:set OPENROUTER_API_KEY=your-key  # For NLP translation
heroku config:set VALID_API_KEYS=key1,key2
echo "web: cd api && python -m uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
git push heroku main
```

### Railway (Alternative)
- Connect GitHub repo
- Set environment variables in dashboard
- Auto-deploy on push
- See `railway.toml` for configuration

### Docker
```bash
cd api && docker-compose up --build
```

**Security Checklist:**
- ✅ Never commit `.env` files
- ✅ Use secrets management in production
- ✅ Change default credentials
- ✅ Rotate API keys periodically

## Additional Resources

**Documentation:**
- See `docs/` directory for detailed guides
- API docs at `/docs` endpoint when API is running
- Examples in `api/demos/` and `iyp_query/examples.py`

**Development Files:**
- `DEPLOYMENT_GUIDE.md`: Separated frontend/backend deployment strategy
- `README.md`: Project overview and quick start guide
- `data/schemas/yellow_page_info/`: Complete Neo4j schema documentation
- `docs/deployment/STREAMLIT_DEPLOYMENT.md`: Detailed Streamlit Cloud deployment
- `docs/development/SYNTAX.md`: Query syntax reference

## Known Issues & Notes

**Active Development:**
- The `overripe_frontend_fresh/` directory contains newer features (NLP translation, enhanced security)
- Consider migrating changes from `overripe_frontend_fresh/` to main directories
- `temp_sync/` directory appears to be a backup - verify before deletion

**Git Status:**
- `private_backend/` directory deleted (see git status)
- Several untracked files in `overripe_frontend_fresh/` - commit if needed

**Common Fixes:**
- Streamlit deprecated warnings: Use `width="stretch"` instead of `use_container_width=True`
- CSV path issues: Use absolute paths with `os.path.dirname(__file__)`
- AST parsing: Use `ast.literal_eval()` for JSON-stored lists in DataFrames
