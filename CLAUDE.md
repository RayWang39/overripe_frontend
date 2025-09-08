# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains four main components:

## Primary Components

### IYP (Internet Yellow Pages) System
Three interconnected components for querying and visualizing the Neo4j Internet Yellow Pages Database:

1. **IYP Query Library** (`iyp_query/`) - Core Python library providing SQL-like query builder interface
2. **Method Chain Translation API** (`api/`) - FastAPI service that translates method chains to Cypher queries
3. **Streamlit Frontend** (`frontend/app.py`) - Interactive web interface for query execution and graph visualization

The core mission is to allow technical users to query internet infrastructure data (ASNs, IP prefixes, organizations, IXPs, etc.) WITHOUT needing to learn Cypher query language.

### Companies House Dashboard System
4. **Companies House Dashboard** (`frontend/pages/streamlit_dashboard_mvp.py`) - Advanced analytics dashboard for UK Companies House data analysis with address-based clustering and risk assessment

## Architecture Components

### 1. IYP Query Library (`iyp_query/`)
Core Python library with three query interfaces:
- **High-Level Domain-Specific Methods** - Pre-built queries for common network analysis
- **SQL-like Query Builder** - Chainable methods with Q objects for complex boolean conditions
- **Raw Cypher Escape Hatch** - Direct Cypher execution for advanced users

### 2. Method Chain Translation API (`api/`)
FastAPI web service for **translation-only**:
- Converts method chains like `.find.with_organizations.upstream` into Cypher queries
- Does NOT execute queries - only generates them for integration into other systems
- Provides REST endpoints for programmatic Cypher generation
- Runs on port 8001 by default

### 3. Streamlit Frontend (`frontend/app.py`)
Interactive web interface with two main features:
- **Method Chain Translator** - Converts method chains to Cypher queries via API integration
- **Query Visualizer** - Executes Cypher queries and displays results as interactive network graphs using PyVis
- Integrates with the Translation API for method chain conversion
- Direct connection to Neo4j for query execution and visualization
- Runs on port 8501 by default

### 4. Companies House Dashboard (`frontend/pages/streamlit_dashboard_mvp.py`)
Advanced analytics dashboard for UK Companies House corporate data analysis:
- **Address-Based Clustering** - Groups companies by physical addresses to identify hub locations
- **Risk Assessment Metrics** - Compares company filing patterns against national baselines
- **Interactive Visualizations** - Hub distribution charts, company metrics, and outlier detection
- **Geographic Analysis** - Postcode-level company concentration analysis
- **Company Profile Details** - Individual company information with filing status and dormancy tracking
- **Baseline Comparison** - National averages for micro entities, dormant companies, and filing exemptions
- **Export and Documentation** - Comprehensive help section and data export capabilities

## Database Schema

### Node Types (from data/schemas/yellow_page_info)
Key node types include: AS, Organization, Prefix (with subtypes: BGPPrefix, GeoPrefix, RIRPrefix, RPKIPrefix, PeeringLAN, RDNSPrefix), IXP, Country, IP, HostName, DomainName, Facility, Tag, URL, and various ID nodes (CaidaIXID, CaidaOrgID, PeeringdbIXID, etc.)

### Relationship Types (from data/schemas/yellow_page_info)
Critical relationships: DEPENDS_ON (upstream providers), MANAGED_BY (organization ownership), PEERS_WITH (AS peering), MEMBER_OF (IXP membership), COUNTRY (location), CATEGORIZED (tagging), ORIGINATE (BGP prefix origination)

## Project Structure

```
# Core Python Library
iyp_query/                  # Core query library
├── __init__.py            # Public API exports (connect, Q, And, Or, etc.)
├── builder.py             # IYPQueryBuilder - main SQL-like interface
├── conditions.py          # Q, And, Or, Not boolean logic
├── domain.py              # IYPQuery - high-level domain methods
├── executors.py           # IYPDatabase, QueryExecutor - Neo4j connection
├── traversals.py          # TraversalBuilder, CommonTraversals
├── types.py               # NodeType, RelationshipType enums
├── validators.py          # QueryValidator, validation logic
└── examples.py            # Usage examples and demonstrations

# FastAPI Translation Service
api/                        # Web API for method chain translation
├── main.py                # FastAPI application entry point
├── config.py              # Configuration settings
├── models/                # Pydantic request/response models
├── routers/               # API route handlers
├── services/              # Business logic layer
├── middleware/            # Custom middleware
├── static/                # Web interface
├── docs/                  # API documentation
├── demos/                 # Example scripts
├── scripts/               # Utility scripts
└── requirements.txt       # API-specific dependencies

# Streamlit Frontend
frontend/                   # Interactive web interfaces
├── app.py                 # Main IYP Query interface
├── pages/                 # Additional dashboard pages
│   ├── streamlit_dashboard_mvp.py  # Companies House dashboard
│   ├── tuesday_mvp.csv    # Companies House data (4.5MB)
│   └── baselines_final.csv # UK national company filing baselines
└── utils.py               # Shared utilities

# Documentation
docs/                       # Organized documentation
├── user-guides/           # Getting started and tutorials
├── api-docs/             # API reference docs
├── development/          # Development guides
├── deployment/           # Deployment configs
└── examples/             # Example queries

# Data
data/                       # Organized data files
├── samples/              # Sample datasets
└── schemas/              # Database schemas
    └── yellow_page_info/ # IYP database schema

# Analysis
notebook/                   # Data analysis notebooks
testing_data/              # Test data
requirements.txt          # Core dependencies
```

## Development Commands

### Environment Setup
```bash
# Create virtual environment
pyenv virtualenv 3.12.9 overripe
pyenv activate overripe

# Install dependencies (choose based on what you're working on)
pip install -r requirements.txt                    # Core library
pip install -r api/requirements.txt               # API service
```

### IYP Query Library Development
```bash
# Test the core library
python -m iyp_query.examples

# Interactive development
python
>>> from iyp_query import connect, Q, And
>>> iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'lewagon25omgbbq')
>>> results = iyp.builder().find('AS', asn=15169).execute()

# Debug queries (see generated Cypher)
>>> query = iyp.builder().find('AS', asn=15169).upstream(hops=2)
>>> cypher, params = query.to_cypher()
>>> print(cypher)
```

### Running the Full Stack

```bash
# 1. Start the Translation API (required for Streamlit)
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 2. Start the IYP Streamlit Frontend (in a new terminal)
streamlit run frontend/app.py

# 3. Start the Companies House Dashboard (optional, in a new terminal)
streamlit run frontend/pages/streamlit_dashboard_mvp.py --server.port 8502

# The system will be available at:
# - IYP Query UI: http://localhost:8501
# - Companies House Dashboard: http://localhost:8502
# - API Documentation: http://localhost:8001/docs
# - API Interactive Test: http://localhost:8001
```

### API-Only Development
```bash
# Using helper script
./api/scripts/run_api.sh

# Using Docker
cd api && docker-compose up --build

# Test the API
cd api && python demos/method_chain_demo.py

# Manual API testing
curl -X POST "http://localhost:8001/api/v1/translate/method-chain" \
  -H "Content-Type: application/json" \
  -d '{"method_chain": ".find.with_organizations", "parameters": {"asn": 15169}}'
```

### Testing
```bash
# Currently no formal test suite - validate manually:

# Core library validation
python -m iyp_query.examples

# API service validation
cd api && python demos/method_chain_demo.py

# Health check
curl http://localhost:8001/api/v1/health
```

### Code Quality
```bash
# Format code
black iyp_query/ api/

# Linting
flake8 iyp_query/ api/

# Type checking
mypy iyp_query/ api/
```

## Key Architecture Concepts

### Three-Layer Architecture
1. **Core Library** (`iyp_query/`): Direct database execution with complex query building
2. **Translation API** (`api/`): Translation-only service for generating Cypher queries
3. **Streamlit Frontend** (`frontend/`): User interface combining translation and visualization

### Data Flow Patterns

#### Method Chain Translation Flow
1. User enters method chain in Streamlit UI
2. Streamlit calls Translation API endpoint
3. API's `CypherTranslationService` parses the chain
4. Uses `iyp_query` library to build query with method chaining
5. Returns Cypher query to Streamlit
6. Streamlit can execute the query directly against Neo4j

#### Direct Query Execution Flow
1. User enters Cypher query in Streamlit
2. Streamlit executes query directly against Neo4j
3. Results processed and visualized using PyVis network graphs
4. Data also displayed in tabular format

### Important Class Relationships
```python
# Translation Flow
Streamlit -> MethodChainRequest -> API -> CypherTranslationService -> IYPQueryBuilder -> Cypher

# Execution Flow
Streamlit -> Neo4j Driver -> Query Results -> PyVis Visualization

# Core Library Flow
connect() -> IYPQuery -> IYPQueryBuilder -> QueryExecutor -> Results
```

## Database Configuration

### Environment Variables (Recommended for Deployment)
The application now uses environment variables for secure configuration:

```bash
# Required environment variables
NEO4J_URI=neo4j+s://iyp.christyquinn.com:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=lewagon25omgbbq
API_BASE_URL=http://localhost:8001
```

### Default Configuration (Development)
If environment variables are not set, the system falls back to:
- **URI**: neo4j+s://iyp.christyquinn.com:7687 (Streamlit) / bolt+s://iyp.christyquinn.com:7687 (API)
- **Credentials**: neo4j / lewagon25omgbbq
- **Connection**: SSL-enabled Neo4j Bolt protocol
- **API Base**: http://localhost:8001

### Setup Instructions
1. Copy `.env.example` to `.env` in the root directory
2. Copy `api/.env.example` to `api/.env` for API-specific configuration
3. Update values as needed for your environment

## Critical Implementation Notes

- **DEPENDS_ON relationship** is crucial for finding upstream providers
- **EXTERNAL_ID relationships** handle loosely identified entities (Organizations, IXPs)
- **SIBLING_OF relationships** indicate the same entity with different identifiers
- Some entities have multiple subtypes (e.g., Prefix has BGPPrefix, GeoPrefix, etc.)
- Always validate queries before sending to Neo4j to fail fast
- Include .to_cypher() method for debugging generated queries
- Implement proper Cypher injection prevention

## Common Usage Patterns

### Core Library Usage
```python
from iyp_query import connect, Q, And

# Connect and query
iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'lewagon25omgbbq')
results = (iyp.builder()
    .find('AS', asn=15169)
    .with_organizations()
    .upstream(hops=2)
    .where(Q('upstream.asn').in_([174, 3356, 1299]))
    .execute())
```

### API Service Usage
```bash
# Method chain translation
curl -X POST "http://localhost:8001/api/v1/translate/method-chain" \
  -H "Content-Type: application/json" \
  -d '{
    "method_chain": ".find.with_organizations.upstream",
    "parameters": {"asn": 15169, "hops": 2}
  }'
```

### Available Method Chains
- `.find` - Basic node lookup
- `.find.with_organizations` - Include organization details
- `.find.upstream` - Find upstream providers
- `.find.downstream` - Find downstream customers
- `.find.peers` - Find peering partners
- `.find.with_relationship` - Custom relationship traversal
- `.find.upstream.limit` - Complex chains with multiple methods

## Troubleshooting Common Issues

### Database Connection Issues
- Ensure the Neo4j URI uses `bolt+s://` for SSL connections
- Verify credentials are correct for the live IYP database
- Connection is established on startup - check startup logs for connection status

### Query Validation Errors
- **Invalid node types**: Use enums from `types.py` for validation
- **Cypher syntax errors**: Check generated Cypher with `.to_cypher()` method for debugging
- **Large result sets**: Use `.limit()` in queries to prevent performance issues

### API Service Issues
- **Import errors**: API service requires `PYTHONPATH=..` to import `iyp_query` library
- **Port conflicts**: Default API port is 8001, not 8000
- **Method name mismatches**: Use `with_organizations` (plural), not `with_organization`

## Streamlit Frontend Features

### Method Chain Translator Section
- Converts method chains to Cypher queries using the Translation API
- Input fields for ASN and additional JSON parameters
- "Use This Cypher Query" button to copy translated query to main query box
- Comprehensive help section with examples

### Query Visualizer Section
- Direct Cypher query execution against Neo4j
- Interactive network graph visualization using PyVis
- Automatic node coloring by type (AS=red, Organization=teal, Country=blue, etc.)
- Tabular data display alongside graph
- Handles nodes, relationships, paths, and aggregated results

### Python Interpreter Section
- Execute Python code on query results in real-time
- Access to query results as pandas DataFrames, node lists, and relationship lists
- Pre-imported libraries: pandas, numpy, collections, itertools
- Three-tab interface: Code Editor, Data Preview, Available Variables
- Captures print output and displays new DataFrames created
- Includes example code snippets and variable documentation
- Shows column statistics and data types

### Visualization Capabilities
- Processes Neo4j nodes, relationships, and path objects
- Creates virtual nodes for scalar/aggregated data
- Hover tooltips showing node/relationship properties
- Force-directed graph layout for optimal viewing
- Filters out "connecting" relationships for cleaner visualization

## Working Configuration

### Current Database Connection
- **URI**: `neo4j+s://iyp.christyquinn.com:7687` (SSL-enabled for Streamlit)
- **URI**: `bolt+s://iyp.christyquinn.com:7687` (SSL-enabled for API/Library)
- **Credentials**: `neo4j` / `lewagon25omgbbq`
- **Connection verified working** as of current session

### Service Ports
- **Translation API**: http://localhost:8001
- **IYP Query Frontend**: http://localhost:8501
- **Companies House Dashboard**: http://localhost:8502 (when running)
- **Jupyter Notebooks**: http://localhost:8888

### File Organization Status
- ✅ **API files organized** in `/api/` directory structure
- ✅ **Streamlit frontend** in `/frontend/app.py` with full integration
- ✅ **Documentation created** with README files and quick start guides
- ✅ **Demo scripts working** in `/api/demos/`
- ✅ **Git cleanup completed** with proper `.gitignore` to prevent cache file conflicts
- ✅ **Method chain translation fully functional**
- ✅ **Graph visualization working** with PyVis integration
- ✅ **Python interpreter integrated** for data analysis

### Known Working Commands
```bash
# Start full stack (two terminals needed)
# Terminal 1: Start API
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start Streamlit
streamlit run frontend/app.py

# Test API standalone
cd api && python demos/method_chain_demo.py

# Interactive query building (using environment variables)
python -c "from iyp_query import connect; import os; iyp = connect(os.getenv('NEO4J_URI', 'bolt+s://iyp.christyquinn.com:7687'), os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'lewagon25omgbbq')); print('Connected successfully')"

# Run Jupyter notebooks for data analysis
jupyter notebook
```

## Deployment Configuration

### Environment Variables Setup
The application is now configured for secure deployment using environment variables:

#### For Development:
```bash
# Copy example files and customize
cp .env.example .env
cp api/.env.example api/.env
# Edit .env files with your configuration
```

#### For Streamlit Cloud:
Add these secrets in your Streamlit Cloud dashboard:
```toml
[database]
NEO4J_URI = "neo4j+s://iyp.christyquinn.com:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lewagon25omgbbq"

[api]
API_BASE_URL = "https://your-deployed-api.herokuapp.com"
```

#### For Heroku/Cloud Deployment:
```bash
# Set environment variables
heroku config:set NEO4J_URI=neo4j+s://iyp.christyquinn.com:7687
heroku config:set NEO4J_USERNAME=neo4j
heroku config:set NEO4J_PASSWORD=lewagon25omgbbq
heroku config:set API_BASE_URL=https://your-api-url.com
```

#### For Docker Deployment:
```bash
# Use .env file with docker-compose
docker-compose --env-file .env up
```

### Security Notes
- ✅ **Environment variables implemented** for all sensitive configuration
- ✅ **Fallback values provided** for development convenience
- ✅ **Example files created** (`.env.example`) for easy setup
- ⚠️ **Never commit** actual `.env` files to version control
- ⚠️ **Change default credentials** in production environments

## Companies House Dashboard

### Overview
The Companies House Dashboard (`frontend/pages/streamlit_dashboard_mvp.py`) is a comprehensive analytics tool for analyzing UK corporate registration data. It focuses on address-based clustering to identify potential hub locations and assess company filing patterns against national baselines.

### Key Features

#### 1. Address-Based Hub Detection
- Groups companies by physical addresses to identify concentration points
- Default analysis focuses on "71-75 SHELTON STREET" as a high-activity location
- Postcode-level filtering with automatic selection when specific addresses are chosen
- Hub distribution visualizations with outlier detection using IQR methodology

#### 2. Risk Assessment Metrics
- **Baseline Comparison**: Compares local patterns against UK national averages
- **Key Risk Indicators**:
  - Dormant company rates (national average: 12.4%)
  - No accounts filed rates (national average: 25.9%)
  - Micro entity percentages (national average: 29.5%)
  - Full/abbreviated filing patterns

#### 3. Interactive Data Exploration
- **Company Search**: Filter by address, postcode, or company characteristics
- **Dynamic KPIs**: Real-time metrics update based on selected filters
- **Visualization Suite**: 
  - Hub distribution charts with spike detection
  - Company metrics comparison with national baselines
  - Interactive Plotly charts with hover details
- **Reset Functionality**: Smart reset preserves defaults when refreshing, clears all when explicitly reset

#### 4. Documentation and Context
- **Comprehensive Help**: Built-in documentation explaining Companies House data structure
- **Baseline Data Integration**: National filing statistics for context and comparison
- **Data Export**: Access to underlying datasets for further analysis

### Data Sources

#### Primary Dataset (`tuesday_mvp.csv` - 4.5MB)
Contains processed UK Companies House data with fields:
- `PostCode_clean`: Standardized UK postcodes
- `Address_street`: Street addresses for clustering
- `FullAddress_best`: Complete formatted addresses
- `company_ids_list`: JSON arrays of company registration numbers
- `company_names_list`: Corresponding company names
- Company metrics: dormant rates, filing patterns, entity types
- Geographic aggregations: companies per address/postcode

#### Baseline Dataset (`baselines_final.csv`)
National UK statistics for comparison:
- Filing type distributions (micro entity, dormant, full accounts, etc.)
- National percentages for risk assessment
- Used for spike detection and anomaly identification

### Running the Dashboard

```bash
# Standalone dashboard (recommended)
streamlit run frontend/pages/streamlit_dashboard_mvp.py --server.port 8502

# Alternative: Run from pages directory
cd frontend/pages
streamlit run streamlit_dashboard_mvp.py

# The dashboard will be available at: http://localhost:8502
```

### Development Notes

#### Session State Management
The dashboard uses sophisticated Streamlit session state management:
- Differentiates between page refresh (shows defaults) and reset button (clears all)
- Maintains filter state across interactions
- Automatic postcode filtering when specific addresses are selected

#### Key Implementation Details
- **Default Search**: "71-75 SHELTON STREET" with postcode "WC2H 9JQ"
- **Data Loading**: Uses `@st.cache_data` for performance with large datasets
- **AST Parsing**: Safely evaluates JSON-stored company lists using `ast.literal_eval()`
- **Error Handling**: Graceful degradation when data parsing fails

#### Common Fixes Applied
- Fixed deprecated `use_container_width=True` → `width="stretch"`
- Resolved selectbox serialization with explicit type conversions
- Implemented absolute path resolution for CSV loading
- Added conditional logic for display functions

### Architecture Integration
- **Standalone Operation**: Dashboard runs independently without requiring IYP/Neo4j components
- **Shared Infrastructure**: Uses same Streamlit framework and environment as main frontend
- **Data Pipeline**: Processes offline Companies House extracts rather than live API connections
- **Visualization Stack**: Matplotlib, Plotly, and Streamlit native components

## Streamlit Cloud Deployment

### Overview
Both the IYP Query interface and Companies House Dashboard can be deployed on Streamlit Cloud. Each component can be deployed separately as they have different requirements and data dependencies.

### Prerequisites
- GitHub repository with the code
- Streamlit Cloud account (https://streamlit.io/cloud)
- Environment variables and secrets configured

### 1. IYP Query Frontend Deployment

#### Repository Setup
```bash
# Ensure your repository is pushed to GitHub
git add .
git commit -m "Deploy IYP Query Frontend"
git push origin main
```

#### Streamlit Cloud Configuration
- **Main file path**: `frontend/app.py`
- **Python version**: 3.12 (or compatible)
- **Requirements**: Uses root `requirements.txt`

#### Required Secrets (in Streamlit Cloud dashboard):
```toml
[database]
NEO4J_URI = "neo4j+s://iyp.christyquinn.com:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "lewagon25omgbbq"

[api]
API_BASE_URL = "https://your-deployed-api-url.herokuapp.com"
```

### 2. Companies House Dashboard Deployment

#### Repository Setup
The dashboard requires its data files to be in the correct location:
```bash
# Ensure data files are in the repository
ls frontend/pages/tuesday_mvp.csv frontend/pages/baselines_final.csv

# Commit data files (they are required for deployment)
git add frontend/pages/*.csv
git commit -m "Add Companies House data files for deployment"
git push origin main
```

#### Streamlit Cloud Configuration
- **Main file path**: `frontend/pages/streamlit_dashboard_mvp.py`
- **Python version**: 3.12 (or compatible)
- **Requirements**: Uses root `requirements.txt`

#### No Secrets Required
The Companies House Dashboard operates entirely with local CSV files and requires no external API connections or database credentials.

#### Dependencies Check
Ensure your `requirements.txt` includes all necessary packages:
```txt
streamlit
pandas>=1.3.0
matplotlib
plotly
numpy
```

### 3. Deployment Steps

#### Step 1: Prepare Repository
```bash
# Navigate to your repository
cd /path/to/your/repo

# Ensure all files are committed
git status
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### Step 2: Deploy on Streamlit Cloud

**For IYP Query Frontend:**
1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Select your GitHub repository
4. Set main file: `frontend/app.py`
5. Add secrets as shown above
6. Click "Deploy"

**For Companies House Dashboard:**
1. Go to https://streamlit.io/cloud  
2. Click "New app"
3. Select your GitHub repository
4. Set main file: `frontend/pages/streamlit_dashboard_mvp.py`
5. No secrets needed
6. Click "Deploy"

#### Step 3: Post-Deployment Verification

**IYP Query Frontend Checklist:**
- [ ] Neo4j connection established
- [ ] Method chain translation working
- [ ] Graph visualizations rendering
- [ ] Python interpreter functional

**Companies House Dashboard Checklist:**
- [ ] CSV files loading correctly
- [ ] Default search showing "71-75 SHELTON STREET"
- [ ] KPIs displaying properly
- [ ] Interactive charts working
- [ ] Documentation section accessible
- [ ] Reset functionality working

### 4. Troubleshooting Deployment Issues

#### Common IYP Frontend Issues
```bash
# Connection errors
- Verify NEO4J_URI uses neo4j+s:// (not bolt+s://)
- Check API_BASE_URL is accessible from Streamlit Cloud
- Ensure API service is deployed and running

# Import errors
- Verify iyp_query package is properly structured
- Check all dependencies in requirements.txt
```

#### Common Dashboard Issues  
```bash
# File not found errors
- Ensure CSV files are in frontend/pages/ directory
- Verify paths are relative and use os.path.join()
- Check file permissions and git LFS if files are large

# Performance issues
- Consider using st.cache_data for large datasets
- Optimize DataFrame operations
- Reduce visualization complexity if needed
```

### 5. Multiple App Deployment

You can deploy both apps from the same repository:

**App 1 - IYP Query:**
- URL: `https://your-app-iyp-query.streamlit.app`
- Main file: `frontend/app.py`
- Requires: Neo4j secrets

**App 2 - Companies House Dashboard:**
- URL: `https://your-app-companies-house.streamlit.app`
- Main file: `frontend/pages/streamlit_dashboard_mvp.py`
- Requires: No secrets

### 6. Environment Variables for Deployment

#### Local Development (.env file):
```bash
# For local development only - never commit this file
NEO4J_URI=neo4j+s://iyp.christyquinn.com:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=lewagon25omgbbq
API_BASE_URL=http://localhost:8001
```

#### Streamlit Cloud (secrets.toml):
```toml
# Add via Streamlit Cloud dashboard only
[database]
NEO4J_URI = "neo4j+s://iyp.christyquinn.com:7687"
NEO4J_USERNAME = "neo4j" 
NEO4J_PASSWORD = "lewagon25omgbbq"

[api]
API_BASE_URL = "https://your-api-deployment.herokuapp.com"
```

### 7. Production Considerations

#### Security
- ✅ Never commit credentials to repository
- ✅ Use Streamlit Cloud secrets management
- ✅ Rotate passwords periodically
- ⚠️ Monitor access logs for suspicious activity

#### Performance
- ✅ Use `@st.cache_data` for expensive operations
- ✅ Optimize DataFrame operations with pandas
- ✅ Consider data sampling for large datasets
- ⚠️ Monitor memory usage on Streamlit Cloud

#### Maintenance
- ✅ Keep dependencies updated
- ✅ Monitor application logs
- ✅ Test deployments in staging environment
- ⚠️ Have rollback plan for failed deployments