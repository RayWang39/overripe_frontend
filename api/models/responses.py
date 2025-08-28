"""Response models for the API"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class QueryResponse(BaseModel):
    """Standard query response"""
    success: bool = Field(..., description="Whether the query executed successfully")
    data: Union[List[Dict[str, Any]], Dict[str, Any], str] = Field(..., description="Query results")
    count: int = Field(..., description="Number of results returned")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    cached: bool = Field(False, description="Whether results were from cache")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [{"asn": 15169, "name": "Google"}],
                "count": 1,
                "query_time_ms": 45.2,
                "cached": False
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False)
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid query operation",
                "error_type": "ValidationError",
                "details": {"field": "operations", "issue": "Empty operations list"}
            }
        }

class ASDetails(BaseModel):
    """AS details response"""
    asn: int
    name: Optional[str] = None
    country: Optional[str] = None
    organization: Optional[Dict[str, Any]] = None
    upstream_count: Optional[int] = None
    downstream_count: Optional[int] = None
    peer_count: Optional[int] = None
    prefix_count: Optional[int] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_connected: bool
    cache_connected: bool
    version: str
    
class StatsResponse(BaseModel):
    """API statistics response"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_query_time_ms: float
    cache_hit_rate: float
    uptime_seconds: float

class CypherValidationResponse(BaseModel):
    """Cypher query validation response"""
    valid: bool
    query: str
    estimated_cost: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)