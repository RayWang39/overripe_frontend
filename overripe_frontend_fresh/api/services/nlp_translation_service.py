"""Natural Language to Cypher translation service using LLM API"""
import httpx
import json
from typing import Any, Dict, Optional
from config import settings

class NLPTranslationService:
    """Service for translating natural language to Cypher queries using LLM"""
    
    def __init__(self):
        """Initialize the NLP translation service"""
        self.api_key = os.getenv('OPENROUTER_API_KEY', '')
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"
        print("NLP Translation service initialized with LLM API")
    
    def translate_natural_language(self, natural_query: str) -> Dict[str, Any]:
        """
        Translate natural language query to Cypher
        
        Args:
            natural_query: Natural language description like "Find Google's upstream providers"
            
        Returns:
            Dict with success status, cypher query, and explanation
        """
        try:
            # Create prompt with schema context
            prompt = self._build_prompt(natural_query)
            
            # Call LLM API
            response = self._call_llm_api(prompt)
            
            if not response["success"]:
                return response
            
            # Parse LLM response
            llm_content = response["content"]
            
            # Extract Cypher query from response
            cypher_query = self._extract_cypher(llm_content)
            
            if not cypher_query:
                return {
                    "success": False,
                    "error": "Could not extract valid Cypher query from LLM response",
                    "llm_response": llm_content
                }
            
            # Validate query safety
            if not self._is_safe_query(cypher_query):
                return {
                    "success": False,
                    "error": "Generated query contains unsafe operations",
                    "cypher": cypher_query
                }
            
            return {
                "success": True,
                "natural_language": natural_query,
                "cypher": cypher_query,
                "explanation": self._explain_query(cypher_query),
                "llm_reasoning": llm_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Translation error: {str(e)}",
                "natural_language": natural_query
            }
    
    def _build_prompt(self, natural_query: str) -> str:
        """Build prompt with schema context and examples"""
        return f"""You are an expert Neo4j Cypher query generator for internet infrastructure data.

DATABASE SCHEMA:
Node Types:
- AS (Autonomous System): Properties: asn (integer), name (string)
- Organization: Properties: name (string), country (string)
- Country: Properties: country_code (string), name (string)
- Prefix: Properties: prefix (string), type (string)
- IXP: Properties: name (string), city (string)

Relationship Types:
- DEPENDS_ON: AS → AS (upstream/downstream relationships)
- MANAGED_BY: AS → Organization (ownership)
- PEERS_WITH: AS ↔ AS (peering relationships)
- MEMBER_OF: AS → IXP (IXP membership)
- COUNTRY: AS/Organization → Country (location)
- ORIGINATE: AS → Prefix (BGP origination)

EXAMPLES:
Natural: "Find Google's AS information"
Cypher: MATCH (as:AS {{name: 'Google'}}) RETURN as LIMIT 10

Natural: "Show upstream providers of AS 15169"
Cypher: MATCH (as:AS {{asn: 15169}})-[:DEPENDS_ON]->(upstream:AS) RETURN as, upstream LIMIT 20

Natural: "Find all ASes managed by Google"
Cypher: MATCH (org:Organization {{name: 'Google'}})<-[:MANAGED_BY]-(as:AS) RETURN org, as LIMIT 20

Natural: "Show peering partners of Cloudflare"
Cypher: MATCH (as:AS {{name: 'Cloudflare'}})-[:PEERS_WITH]-(peer:AS) RETURN as, peer LIMIT 15

RULES:
1. Always include LIMIT clause (max 50)
2. Use exact property names from schema
3. Only use READ operations (MATCH, RETURN, WHERE, etc.)
4. Be specific with node labels and relationships
5. Return only the Cypher query, nothing else

USER QUERY: "{natural_query}"

Generate the corresponding Cypher query:"""

    def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """Call the LLM API with the prompt"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "content": content.strip(),
                    "usage": data.get("usage", {})
                }
                
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error calling LLM API: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error calling LLM API: {str(e)}"
            }
    
    def _extract_cypher(self, llm_response: str) -> Optional[str]:
        """Extract Cypher query from LLM response"""
        # Remove markdown code blocks if present
        content = llm_response.strip()
        
        # Remove ```cypher and ``` markers
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```cypher or similar)
            if len(lines) > 0:
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Basic validation - should start with MATCH
        if content.upper().startswith("MATCH"):
            return content
        
        return None
    
    def _is_safe_query(self, cypher: str) -> bool:
        """Check if the query is safe (no write operations)"""
        unsafe_keywords = [
            "CREATE", "DELETE", "REMOVE", "SET", "MERGE", "DROP", 
            "DETACH", "LOAD", "CALL", "USING"
        ]
        
        cypher_upper = cypher.upper()
        return not any(keyword in cypher_upper for keyword in unsafe_keywords)
    
    def _explain_query(self, cypher: str) -> str:
        """Generate human-readable explanation of the query"""
        explanations = []
        
        cypher_upper = cypher.upper()
        
        if "AS:" in cypher_upper:
            explanations.append("Searches Autonomous System nodes")
        if "ORGANIZATION:" in cypher_upper:
            explanations.append("Includes organization data")
        if "DEPENDS_ON" in cypher_upper:
            explanations.append("Follows upstream/downstream relationships")
        if "PEERS_WITH" in cypher_upper:
            explanations.append("Finds peering relationships")
        if "MANAGED_BY" in cypher_upper:
            explanations.append("Shows organizational ownership")
        if "LIMIT" in cypher_upper:
            explanations.append("Limits result count for performance")
            
        return "; ".join(explanations) if explanations else "Basic graph query"

    def test_api_connection(self) -> Dict[str, Any]:
        """Test the LLM API connection with a simple query"""
        test_query = "Find AS information for Google"
        
        print("🧪 Testing LLM API connection...")
        result = self.translate_natural_language(test_query)
        
        if result["success"]:
            print("✅ LLM API connection successful!")
            print(f"Generated Cypher: {result['cypher']}")
        else:
            print("❌ LLM API connection failed!")
            print(f"Error: {result['error']}")
            
        return result

# Singleton instance
nlp_translation_service = NLPTranslationService()