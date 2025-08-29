"""Request models for the API"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class QueryType(str, Enum):
    BUILDER = "builder"
    CYPHER = "cypher"
    DOMAIN = "domain"

class ReturnFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    DATAFRAME = "dataframe"

class QueryOperation(BaseModel):
    """Single operation in a query chain"""
    method: str = Field(..., description="Method name like 'find', 'with_relationship', 'where'")
    params: Dict[str, Any] = Field(default={}, description="Parameters for the method")
    
    class Config:
        json_schema_extra = {
            "example": {
                "method": "find",
                "params": {"node_type": "AS", "asn": 15169}
            }
        }

class QueryRequest(BaseModel):
    """Request model for executing queries"""
    query_type: QueryType = Field(QueryType.BUILDER, description="Type of query to execute")
    operations: List[QueryOperation] = Field(..., description="List of operations to perform")
    return_format: ReturnFormat = Field(ReturnFormat.JSON, description="Format for the response")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of results")
    return_fields: Optional[List[str]] = Field(None, description="Specific fields to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_type": "builder",
                "operations": [
                    {"method": "find", "params": {"node_type": "AS", "asn": 15169}},
                    {"method": "with_organizations", "params": {}},
                    {"method": "limit", "params": {"n": 10}}
                ],
                "return_format": "json",
                "limit": 10
            }
        }

class CypherQueryRequest(BaseModel):
    """Request model for raw Cypher queries"""
    query: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(default={}, description="Query parameters")
    return_format: ReturnFormat = Field(ReturnFormat.JSON)
    
    @validator('query')
    def validate_query(cls, v):
        # Basic validation to prevent destructive operations
        forbidden_keywords = ['CREATE', 'DELETE', 'MERGE', 'SET', 'REMOVE', 'DROP']
        query_upper = v.upper()
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        return v

class ASQueryRequest(BaseModel):
    """Request for AS-specific queries"""
    asn: int = Field(..., description="Autonomous System Number")
    include_organizations: bool = Field(False, description="Include organization details")
    include_prefixes: bool = Field(False, description="Include announced prefixes")
    include_peers: bool = Field(False, description="Include peering relationships")
    max_hops: Optional[int] = Field(1, ge=1, le=3, description="Maximum hops for traversal")

class CountryQueryRequest(BaseModel):
    """Request for country-specific queries"""
    country_code: str = Field(..., description="ISO 2-letter country code", min_length=2, max_length=2)
    include_organizations: bool = Field(False)
    limit: Optional[int] = Field(100, ge=1, le=1000)