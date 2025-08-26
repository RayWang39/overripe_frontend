"""
Neo4j execution and result formatting utilities.
"""

from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import json


class IYPDatabase:
    """Neo4j database connection and query execution."""
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize connection to Neo4j database.
        
        Args:
            uri: Neo4j connection URI (e.g., 'bolt://localhost:7687')
            username: Database username
            password: Database password
        """
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
        except ImportError:
            raise ImportError("neo4j package is required. Install with: pip install neo4j")
        
        self._test_connection()
    
    def _test_connection(self):
        """Test the database connection."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")
    
    @contextmanager
    def session(self):
        """Context manager for database sessions."""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dictionaries.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        with self.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]
    
    def execute_query_raw(self, cypher: str, params: Optional[Dict[str, Any]] = None):
        """
        Execute a Cypher query and return raw Neo4j records.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            Neo4j Result object
        """
        with self.session() as session:
            return list(session.run(cypher, params or {}))
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class QueryExecutor:
    """Executes queries and formats results."""
    
    def __init__(self, database: IYPDatabase):
        """
        Initialize query executor.
        
        Args:
            database: IYPDatabase instance
        """
        self.database = database
    
    def execute(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute query and return results as list of dictionaries.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            List of dictionaries
        """
        return self.database.execute_query(cypher, params)
    
    def execute_df(self, cypher: str, params: Optional[Dict[str, Any]] = None):
        """
        Execute query and return results as pandas DataFrame.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            pandas DataFrame
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for DataFrame output. Install with: pip install pandas")
        
        results = self.execute(cypher, params)
        if not results:
            return pd.DataFrame()
        
        return pd.DataFrame(results)
    
    def execute_raw(self, cypher: str, params: Optional[Dict[str, Any]] = None):
        """
        Execute query and return raw Neo4j records.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            List of Neo4j Record objects
        """
        return self.database.execute_query_raw(cypher, params)
    
    def execute_json(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute query and return results as JSON string.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            JSON string
        """
        results = self.execute(cypher, params)
        return json.dumps(results, indent=2, default=str)
    
    def execute_single(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single result.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            Single dictionary or None if no results
        """
        results = self.execute(cypher, params)
        return results[0] if results else None
    
    def count(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute count query and return integer result.
        
        Args:
            cypher: Cypher query string (should return COUNT)
            params: Query parameters
            
        Returns:
            Count as integer
        """
        result = self.execute_single(cypher, params)
        if result:
            for value in result.values():
                return int(value)
        return 0


def format_results(results: List[Dict[str, Any]], format_type: str = 'dict') -> Union[List[Dict], str]:
    """
    Format query results in different formats.
    
    Args:
        results: Query results
        format_type: Output format ('dict', 'json', 'table')
        
    Returns:
        Formatted results
    """
    if format_type == 'dict':
        return results
    
    elif format_type == 'json':
        return json.dumps(results, indent=2, default=str)
    
    elif format_type == 'table':
        if not results:
            return "No results"
        
        try:
            from tabulate import tabulate
            headers = list(results[0].keys())
            rows = [[row.get(h, '') for h in headers] for row in results]
            return tabulate(rows, headers=headers, tablefmt='grid')
        except ImportError:
            raise ImportError("tabulate is required for table output. Install with: pip install tabulate")
    
    else:
        raise ValueError(f"Unknown format type: {format_type}")