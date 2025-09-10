"""Pydantic models for natural language translation endpoints"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class NaturalLanguageRequest(BaseModel):
    """Request model for natural language translation"""
    query: str = Field(..., description="Natural language query description", min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find all upstream providers for Google"
            }
        }

class NLPTranslationResponse(BaseModel):
    """Response model for natural language translation"""
    success: bool = Field(..., description="Whether the translation was successful")
    natural_language: Optional[str] = Field(None, description="Original natural language query")
    cypher: Optional[str] = Field(None, description="Generated Cypher query")
    explanation: Optional[str] = Field(None, description="Human-readable explanation of the query")
    llm_reasoning: Optional[str] = Field(None, description="Full LLM response for debugging")
    error: Optional[str] = Field(None, description="Error message if translation failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "natural_language": "Find all upstream providers for Google",
                "cypher": "MATCH (as:AS {name: 'Google'})-[:DEPENDS_ON]->(upstream:AS) RETURN as, upstream LIMIT 20",
                "explanation": "Searches Autonomous System nodes; Follows upstream/downstream relationships; Limits result count for performance",
                "llm_reasoning": "Generated query to find upstream providers...",
                "error": None
            }
        }

class APITestResponse(BaseModel):
    """Response model for API connection test"""
    success: bool = Field(..., description="Whether the API test was successful")
    message: str = Field(..., description="Test result message")
    test_query: Optional[str] = Field(None, description="Query used for testing")
    generated_cypher: Optional[str] = Field(None, description="Cypher generated during test")
    error: Optional[str] = Field(None, description="Error message if test failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "LLM API connection successful",
                "test_query": "Find AS information for Google",
                "generated_cypher": "MATCH (as:AS {name: 'Google'}) RETURN as LIMIT 10",
                "error": None
            }
        }