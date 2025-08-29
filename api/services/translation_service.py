"""Cypher query translation service"""
import sys
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import json

# Add parent directory to path to import iyp_query
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from iyp_query import connect, Q, And, Or
from config import settings

class CypherTranslationService:
    """Service for translating queries to Cypher without executing them"""
    
    def __init__(self):
        """Initialize the translation service"""
        self.iyp = None
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Connect to database for query building (but not execution)"""
        try:
            self.iyp = connect(
                settings.neo4j_uri,
                settings.neo4j_user,
                settings.neo4j_password
            )
            return True
        except Exception as e:
            print(f"Warning: Database connection failed: {e}")
            return False
    
    def translate_method_chain(self, method_chain: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Translate method chain like '.find.with_organization.upstream' to Cypher
        
        Args:
            method_chain: String like '.find.with_organization.upstream'
            params: Optional parameters like {'asn': 15169, 'hops': 2}
        """
        try:
            if not self.iyp:
                return {
                    "success": False,
                    "error": "Database connection not available for query building",
                    "cypher": None,
                    "parameters": {}
                }
            
            params = params or {}
            
            # Clean and split the method chain
            chain = method_chain.strip()
            if chain.startswith('.'):
                chain = chain[1:]
            
            methods = [m.strip() for m in chain.split('.') if m.strip()]
            
            if not methods:
                return {
                    "success": False,
                    "error": "Empty method chain",
                    "cypher": None,
                    "parameters": {}
                }
            
            # Start with the builder
            query = self.iyp.builder()
            applied_methods = []
            
            # Apply each method in the chain
            for method_name in methods:
                method_params = self._get_method_params(method_name, params)
                applied_methods.append(f"{method_name}({method_params})")
                
                try:
                    if hasattr(query, method_name):
                        method = getattr(query, method_name)
                        
                        # Apply method with appropriate parameters
                        if method_name == 'find':
                            node_type = params.get('node_type', 'AS')
                            asn = params.get('asn')
                            alias = params.get('alias', 'node')
                            
                            if asn:
                                query = method(node_type, alias=alias, asn=asn)
                            else:
                                query = method(node_type, alias=alias)
                                
                        elif method_name in ['with_organizations', 'with_organization']:
                            query = query.with_organizations()
                            
                        elif method_name == 'upstream':
                            hops = params.get('hops', 1)
                            alias = params.get('upstream_alias', 'upstream')
                            query = method(hops=hops, alias=alias)
                            
                        elif method_name == 'downstream':
                            hops = params.get('hops', 1)
                            alias = params.get('downstream_alias', 'downstream')
                            query = method(hops=hops, alias=alias)
                            
                        elif method_name == 'peers':
                            alias = params.get('peer_alias', 'peer')
                            query = method(alias=alias)
                            
                        elif method_name == 'with_relationship':
                            rel_type = params.get('relationship', 'DEPENDS_ON')
                            to_type = params.get('to', 'AS')
                            alias = params.get('rel_alias', 'related')
                            query = method(rel_type, to=to_type, alias=alias)
                            
                        elif method_name == 'where':
                            condition = params.get('condition')
                            if condition:
                                query = method(condition)
                            
                        elif method_name == 'limit':
                            n = params.get('limit', 10)
                            query = method(n)
                            
                        elif method_name == 'return_fields':
                            fields = params.get('fields', ['*'])
                            query = method(fields)
                            
                        else:
                            # Try to call method with no parameters
                            query = method()
                    else:
                        return {
                            "success": False,
                            "error": f"Unknown method: {method_name}",
                            "cypher": None,
                            "parameters": {}
                        }
                        
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error applying method '{method_name}': {str(e)}",
                        "cypher": None,
                        "parameters": {}
                    }
            
            # Generate Cypher query
            try:
                cypher, cypher_params = query.to_cypher()
                
                return {
                    "success": True,
                    "method_chain": " → ".join(applied_methods),
                    "cypher": cypher,
                    "parameters": cypher_params,
                    "explanation": self._explain_cypher(cypher)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error generating Cypher: {str(e)}",
                    "cypher": None,
                    "parameters": {}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Translation error: {str(e)}",
                "cypher": None,
                "parameters": {}
            }
    
    def _get_method_params(self, method_name: str, params: Dict[str, Any]) -> str:
        """Get parameter description for method"""
        if method_name == 'find':
            node_type = params.get('node_type', 'AS')
            asn = params.get('asn')
            if asn:
                return f"'{node_type}', asn={asn}"
            return f"'{node_type}'"
        elif method_name == 'upstream':
            hops = params.get('hops', 1)
            return f"hops={hops}"
        elif method_name == 'downstream':
            hops = params.get('hops', 1)
            return f"hops={hops}"
        elif method_name == 'limit':
            n = params.get('limit', 10)
            return str(n)
        return ""
    
    
    def _explain_cypher(self, cypher: str) -> str:
        """Generate human-readable explanation of Cypher query"""
        explanations = []
        
        if 'MATCH' in cypher:
            if ':AS' in cypher:
                explanations.append("Finds Autonomous System nodes")
            if ':Organization' in cypher:
                explanations.append("Includes organization information")
            if ':Country' in cypher:
                explanations.append("Includes country information")
        
        if 'DEPENDS_ON' in cypher:
            explanations.append("Follows provider-customer relationships")
        elif 'PEERS_WITH' in cypher:
            explanations.append("Follows peering relationships")
        elif 'MANAGED_BY' in cypher:
            explanations.append("Follows organization management relationships")
        
        if 'WHERE' in cypher:
            explanations.append("Applies filtering conditions")
        
        if 'LIMIT' in cypher:
            explanations.append("Limits the number of results")
        
        return "; ".join(explanations) if explanations else "Basic graph query"
    
    def get_common_examples(self) -> Dict[str, Any]:
        """Get common query examples with their translations"""
        examples = [
            {
                "name": "Find AS with organization", 
                "method_chain": ".find.with_organizations",  # Fixed to use plural
                "params": {"asn": 15169},
                "description": "Get AS details including managing organization"
            },
            {
                "name": "Find upstream providers",
                "method_chain": ".find.upstream",
                "params": {"asn": 216139, "hops": 2},
                "description": "Get upstream providers up to 2 hops away"
            },
            {
                "name": "Find AS peers",
                "method_chain": ".find.peers",
                "params": {"asn": 15169},
                "description": "Get direct peering partners"
            },
            {
                "name": "Complex relationship query",
                "method_chain": ".find.with_relationship.limit",
                "params": {"asn": 15169, "relationship": "COUNTRY", "to": "Country", "limit": 5},
                "description": "Find AS with specific relationship type"
            }
        ]
        
        results = []
        for example in examples:
            translation = self.translate_method_chain(
                example["method_chain"], 
                example["params"]
            )
            results.append({
                "example": example,
                "translation": translation
            })
        
        return {"examples": results}

# Singleton instance
translation_service = CypherTranslationService()