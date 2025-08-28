"""Query endpoints router"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict

from models.requests import QueryRequest, CypherQueryRequest
from models.responses import QueryResponse, ErrorResponse, CypherValidationResponse
from services.query_service import query_service
from middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1/query", tags=["Query"])

@router.post("/execute", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Execute a query using the builder pattern
    
    This endpoint allows you to chain multiple operations to build complex queries.
    """
    result = query_service.execute_builder_query(
        operations=request.operations,
        return_format=request.return_format,
        limit=request.limit,
        return_fields=request.return_fields
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/cypher", response_model=QueryResponse)
async def execute_cypher(
    request: CypherQueryRequest,
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Execute a raw Cypher query
    
    Note: Only read operations are allowed. Write operations will be rejected.
    """
    # Validate the query first
    validation = query_service.validate_cypher_query(request.query)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query: {', '.join(validation['errors'])}"
        )
    
    result = query_service.execute_cypher_query(
        query=request.query,
        parameters=request.parameters,
        return_format=request.return_format
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/validate", response_model=CypherValidationResponse)
async def validate_query(
    request: CypherQueryRequest,
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Validate a Cypher query without executing it
    """
    return query_service.validate_cypher_query(request.query)