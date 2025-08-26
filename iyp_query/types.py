"""
Type definitions for IYP node types and relationship types.
Based on the Internet Yellow Pages documentation.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """Node types available in IYP database."""
    
    AS = "AS"
    ATLAS_MEASUREMENT = "AtlasMeasurement"
    ATLAS_PROBE = "AtlasProbe"
    AUTHORITATIVE_NAME_SERVER = "AuthoritativeNameServer"
    BGP_COLLECTOR = "BGPCollector"
    BGP_PREFIX = "BGPPrefix"
    CAIDA_IX_ID = "CaidaIXID"
    CAIDA_ORG_ID = "CaidaOrgID"
    COUNTRY = "Country"
    DOMAIN_NAME = "DomainName"
    ESTIMATE = "Estimate"
    FACILITY = "Facility"
    GEO_PREFIX = "GeoPrefix"
    HOST_NAME = "HostName"
    IP = "IP"
    IXP = "IXP"
    NAME = "Name"
    OPAQUE_ID = "OpaqueID"
    ORGANIZATION = "Organization"
    PEERINGDB_FAC_ID = "PeeringdbFacID"
    PEERINGDB_IX_ID = "PeeringdbIXID"
    PEERINGDB_NET_ID = "PeeringdbNetID"
    PEERINGDB_ORG_ID = "PeeringdbOrgID"
    PEERING_LAN = "PeeringLAN"
    POINT = "Point"
    PREFIX = "Prefix"
    RANKING = "Ranking"
    RESOLVER = "Resolver"
    RDNS_PREFIX = "RDNSPrefix"
    RIR_PREFIX = "RIRPrefix"
    RPKI_PREFIX = "RPKIPrefix"
    TAG = "Tag"
    URL = "URL"


class RelationshipType(str, Enum):
    """Relationship types available in IYP database."""
    
    ALIAS_OF = "ALIAS_OF"
    ASSIGNED = "ASSIGNED"
    AVAILABLE = "AVAILABLE"
    CATEGORIZED = "CATEGORIZED"
    CENSORED = "CENSORED"
    COUNTRY = "COUNTRY"
    DEPENDS_ON = "DEPENDS_ON"
    EXTERNAL_ID = "EXTERNAL_ID"
    LOCATED_IN = "LOCATED_IN"
    MANAGED_BY = "MANAGED_BY"
    MEMBER_OF = "MEMBER_OF"
    NAME = "NAME"
    ORIGINATE = "ORIGINATE"
    PARENT = "PARENT"
    PART_OF = "PART_OF"
    PEERS_WITH = "PEERS_WITH"
    POPULATION = "POPULATION"
    QUERIED_FROM = "QUERIED_FROM"
    RANK = "RANK"
    RESERVED = "RESERVED"
    RESOLVES_TO = "RESOLVES_TO"
    ROUTE_ORIGIN_AUTHORIZATION = "ROUTE_ORIGIN_AUTHORIZATION"
    SIBLING_OF = "SIBLING_OF"
    TARGET = "TARGET"
    WEBSITE = "WEBSITE"


NODE_PROPERTIES = {
    NodeType.AS: ["asn", "name"],
    NodeType.ATLAS_MEASUREMENT: ["id"],
    NodeType.ATLAS_PROBE: ["id"],
    NodeType.AUTHORITATIVE_NAME_SERVER: ["name"],
    NodeType.BGP_COLLECTOR: ["name"],
    NodeType.BGP_PREFIX: ["prefix", "af"],
    NodeType.CAIDA_IX_ID: ["id"],
    NodeType.CAIDA_ORG_ID: ["id"],
    NodeType.COUNTRY: ["country_code", "alpha3", "name"],
    NodeType.DOMAIN_NAME: ["name"],
    NodeType.FACILITY: ["name"],
    NodeType.GEO_PREFIX: ["prefix", "af"],
    NodeType.HOST_NAME: ["name"],
    NodeType.IP: ["ip", "af"],
    NodeType.IXP: ["name"],
    NodeType.NAME: ["name"],
    NodeType.OPAQUE_ID: ["id"],
    NodeType.ORGANIZATION: ["name"],
    NodeType.PEERINGDB_FAC_ID: ["id"],
    NodeType.PEERINGDB_IX_ID: ["id"],
    NodeType.PEERINGDB_NET_ID: ["id"],
    NodeType.PEERINGDB_ORG_ID: ["id"],
    NodeType.PEERING_LAN: ["prefix", "af"],
    NodeType.POINT: ["position"],
    NodeType.PREFIX: ["prefix", "af"],
    NodeType.RANKING: ["name"],
    NodeType.RDNS_PREFIX: ["prefix", "af"],
    NodeType.RIR_PREFIX: ["prefix", "af"],
    NodeType.RPKI_PREFIX: ["prefix", "af"],
    NodeType.TAG: ["label"],
    NodeType.URL: ["url"],
}


PREFIX_SUBTYPES = [
    NodeType.BGP_PREFIX,
    NodeType.GEO_PREFIX,
    NodeType.PEERING_LAN,
    NodeType.RDNS_PREFIX,
    NodeType.RIR_PREFIX,
    NodeType.RPKI_PREFIX,
]


def validate_node_type(node_type: str) -> bool:
    """Check if a node type is valid."""
    try:
        NodeType(node_type)
        return True
    except ValueError:
        return False


def validate_relationship_type(rel_type: str) -> bool:
    """Check if a relationship type is valid."""
    try:
        RelationshipType(rel_type)
        return True
    except ValueError:
        return False


def get_node_properties(node_type: NodeType) -> List[str]:
    """Get valid properties for a node type."""
    return NODE_PROPERTIES.get(node_type, [])