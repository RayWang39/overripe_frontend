# IYP Query - Python API for Internet Yellow Pages Database

A Python-based query builder API that allows technical users to query the Neo4j Internet Yellow Pages (IYP) graph database containing internet infrastructure data (ASNs, IP prefixes, organizations, etc.) WITHOUT needing to learn Cypher query language.

## Documentation

- **[User Guides](docs/user-guides/)** - Getting started and tutorials
- **[API Documentation](docs/api-docs/)** - API reference and integration guides
- **[Development](docs/development/)** - Development setup and contribution guidelines
- **[Deployment](docs/deployment/)** - Deployment configurations and guides
- **[Examples](docs/examples/)** - Sample queries and use cases

## Features

- **Three Query Interfaces**:
  1. High-level domain-specific methods for common network analysis
  2. SQL-like query builder with method chaining
  3. Raw Cypher escape hatch for advanced users

- **Complex Boolean Logic**: Support for nested AND/OR/NOT operations
- **Graph Traversal Helpers**: Intuitive methods for common graph patterns  
- **Type Safety**: Validation with clear error messages and IDE autocomplete
- **Multiple Output Formats**: Dict, pandas DataFrame, raw Neo4j records, JSON
- **Cypher Injection Prevention**: Built-in validation and parameterized queries

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package (development mode)
pip install -e .
```

## Quick Start

```python
from iyp_query import connect, Q, And, Or

# Connect to IYP database
iyp = connect('bolt://localhost:7687', 'neo4j', 'password')

# High-level domain queries
providers = iyp.find_upstream_providers(asn=216139)
ixp_peers = iyp.find_peers_at_ixp('DE-CIX Frankfurt')

# SQL-like query builder
results = (iyp.builder()
           .find('AS', asn=216139)
           .upstream(hops=2, alias='upstream')
           .with_organizations('org')
           .where(
               And(
                   Q('org.country') == 'US',
                   Q('upstream.asn').in_([174, 3356, 1299])
               )
           )
           .return_fields(['as.asn', 'upstream.name', 'org.name'])
           .execute())

# Raw Cypher for advanced users  
results = iyp.raw_query(\"\"\"
    MATCH (as:AS {asn: $asn})-[:DEPENDS_ON]->(upstream:AS)
    RETURN as.asn, upstream.asn
\"\"\", {'asn': 216139})
```

## Core Concepts

### Node Types
The IYP database contains these main node types:
- **AS**: Autonomous Systems 
- **Organization**: Network operators
- **Prefix**: IP prefixes (with subtypes: BGPPrefix, GeoPrefix, etc.)
- **IXP**: Internet Exchange Points
- **Country**: Geographic entities
- **Tag**: Classification labels

### Relationship Types  
Key relationships for network analysis:
- **DEPENDS_ON**: Upstream/downstream AS relationships
- **MANAGED_BY**: Organization ownership
- **PEERS_WITH**: AS peering relationships
- **MEMBER_OF**: IXP membership
- **ORIGINATE**: BGP prefix origination
- **COUNTRY**: Geographic location

## Query Examples

### 1. Basic AS Lookup
```python
# Find AS with organization and country info
results = (iyp.builder()
           .find('AS', asn=15169)  # Google
           .with_organizations('org')
           .in_country('country')
           .execute())
```

### 2. Complex Boolean Conditions
```python
# Find US/UK ASes with specific upstream providers
results = (iyp.builder()
           .find('AS', alias='target')
           .in_country('country') 
           .upstream('upstream')
           .where(
               And(
                   Q('country.country_code').in_(['US', 'UK']),
                   Q('upstream.asn').in_([174, 3356, 1299])
               )
           )
           .execute())
```

### 3. Multi-hop Traversals
```python
# Find 2-hop upstream providers
results = (iyp.builder()
           .find('AS', asn=216139)
           .upstream(hops=2, alias='upstream_chain')
           .execute())
```

### 4. Aggregation and Grouping
```python
# Count ASes by country
results = (iyp.builder()
           .find('Country', alias='country')
           .with_relationship('COUNTRY', direction='in', to='AS', alias='as')
           .group_by(['country.country_code'])
           .return_fields(['country.country_code', 'count(as) as as_count'])
           .order_by(['-as_count'])
           .execute())
```

## High-Level Domain API

The `IYPQuery` class provides pre-built methods for common network analysis:

```python
# Network dependency analysis
analysis = iyp.find_network_dependencies(asn=15169, max_depth=3)
print(f"Upstream providers: {analysis['upstream_count']}")
print(f"Downstream customers: {analysis['downstream_count']}")

# Find suspicious networks
suspicious = iyp.find_suspicious_hosting(['bulletproof', 'malicious'])

# Regional network analysis  
regional_nets = iyp.find_regional_networks(['US', 'CA'], min_customers=100)

# IXP interconnection analysis
ixp_memberships = iyp.find_ixp_interconnections(asn=15169)
```

## Output Formats

```python
# Dictionary (default)
results = query.execute()

# Pandas DataFrame
df = query.execute_df()

# Raw Neo4j records
raw = query.execute_raw()

# Single result
single = query.execute_single()

# Count only
count = query.count()

# Debug: View generated Cypher
cypher, params = query.to_cypher()
print(cypher)
```

## Graph Traversal Helpers

```python
# Common traversal patterns
query = (iyp.builder()
         .find('AS', asn=15169)
         .upstream(hops=2)           # Follow upstream dependencies
         .downstream()               # Find customers  
         .peers()                    # Find peers
         .with_organizations()       # Add organization info
         .in_country()              # Add country info
         .categorized_as()          # Add tags/categories
         .execute())
```

## Error Handling and Validation

The API provides comprehensive validation:

```python
try:
    results = (iyp.builder()
               .find('InvalidNodeType')  # Will raise QueryValidationError
               .execute())
except QueryValidationError as e:
    print(f"Query validation failed: {e}")
```

## Performance Considerations

- Use `limit()` for large result sets
- Leverage indexes on ASN, prefix, and name properties
- Use `group_by()` and aggregations to reduce data transfer
- Monitor query complexity with `to_cypher()` for debugging

## Development Setup

```bash
# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests
pytest

# Code formatting
black iyp_query/

# Type checking  
mypy iyp_query/

# Linting
flake8 iyp_query/
```

## Architecture

```
iyp_query/
├── __init__.py          # Public API exports
├── builder.py           # Main IYPQueryBuilder class
├── conditions.py        # Boolean logic (Q, And, Or, Not) 
├── domain.py           # High-level IYPQuery methods
├── executors.py        # Neo4j connection and execution
├── traversals.py       # Graph traversal helpers
├── types.py            # Node and relationship type enums
├── validators.py       # Query validation
└── examples.py         # Usage examples
```

## Contributing

1. Follow the existing code style (Black formatting)
2. Add type hints for all new functions
3. Include docstrings with examples
4. Add tests for new functionality
5. Update documentation for new features

## License

MIT License - see LICENSE file for details.

## Database Schema

See the `data/schemas/yellow_page_info/` directory for complete documentation of:
- Node types and their properties
- Relationship types and semantics
- Data source information

## Support

- Check `examples.py` for usage patterns
- Review `CLAUDE.md` for development guidance
- File issues for bugs or feature requests