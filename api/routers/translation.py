"""Translation endpoints router"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict

from models.translation import (
    MethodChainRequest, 
    TranslationResponse, 
    ExamplesResponse
)
from services.translation_service import translation_service
from middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1/translate", tags=["Translation"])

@router.post("/method-chain", response_model=TranslationResponse)
async def translate_method_chain(
    request: MethodChainRequest,
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Translate method chain to Cypher query
    
    Translates queries like '.find.with_organizations.upstream' into Cypher.
    This is the main endpoint for programmatic query building.
    
    **Example method chains:**
    - `.find` - Basic AS lookup
    - `.find.with_organizations` - AS with organization details  
    - `.find.upstream` - AS with upstream providers
    - `.find.peers` - AS with peering relationships
    - `.find.with_organizations.upstream.limit` - Complex chain
    
    **Common parameters:**
    - `asn`: AS number to search for
    - `hops`: Number of relationship hops (for upstream/downstream)
    - `limit`: Maximum results to return
    - `node_type`: Type of node to find (default: 'AS')
    """
    result = translation_service.translate_method_chain(
        method_chain=request.method_chain,
        params=request.parameters
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/examples", response_model=ExamplesResponse)
async def get_translation_examples(
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get example translations showing common query patterns
    
    Returns a collection of example method chains with their
    corresponding Cypher translations. Useful for understanding
    the translation patterns and learning the method chain syntax.
    """
    return translation_service.get_common_examples()

@router.get("/help")
async def get_translation_help(
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get help information for query translation
    
    Provides documentation on method chain syntax, available methods,
    parameter options, and usage examples.
    """
    return {
        "method_chain_syntax": {
            "format": ".method1.method2.method3",
            "description": "Chain methods with dots, starting with a dot",
            "examples": [
                ".find",
                ".find.with_organizations", 
                ".find.upstream.limit",
                ".find.with_relationship.where"
            ]
        },
        "available_methods": {
            "find": {
                "description": "Find nodes by type and properties",
                "parameters": ["node_type", "asn", "alias"],
                "example": ".find (params: {asn: 15169})"
            },
            "with_organizations": {
                "description": "Include organization details",
                "parameters": [],
                "example": ".find.with_organizations"
            },
            "upstream": {
                "description": "Find upstream providers",
                "parameters": ["hops", "upstream_alias"],
                "example": ".find.upstream (params: {hops: 2})"
            },
            "downstream": {
                "description": "Find downstream customers", 
                "parameters": ["hops", "downstream_alias"],
                "example": ".find.downstream (params: {hops: 1})"
            },
            "peers": {
                "description": "Find peering partners",
                "parameters": ["peer_alias"],
                "example": ".find.peers"
            },
            "with_relationship": {
                "description": "Add custom relationship traversal",
                "parameters": ["relationship", "to", "rel_alias"],
                "example": ".find.with_relationship (params: {relationship: 'COUNTRY', to: 'Country'})"
            },
            "where": {
                "description": "Add filtering conditions",
                "parameters": ["condition"],
                "example": ".find.where (params: {condition: 'node.asn > 1000'})"
            },
            "limit": {
                "description": "Limit number of results",
                "parameters": ["limit"],
                "example": ".find.limit (params: {limit: 10})"
            },
            "return_fields": {
                "description": "Specify fields to return",
                "parameters": ["fields"],
                "example": ".find.return_fields (params: {fields: ['node.asn', 'node.name']})"
            }
        },
        "common_parameters": {
            "asn": "Autonomous System Number (integer)",
            "hops": "Number of relationship hops to traverse (1-3)",
            "limit": "Maximum number of results (1-1000)",
            "node_type": "Type of node to find ('AS', 'Organization', 'Country')",
            "alias": "Alias name for the node in the query",
            "relationship": "Relationship type ('DEPENDS_ON', 'PEERS_WITH', 'COUNTRY', etc.)",
            "to": "Target node type for relationships"
        },
        "tips": [
            "Always start method chains with a dot (.)",
            "Parameters are passed separately from the method chain",
            "Use 'asn' parameter to specify which AS to query",
            "Chain methods in logical order: find → relationships → filtering → output",
            "Test with /translate/examples to see working patterns"
        ]
    }