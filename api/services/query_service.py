"""Query execution service"""
import sys
import os
import time
import json
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from datetime import datetime
import neo4j.time

# Add parent directory to path to import iyp_query
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from iyp_query import connect, Q, And, Or
from config import settings
from models.requests import QueryOperation, ReturnFormat

def serialize_neo4j_types(obj):
    """Convert Neo4j types to JSON-serializable types"""
    if isinstance(obj, neo4j.time.DateTime):
        return obj.iso_format()
    elif isinstance(obj, (neo4j.time.Date, neo4j.time.Time, neo4j.time.Duration)):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_neo4j_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_neo4j_types(item) for item in obj]
    return obj

class QueryService:
    """Service for executing IYP queries"""
    
    def __init__(self):
        """Initialize the query service with database connection"""
        self.iyp = None
        self.connect_to_database()
    
    def connect_to_database(self):
        """Establish connection to Neo4j database"""
        try:
            self.iyp = connect(
                settings.neo4j_uri,
                settings.neo4j_user,
                settings.neo4j_password
            )
            return True
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            return False
    
    def execute_builder_query(
        self,
        operations: List[QueryOperation],
        return_format: ReturnFormat = ReturnFormat.JSON,
        limit: Optional[int] = None,
        return_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute a builder-style query"""
        start_time = time.time()
        
        try:
            # Start with the builder
            query = self.iyp.builder()
            
            # Apply each operation in sequence
            for op in operations:
                method_name = op.method
                params = op.params or {}
                
                # Get the method from the query object
                if hasattr(query, method_name):
                    method = getattr(query, method_name)
                    query = method(**params)
                else:
                    raise ValueError(f"Unknown method: {method_name}")
            
            # Apply limit if specified
            if limit:
                query = query.limit(limit)
            
            # Apply return fields if specified
            if return_fields:
                query = query.return_fields(return_fields)
            
            # Execute based on return format
            if return_format == ReturnFormat.DATAFRAME:
                result = query.execute_df()
                data = result.to_dict(orient='records')
            else:
                result = query.execute()
                data = result
            
            # Serialize Neo4j types
            data = serialize_neo4j_types(data)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "data": data,
                "count": len(data) if isinstance(data, list) else 1,
                "query_time_ms": execution_time,
                "cached": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query_time_ms": (time.time() - start_time) * 1000
            }
    
    def execute_cypher_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        return_format: ReturnFormat = ReturnFormat.JSON
    ) -> Dict[str, Any]:
        """Execute a raw Cypher query"""
        start_time = time.time()
        
        try:
            # Execute the Cypher query
            result = self.iyp.execute_cypher(query, parameters or {})
            
            # Format the result based on return format
            if return_format == ReturnFormat.JSON:
                data = list(result)
            elif return_format == ReturnFormat.CSV:
                df = pd.DataFrame(result)
                data = df.to_csv(index=False)
            else:
                df = pd.DataFrame(result)
                data = df.to_dict(orient='records')
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "data": data,
                "count": len(data) if isinstance(data, list) else 1,
                "query_time_ms": execution_time,
                "cached": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query_time_ms": (time.time() - start_time) * 1000
            }
    
    def get_as_details(self, asn: int, **kwargs) -> Dict[str, Any]:
        """Get details for a specific AS"""
        start_time = time.time()
        
        try:
            query = self.iyp.builder().find('AS', asn=asn)
            
            # Add optional relationships
            if kwargs.get('include_organizations'):
                query = query.with_organizations()
            
            if kwargs.get('include_peers'):
                query = query.with_relationship('PEERS_WITH', to='AS', alias='peer')
            
            result = query.execute()
            
            # Process and format the result
            as_details = {}
            if result:
                first_result = result[0]
                as_details = {
                    "asn": asn,
                    "name": first_result.get('as', {}).get('name'),
                    "country": first_result.get('country', {}).get('country_code') if 'country' in first_result else None,
                    "organization": first_result.get('organization') if 'organization' in first_result else None
                }
            
            # Serialize Neo4j types
            as_details = serialize_neo4j_types(as_details)
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "data": as_details,
                "count": 1 if as_details else 0,
                "query_time_ms": execution_time,
                "cached": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query_time_ms": (time.time() - start_time) * 1000
            }
    
    def find_upstream_providers(self, asn: int, max_hops: int = 1) -> Dict[str, Any]:
        """Find upstream providers for an AS"""
        start_time = time.time()
        
        try:
            providers = self.iyp.find_upstream_providers(asn=asn, max_hops=max_hops)
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "data": providers,
                "count": len(providers),
                "query_time_ms": execution_time,
                "cached": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query_time_ms": (time.time() - start_time) * 1000
            }
    
    def find_as_by_country(self, country_code: str, limit: int = 100) -> Dict[str, Any]:
        """Find ASes in a specific country"""
        start_time = time.time()
        
        try:
            result = (self.iyp.builder()
                     .find('AS', alias='as_node')
                     .with_relationship('COUNTRY', to='Country', alias='country')
                     .where(Q('country.country_code') == country_code.upper())
                     .limit(limit)
                     .return_fields(['as_node.asn', 'as_node.name', 'country.country_code'])
                     .execute())
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "data": result,
                "count": len(result),
                "query_time_ms": execution_time,
                "cached": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "query_time_ms": (time.time() - start_time) * 1000
            }
    
    def validate_cypher_query(self, query: str) -> Dict[str, Any]:
        """Validate a Cypher query without executing it"""
        warnings = []
        errors = []
        
        # Check for forbidden operations
        forbidden_keywords = ['CREATE', 'DELETE', 'MERGE', 'SET', 'REMOVE', 'DROP']
        query_upper = query.upper()
        
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                errors.append(f"Query contains forbidden keyword: {keyword}")
        
        # Check for MATCH clause
        if 'MATCH' not in query_upper:
            warnings.append("Query does not contain a MATCH clause")
        
        # Check for RETURN clause
        if 'RETURN' not in query_upper:
            warnings.append("Query does not contain a RETURN clause")
        
        return {
            "valid": len(errors) == 0,
            "query": query,
            "warnings": warnings,
            "errors": errors
        }

# Singleton instance
query_service = QueryService()