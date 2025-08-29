# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains three interconnected components for querying and visualizing the Neo4j Internet Yellow Pages (IYP) Database:

1. **IYP Query Library** (`iyp_query/`) - Core Python library providing SQL-like query builder interface
2. **Method Chain Translation API** (`api/`) - FastAPI service that translates method chains to Cypher queries
3. **Streamlit Frontend** (`frontend/app.py`) - Interactive web interface for query execution and graph visualization

The core mission is to allow technical users to query internet infrastructure data (ASNs, IP prefixes, organizations, IXPs, etc.) WITHOUT needing to learn Cypher query language.

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

## Database Schema

### Node Types (from documentation)
Key node types include: AS, Organization, Prefix (with subtypes: BGPPrefix, GeoPrefix, RIRPrefix, RPKIPrefix, PeeringLAN, RDNSPrefix), IXP, Country, IP, HostName, DomainName, Facility, Tag, URL, and various ID nodes (CaidaIXID, CaidaOrgID, PeeringdbIXID, etc.)

### Relationship Types (from documentation)
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
frontend/                   # Interactive web interface
└── app.py                 # Main Streamlit application

# Data and Documentation
notebook/                   # Data analysis notebooks
yellow_page_info/          # Database schema documentation
RIPE_data/                 # Sample data files
testing_data/              # Test data and example queries
requirements.txt          # Core library dependencies
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

# 2. Start the Streamlit Frontend (in a new terminal)
streamlit run frontend/app.py

# The system will be available at:
# - Streamlit UI: http://localhost:8501
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

The core API connects to the live IYP database:
- **URI**: bolt+s://iyp.christyquinn.com:7687
- **Credentials**: neo4j / lewagon25omgbbq
- **Connection**: SSL-enabled Neo4j Bolt protocol

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
- **Streamlit Frontend**: http://localhost:8501
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

# Interactive query building
python -c "from iyp_query import connect; iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'lewagon25omgbbq'); print('Connected successfully')"

# Run Jupyter notebooks for data analysis
jupyter notebook
```
