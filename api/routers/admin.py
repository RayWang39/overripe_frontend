"""Admin and health check endpoints"""
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Any, Dict
import time

from models.responses import HealthResponse, StatsResponse
from services.query_service import query_service
from config import settings

router = APIRouter(prefix="/api/v1", tags=["Admin"])

# Track some basic stats
start_time = time.time()
query_stats = {
    "total": 0,
    "successful": 0,
    "failed": 0,
    "total_time": 0
}

@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, Any]:
    """
    Check the health status of the API
    """
    # Check database connection
    db_connected = query_service.iyp is not None
    
    # Try to reconnect if disconnected
    if not db_connected:
        db_connected = query_service.connect_to_database()
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.utcnow(),
        "database_connected": db_connected,
        "cache_connected": False,  # Redis not implemented yet
        "version": settings.api_version
    }

@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> Dict[str, Any]:
    """
    Get API usage statistics
    """
    uptime = time.time() - start_time
    avg_time = query_stats["total_time"] / max(query_stats["total"], 1)
    
    return {
        "total_queries": query_stats["total"],
        "successful_queries": query_stats["successful"],
        "failed_queries": query_stats["failed"],
        "average_query_time_ms": avg_time,
        "cache_hit_rate": 0.0,  # Not implemented yet
        "uptime_seconds": uptime
    }

@router.get("/info")
async def get_api_info() -> Dict[str, Any]:
    """
    Get API information and capabilities
    """
    return {
        "title": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "query": {
                "builder": "/api/v1/query/execute",
                "cypher": "/api/v1/query/cypher",
                "validate": "/api/v1/query/validate"
            },
            "search": {
                "as_details": "/api/v1/as/{asn}",
                "upstream": "/api/v1/as/{asn}/upstream",
                "downstream": "/api/v1/as/{asn}/downstream",
                "peers": "/api/v1/as/{asn}/peers",
                "country_as": "/api/v1/country/{country_code}/as",
                "search": "/api/v1/search/as"
            },
            "admin": {
                "health": "/api/v1/health",
                "stats": "/api/v1/stats",
                "docs": "/docs"
            }
        },
        "features": {
            "authentication": settings.api_key_enabled,
            "rate_limiting": settings.rate_limit_enabled,
            "caching": settings.cache_enabled,
            "max_query_limit": settings.max_query_limit
        }
    }