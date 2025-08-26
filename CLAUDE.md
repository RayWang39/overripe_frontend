# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python Query API for the Neo4j Internet Yellow Pages (IYP) Database - a graph database containing internet infrastructure data (ASNs, IP prefixes, organizations, IXPs, etc.). The goal is to provide a SQL-like query builder interface that allows technical users to query the database WITHOUT needing to learn Cypher query language.

## Key Requirements

### Core Functionality
- **Read-only operations** - No create, update, or delete operations
- **Complex boolean logic** - Support nested AND/OR/NOT operations for filtering
- **Target users** - Technical users who know SQL/Python but not Cypher
- **Graph traversals** - Support multi-hop relationship traversals

### Three Query Interfaces to Implement

1. **High-Level Domain-Specific Methods** - Pre-built queries for common network analysis tasks
2. **SQL-like Query Builder** (Main Interface) - Chainable methods with Q objects for complex conditions
3. **Raw Cypher Escape Hatch** - Direct Cypher query execution for advanced users

## Database Schema

### Node Types (from documentation)
Key node types include: AS, Organization, Prefix (with subtypes: BGPPrefix, GeoPrefix, RIRPrefix, RPKIPrefix, PeeringLAN, RDNSPrefix), IXP, Country, IP, HostName, DomainName, Facility, Tag, URL, and various ID nodes (CaidaIXID, CaidaOrgID, PeeringdbIXID, etc.)

### Relationship Types (from documentation)
Critical relationships: DEPENDS_ON (upstream providers), MANAGED_BY (organization ownership), PEERS_WITH (AS peering), MEMBER_OF (IXP membership), COUNTRY (location), CATEGORIZED (tagging), ORIGINATE (BGP prefix origination)

## Project Structure

```
iyp_query/                  # Core API library
├── __init__.py
├── builder.py              # Main query builder class
├── conditions.py           # AND/OR/NOT logic implementation
├── traversals.py           # Graph traversal helpers
├── domain.py              # High-level domain-specific queries
├── types.py               # Enums for node/relationship types
├── validators.py          # Query validation
├── executors.py           # Neo4j execution and result formatting
└── examples.py            # Usage examples

test_*.py                   # Various test files for API validation
requirements.txt            # Core API dependencies
```

## Development Commands

### Setting Up the Environment
```bash
# Create virtual environment
pyenv virtualenv 3.12.9 overripe
pyenv activate overripe

# Install core API dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Test the API interactively
python test_interactive.py

# Run basic API tests
python test_basic.py

# Test with live database (requires connection details)
python test_live_db.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=iyp_query

# Run specific test file
pytest tests/test_builder.py
```

### Code Quality
```bash
# Format code with black
black iyp_query/

# Check linting with flake8
flake8 iyp_query/

# Type checking with mypy
mypy iyp_query/
```

## Implementation Priorities

1. **Core Query Builder** - Implement the base builder class with method chaining
2. **Boolean Conditions** - Q objects and And/Or/Not combinators
3. **Graph Traversals** - Common patterns like upstream(), downstream(), peers()
4. **Type Safety** - Enums from node/relationship documentation
5. **Neo4j Integration** - Connection management and query execution
6. **Result Formatting** - Support for dict, DataFrame, and raw outputs

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

## Example Query Pattern

The system should handle complex queries like:
```python
query = (iyp
    .find('AS', alias='target_as')
    .with_relationship('COUNTRY', to='Country', alias='as_country')
    .with_relationship('DEPENDS_ON', to='AS', alias='upstream')
    .where(
        And(
            Q('as_country.country_code') == 'US',
            Q('upstream.asn').in_([174, 3356, 1299])
        )
    )
    .return_fields(['target_as.asn', 'target_as.name'])
)

## Troubleshooting Common Issues

### Database Connection Issues
- Ensure the Neo4j URI uses `bolt+s://` for SSL connections
- Verify credentials are correct for the live IYP database
- Connection is established on startup - check startup logs for connection status

### Query Validation Errors
- **Invalid node types**: Use enums from `types.py` for validation
- **Cypher syntax errors**: Check generated Cypher with `.to_cypher()` method for debugging
- Large result sets may cause performance issues - use `.limit()` in queries