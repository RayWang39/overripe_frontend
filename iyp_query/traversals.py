"""
Graph traversal helpers for common network analysis patterns.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from .types import NodeType, RelationshipType


@dataclass
class TraversalStep:
    """Represents a single step in a graph traversal."""
    relationship: RelationshipType
    direction: str  # 'out', 'in', 'both'
    target_node_type: Optional[NodeType] = None
    alias: Optional[str] = None
    hops: int = 1
    
    def to_cypher_pattern(self, source_alias: str) -> str:
        """Convert traversal step to Cypher pattern."""
        if self.direction == 'out':
            arrow = '->'
        elif self.direction == 'in':
            arrow = '<-'
        else:  # both
            arrow = '-'
        
        # Build relationship pattern
        rel_pattern = f"[:{self.relationship}"
        if self.hops > 1:
            rel_pattern += f"*1..{self.hops}"
        rel_pattern += "]"
        
        # Build target node pattern
        target_pattern = ""
        if self.target_node_type:
            target_pattern = f"{self.target_node_type}"
        if self.alias:
            target_pattern = f"{self.alias}:{target_pattern}" if target_pattern else self.alias
        
        if self.direction == 'in':
            return f"({target_pattern}){arrow}{rel_pattern}-({source_alias})"
        else:
            return f"({source_alias}){arrow}{rel_pattern}-({target_pattern})"


class TraversalBuilder:
    """Helper class for building graph traversals."""
    
    def __init__(self, source_alias: str):
        self.source_alias = source_alias
        self.steps: List[TraversalStep] = []
    
    def upstream(self, hops: int = 1, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Follow upstream dependencies (DEPENDS_ON relationship)."""
        step = TraversalStep(
            relationship=RelationshipType.DEPENDS_ON,
            direction='out',
            target_node_type=NodeType.AS,
            alias=alias or f"upstream_{len(self.steps)}",
            hops=hops
        )
        self.steps.append(step)
        return self
    
    def downstream(self, hops: int = 1, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Follow downstream dependencies (reverse DEPENDS_ON)."""
        step = TraversalStep(
            relationship=RelationshipType.DEPENDS_ON,
            direction='in',
            target_node_type=NodeType.AS,
            alias=alias or f"downstream_{len(self.steps)}",
            hops=hops
        )
        self.steps.append(step)
        return self
    
    def peers(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Follow peering relationships."""
        step = TraversalStep(
            relationship=RelationshipType.PEERS_WITH,
            direction='both',
            target_node_type=NodeType.AS,
            alias=alias or f"peer_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def with_organizations(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Add organization relationships."""
        step = TraversalStep(
            relationship=RelationshipType.MANAGED_BY,
            direction='out',
            target_node_type=NodeType.ORGANIZATION,
            alias=alias or f"org_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def in_country(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Add country relationships."""
        step = TraversalStep(
            relationship=RelationshipType.COUNTRY,
            direction='out',
            target_node_type=NodeType.COUNTRY,
            alias=alias or f"country_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def categorized_as(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Add categorization/tagging relationships."""
        step = TraversalStep(
            relationship=RelationshipType.CATEGORIZED,
            direction='out',
            target_node_type=NodeType.TAG,
            alias=alias or f"tag_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def members_of_ixp(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Find IXP memberships."""
        step = TraversalStep(
            relationship=RelationshipType.MEMBER_OF,
            direction='out',
            target_node_type=NodeType.IXP,
            alias=alias or f"ixp_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def originates_prefixes(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Find originated prefixes."""
        step = TraversalStep(
            relationship=RelationshipType.ORIGINATE,
            direction='in',
            target_node_type=NodeType.PREFIX,
            alias=alias or f"prefix_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def siblings(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Find sibling entities (same organization)."""
        step = TraversalStep(
            relationship=RelationshipType.SIBLING_OF,
            direction='both',
            target_node_type=None,  # Could be AS or Organization
            alias=alias or f"sibling_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def external_ids(self, alias: Optional[str] = None) -> 'TraversalBuilder':
        """Find external identifiers."""
        step = TraversalStep(
            relationship=RelationshipType.EXTERNAL_ID,
            direction='out',
            target_node_type=None,  # Various ID types
            alias=alias or f"ext_id_{len(self.steps)}",
            hops=1
        )
        self.steps.append(step)
        return self
    
    def custom_relationship(self, relationship: RelationshipType, 
                          direction: str = 'out',
                          target_node_type: Optional[NodeType] = None,
                          alias: Optional[str] = None,
                          hops: int = 1) -> 'TraversalBuilder':
        """Add a custom relationship traversal."""
        step = TraversalStep(
            relationship=relationship,
            direction=direction,
            target_node_type=target_node_type,
            alias=alias or f"custom_{len(self.steps)}",
            hops=hops
        )
        self.steps.append(step)
        return self
    
    def to_cypher_patterns(self) -> List[str]:
        """Convert all traversal steps to Cypher patterns."""
        patterns = []
        current_alias = self.source_alias
        
        for step in self.steps:
            pattern = step.to_cypher_pattern(current_alias)
            patterns.append(pattern)
            current_alias = step.alias or current_alias
        
        return patterns
    
    def get_all_aliases(self) -> List[str]:
        """Get all aliases used in the traversal."""
        aliases = [self.source_alias]
        for step in self.steps:
            if step.alias:
                aliases.append(step.alias)
        return aliases


def build_path_traversal(from_node: str, to_node: str, 
                        relationship: RelationshipType,
                        max_hops: int = 5) -> str:
    """
    Build a Cypher pattern for finding paths between nodes.
    
    Args:
        from_node: Source node alias
        to_node: Target node alias  
        relationship: Relationship type to traverse
        max_hops: Maximum number of hops
        
    Returns:
        Cypher path pattern
    """
    return f"({from_node})-[:{relationship}*1..{max_hops}]-({to_node})"


def build_shortest_path(from_node: str, to_node: str,
                       relationship: RelationshipType,
                       max_hops: int = 5) -> str:
    """
    Build a Cypher pattern for finding shortest paths.
    
    Args:
        from_node: Source node alias
        to_node: Target node alias
        relationship: Relationship type to traverse
        max_hops: Maximum number of hops
        
    Returns:
        Cypher shortest path pattern
    """
    return f"shortestPath(({from_node})-[:{relationship}*1..{max_hops}]-({to_node}))"


class CommonTraversals:
    """Collection of common network analysis traversal patterns."""
    
    @staticmethod
    def find_upstream_providers(as_alias: str = "as", max_hops: int = 3) -> TraversalBuilder:
        """Find upstream providers of an AS."""
        return TraversalBuilder(as_alias).upstream(hops=max_hops)
    
    @staticmethod
    def find_downstream_customers(as_alias: str = "as", max_hops: int = 2) -> TraversalBuilder:
        """Find downstream customers of an AS."""
        return TraversalBuilder(as_alias).downstream(hops=max_hops)
    
    @staticmethod
    def find_as_organization_country(as_alias: str = "as") -> TraversalBuilder:
        """Find AS with its organization and country."""
        return (TraversalBuilder(as_alias)
                .with_organizations("org")
                .in_country("country"))
    
    @staticmethod
    def find_ixp_members(ixp_alias: str = "ixp") -> TraversalBuilder:
        """Find all members of an IXP."""
        return TraversalBuilder(ixp_alias).custom_relationship(
            RelationshipType.MEMBER_OF, 
            direction='in',
            target_node_type=NodeType.AS,
            alias="member"
        )
    
    @staticmethod
    def find_prefix_origin_chain(prefix_alias: str = "prefix") -> TraversalBuilder:
        """Find prefix with its origin AS and upstream chain."""
        return (TraversalBuilder(prefix_alias)
                .custom_relationship(RelationshipType.ORIGINATE, 
                                   direction='out', 
                                   target_node_type=NodeType.AS,
                                   alias="origin_as")
                .upstream(hops=2, alias="upstream_as"))
    
    @staticmethod
    def find_organization_assets(org_alias: str = "org") -> TraversalBuilder:
        """Find all assets managed by an organization."""
        return TraversalBuilder(org_alias).custom_relationship(
            RelationshipType.MANAGED_BY,
            direction='in',
            alias="asset"
        )