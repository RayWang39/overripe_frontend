"""Natural Language to Cypher translation service using LLM API"""
import httpx
import json
import os
from typing import Any, Dict, Optional
from config import settings

class NLPTranslationService:
    """Service for translating natural language to Cypher queries using LLM"""
    
    def __init__(self):
        """Initialize the NLP translation service"""
        self.api_key = os.getenv('OPENROUTER_API_KEY', '')
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "deepseek/deepseek-r1-0528:free"  # Using free DeepSeek model
        print("NLP Translation service initialized with free DeepSeek model")
    
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
        """Build prompt with schema context and examples - optimized for DeepSeek R1"""
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

IMPORTANT INSTRUCTIONS:
1. Always include LIMIT clause (max 50)
2. Use exact property names from schema
3. Only use READ operations (MATCH, RETURN, WHERE, etc.)
4. Be specific with node labels and relationships
5. CRITICAL: Your response must contain ONLY the Cypher query
6. Do not include explanations, reasoning, or additional text
7. Start your response directly with MATCH or other Cypher keywords
8. Do not use markdown code blocks or formatting

USER QUERY: "{natural_query}"

Provide only the Cypher query (no explanations or reasoning):"""

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
        """Extract Cypher query from LLM response with multiple parsing strategies"""
        import re
        
        content = llm_response.strip()
        
        # Strategy 1: Remove markdown code blocks
        if "```" in content:
            # Extract content between code blocks
            code_block_pattern = r'```(?:cypher|sql)?\s*([\s\S]*?)```'
            matches = re.findall(code_block_pattern, content, re.IGNORECASE)
            if matches:
                content = matches[0].strip()
        
        # Strategy 2: Look for lines starting with MATCH (most common Cypher start)
        lines = content.split('\n')
        cypher_lines = []
        found_match = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('MATCH'):
                found_match = True
                cypher_lines.append(line)
            elif found_match and line:
                # Continue collecting lines after MATCH
                if any(keyword in line.upper() for keyword in ['RETURN', 'WHERE', 'WITH', 'LIMIT', 'ORDER']):
                    cypher_lines.append(line)
                elif line.upper().startswith(('CREATE', 'DELETE', 'SET')):
                    # Stop at unsafe operations
                    break
                elif line and not line.startswith('#') and not line.startswith('//'):
                    cypher_lines.append(line)
        
        if cypher_lines:
            extracted = ' '.join(cypher_lines)
            if self._is_valid_cypher_structure(extracted):
                return extracted
        
        # Strategy 3: Find any MATCH statement in the text
        match_pattern = r'(MATCH\s+[^\n]*(?:\n[^\n]*)*?(?:LIMIT\s+\d+|$))'
        matches = re.findall(match_pattern, content, re.IGNORECASE | re.MULTILINE)
        if matches:
            candidate = matches[0].strip()
            if self._is_valid_cypher_structure(candidate):
                return candidate
        
        # Strategy 4: Look for any line that looks like Cypher
        for line in lines:
            line = line.strip()
            if (line.upper().startswith('MATCH') and 
                ('RETURN' in line.upper() or 'WHERE' in line.upper())):
                if self._is_valid_cypher_structure(line):
                    return line
        
        # Strategy 5: Return the whole response if it looks like Cypher
        if self._is_valid_cypher_structure(content):
            return content
        
        return None
    
    def _is_valid_cypher_structure(self, text: str) -> bool:
        """Check if text has basic Cypher structure"""
        text_upper = text.upper()
        return (text_upper.startswith('MATCH') and 
                ('RETURN' in text_upper or 'WHERE' in text_upper) and
                len(text.strip()) > 10)
    
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