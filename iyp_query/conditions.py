"""
Boolean logic implementation for query conditions.
Supports Q objects and And/Or/Not combinators similar to Django ORM.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


class Condition(ABC):
    """Base class for all conditions."""
    
    @abstractmethod
    def to_cypher(self, param_counter: Dict[str, int]) -> tuple[str, Dict[str, Any]]:
        """
        Convert condition to Cypher WHERE clause.
        Returns (cypher_string, parameters_dict).
        """
        pass
    
    def __and__(self, other: 'Condition') -> 'And':
        """Support & operator for combining conditions."""
        return And(self, other)
    
    def __or__(self, other: 'Condition') -> 'Or':
        """Support | operator for combining conditions."""
        return Or(self, other)
    
    def __invert__(self) -> 'Not':
        """Support ~ operator for negating conditions."""
        return Not(self)


@dataclass
class Q(Condition):
    """
    Query condition for a single field comparison.
    
    Examples:
        Q('as.asn') == 12345
        Q('org.country').in_(['US', 'UK'])
        Q('peer_count') > 50
    """
    
    field: str
    operator: Optional[str] = None
    value: Any = None
    
    def __eq__(self, other: Any) -> 'Q':
        """Equality comparison."""
        return Q(self.field, '=', other)
    
    def __ne__(self, other: Any) -> 'Q':
        """Inequality comparison."""
        return Q(self.field, '<>', other)
    
    def __lt__(self, other: Any) -> 'Q':
        """Less than comparison."""
        return Q(self.field, '<', other)
    
    def __le__(self, other: Any) -> 'Q':
        """Less than or equal comparison."""
        return Q(self.field, '<=', other)
    
    def __gt__(self, other: Any) -> 'Q':
        """Greater than comparison."""
        return Q(self.field, '>', other)
    
    def __ge__(self, other: Any) -> 'Q':
        """Greater than or equal comparison."""
        return Q(self.field, '>=', other)
    
    def in_(self, values: List[Any]) -> 'Q':
        """Check if field value is in list."""
        return Q(self.field, 'IN', values)
    
    def not_in(self, values: List[Any]) -> 'Q':
        """Check if field value is not in list."""
        return Q(self.field, 'NOT IN', values)
    
    def contains(self, substring: str) -> 'Q':
        """Check if field contains substring."""
        return Q(self.field, 'CONTAINS', substring)
    
    def starts_with(self, prefix: str) -> 'Q':
        """Check if field starts with prefix."""
        return Q(self.field, 'STARTS WITH', prefix)
    
    def ends_with(self, suffix: str) -> 'Q':
        """Check if field ends with suffix."""
        return Q(self.field, 'ENDS WITH', suffix)
    
    def is_null(self) -> 'Q':
        """Check if field is null."""
        return Q(self.field, 'IS NULL', None)
    
    def is_not_null(self) -> 'Q':
        """Check if field is not null."""
        return Q(self.field, 'IS NOT NULL', None)
    
    def regex(self, pattern: str) -> 'Q':
        """Match field against regex pattern."""
        return Q(self.field, '=~', pattern)
    
    def to_cypher(self, param_counter: Dict[str, int]) -> tuple[str, Dict[str, Any]]:
        """Convert Q condition to Cypher."""
        if self.operator is None:
            raise ValueError(f"Q condition for field '{self.field}' has no operator")
        
        params = {}
        
        if self.operator in ['IS NULL', 'IS NOT NULL']:
            cypher = f"{self.field} {self.operator}"
        elif self.operator in ['IN', 'NOT IN']:
            param_name = f"param_{len(param_counter)}"
            param_counter[param_name] = len(param_counter)
            params[param_name] = self.value
            cypher = f"{self.field} {self.operator} ${param_name}"
        else:
            param_name = f"param_{len(param_counter)}"
            param_counter[param_name] = len(param_counter)
            params[param_name] = self.value
            cypher = f"{self.field} {self.operator} ${param_name}"
        
        return cypher, params


@dataclass
class And(Condition):
    """Combine multiple conditions with AND logic."""
    
    conditions: List[Condition] = field(default_factory=list)
    
    def __init__(self, *conditions: Condition):
        self.conditions = list(conditions)
    
    def add(self, condition: Condition) -> 'And':
        """Add another condition to the AND group."""
        self.conditions.append(condition)
        return self
    
    def to_cypher(self, param_counter: Dict[str, int]) -> tuple[str, Dict[str, Any]]:
        """Convert AND condition to Cypher."""
        if not self.conditions:
            return "true", {}
        
        cypher_parts = []
        all_params = {}
        
        for condition in self.conditions:
            part, params = condition.to_cypher(param_counter)
            cypher_parts.append(f"({part})")
            all_params.update(params)
        
        cypher = " AND ".join(cypher_parts)
        return cypher, all_params


@dataclass
class Or(Condition):
    """Combine multiple conditions with OR logic."""
    
    conditions: List[Condition] = field(default_factory=list)
    
    def __init__(self, *conditions: Condition):
        self.conditions = list(conditions)
    
    def add(self, condition: Condition) -> 'Or':
        """Add another condition to the OR group."""
        self.conditions.append(condition)
        return self
    
    def to_cypher(self, param_counter: Dict[str, int]) -> tuple[str, Dict[str, Any]]:
        """Convert OR condition to Cypher."""
        if not self.conditions:
            return "false", {}
        
        cypher_parts = []
        all_params = {}
        
        for condition in self.conditions:
            part, params = condition.to_cypher(param_counter)
            cypher_parts.append(f"({part})")
            all_params.update(params)
        
        cypher = " OR ".join(cypher_parts)
        return f"({cypher})", all_params


@dataclass
class Not(Condition):
    """Negate a condition."""
    
    condition: Condition
    
    def to_cypher(self, param_counter: Dict[str, int]) -> tuple[str, Dict[str, Any]]:
        """Convert NOT condition to Cypher."""
        cypher, params = self.condition.to_cypher(param_counter)
        return f"NOT ({cypher})", params


def dict_to_condition(condition_dict: Dict[str, Any]) -> Condition:
    """
    Convert dictionary-based condition to Condition object.
    
    Example:
        {
            'AND': [
                {'country': 'US'},
                {'OR': [
                    {'tier': 1},
                    {'AND': [
                        {'peer_count': {'>': 50}},
                        {'customer_count': {'>': 100}}
                    ]}
                ]}
            ]
        }
    """
    if 'AND' in condition_dict:
        conditions = [dict_to_condition(c) for c in condition_dict['AND']]
        return And(*conditions)
    
    elif 'OR' in condition_dict:
        conditions = [dict_to_condition(c) for c in condition_dict['OR']]
        return Or(*conditions)
    
    elif 'NOT' in condition_dict:
        return Not(dict_to_condition(condition_dict['NOT']))
    
    else:
        for field, value in condition_dict.items():
            if isinstance(value, dict):
                for op, val in value.items():
                    if op == '=':
                        return Q(field) == val
                    elif op == '!=':
                        return Q(field) != val
                    elif op == '<':
                        return Q(field) < val
                    elif op == '<=':
                        return Q(field) <= val
                    elif op == '>':
                        return Q(field) > val
                    elif op == '>=':
                        return Q(field) >= val
                    elif op == 'in':
                        return Q(field).in_(val)
                    elif op == 'not_in':
                        return Q(field).not_in(val)
                    elif op == 'contains':
                        return Q(field).contains(val)
                    elif op == 'starts_with':
                        return Q(field).starts_with(val)
                    elif op == 'ends_with':
                        return Q(field).ends_with(val)
                    elif op == 'regex':
                        return Q(field).regex(val)
                    else:
                        raise ValueError(f"Unknown operator: {op}")
            else:
                return Q(field) == value
    
    raise ValueError(f"Invalid condition dictionary: {condition_dict}")