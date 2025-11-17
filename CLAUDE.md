# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**OverRipe IYP Query System** - A three-layer Python application for querying Internet Yellow Pages (IYP) Neo4j database containing network infrastructure data (ASNs, IP prefixes, organizations, IXPs).

### Architecture Components

1. **IYP Query Library** (`iyp_query/`) - Core Python library with SQL-like query builder
2. **Translation API** (`api/`) - FastAPI service for method chain to Cypher translation
3. **Streamlit Frontend** (`frontend/`) - Two interactive UIs:
   - **Main App** (`app.py`) - IYP Query translator, executor, and graph visualizer
   - **Companies House Dashboard** (`pages/2_Companies_House_Dashboard.py`) - UK corporate data analytics
   - **Demo Workflow** (`pages/1_Demo_Workflow.py`) - Graph query testing interface
4. **Authentication System** (`frontend/auth.py`) - Bcrypt-based username/password authentication

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
pyenv virtualenv 3.12.9 overripe && pyenv activate overripe

# Install dependencies
pip install -r requirements.txt        # Frontend + core library
pip install -r api/requirements.txt    # API service
```

### Running Services

**Local Development (Full Stack):**
```bash
# Terminal 1: API Service
cd api
PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Streamlit Frontend
streamlit run frontend/app.py
# Main app: http://localhost:8501
# Dashboard: http://localhost:8502 (auto-starts if 8501 in use)
```

**API Only:**
```bash
cd api
PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# API docs: http://localhost:8001/docs
```

**Frontend Only:**
```bash
streamlit run frontend/app.py
# Works without API - method chain translation will fail but direct queries work
```

### Testing & Validation
```bash
# Test core library
python -m iyp_query.examples

# Test API translation
cd api && python demos/method_chain_demo.py

# API health check
curl http://localhost:8001/api/v1/health

# Code quality
black iyp_query/ api/ frontend/ && \
flake8 iyp_query/ api/ && \
mypy iyp_query/ api/
```

## Critical Architecture Patterns

### 1. Neo4j Connection - Two Protocols
- **Streamlit**: Uses `neo4j+s://` protocol (Neo4j Python driver)
- **API/Library**: Uses `bolt+s://` protocol (Bolt protocol)
- Both connect to the same host, just different protocol prefixes

### 2. Credentials Management - Dual Source Pattern
**IMPORTANT:** All database credentials use environment-first, never hardcoded.

**Streamlit Cloud (Production):**
```python
# Check st.secrets FIRST (root level, not nested)
if "NEO4J_URI" in st.secrets:
    URI = st.secrets["NEO4J_URI"]
# Then fall back to os.getenv() for local dev
```

**Local Development:**
```bash
# .env file (gitignored)
NEO4J_URI=neo4j+s://host:7687
NEO4J_USERNAME=username
NEO4J_PASSWORD=password
```

**Streamlit Secrets Format (MUST be root level):**
```toml
# Correct - root level
NEO4J_URI = "neo4j+s://host:7687"
NEO4J_USERNAME = "username"
NEO4J_PASSWORD = "password"

# Authentication users (in section)
[users]
[users.admin]
password_hash = "..."
```

### 3. Authentication Pattern
All Streamlit pages MUST include at module level (before ANY other Streamlit commands):
```python
from auth import check_authentication, show_logout_button

# MUST be right after st.set_page_config() or at top of file
if not check_authentication():
    st.stop()
```

**User Management:**
- Users stored in `frontend/users.json` (gitignored) OR Streamlit Secrets `[users]` section
- Passwords hashed with bcrypt (12 rounds)
- Generate hashes: `python frontend/scripts/hash_password.py`
- Three roles: `admin`, `analyst`, `viewer`

### 4. Streamlit Multipage Pattern
**CRITICAL:** Do NOT wrap page code in functions called at module level.

**❌ WRONG:**
```python
def run_page():
    st.title("My Page")
    # ... page code

run_page()  # Called at module level - st.secrets may not be ready
```

**✅ CORRECT:**
```python
# Code executes directly at module level
st.title("My Page")
# ... page code
```

### 5. Lazy Driver Initialization
Database drivers MUST be created inside button click handlers, never at module level:

```python
def get_neo4j_driver():
    """Get driver - call this inside button handlers"""
    # Check secrets, then env vars, then raise error
    return GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# ✅ CORRECT - inside button handler
if st.button("Run Query"):
    driver = get_neo4j_driver()
    results = run_query(query, driver)

# ❌ WRONG - at module level
driver = get_neo4j_driver()  # Will fail on Streamlit Cloud
```

## Key Database Schema

**Node Types:**
- `AS` - Autonomous Systems (property: `asn`)
- `Organization` - Network operators (property: `name`)
- `Prefix` - IP prefixes (subtypes: BGPPrefix, GeoPrefix)
- `IXP` - Internet Exchange Points
- `Country` - Geographic entities (property: `country_code`)

**Critical Relationships:**
- `DEPENDS_ON` - Upstream/downstream AS dependencies (network analysis)
- `MANAGED_BY` - Organization ownership
- `PEERS_WITH` - AS peering at IXPs
- `MEMBER_OF` - IXP membership
- `COUNTRY` - Geographic location
- `EXTERNAL_ID` - Resolves loosely identified entities
- `SIBLING_OF` - Links same entity with different identifiers

**Schema Location:** `data/schemas/yellow_page_info/`

## Method Chain Translation Flow

```
User Input: ".find.with_organizations.upstream"
    ↓
Streamlit → API POST /api/v1/translate/method-chain
    ↓
API uses IYPQueryBuilder → Generates Cypher
    ↓
Returns: {"success": true, "cypher": "MATCH...", "parameters": {...}}
    ↓
Streamlit executes Cypher → Neo4j → PyVis graph visualization
```

**Available Method Chains:**
- `.find` - Basic node lookup
- `.with_organizations` - Include organization info (**plural**, not singular)
- `.upstream` - Find upstream providers (params: `hops`)
- `.downstream` - Find downstream customers
- `.peers` - Find peering partners
- `.in_country` - Filter by country
- `.with_relationship` - Custom relationship traversal
- `.limit` - Limit results

## Common Pitfalls & Solutions

### 1. API Import Errors
**Problem:** `ModuleNotFoundError: No module named 'iyp_query'`
**Solution:** MUST use `PYTHONPATH=..` when running API from `api/` directory
```bash
cd api && PYTHONPATH=.. python -m uvicorn main:app
```

### 2. Streamlit Secrets Access
**Problem:** Credentials not found despite being in secrets
**Solution:**
- Ensure credentials are at ROOT level, not nested under `[database]` section
- Use bracket notation: `st.secrets["KEY"]` not `st.secrets.get("KEY")`
- Check with: `list(st.secrets.keys())` to debug

### 3. Method Naming
**Problem:** `.with_organization()` fails
**Solution:** Use **plural**: `.with_organizations()` (note the 's')

### 4. Query Performance
**Problem:** Slow or hanging queries
**Solution:**
- Always use `.limit()` for exploratory queries
- Check generated Cypher with `.to_cypher()` before executing
- Use `max_records` parameter in `run_query()`

### 5. Password Leakage Prevention
**Files that MUST stay gitignored:**
- `.env` and `api/.env` - Local credentials
- `frontend/users.json` - Password hashes
- `CLAUDE.md` - This file (contains setup context)
- `.streamlit/secrets.toml` - Local secrets

**Never commit:**
- Hardcoded credentials (use `os.getenv()` always)
- Real passwords in example files
- Database connection strings with credentials

## Companies House Dashboard Specifics

**Data Files (in `frontend/pages/`):**
- `tuesday_mvp.csv` - 4.5MB Companies House data
- `baselines_final.csv` - UK national statistics

**Key Features:**
- Address-based clustering analysis
- Risk metrics vs national baselines:
  - Dormant company rate (baseline: 12.4%)
  - No accounts filed (baseline: 25.9%)
  - Micro entity % (baseline: 29.5%)
- Default analysis: "71-75 SHELTON STREET", postcode "WC2H 9JQ"

**Important:** Uses `ast.literal_eval()` to parse JSON-stored lists in DataFrames

## Configuration Files

**.env Structure (both root and api/):**
```bash
# Neo4j Connection
NEO4J_URI=neo4j+s://host:7687  # or bolt+s:// for API
NEO4J_USERNAME=username
NEO4J_PASSWORD=password

# API Service (for API only)
API_KEY_ENABLED=false
API_KEYS=test-key-1,test-key-2
RATE_LIMIT_REQUESTS=100
```

**Environment Variable Names:**
- Neo4j: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` (Note: API uses `NEO4J_USER` in some places, not `NEO4J_USERNAME`)
- API: `API_BASE_URL` (default: `https://overripefrontend-production.up.railway.app`)

## Deployment Notes

**Streamlit Cloud:**
- Main file: `frontend/app.py`
- Configure secrets in dashboard (root level, not nested)
- Both Neo4j credentials AND `[users]` section needed
- Auto-deploys on git push

**API Service (Railway/Heroku):**
```bash
# Set environment variables in dashboard
NEO4J_URI=bolt+s://host:7687
NEO4J_USER=username  # Note: USER not USERNAME
NEO4J_PASSWORD=password
```

**Railway Config:** See `railway.toml` for build/start commands

## File Structure Reference

```
iyp_query/              # Core query builder library
├── builder.py          # Main IYPQueryBuilder class
├── conditions.py       # Q, And, Or, Not boolean logic
├── executors.py        # Neo4j connection & execution
├── types.py            # NodeType/RelationshipType enums
└── examples.py         # Usage examples

api/                    # FastAPI translation service
├── main.py             # FastAPI app entry point
├── config.py           # Settings (validates env vars)
├── routers/
│   ├── translation.py  # Method chain translation endpoint
│   ├── query.py        # Direct query execution
│   └── search.py       # Search endpoints
└── services/
    └── translation_service.py  # Translation logic

frontend/
├── app.py              # Main IYP query interface
├── auth.py             # Authentication module
├── utils.py            # Shared utilities (driver, queries, viz)
├── pages/
│   ├── 1_Demo_Workflow.py          # Graph query testing
│   └── 2_Companies_House_Dashboard.py  # UK corporate analytics
└── scripts/
    └── hash_password.py  # Password hashing utility
```

## Security Best Practices

1. **Never commit real credentials** - use environment variables only
2. **Streamlit Secrets at root level** - not nested under sections (except `[users]`)
3. **Use bracket notation** for st.secrets - `st.secrets["KEY"]`
4. **Lazy driver initialization** - create drivers inside button handlers
5. **Validate env vars on startup** - `api/config.py` does this for API
6. **Gitignore sensitive files** - `.env`, `users.json`, `secrets.toml`
7. **Strong passwords** - 12+ characters, bcrypt hashing for user auth
8. **API keys** - Use `API_KEY_ENABLED=true` and secure keys in production

## Quick Debug Commands

```bash
# Check what secrets are available
python -c "import streamlit as st; print(list(st.secrets.keys()))"

# Test Neo4j connection
python -c "from neo4j import GraphDatabase; import os; \
driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), \
auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))); \
driver.verify_connectivity(); print('✅ Connected')"

# Generate password hash
python frontend/scripts/hash_password.py

# View API config
cd api && python -c "from config import settings; print(settings)"
```

## Common Development Tasks

**Add new user:**
1. Generate hash: `python frontend/scripts/hash_password.py`
2. Edit `frontend/users.json` or Streamlit Secrets `[users]` section
3. Add entry with `password_hash`, `full_name`, `role`, `enabled`

**Add new Streamlit page:**
1. Create `frontend/pages/N_Page_Name.py` (N is sort order)
2. Add authentication check at top
3. Add `show_logout_button()` in sidebar
4. Code directly at module level (no wrapper function)

**Add new API endpoint:**
1. Create router in `api/routers/`
2. Import and include in `api/main.py`
3. Add service logic in `api/services/` if complex
4. Update API docs

**Modify graph visualization:**
- Edit `frontend/utils.py` - `create_graph_visualization()` function
- Uses PyVis for rendering
- Node colors mapped by label (AS=red, Organization=teal, etc.)
