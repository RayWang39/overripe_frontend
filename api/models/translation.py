"""Translation request and response models"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MethodChainRequest(BaseModel):
    """Request for method chain translation"""
    method_chain: str = Field(..., description="Method chain like '.find.with_organization.upstream'")
    parameters: Dict[str, Any] = Field(default={}, description="Parameters for the methods")
    
    class Config:
        json_schema_extra = {
            "example": {
                "method_chain": ".find.with_organization.upstream",
                "parameters": {
                    "asn": 15169,
                    "hops": 2,
                    "limit": 10
                }
            }
        }

class NaturalLanguageRequest(BaseModel):
    """Request for natural language translation"""
    query: str = Field(..., description="Natural language query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find Google's upstream providers"
            }
        }

class TranslationResponse(BaseModel):
    """Response from translation service"""
    success: bool = Field(..., description="Whether translation was successful")
    cypher: Optional[str] = Field(None, description="Generated Cypher query")
    parameters: Dict[str, Any] = Field(default={}, description="Cypher parameters")
    explanation: Optional[str] = Field(None, description="Human-readable explanation")
    method_chain: Optional[str] = Field(None, description="Applied method chain")
    interpretation: Optional[str] = Field(None, description="How the query was interpreted")
    natural_language: Optional[str] = Field(None, description="Original natural language query")
    error: Optional[str] = Field(None, description="Error message if translation failed")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing the query")
    examples: Optional[List[str]] = Field(None, description="Example queries")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "cypher": "MATCH (as:AS {asn: $param_0}) RETURN as",
                "parameters": {"param_0": 15169},
                "explanation": "Finds Autonomous System nodes; Basic graph query",
                "method_chain": "find('AS', asn=15169)"
            }
        }

class ExampleTranslation(BaseModel):
    """Example translation"""
    name: str
    method_chain: str
    params: Dict[str, Any] = {}
    description: str
    translation: TranslationResponse

class ExamplesResponse(BaseModel):
    """Response with translation examples"""
    examples: List[Dict[str, Any]]