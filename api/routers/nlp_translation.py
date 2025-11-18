"""NLP translation router for natural language to Cypher translation"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from services.llm_service import DeepSeekLLMService

router = APIRouter(prefix="/api/v1/nlp", tags=["NLP Translation"])


class NLPTranslationRequest(BaseModel):
    query: str
    context: Optional[Dict] = None


class NLPTranslationResponse(BaseModel):
    success: bool
    cypher: Optional[str] = None
    explanation: Optional[str] = None
    parameters: Optional[Dict] = None
    error: Optional[str] = None


# Initialize LLM service
try:
    llm_service = DeepSeekLLMService()
except ValueError as e:
    # If API key not configured, service will be None
    llm_service = None


@router.post("/translate", response_model=NLPTranslationResponse)
async def translate_natural_language(request: NLPTranslationRequest):
    """
    Translate natural language query to Cypher using LLM

    Example:
    ```json
    {
        "query": "Find all upstream providers of Google",
        "context": {"asn": 15169}
    }
    ```
    """
    if llm_service is None:
        raise HTTPException(
            status_code=503,
            detail="LLM service not configured. Set DEEPSEEK_API_KEY environment variable."
        )

    result = await llm_service.translate_to_cypher(
        request.query,
        request.context
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/health")
async def health_check():
    """Check if NLP translation service is available"""
    return {
        "status": "healthy" if llm_service is not None else "unconfigured",
        "service": "NLP Translation",
        "llm_configured": llm_service is not None
    }
