# IYP Query API Syntax Guide

A comprehensive guide to using the Python-like query syntax for the Internet Yellow Pages database.

## Table of Contents
1. [Basic Concepts](#basic-concepts)
2. [Query Building Pattern](#query-building-pattern)
3. [Core Methods](#core-methods)
4. [Filtering with Conditions](#filtering-with-conditions)
5. [Graph Traversal Methods](#graph-traversal-methods)
6. [Query Execution](#query-execution)
7. [Complete Examples](#complete-examples)

## Basic Concepts

### What is `iyp`?
`iyp` is your connection object to the database. Think of it as your "database handle" that knows how to talk to Neo4j.

```python
from iyp_query import connect

# Create connection to database
iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'password')
```

Once connected, `iyp` provides two main interfaces:
- `iyp.builder()` - Start building a custom query (like SQL SELECT)
- `iyp.find_upstream_providers()` - Use pre-built queries

### What is `builder()`?
`builder()` creates a new query builder object. It's like starting a SQL SELECT statement:

```python
query = iyp.builder()  # Start a new query
```

Think of it as:
- SQL: `SELECT ...`
- Our API: `iyp.builder()...`

### What is `.find()`?
`.find()` specifies what type of node you want to search for and any initial filters:

```python
# Find all AS nodes (automatically uses 'as' as alias)
query = iyp.builder().find('AS')

# Find specific AS by number
query = iyp.builder().find('AS', asn=15169)

# Find with multiple filters
query = iyp.builder().find('AS', asn=15169, name='Google')

# NO NEED for manual aliases in most cases - auto-generated aliases work fine!
# But if you want custom alias for clarity:
query = iyp.builder().find('AS', alias='target_network', asn=15169)
```

**Important**: Each `iyp.builder()` call creates a fresh, independent query builder. There are no conflicts between different queries.

SQL equivalent:
```sql
-- Our: iyp.builder().find('AS', asn=15169)
-- SQL: SELECT * FROM AS WHERE asn = 15169
```

## Query Building Pattern

Queries follow a **method chaining** pattern where each method returns the query object, allowing you to chain multiple operations:

```python
query = (iyp.builder()          # Start query
         .find('AS', asn=15169)  # Find node
         .with_organizations()    # Add related data
         .in_country()           # Add more relations
         .where(...)             # Filter results
         .return_fields([...])   # Specify output
         .limit(10)              # Limit results
         .execute())             # Run query
```

Each method adds a piece to your query, like building blocks!

## Core Methods

### 1. `find(node_type, alias=None, **filters)`
Start your query by finding nodes of a specific type.

**Parameters:**
- `node_type`: Type of node ('AS', 'Organization', 'Country', etc.)
- `alias`: Optional name to reference this node later
- `**filters`: Property filters (asn=15169, name='Google', etc.)

**Examples:**
```python
# Find all AS nodes
.find('AS')

# Find specific AS
.find('AS', asn=15169)

# Find with alias
.find('AS', alias='target_as', asn=15169)

# Find countries
.find('Country', country_code='US')

# Find organizations
.find('Organization', name='Google LLC')
```

### 2. `with_relationship(relationship, direction='out', to=None, alias=None, **filters)`
Add relationships to traverse in the graph.

**Parameters:**
- `relationship`: Relationship type ('DEPENDS_ON', 'MANAGED_BY', etc.)
- `direction`: 'out' (→), 'in' (←), or 'both' (—)
- `to`: Target node type
- `alias`: Name for the target node
- `**filters`: Filters for target node

**Examples:**
```python
# Follow MANAGED_BY relationship to Organization
.with_relationship('MANAGED_BY', to='Organization', alias='org')

# Follow incoming COUNTRY relationship
.with_relationship('COUNTRY', direction='in', to='AS', alias='as_nodes')

# With filters on target
.with_relationship('DEPENDS_ON', to='AS', alias='upstream', asn=174)
```

### 3. `where(condition)`
Add filtering conditions using Q objects and boolean logic.

**Examples:**
```python
# Simple condition
.where(Q('as.asn') == 15169)

# String operations
.where(Q('org.name').contains('Google'))

# Comparison operators
.where(Q('asn') > 1000)
.where(Q('customer_count') >= 100)

# List membership
.where(Q('asn').in_([174, 3356, 1299]))

# Complex boolean logic
.where(
    And(
        Q('country.code') == 'US',
        Or(
            Q('asn') < 1000,
            Q('asn') > 60000
        )
    )
)
```

### 4. `return_fields(fields)`
Specify which fields to return (like SELECT columns in SQL).

```python
# Return specific fields
.return_fields(['as.asn', 'as.name', 'org.name'])

# Return with aggregations
.return_fields(['country.code', 'count(as) as as_count'])
```

### 5. `limit(n)` and `skip(n)`
Control result pagination.

```python
# Get first 10 results
.limit(10)

# Skip first 100, then get 10
.skip(100).limit(10)
```

### 6. `order_by(fields)`
Sort results.

```python
# Sort ascending
.order_by(['as.asn'])

# Sort descending (prefix with -)
.order_by(['-as.asn'])

# Multiple sort fields
.order_by(['country.code', '-as.asn'])
```

### 7. `group_by(fields)`
Group results for aggregation.

```python
# Group by country
.group_by(['country.code'])
.return_fields(['country.code', 'count(as) as total'])
```

## Filtering with Conditions

### Q Objects
`Q` objects represent field conditions:

```python
from iyp_query import Q, And, Or, Not

# Create Q object for a field
q = Q('as.asn')

# Apply operators
q == 15169           # Equals
q != 15169           # Not equals
q > 1000            # Greater than
q >= 1000           # Greater or equal
q < 60000           # Less than
q <= 60000          # Less or equal
q.in_([1, 2, 3])    # In list
q.contains('Google') # String contains
```

### Boolean Combinators

#### `And(*conditions)`
All conditions must be true:
```python
And(
    Q('country.code') == 'US',
    Q('asn') > 1000,
    Q('name').contains('Inc')
)
```

#### `Or(*conditions)`
At least one condition must be true:
```python
Or(
    Q('asn') == 15169,
    Q('asn') == 13335,
    Q('asn') == 16509
)
```

#### `Not(condition)`
Negates a condition:
```python
Not(Q('country.code') == 'CN')
```

#### Nested Combinations
```python
And(
    Q('country.code').in_(['US', 'CA']),
    Or(
        Q('asn') < 1000,
        And(
            Q('asn') > 60000,
            Q('name').contains('Cloud')
        )
    ),
    Not(Q('name').contains('Spam'))
)
```

## Graph Traversal Methods

These are shortcuts for common relationship patterns:

### `upstream(hops=1, alias='upstream')`
Follow DEPENDS_ON relationships to find providers.

```python
# Direct upstream (1 hop)
.upstream()

# Two levels up
.upstream(hops=2)

# With custom alias
.upstream(alias='provider')
```

### `downstream(alias='downstream')`
Find customers (reverse of DEPENDS_ON).

```python
.downstream()
```

### `peers(alias='peer')`
Find peering partners.

```python
.peers()
```

### `with_organizations(alias='org')`
Add organization information.

```python
.with_organizations()
.with_organizations('organization')  # Custom alias
```

### `in_country(alias='country')`
Add country information.

```python
.in_country()
.in_country('location')  # Custom alias
```

### `categorized_as(alias='tag')`
Add categorization tags.

```python
.categorized_as()
```

### `originate_prefix(alias='prefix')`
Find originated IP prefixes.

```python
.originate_prefix()
```

### `member_of_ixp(alias='ixp')`
Find IXP memberships.

```python
.member_of_ixp()
```

## Query Execution

### `execute()`
Run the query and return results as list of dictionaries.

```python
results = query.execute()
# Returns: [{'as.asn': 15169, 'as.name': 'Google'}, ...]
```

### `execute_df()`
Return results as pandas DataFrame.

```python
df = query.execute_df()
# Returns pandas DataFrame
```

### `execute_single()`
Return only the first result.

```python
result = query.execute_single()
# Returns: {'as.asn': 15169, 'as.name': 'Google'}
```

### `count()`
Return count of results without fetching data.

```python
total = query.count()
# Returns: 42
```

### `to_cypher()`
See the generated Cypher query (for debugging).

```python
cypher, params = query.to_cypher()
print(cypher)
# MATCH (as:AS {asn: $param_0})
# MATCH (as)-[:MANAGED_BY]->(org:Organization)
# RETURN as.asn, org.name
```

## Complete Examples

### Example 1: Simple AS Lookup (No Manual Aliases)
```python
# Find Google's AS with organization and country
result = (iyp.builder()
          .find('AS', asn=15169)                    # auto-alias: 'as'
          .with_organizations()                     # auto-alias: 'organization' 
          .in_country()                             # auto-alias: 'country'
          .return_fields(['as.asn', 'organization.name', 'country.name'])
          .execute_single())

print(f"AS{result['as.asn']}: {result['organization.name']} in {result['country.name']}")
```

### Example 1b: Same Query with Custom Aliases (if you prefer)
```python
# Same query but with custom aliases for clarity
result = (iyp.builder()
          .find('AS', alias='network', asn=15169)
          .with_organizations('org')
          .in_country('location')
          .return_fields(['network.asn', 'org.name', 'location.name'])
          .execute_single())

print(f"AS{result['network.asn']}: {result['org.name']} in {result['location.name']}")
```

### Example 2: Find US Networks with Specific Upstreams
```python
# Find US networks that use Level3, Cogent, or NTT as upstream
results = (iyp.builder()
           .find('AS', alias='network')
           .in_country('country')
           .upstream('provider')
           .where(
               And(
                   Q('country.country_code') == 'US',
                   Q('provider.asn').in_([3356, 174, 2914])  # Level3, Cogent, NTT
               )
           )
           .return_fields(['network.asn', 'network.name', 'provider.asn'])
           .limit(10)
           .execute())

for r in results:
    print(f"AS{r['network.asn']} uses AS{r['provider.asn']} as upstream")
```

### Example 3: Multi-hop Upstream Analysis
```python
# Find 2-hop upstream providers
upstreams = (iyp.builder()
             .find('AS', asn=216139)
             .upstream(hops=2, alias='provider_chain')
             .return_fields(['provider_chain.asn', 'provider_chain.name'])
             .execute())

print("2-hop upstream providers:")
for u in upstreams:
    print(f"  - AS{u['provider_chain.asn']}: {u['provider_chain.name']}")
```

### Example 4: Country Statistics
```python
# Count ASes per country
stats = (iyp.builder()
         .find('Country', alias='c')
         .with_relationship('COUNTRY', direction='in', to='AS', alias='a')
         .group_by(['c.country_code', 'c.name'])
         .return_fields(['c.country_code', 'c.name', 'count(a) as as_count'])
         .order_by(['-as_count'])
         .limit(10)
         .execute())

print("Top 10 countries by AS count:")
for s in stats:
    print(f"  {s['c.country_code']}: {s['as_count']} ASes")
```

### Example 5: Complex Boolean Query
```python
# Find cloud providers in US or EU with many customers
results = (iyp.builder()
           .find('AS', alias='provider')
           .in_country('country')
           .downstream('customer')
           .with_organizations('org')
           .where(
               And(
                   Or(
                       Q('country.country_code') == 'US',
                       Q('country.country_code').in_(['DE', 'FR', 'NL', 'UK'])
                   ),
                   Q('org.name').contains('Cloud'),
                   Not(Q('provider.asn') < 1000)  # Exclude very low ASNs
               )
           )
           .group_by(['provider.asn', 'provider.name', 'org.name'])
           .return_fields([
               'provider.asn',
               'provider.name', 
               'org.name',
               'count(customer) as customer_count'
           ])
           .order_by(['-customer_count'])
           .limit(20)
           .execute())

print("Top cloud providers by customer count:")
for r in results:
    print(f"AS{r['provider.asn']} ({r['org.name']}): {r['customer_count']} customers")
```

### Example 6: Using Pre-built Domain Queries
```python
# Use high-level API for common queries
upstream_providers = iyp.find_upstream_providers(asn=15169, max_hops=1)
print(f"Google has {len(upstream_providers)} direct upstream providers")

# Find networks in specific region
regional = iyp.find_regional_networks(['US', 'CA'], min_customers=100)
print(f"Found {len(regional)} large North American networks")

# Analyze network dependencies
deps = iyp.find_network_dependencies(asn=15169, max_depth=3)
print(f"Network dependency analysis: {deps}")
```

## Quick Reference Card

| Method | Purpose | Example |
|--------|---------|---------|
| `iyp.builder()` | Start new query | `iyp.builder()` |
| `.find()` | Select node type | `.find('AS', asn=15169)` |
| `.where()` | Filter results | `.where(Q('asn') > 1000)` |
| `.with_relationship()` | Add relationship | `.with_relationship('MANAGED_BY', to='Organization')` |
| `.upstream()` | Find providers | `.upstream(hops=2)` |
| `.downstream()` | Find customers | `.downstream()` |
| `.with_organizations()` | Add org info | `.with_organizations('org')` |
| `.in_country()` | Add country | `.in_country()` |
| `.return_fields()` | Select output | `.return_fields(['as.asn', 'as.name'])` |
| `.limit()` | Limit results | `.limit(10)` |
| `.order_by()` | Sort results | `.order_by(['-asn'])` |
| `.group_by()` | Group for aggregation | `.group_by(['country'])` |
| `.execute()` | Run query | `.execute()` |
| `.to_cypher()` | See generated Cypher | `.to_cypher()` |

## Common Patterns

### Pattern 1: Start Simple, Add Complexity
```python
# Start simple
query = iyp.builder().find('AS', asn=15169)

# Add relationships
query = query.with_organizations()

# Add filters
query = query.where(Q('org.name').contains('Google'))

# Execute
results = query.execute()
```

### Pattern 2: Use Aliases for Clarity
```python
(iyp.builder()
 .find('AS', alias='customer')
 .upstream('provider')
 .with_organizations(alias='provider_org')
 .return_fields(['customer.asn', 'provider.asn', 'provider_org.name']))
```

### Pattern 3: Debugging with to_cypher()
```python
query = iyp.builder().find('AS').upstream().where(Q('upstream.asn') == 174)

# Check what Cypher will be generated
cypher, params = query.to_cypher()
print("Generated Cypher:")
print(cypher)
print(f"Parameters: {params}")

# If it looks good, execute
results = query.execute()
```

## Tips and Best Practices

1. **Start with `find()`**: Every query starts by finding a node type
2. **No need for manual aliases**: Auto-generated aliases work fine for most cases
3. **Chain methods**: Each method returns the query for chaining
4. **Test with `limit()`**: Add `.limit(5)` while testing
5. **Debug with `to_cypher()`**: See what Cypher gets generated
6. **Use traversal shortcuts**: `.upstream()` is cleaner than `.with_relationship('DEPENDS_ON'...)`
7. **Group complex conditions**: Use And/Or/Not for readability
8. **Return specific fields**: Don't fetch more data than needed

## Jupyter Notebook Tips

### Fresh Queries
Each `iyp.builder()` creates a completely independent query - no conflicts:

```python
# These are completely separate - no conflicts!
query1 = iyp.builder().find('AS', asn=15169)      # uses 'as' alias
query2 = iyp.builder().find('AS', asn=216139)     # also uses 'as' alias - NO PROBLEM!
query3 = iyp.builder().find('Organization')       # uses 'organization' alias
```

### If You Get Alias Errors in Jupyter
If you somehow get alias conflicts in Jupyter, just restart the kernel or re-run the connection:

```python
# Re-establish connection if needed
from iyp_query import connect
iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'lewagon25omgbbq')
```

### Recommended Pattern for Jupyter
```python
# Cell 1: Setup
from iyp_query import connect, Q, And, Or
iyp = connect('bolt+s://iyp.christyquinn.com:7687', 'neo4j', 'lewagon25omgbbq')

# Cell 2: Query 1 (use auto-aliases)
query1 = (iyp.builder()
          .find('AS', asn=15169)
          .with_organizations()
          .execute())
print(query1)

# Cell 3: Query 2 (independent of previous)  
query2 = (iyp.builder()
          .find('AS', asn=216139)
          .upstream()
          .execute())
print(query2)

# Cell 4: See generated Cypher
query = iyp.builder().find('AS', asn=15169).upstream()
cypher, params = query.to_cypher()
print("Generated Cypher:")
print(cypher)
```