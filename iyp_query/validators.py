"""
Query validation utilities to ensure correct queries before execution.
"""

from typing import Any, Dict, List, Optional, Set
from .types import NodeType, RelationshipType, validate_node_type, validate_relationship_type, get_node_properties


class QueryValidationError(Exception):
    """Raised when query validation fails."""
    pass


class QueryValidator:
    """Validates query components before execution."""
    
    def __init__(self):
        self.defined_aliases: Set[str] = set()
        self.node_types: Dict[str, NodeType] = {}
        
    def validate_node_type(self, node_type: str) -> NodeType:
        """Validate and return NodeType enum."""
        if not validate_node_type(node_type):
            raise QueryValidationError(f"Invalid node type: {node_type}")
        return NodeType(node_type)
    
    def validate_relationship_type(self, rel_type: str) -> RelationshipType:
        """Validate and return RelationshipType enum."""
        if not validate_relationship_type(rel_type):
            raise QueryValidationError(f"Invalid relationship type: {rel_type}")
        return RelationshipType(rel_type)
    
    def register_alias(self, alias: str, node_type: NodeType):
        """Register an alias for a node."""
        if alias in self.defined_aliases:
            raise QueryValidationError(f"Alias '{alias}' is already defined")
        self.defined_aliases.add(alias)
        self.node_types[alias] = node_type
    
    def validate_property(self, alias_or_property: str) -> tuple[Optional[str], str]:
        """
        Validate a property reference like 'as.asn' or just 'asn'.
        Returns (alias, property_name).
        """
        parts = alias_or_property.split('.', 1)
        
        if len(parts) == 2:
            alias, prop = parts
            if alias not in self.defined_aliases:
                raise QueryValidationError(f"Unknown alias: {alias}")
            
            node_type = self.node_types.get(alias)
            if node_type:
                valid_props = get_node_properties(node_type)
                if valid_props and prop not in valid_props:
                    raise QueryValidationError(
                        f"Invalid property '{prop}' for node type {node_type}. "
                        f"Valid properties: {', '.join(valid_props)}"
                    )
            
            return alias, prop
        else:
            return None, parts[0]
    
    def validate_return_fields(self, fields: List[str]):
        """Validate fields to be returned."""
        for field in fields:
            self.validate_property(field)
    
    def validate_cypher_injection(self, value: Any) -> bool:
        """
        Basic validation to prevent Cypher injection.
        Returns True if value appears safe.
        """
        if isinstance(value, str):
            dangerous_patterns = [
                'DELETE', 'CREATE', 'MERGE', 'SET', 'REMOVE',
                'DETACH', 'DROP', 'CALL', 'FOREACH', 'LOAD',
                '//', '/*', '*/', '--'
            ]
            value_upper = value.upper()
            for pattern in dangerous_patterns:
                if pattern in value_upper:
                    raise QueryValidationError(
                        f"Potential Cypher injection detected: {pattern} in value"
                    )
        return True
    
    def validate_limit(self, limit: Optional[int]):
        """Validate limit parameter."""
        if limit is not None:
            if not isinstance(limit, int):
                raise QueryValidationError("Limit must be an integer")
            if limit < 0:
                raise QueryValidationError("Limit must be non-negative")
            if limit > 100000:
                raise QueryValidationError("Limit cannot exceed 100000")
    
    def validate_skip(self, skip: Optional[int]):
        """Validate skip parameter."""
        if skip is not None:
            if not isinstance(skip, int):
                raise QueryValidationError("Skip must be an integer")
            if skip < 0:
                raise QueryValidationError("Skip must be non-negative")
    
    def validate_order_by(self, order_by: Optional[List[str]]):
        """Validate order by fields."""
        if order_by:
            for field in order_by:
                field_name = field.lstrip('-')
                self.validate_property(field_name)


def sanitize_string_value(value: str) -> str:
    """
    Sanitize string values for use in Cypher queries.
    Escapes special characters to prevent injection.
    """
    return value.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def validate_parameter_name(name: str) -> bool:
    """Validate that a parameter name is safe to use."""
    import re
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, name))