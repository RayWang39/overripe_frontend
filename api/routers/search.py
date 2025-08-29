"""High-level search endpoints router"""
from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery, status
from typing import Any, Dict, Optional

from models.requests import ASQueryRequest, CountryQueryRequest
from models.responses import QueryResponse, ASDetails
from services.query_service import query_service
from middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1", tags=["Search"])

@router.get("/as/{asn}", response_model=QueryResponse)
async def get_as_details(
    asn: int,
    include_organizations: bool = FastAPIQuery(False, description="Include organization details"),
    include_peers: bool = FastAPIQuery(False, description="Include peering relationships"),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get details for a specific Autonomous System
    """
    result = query_service.get_as_details(
        asn=asn,
        include_organizations=include_organizations,
        include_peers=include_peers
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AS{asn} not found"
        )
    
    return result

@router.get("/as/{asn}/upstream", response_model=QueryResponse)
async def get_upstream_providers(
    asn: int,
    max_hops: int = FastAPIQuery(1, ge=1, le=3, description="Maximum hops to traverse"),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get upstream providers for an AS
    """
    result = query_service.find_upstream_providers(asn=asn, max_hops=max_hops)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/as/{asn}/downstream", response_model=QueryResponse)
async def get_downstream_customers(
    asn: int,
    max_hops: int = FastAPIQuery(1, ge=1, le=3, description="Maximum hops to traverse"),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get downstream customers for an AS
    """
    # This would use a downstream method similar to upstream
    # For now, returning a placeholder
    return {
        "success": True,
        "data": [],
        "count": 0,
        "query_time_ms": 0,
        "cached": False
    }

@router.get("/as/{asn}/peers", response_model=QueryResponse)
async def get_as_peers(
    asn: int,
    limit: int = FastAPIQuery(100, ge=1, le=1000),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get peering partners for an AS
    """
    operations = [
        {"method": "find", "params": {"node_type": "AS", "asn": asn, "alias": "source"}},
        {"method": "with_relationship", "params": {"rel_type": "PEERS_WITH", "to": "AS", "alias": "peer"}},
        {"method": "limit", "params": {"n": limit}},
        {"method": "return_fields", "params": {"fields": ["peer.asn", "peer.name"]}}
    ]
    
    result = query_service.execute_builder_query(operations)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/country/{country_code}/as", response_model=QueryResponse)
async def get_country_ases(
    country_code: str,
    limit: int = FastAPIQuery(100, ge=1, le=1000),
    include_organizations: bool = FastAPIQuery(False),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get all ASes in a specific country
    """
    if len(country_code) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Country code must be 2 letters (ISO 3166-1 alpha-2)"
        )
    
    result = query_service.find_as_by_country(
        country_code=country_code.upper(),
        limit=limit
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/search/as", response_model=QueryResponse)
async def search_as(
    name: Optional[str] = FastAPIQuery(None, description="Search by AS name"),
    country: Optional[str] = FastAPIQuery(None, description="Filter by country code"),
    min_asn: Optional[int] = FastAPIQuery(None, description="Minimum ASN"),
    max_asn: Optional[int] = FastAPIQuery(None, description="Maximum ASN"),
    limit: int = FastAPIQuery(100, ge=1, le=1000),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Search for ASes with various filters
    """
    operations = [{"method": "find", "params": {"node_type": "AS", "alias": "as_node"}}]
    
    # Build where conditions
    conditions = []
    if min_asn is not None:
        conditions.append(f"as_node.asn >= {min_asn}")
    if max_asn is not None:
        conditions.append(f"as_node.asn <= {max_asn}")
    
    if country:
        operations.append({
            "method": "with_relationship",
            "params": {"rel_type": "COUNTRY", "to": "Country", "alias": "country"}
        })
        conditions.append(f"country.country_code = '{country.upper()}'")
    
    if conditions:
        where_clause = " AND ".join(conditions)
        operations.append({"method": "where_raw", "params": {"condition": where_clause}})
    
    operations.append({"method": "limit", "params": {"n": limit}})
    operations.append({
        "method": "return_fields",
        "params": {"fields": ["as_node.asn", "as_node.name"]}
    })
    
    result = query_service.execute_builder_query(operations)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result