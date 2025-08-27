"""
Main query builder class for IYP database queries.
Provides SQL-like interface for building Cypher queries.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from .types import NodeType, RelationshipType, validate_node_type, validate_relationship_type
from .conditions import Condition, Q, And, Or, Not, dict_to_condition
from .validators import QueryValidator, QueryValidationError
from .executors import QueryExecutor
from .traversals import TraversalBuilder, CommonTraversals


@dataclass
class RelationshipSpec:
    """Specification for a relationship in the query."""
    relationship_type: RelationshipType
    to_node_type: Optional[NodeType] = None
    from_node_alias: Optional[str] = None
    to_node_alias: Optional[str] = None
    direction: str = 'out'  # 'out', 'in', 'both'
    hops: int = 1


@dataclass 
class QueryPart:
    """Individual part of the query being built."""
    match_clauses: List[str] = field(default_factory=list)
    where_conditions: List[Condition] = field(default_factory=list)
    return_fields: List[str] = field(default_factory=list)
    order_by: List[str] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    having_conditions: List[Condition] = field(default_factory=list)
    limit: Optional[int] = None
    skip: Optional[int] = None


class IYPQueryBuilder:
    """Main query builder for IYP database queries."""
    
    def __init__(self, executor: QueryExecutor):
        """
        Initialize query builder.
        
        Args:
            executor: QueryExecutor instance for running queries
        """
        self.executor = executor
        self.validator = QueryValidator()
        self.query_parts = QueryPart()
        self.param_counter: Dict[str, int] = {}
        self.relationships: List[RelationshipSpec] = []
        self.root_alias: Optional[str] = None
        self.root_node_type: Optional[NodeType] = None
    
    def find(self, node_type: str, alias: Optional[str] = None, **filters) -> 'IYPQueryBuilder':
        """
        Start query by finding nodes of a specific type.
        
        Args:
            node_type: Type of node to find (e.g., 'AS', 'Organization')
            alias: Alias for the node in the query (if None, auto-generates unique alias)
            **filters: Property filters (e.g., asn=12345, name="Example")
            
        Returns:
            Query builder for chaining
        """
        validated_type = self.validator.validate_node_type(node_type)
        
        if alias is None:
            # Generate a unique alias based on node type and existing aliases
            base_alias = node_type.lower()
            alias = base_alias
            counter = 1
            while alias in self.validator.defined_aliases:
                alias = f"{base_alias}_{counter}"
                counter += 1
        
        self.validator.register_alias(alias, validated_type)
        self.root_alias = alias
        self.root_node_type = validated_type
        
        # Build MATCH clause
        match_clause = f"({alias}:{validated_type.value})"
        
        # Add property filters
        filter_params = {}
        if filters:
            filter_parts = []
            for prop, value in filters.items():
                self.validator.validate_cypher_injection(value)
                param_name = f"param_{len(self.param_counter)}"
                self.param_counter[param_name] = len(self.param_counter)
                filter_params[param_name] = value
                filter_parts.append(f"{prop}: ${param_name}")
            
            if filter_parts:
                match_clause = f"({alias}:{validated_type.value} {{{', '.join(filter_parts)}}})"
        
        # Store filter parameters
        if not hasattr(self, '_filter_params'):
            self._filter_params = {}
        self._filter_params.update(filter_params)
        
        self.query_parts.match_clauses.append(f"MATCH {match_clause}")
        
        return self
    
    def with_relationship(self, relationship: str, 
                         to: Optional[str] = None,
                         from_node: Optional[str] = None,
                         alias: Optional[str] = None,
                         direction: str = 'out',
                         hops: int = 1) -> 'IYPQueryBuilder':
        """
        Add a relationship traversal to the query.
        
        Args:
            relationship: Relationship type (e.g., 'MANAGED_BY', 'DEPENDS_ON')
            to: Target node type
            from_node: Source node alias (defaults to previous node)
            alias: Alias for the target node
            direction: 'out', 'in', or 'both'
            hops: Number of hops (for variable-length paths)
            
        Returns:
            Query builder for chaining
        """
        rel_type = self.validator.validate_relationship_type(relationship)
        
        from_alias = from_node or self.root_alias
        if from_alias not in self.validator.defined_aliases:
            raise QueryValidationError(f"Unknown source alias: {from_alias}")
        
        to_node_type = None
        if to:
            to_node_type = self.validator.validate_node_type(to)
        
        if alias is None:
            if to:
                # Generate unique alias for the target node type
                base_alias = to.lower()
                to_alias = base_alias
                counter = 1
                while to_alias in self.validator.defined_aliases:
                    to_alias = f"{base_alias}_{counter}"
                    counter += 1
            else:
                to_alias = f"node_{len(self.relationships)}"
        else:
            to_alias = alias
        
        if to_node_type:
            self.validator.register_alias(to_alias, to_node_type)
        
        # Build relationship pattern
        rel_spec = RelationshipSpec(
            relationship_type=rel_type,
            to_node_type=to_node_type,
            from_node_alias=from_alias,
            to_node_alias=to_alias,
            direction=direction,
            hops=hops
        )
        self.relationships.append(rel_spec)
        
        # Build MATCH clause
        if direction == 'out':
            arrow = '->'
        elif direction == 'in':
            arrow = '<-'
        else:
            arrow = '-'
        
        rel_pattern = f"[:{rel_type.value}"
        if hops > 1:
            rel_pattern += f"*1..{hops}"
        rel_pattern += "]"
        
        to_pattern = f"({to_alias}"
        if to_node_type:
            to_pattern += f":{to_node_type.value}"
        to_pattern += ")"
        
        if direction == 'in':
            match_clause = f"MATCH {to_pattern}-{rel_pattern}-({from_alias})"
        elif direction == 'out':
            match_clause = f"MATCH ({from_alias})-{rel_pattern}->{to_pattern}"
        else:  # both
            match_clause = f"MATCH ({from_alias})-{rel_pattern}-{to_pattern}"
        
        self.query_parts.match_clauses.append(match_clause)
        
        return self
    
    def where(self, condition: Union[Condition, Dict[str, Any]]) -> 'IYPQueryBuilder':
        """
        Add WHERE conditions to the query.
        
        Args:
            condition: Q object, combined condition, or dictionary
            
        Returns:
            Query builder for chaining
        """
        if isinstance(condition, dict):
            condition = dict_to_condition(condition)
        
        if not isinstance(condition, Condition):
            raise QueryValidationError("Condition must be a Condition object or dictionary")
        
        self.query_parts.where_conditions.append(condition)
        
        return self
    
    def return_fields(self, fields: List[str]) -> 'IYPQueryBuilder':
        """
        Specify fields to return in the query.
        
        Args:
            fields: List of field names (e.g., ['as.asn', 'org.name'])
            
        Returns:
            Query builder for chaining
        """
        self.validator.validate_return_fields(fields)
        self.query_parts.return_fields = fields
        
        return self
    
    def order_by(self, fields: List[str]) -> 'IYPQueryBuilder':
        """
        Add ORDER BY clause.
        
        Args:
            fields: List of fields to order by (prefix with '-' for DESC)
            
        Returns:
            Query builder for chaining
        """
        self.validator.validate_order_by(fields)
        self.query_parts.order_by = fields
        
        return self
    
    def group_by(self, fields: List[str]) -> 'IYPQueryBuilder':
        """
        Add GROUP BY clause.
        
        Args:
            fields: List of fields to group by
            
        Returns:
            Query builder for chaining
        """
        self.validator.validate_return_fields(fields)
        self.query_parts.group_by = fields
        
        return self
    
    def having(self, condition: Union[Condition, Dict[str, Any]]) -> 'IYPQueryBuilder':
        """
        Add HAVING conditions (for use with GROUP BY).
        
        Args:
            condition: Q object, combined condition, or dictionary
            
        Returns:
            Query builder for chaining
        """
        if isinstance(condition, dict):
            condition = dict_to_condition(condition)
        
        if not isinstance(condition, Condition):
            raise QueryValidationError("Condition must be a Condition object or dictionary")
        
        self.query_parts.having_conditions.append(condition)
        
        return self
    
    def limit(self, count: int) -> 'IYPQueryBuilder':
        """
        Add LIMIT clause.
        
        Args:
            count: Maximum number of results
            
        Returns:
            Query builder for chaining
        """
        self.validator.validate_limit(count)
        self.query_parts.limit = count
        
        return self
    
    def skip(self, count: int) -> 'IYPQueryBuilder':
        """
        Add SKIP clause.
        
        Args:
            count: Number of results to skip
            
        Returns:
            Query builder for chaining
        """
        self.validator.validate_skip(count)
        self.query_parts.skip = count
        
        return self
    
    def upstream(self, hops: int = 1, alias: Optional[str] = None) -> 'IYPQueryBuilder':
        """Add upstream dependency traversal."""
        return self.with_relationship('DEPENDS_ON', to='AS', alias=alias, hops=hops)
    
    def downstream(self, hops: int = 1, alias: Optional[str] = None) -> 'IYPQueryBuilder':
        """Add downstream dependency traversal."""
        return self.with_relationship('DEPENDS_ON', to='AS', alias=alias, direction='in', hops=hops)
    
    def peers(self, alias: Optional[str] = None) -> 'IYPQueryBuilder':
        """Add peering relationship traversal."""
        return self.with_relationship('PEERS_WITH', to='AS', alias=alias, direction='both')
    
    def with_organizations(self, alias: Optional[str] = None) -> 'IYPQueryBuilder':
        """Add organization relationship traversal."""
        return self.with_relationship('MANAGED_BY', to='Organization', alias=alias)
    
    def in_country(self, alias: Optional[str] = None) -> 'IYPQueryBuilder':
        """Add country relationship traversal."""
        return self.with_relationship('COUNTRY', to='Country', alias=alias)
    
    def categorized_as(self, alias: Optional[str] = None) -> 'IYPQueryBuilder':
        """Add tag/category relationship traversal."""
        return self.with_relationship('CATEGORIZED', to='Tag', alias=alias)
    
    def to_cypher(self) -> tuple[str, Dict[str, Any]]:
        """
        Generate the final Cypher query and parameters.
        
        Returns:
            Tuple of (cypher_query, parameters)
        """
        if not self.query_parts.match_clauses:
            raise QueryValidationError("No MATCH clauses defined")
        
        cypher_parts = []
        all_params = {}
        
        # Add MATCH clauses
        cypher_parts.extend(self.query_parts.match_clauses)
        
        # Add WHERE clause
        if self.query_parts.where_conditions:
            if len(self.query_parts.where_conditions) == 1:
                where_condition = self.query_parts.where_conditions[0]
            else:
                where_condition = And(*self.query_parts.where_conditions)
            
            where_cypher, where_params = where_condition.to_cypher(self.param_counter)
            cypher_parts.append(f"WHERE {where_cypher}")
            all_params.update(where_params)
        
        # Handle GROUP BY with proper WITH clause structure
        if self.query_parts.group_by:
            # In Neo4j, GROUP BY is done with WITH and aggregations
            if self.query_parts.return_fields:
                # For aggregation queries, build proper WITH clause
                # Extract field names and create aliases
                return_fields = ", ".join(self.query_parts.return_fields)
                
                # Build WITH clause for grouping
                with_parts = []
                for field in self.query_parts.group_by:
                    # For fields like 'country.country_code', keep as is
                    with_parts.append(field)
                
                # Add all fields from return clause that aren't aggregations
                for field in self.query_parts.return_fields:
                    if 'count(' not in field.lower() and 'sum(' not in field.lower() and 'avg(' not in field.lower():
                        if field not in with_parts:
                            with_parts.append(field)
                
                cypher_parts.append(f"WITH {', '.join(with_parts)}")
                
                # Add HAVING clause if present
                if self.query_parts.having_conditions:
                    if len(self.query_parts.having_conditions) == 1:
                        having_condition = self.query_parts.having_conditions[0]
                    else:
                        having_condition = And(*self.query_parts.having_conditions)
                    
                    having_cypher, having_params = having_condition.to_cypher(self.param_counter)
                    cypher_parts.append(f"WHERE {having_cypher}")
                    all_params.update(having_params)
                
                cypher_parts.append(f"RETURN {return_fields}")
            else:
                group_fields = ", ".join(self.query_parts.group_by)
                cypher_parts.append(f"RETURN {group_fields}")
        else:
            # Add RETURN clause
            if self.query_parts.return_fields:
                return_fields = ", ".join(self.query_parts.return_fields)
            else:
                # Return all defined aliases
                return_fields = ", ".join(self.validator.defined_aliases)
            cypher_parts.append(f"RETURN {return_fields}")
        
        # Add ORDER BY clause
        if self.query_parts.order_by:
            order_fields = []
            for field in self.query_parts.order_by:
                if field.startswith('-'):
                    order_fields.append(f"{field[1:]} DESC")
                else:
                    order_fields.append(f"{field} ASC")
            cypher_parts.append(f"ORDER BY {', '.join(order_fields)}")
        
        # Add SKIP clause
        if self.query_parts.skip is not None:
            cypher_parts.append(f"SKIP {self.query_parts.skip}")
        
        # Add LIMIT clause
        if self.query_parts.limit is not None:
            cypher_parts.append(f"LIMIT {self.query_parts.limit}")
        
        # Add parameters from filters
        if hasattr(self, '_filter_params'):
            all_params.update(self._filter_params)
        
        cypher_query = "\n".join(cypher_parts)
        
        return cypher_query, all_params
    
    def execute(self) -> List[Dict[str, Any]]:
        """Execute the query and return results as list of dictionaries."""
        cypher, params = self.to_cypher()
        return self.executor.execute(cypher, params)
    
    def execute_df(self):
        """Execute the query and return results as pandas DataFrame."""
        cypher, params = self.to_cypher()
        return self.executor.execute_df(cypher, params)
    
    def execute_raw(self):
        """Execute the query and return raw Neo4j records."""
        cypher, params = self.to_cypher()
        return self.executor.execute_raw(cypher, params)
    
    def execute_single(self) -> Optional[Dict[str, Any]]:
        """Execute the query and return single result."""
        cypher, params = self.to_cypher()
        return self.executor.execute_single(cypher, params)
    
    def count(self) -> int:
        """Execute a count query."""
        # Modify query to return count
        count_query = IYPQueryBuilder(self.executor)
        count_query.validator = self.validator
        count_query.query_parts.match_clauses = self.query_parts.match_clauses[:]
        count_query.query_parts.where_conditions = self.query_parts.where_conditions[:]
        count_query.query_parts.return_fields = ["count(*) as count"]
        
        result = count_query.execute_single()
        return result['count'] if result else 0


def count(field: str) -> str:
    """Helper function for count aggregation in HAVING clauses."""
    return f"count({field})"


def sum_field(field: str) -> str:
    """Helper function for sum aggregation."""
    return f"sum({field})"


def avg(field: str) -> str:
    """Helper function for average aggregation."""
    return f"avg({field})"


def min_field(field: str) -> str:
    """Helper function for minimum aggregation."""
    return f"min({field})"


def max_field(field: str) -> str:
    """Helper function for maximum aggregation."""
    return f"max({field})"