"""
IYP Query - Python Query API for Neo4j Internet Yellow Pages Database

This package provides a SQL-like query builder interface for querying the
Internet Yellow Pages (IYP) Neo4j graph database containing internet 
infrastructure data.

Main interfaces:
1. IYPQuery - High-level domain-specific methods for common network analysis
2. IYPQueryBuilder - SQL-like query builder with method chaining
3. Raw Cypher execution for advanced users

Example usage:

    from iyp_query import IYPDatabase, IYPQuery, Q, And, Or
    
    # Connect to database
    db = IYPDatabase('bolt://localhost:7687', 'neo4j', 'password')
    iyp = IYPQuery(db)
    
    # High-level domain queries  
    providers = iyp.find_upstream_providers(asn=216139)
    
    # SQL-like query builder
    results = (iyp.builder()
               .find('AS', asn=216139)
               .upstream(hops=2, alias='upstream')  
               .where(Q('upstream.asn').in_([174, 3356, 1299]))
               .execute())
               
    # Raw Cypher
    results = iyp.raw_query("MATCH (a:AS {asn: $asn}) RETURN a", {'asn': 216139})
"""

from .types import NodeType, RelationshipType
from .conditions import Q, And, Or, Not, Condition, dict_to_condition
from .validators import QueryValidator, QueryValidationError
from .executors import IYPDatabase, QueryExecutor, format_results
from .traversals import TraversalBuilder, CommonTraversals
from .builder import IYPQueryBuilder, count, sum_field, avg, min_field, max_field
from .domain import IYPQuery

__version__ = "0.1.0"
__author__ = "Claude Code"
__description__ = "Python Query API for Neo4j Internet Yellow Pages Database"

__all__ = [
    # Core classes
    'IYPDatabase',
    'IYPQuery', 
    'IYPQueryBuilder',
    'QueryExecutor',
    
    # Condition classes
    'Q',
    'And', 
    'Or',
    'Not',
    'Condition',
    'dict_to_condition',
    
    # Type definitions
    'NodeType',
    'RelationshipType', 
    
    # Validation
    'QueryValidator',
    'QueryValidationError',
    
    # Traversal helpers
    'TraversalBuilder',
    'CommonTraversals',
    
    # Aggregation functions
    'count',
    'sum_field', 
    'avg',
    'min_field',
    'max_field',
    
    # Utility functions
    'format_results',
]


def connect(uri: str, username: str, password: str) -> IYPQuery:
    """
    Convenience function to connect to IYP database and return high-level interface.
    
    Args:
        uri: Neo4j connection URI (e.g., 'bolt://localhost:7687')
        username: Database username
        password: Database password
        
    Returns:
        IYPQuery instance ready for use
        
    Example:
        iyp = connect('bolt://localhost:7687', 'neo4j', 'password')
        results = iyp.find_upstream_providers(asn=216139)
    """
    database = IYPDatabase(uri, username, password)
    executor = QueryExecutor(database)
    return IYPQuery(executor)


def builder(uri: str, username: str, password: str) -> IYPQueryBuilder:
    """
    Convenience function to get query builder interface.
    
    Args:
        uri: Neo4j connection URI (e.g., 'bolt://localhost:7687') 
        username: Database username
        password: Database password
        
    Returns:
        IYPQueryBuilder instance for building queries
        
    Example:
        query = (builder('bolt://localhost:7687', 'neo4j', 'password')
                .find('AS', asn=216139)
                .upstream(hops=2)
                .execute())
    """
    database = IYPDatabase(uri, username, password)
    executor = QueryExecutor(database)
    return IYPQueryBuilder(executor)


# Add builder method to IYPQuery for convenience
def _add_builder_method():
    """Add builder() method to IYPQuery class."""
    def builder_method(self) -> IYPQueryBuilder:
        """Get a query builder instance."""
        return IYPQueryBuilder(self.executor)
    
    IYPQuery.builder = builder_method

_add_builder_method()