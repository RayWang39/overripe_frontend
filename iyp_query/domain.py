"""
High-level domain-specific query methods for common network analysis tasks.
"""

from typing import Any, Dict, List, Optional, Union
from .builder import IYPQueryBuilder
from .conditions import Q, And, Or
from .executors import QueryExecutor


class IYPQuery:
    """High-level interface for common IYP database queries."""
    
    def __init__(self, executor: QueryExecutor):
        """
        Initialize domain query interface.
        
        Args:
            executor: QueryExecutor instance for running queries
        """
        self.executor = executor
    
    def _new_builder(self) -> IYPQueryBuilder:
        """Create a new query builder."""
        return IYPQueryBuilder(self.executor)
    
    def find_upstream_providers(self, asn: int, max_hops: int = 3) -> List[Dict[str, Any]]:
        """
        Find upstream providers for a given ASN.
        
        Args:
            asn: Autonomous System Number
            max_hops: Maximum hops to traverse
            
        Returns:
            List of upstream providers with their details
        """
        return (self._new_builder()
                .find('AS', alias='target', asn=asn)
                .upstream(hops=max_hops, alias='upstream')
                .with_organizations(alias='upstream_org')
                .in_country(alias='upstream_country')
                .return_fields([
                    'target.asn',
                    'target.name', 
                    'upstream.asn',
                    'upstream.name',
                    'upstream_org.name',
                    'upstream_country.country_code'
                ])
                .execute())
    
    def find_downstream_customers(self, asn: int, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Find downstream customers for a given ASN.
        
        Args:
            asn: Autonomous System Number
            max_hops: Maximum hops to traverse
            
        Returns:
            List of downstream customers with their details
        """
        return (self._new_builder()
                .find('AS', alias='provider', asn=asn)
                .downstream(hops=max_hops, alias='customer')
                .with_organizations(alias='customer_org')
                .in_country(alias='customer_country')
                .return_fields([
                    'provider.asn',
                    'provider.name',
                    'customer.asn', 
                    'customer.name',
                    'customer_org.name',
                    'customer_country.country_code'
                ])
                .execute())
    
    def find_organization_assets(self, org_name: str) -> List[Dict[str, Any]]:
        """
        Find all assets managed by an organization.
        
        Args:
            org_name: Organization name
            
        Returns:
            List of assets managed by the organization
        """
        return (self._new_builder()
                .find('Organization', alias='org', name=org_name)
                .with_relationship('MANAGED_BY', direction='in', alias='asset')
                .in_country(from_node='org', alias='org_country')
                .return_fields([
                    'org.name',
                    'asset',
                    'org_country.country_code'
                ])
                .execute())
    
    def find_peers_at_ixp(self, ixp_name: str) -> List[Dict[str, Any]]:
        """
        Find all peers at a specific Internet Exchange Point.
        
        Args:
            ixp_name: IXP name
            
        Returns:
            List of AS members at the IXP
        """
        return (self._new_builder()
                .find('IXP', alias='ixp', name=ixp_name)
                .with_relationship('MEMBER_OF', direction='in', to='AS', alias='member')
                .with_organizations(from_node='member', alias='member_org')
                .in_country(from_node='member_org', alias='member_country')
                .return_fields([
                    'ixp.name',
                    'member.asn',
                    'member.name',
                    'member_org.name',
                    'member_country.country_code'
                ])
                .execute())
    
    def trace_bgp_path(self, from_asn: int, to_prefix: str, max_hops: int = 5) -> List[Dict[str, Any]]:
        """
        Trace potential BGP path from AS to prefix.
        
        Args:
            from_asn: Source ASN
            to_prefix: Target prefix
            max_hops: Maximum hops to traverse
            
        Returns:
            List of path components
        """
        return (self._new_builder()
                .find('AS', alias='source', asn=from_asn)
                .upstream(hops=max_hops, alias='path_as')
                .with_relationship('ORIGINATE', direction='in', to='Prefix', alias='target_prefix')
                .where(Q('target_prefix.prefix') == to_prefix)
                .return_fields([
                    'source.asn',
                    'path_as.asn', 
                    'path_as.name',
                    'target_prefix.prefix'
                ])
                .execute())
    
    def find_as_by_country(self, country_code: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find ASes in a specific country.
        
        Args:
            country_code: ISO country code (e.g., 'US', 'UK')
            limit: Maximum results to return
            
        Returns:
            List of ASes in the country
        """
        return (self._new_builder()
                .find('Country', alias='country', country_code=country_code)
                .with_relationship('COUNTRY', direction='in', to='AS', alias='as')
                .with_organizations(from_node='as', alias='as_org')
                .return_fields([
                    'as.asn',
                    'as.name',
                    'as_org.name',
                    'country.country_code'
                ])
                .limit(limit)
                .execute())
    
    def find_suspicious_hosting(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Find networks categorized with suspicious tags.
        
        Args:
            tags: List of suspicious tag labels
            
        Returns:
            List of networks with suspicious categorizations
        """
        return (self._new_builder()
                .find('Tag', alias='tag')
                .where(Q('tag.label').in_(tags))
                .with_relationship('CATEGORIZED', direction='in', alias='network')
                .with_organizations(from_node='network', alias='network_org')
                .in_country(from_node='network_org', alias='network_country')
                .return_fields([
                    'network',
                    'network_org.name',
                    'network_country.country_code', 
                    'tag.label'
                ])
                .execute())
    
    def find_tier1_providers(self) -> List[Dict[str, Any]]:
        """
        Find Tier 1 providers (ASes with no upstream dependencies).
        
        Returns:
            List of Tier 1 ASes
        """
        # This is a complex query - we'll use raw Cypher for efficiency
        cypher = """
        MATCH (as:AS)
        WHERE NOT (as)-[:DEPENDS_ON]->(:AS)
        OPTIONAL MATCH (as)-[:MANAGED_BY]->(org:Organization)
        OPTIONAL MATCH (org)-[:COUNTRY]->(country:Country)
        RETURN as.asn, as.name, org.name as org_name, country.country_code
        ORDER BY as.asn
        """
        return self.executor.execute(cypher)
    
    def find_prefix_origins(self, prefix: str) -> List[Dict[str, Any]]:
        """
        Find all ASes that originate a specific prefix.
        
        Args:
            prefix: IP prefix (e.g., '192.168.1.0/24')
            
        Returns:
            List of origin ASes for the prefix
        """
        return (self._new_builder()
                .find('Prefix', alias='prefix', prefix=prefix)
                .with_relationship('ORIGINATE', direction='out', to='AS', alias='origin_as')
                .with_organizations(from_node='origin_as', alias='origin_org')
                .return_fields([
                    'prefix.prefix',
                    'origin_as.asn',
                    'origin_as.name',
                    'origin_org.name'
                ])
                .execute())
    
    def find_network_dependencies(self, asn: int, max_depth: int = 3) -> Dict[str, Any]:
        """
        Analyze network dependencies for an AS.
        
        Args:
            asn: Autonomous System Number
            max_depth: Maximum depth to analyze
            
        Returns:
            Dictionary with upstream and downstream dependency analysis
        """
        upstream = self.find_upstream_providers(asn, max_depth)
        downstream = self.find_downstream_customers(asn, max_depth // 2)
        
        # Get peer count
        peer_query = (self._new_builder()
                     .find('AS', alias='as', asn=asn)
                     .peers(alias='peer')
                     .return_fields(['count(peer) as peer_count'])
                     .execute_single())
        
        peer_count = peer_query['peer_count'] if peer_query else 0
        
        return {
            'asn': asn,
            'upstream_count': len(upstream),
            'downstream_count': len(downstream),
            'peer_count': peer_count,
            'upstream_providers': upstream,
            'downstream_customers': downstream
        }
    
    def find_ixp_interconnections(self, asn: int) -> List[Dict[str, Any]]:
        """
        Find IXP interconnections for an AS.
        
        Args:
            asn: Autonomous System Number
            
        Returns:
            List of IXPs where the AS is a member
        """
        return (self._new_builder()
                .find('AS', alias='as', asn=asn)
                .with_relationship('MEMBER_OF', to='IXP', alias='ixp')
                .with_relationship('LOCATED_IN', from_node='ixp', to='Country', alias='ixp_country')
                .return_fields([
                    'as.asn',
                    'ixp.name',
                    'ixp_country.country_code'
                ])
                .execute())
    
    def find_regional_networks(self, country_codes: List[str], 
                              min_customers: int = 10) -> List[Dict[str, Any]]:
        """
        Find significant regional networks in specific countries.
        
        Args:
            country_codes: List of ISO country codes
            min_customers: Minimum number of downstream customers
            
        Returns:
            List of significant regional networks
        """
        return (self._new_builder()
                .find('Country', alias='country')
                .where(Q('country.country_code').in_(country_codes))
                .with_relationship('COUNTRY', direction='in', to='AS', alias='as')
                .downstream(from_node='as', alias='customer')
                .group_by(['as.asn', 'as.name', 'country.country_code'])
                .having(Q('count(customer)') >= min_customers)
                .return_fields([
                    'as.asn',
                    'as.name', 
                    'country.country_code',
                    'count(customer) as customer_count'
                ])
                .order_by(['-customer_count'])
                .execute())
    
    def raw_query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute raw Cypher query.
        
        Args:
            cypher: Raw Cypher query
            params: Query parameters
            
        Returns:
            Query results
        """
        return self.executor.execute(cypher, params)