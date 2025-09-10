"""Natural Language Translation router"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict

from models.nlp_translation import (
    NaturalLanguageRequest,
    NLPTranslationResponse,
    APITestResponse
)
from services.nlp_translation_service import nlp_translation_service
from middleware.auth import verify_api_key

router = APIRouter(prefix="/api/v1/nlp", tags=["Natural Language Translation"])

@router.post("/translate", response_model=NLPTranslationResponse)
async def translate_natural_language(
    request: NaturalLanguageRequest,
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Translate natural language to Cypher query using LLM
    
    Converts natural language descriptions like "Find Google's upstream providers" 
    into corresponding Cypher queries for the Neo4j graph database.
    
    **Example queries:**
    - "Find Google's upstream providers"
    - "Show all ASes managed by Cloudflare"
    - "List peering partners of AS 15169"
    - "Find organizations in the US"
    - "Show country information for AS 216139"
    
    **Features:**
    - Uses Claude 3.5 Sonnet for intelligent query generation
    - Includes safety validation (no write operations)
    - Provides human-readable explanations
    - Handles complex relationship queries
    
    **Safety:**
    - Only generates READ queries (MATCH, RETURN, WHERE)
    - Includes automatic LIMIT clauses
    - Validates against unsafe operations
    """
    result = nlp_translation_service.translate_natural_language(request.query)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/test", response_model=APITestResponse)
async def test_llm_connection(
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Test the LLM API connection
    
    Performs a simple test query to verify that the LLM API is working correctly.
    Useful for debugging and health checks.
    """
    test_result = nlp_translation_service.test_api_connection()
    
    if test_result["success"]:
        return {
            "success": True,
            "message": "LLM API connection successful",
            "test_query": "Find AS information for Google",
            "generated_cypher": test_result.get("cypher"),
            "error": None
        }
    else:
        return {
            "success": False,
            "message": "LLM API connection failed",
            "test_query": "Find AS information for Google",
            "generated_cypher": None,
            "error": test_result.get("error")
        }

@router.get("/examples")
async def get_nlp_examples(
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get example natural language queries
    
    Returns a collection of example natural language queries that can be
    translated to Cypher, along with their expected outputs.
    """
    return {
        "examples": [
            {
                "category": "AS Information",
                "queries": [
                    "Find AS information for Google",
                    "Show details about AS 15169",
                    "Get information about Cloudflare's autonomous system"
                ]
            },
            {
                "category": "Upstream/Downstream",
                "queries": [
                    "Find Google's upstream providers",
                    "Show downstream customers of AS 174",
                    "List all providers for AS 216139"
                ]
            },
            {
                "category": "Peering",
                "queries": [
                    "Find peering partners of Cloudflare",
                    "Show who peers with AS 15169",
                    "List peering relationships for Google"
                ]
            },
            {
                "category": "Organizations",
                "queries": [
                    "Find all ASes managed by Google",
                    "Show organizations that own multiple ASes",
                    "List ASes owned by US companies"
                ]
            },
            {
                "category": "Geographic",
                "queries": [
                    "Find ASes in the United States",
                    "Show organizations located in Germany",
                    "List ASes by country"
                ]
            }
        ],
        "tips": [
            "Be specific about what you're looking for",
            "Use company names or AS numbers for precise results",
            "Mention relationships like 'upstream', 'downstream', 'peers'",
            "Include geographic information when relevant",
            "The system automatically adds LIMIT clauses for performance"
        ]
    }