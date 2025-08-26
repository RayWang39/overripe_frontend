"""
Usage examples for IYP Query API.
Demonstrates various query patterns and use cases for network analysis.
"""

from typing import List, Dict, Any
from iyp_query import connect, IYPQuery, Q, And, Or, Not


def setup_connection() -> IYPQuery:
    """Set up database connection for examples."""
    # Replace with your actual database connection details
    return connect(
        uri='bolt://localhost:7687',
        username='neo4j', 
        password='password'
    )


def example_1_basic_as_lookup():
    """Example 1: Basic AS lookup with organization and country."""
    iyp = setup_connection()
    
    print("=== Example 1: Basic AS Lookup ===")
    
    # Find AS information with organization and country
    results = (iyp.builder()
               .find('AS', asn=216139)
               .with_organizations('org')
               .in_country('country')
               .return_fields(['as.asn', 'as.name', 'org.name', 'country.country_code'])
               .execute())
    
    for result in results:
        print(f"AS{result['as.asn']}: {result['as.name']}")
        print(f"  Organization: {result['org.name']}")
        print(f"  Country: {result['country.country_code']}")


def example_2_upstream_providers():
    """Example 2: Find upstream providers using high-level API."""
    iyp = setup_connection()
    
    print("\n=== Example 2: Upstream Providers ===")
    
    # Use high-level domain API
    providers = iyp.find_upstream_providers(asn=216139, max_hops=2)
    
    print(f"Found {len(providers)} upstream providers for AS216139:")
    for provider in providers:
        print(f"  AS{provider['upstream.asn']}: {provider['upstream.name']}")
        print(f"    Org: {provider['upstream_org.name']}")
        print(f"    Country: {provider['upstream_country.country_code']}")


def example_3_complex_boolean_conditions():
    """Example 3: Complex boolean conditions with Q objects."""
    iyp = setup_connection()
    
    print("\n=== Example 3: Complex Boolean Conditions ===")
    
    # Find ASes in US or UK that are either Tier 1 OR have specific upstreams
    results = (iyp.builder()
               .find('AS', alias='target_as')
               .with_organizations('org')
               .in_country('as_country')
               .upstream(hops=1, alias='upstream')
               .where(
                   And(
                       Or(
                           Q('as_country.country_code') == 'US',
                           Q('as_country.country_code') == 'UK'
                       ),
                       Or(
                           Not(Q('upstream')),  # No upstream (Tier 1)
                           Q('upstream.asn').in_([174, 3356, 1299])  # Specific upstreams
                       )
                   )
               )
               .return_fields(['target_as.asn', 'target_as.name', 'org.name', 'as_country.country_code'])
               .limit(10)
               .execute())
    
    print(f"Found {len(results)} ASes matching complex criteria:")
    for result in results:
        print(f"  AS{result['target_as.asn']}: {result['target_as.name']}")


def example_4_ixp_analysis():
    """Example 4: IXP membership analysis."""
    iyp = setup_connection()
    
    print("\n=== Example 4: IXP Analysis ===")
    
    # Find peers at DE-CIX Frankfurt
    peers = iyp.find_peers_at_ixp('DE-CIX Frankfurt')
    
    print(f"Found {len(peers)} members at DE-CIX Frankfurt:")
    for peer in peers[:10]:  # Show first 10
        print(f"  AS{peer['member.asn']}: {peer['member.name']}")
        print(f"    Country: {peer['member_country.country_code']}")


def example_5_prefix_origin_analysis():
    """Example 5: Prefix origin analysis."""
    iyp = setup_connection()
    
    print("\n=== Example 5: Prefix Origin Analysis ===")
    
    # Find origins for a specific prefix
    origins = iyp.find_prefix_origins('8.8.8.0/24')
    
    print("Origins for 8.8.8.0/24:")
    for origin in origins:
        print(f"  AS{origin['origin_as.asn']}: {origin['origin_as.name']}")
        print(f"    Organization: {origin['origin_org.name']}")


def example_6_dependency_analysis():
    """Example 6: Network dependency analysis."""
    iyp = setup_connection()
    
    print("\n=== Example 6: Network Dependency Analysis ===")
    
    # Comprehensive dependency analysis for Google (AS15169)
    analysis = iyp.find_network_dependencies(asn=15169, max_depth=3)
    
    print(f"Dependency analysis for AS{analysis['asn']}:")
    print(f"  Upstream providers: {analysis['upstream_count']}")
    print(f"  Downstream customers: {analysis['downstream_count']}")  
    print(f"  Peers: {analysis['peer_count']}")
    
    if analysis['upstream_providers']:
        print("  Top upstream providers:")
        for upstream in analysis['upstream_providers'][:5]:
            print(f"    AS{upstream['upstream.asn']}: {upstream['upstream.name']}")


def example_7_suspicious_networks():
    """Example 7: Find networks with suspicious categorization."""
    iyp = setup_connection()
    
    print("\n=== Example 7: Suspicious Networks ===")
    
    # Find networks tagged as bulletproof hosting or malicious
    suspicious = iyp.find_suspicious_hosting(['bulletproof', 'malicious', 'botnet'])
    
    print(f"Found {len(suspicious)} networks with suspicious tags:")
    for network in suspicious[:10]:  # Show first 10
        print(f"  Network: {network['network']}")
        print(f"    Tag: {network['tag.label']}")
        print(f"    Country: {network['network_country.country_code']}")


def example_8_regional_analysis():
    """Example 8: Regional network analysis."""
    iyp = setup_connection()
    
    print("\n=== Example 8: Regional Analysis ===")
    
    # Find significant networks in European countries
    eu_countries = ['DE', 'FR', 'UK', 'IT', 'ES', 'NL']
    regional_nets = iyp.find_regional_networks(eu_countries, min_customers=50)
    
    print(f"Significant regional networks in Europe:")
    for network in regional_nets[:10]:  # Top 10
        print(f"  AS{network['as.asn']}: {network['as.name']}")
        print(f"    Country: {network['country.country_code']}")
        print(f"    Customers: {network['customer_count']}")


def example_9_custom_query_builder():
    """Example 9: Custom query using builder pattern."""
    iyp = setup_connection()
    
    print("\n=== Example 9: Custom Query Builder ===")
    
    # Complex custom query: Find US ASes with Russian/Chinese upstream dependencies
    results = (iyp.builder()
               .find('AS', alias='target_as')
               .in_country('as_country')
               .upstream(hops=2, alias='upstream')
               .with_organizations(from_node='upstream', alias='upstream_org')
               .in_country(from_node='upstream_org', alias='org_country')
               .where(
                   And(
                       Q('as_country.country_code') == 'US',
                       Q('org_country.country_code').in_(['RU', 'CN'])
                   )
               )
               .group_by(['target_as.asn', 'target_as.name', 'as_country.country_code'])
               .return_fields([
                   'target_as.asn', 
                   'target_as.name',
                   'as_country.country_code',
                   'count(upstream) as upstream_count'
               ])
               .order_by(['-upstream_count'])
               .limit(20)
               .execute())
    
    print("US ASes with RU/CN upstream dependencies:")
    for result in results:
        print(f"  AS{result['target_as.asn']}: {result['target_as.name']}")
        print(f"    Upstream count: {result['upstream_count']}")


def example_10_raw_cypher():
    """Example 10: Raw Cypher query for advanced users."""
    iyp = setup_connection()
    
    print("\n=== Example 10: Raw Cypher Query ===")
    
    # Find ASes with the most IXP memberships
    cypher = """
    MATCH (as:AS)-[:MEMBER_OF]->(ixp:IXP)
    WITH as, count(ixp) as ixp_count
    WHERE ixp_count >= 10
    OPTIONAL MATCH (as)-[:MANAGED_BY]->(org:Organization)
    RETURN as.asn, as.name, org.name as org_name, ixp_count
    ORDER BY ixp_count DESC
    LIMIT 10
    """
    
    results = iyp.raw_query(cypher)
    
    print("ASes with most IXP memberships:")
    for result in results:
        print(f"  AS{result['as.asn']}: {result['as.name']}")
        print(f"    Organization: {result['org_name']}")
        print(f"    IXP memberships: {result['ixp_count']}")


def example_11_aggregation_and_grouping():
    """Example 11: Aggregation and grouping."""
    iyp = setup_connection()
    
    print("\n=== Example 11: Aggregation and Grouping ===")
    
    # Count ASes by country
    results = (iyp.builder()
               .find('Country', alias='country')
               .with_relationship('COUNTRY', direction='in', to='AS', alias='as')
               .group_by(['country.country_code'])
               .return_fields(['country.country_code', 'count(as) as as_count'])
               .order_by(['-as_count'])
               .limit(20)
               .execute())
    
    print("AS count by country (Top 20):")
    for result in results:
        print(f"  {result['country.country_code']}: {result['as_count']} ASes")


def run_all_examples():
    """Run all examples."""
    examples = [
        example_1_basic_as_lookup,
        example_2_upstream_providers, 
        example_3_complex_boolean_conditions,
        example_4_ixp_analysis,
        example_5_prefix_origin_analysis,
        example_6_dependency_analysis,
        example_7_suspicious_networks,
        example_8_regional_analysis,
        example_9_custom_query_builder,
        example_10_raw_cypher,
        example_11_aggregation_and_grouping,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")


if __name__ == '__main__':
    print("IYP Query API Examples")
    print("=" * 50)
    
    # Note: These examples require a running IYP Neo4j database
    # Update the connection details in setup_connection() before running
    
    print("Note: Update connection details in setup_connection() before running")
    print("Uncomment the line below to run examples:")
    # run_all_examples()