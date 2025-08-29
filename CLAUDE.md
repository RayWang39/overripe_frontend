# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains two complementary components for querying the Neo4j Internet Yellow Pages (IYP) Database:

1. **IYP Query Library** (`iyp_query/`) - A Python library providing a SQL-like query builder interface
2. **Method Chain Translation API** (`api/`) - A FastAPI service that translates method chains to Cypher queries

The core mission is to allow technical users to query internet infrastructure data (ASNs, IP prefixes, organizations, IXPs, etc.) WITHOUT needing to learn Cypher query language.

## Dual Architecture

### 1. IYP Query Library (`iyp_query/`)
A Python library with three query interfaces:
- **High-Level Domain-Specific Methods** - Pre-built queries for common network analysis
- **SQL-like Query Builder** - Chainable methods with Q objects for complex boolean conditions  
- **Raw Cypher Escape Hatch** - Direct Cypher execution for advanced users

### 2. Method Chain Translation API (`api/`)
A FastAPI web service focused on **translation-only**:
- Converts method chains like `.find.with_organizations.upstream` into Cypher queries
- Does NOT execute queries - only generates them for integration into other systems
- Provides REST endpoints for programmatic Cypher generation

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
│   ├── translation.py     # Method chain translation models
│   ├── requests.py        # General request models
│   └── responses.py       # General response models
├── routers/               # API route handlers
│   ├── translation.py     # Core method chain translation endpoints
│   ├── query.py           # Legacy query endpoints
│   ├── search.py          # Search endpoints
│   └── admin.py           # Admin endpoints
├── services/              # Business logic layer
│   ├── translation_service.py  # CypherTranslationService - core logic
│   └── query_service.py         # Legacy query service
├── middleware/            # Custom middleware
│   └── auth.py            # API key authentication
├── static/                # Web interface
│   └── index.html         # Interactive test interface
├── docs/                  # API documentation
│   ├── API_README.md      # Detailed API docs
│   └── QUICK_START.md     # Quick reference
├── demos/                 # Example scripts
│   └── method_chain_demo.py  # Interactive demo
├── scripts/               # Utility scripts
│   └── run_api.sh         # Server startup script
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Docker orchestration
└── requirements.txt       # API-specific dependencies

# Data and Documentation
notebook/                   # Data analysis notebooks
yellow_page_info/          # Database schema documentation
RIPE_data/                 # Sample data files
UK_ASNs.json              # UK ASN sample data
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

### Method Chain Translation API Development
```bash
# Start the API server (from project root)
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Or use the helper script
./api/scripts/run_api.sh

# Or use Docker
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

### Dual Service Model
The API service (`api/`) uses the core library (`iyp_query/`) but serves a different purpose:
- **Core Library**: Direct database execution with complex query building
- **API Service**: Translation-only service for generating Cypher queries

### Method Chain Translation Flow
1. API receives method chain string (e.g., `.find.with_organizations.upstream`)
2. `CypherTranslationService` parses the chain into individual methods
3. Uses `iyp_query` library to build the query with method chaining
4. Calls `.to_cypher()` to generate Cypher without execution
5. Returns structured response with Cypher, parameters, and explanations

### Important Class Relationships
```python
# API Flow
MethodChainRequest -> CypherTranslationService -> IYPQueryBuilder -> Cypher Output

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

## Working Configuration

### Current Database Connection
- **URI**: `bolt+s://iyp.christyquinn.com:7687` (SSL-enabled)
- **Credentials**: `neo4j` / `lewagon25omgbbq`
- **Connection verified working** as of current session

### File Organization Status
- ✅ **API files organized** in `/api/` directory structure
- ✅ **Documentation created** with README files and quick start guides
- ✅ **Demo scripts working** in `/api/demos/`
- ✅ **Git cleanup completed** with proper `.gitignore` to prevent cache file conflicts
- ✅ **Method chain translation fully functional**

### Known Working Commands
```bash
# Start API (from project root)
cd api && PYTHONPATH=.. python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Test API
cd api && python demos/method_chain_demo.py

# Interactive query building
python -c "from iyp_query import connect; iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'lewagon25omgbbq'); print('Connected successfully')"
```