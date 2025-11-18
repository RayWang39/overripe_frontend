"""LLM service for translating natural language to Cypher queries using DeepSeek API"""
import os
import httpx
from typing import Dict, Optional


class DeepSeekLLMService:
    """Service for translating natural language to Cypher using DeepSeek API"""

    def __init__(self):
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")

    async def translate_to_cypher(
        self,
        natural_query: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Translate natural language to Cypher query

        Args:
            natural_query: User's natural language query
            context: Optional context (schema info, examples)

        Returns:
            {
                "success": bool,
                "cypher": str,
                "explanation": str,
                "parameters": dict,
                "error": str (if failed)
            }
        """

        # Build system prompt with schema context
        system_prompt = self._build_system_prompt()

        # Build user prompt
        user_prompt = self._build_user_prompt(natural_query, context)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "max_tokens": 2048,
                        "temperature": 0.3,  # Lower for more deterministic output
                        "top_p": 0.9,
                        "frequency_penalty": 0.5
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    cypher_response = result["choices"][0]["message"]["content"]

                    # Parse the LLM response
                    return self._parse_llm_response(cypher_response)
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code} - {response.text}"
                    }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout - LLM service took too long to respond"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM service error: {str(e)}"
            }

    def _build_system_prompt(self) -> str:
        """Build system prompt with Neo4j schema context"""
        return """You are a Neo4j Cypher query expert for the Internet Yellow Pages (IYP) database.

**Database Schema:**
- AS (Autonomous Systems): Properties: asn, name
- Organization: Properties: name, country
- Prefix: Properties: prefix (IP prefix)
- IXP: Properties: name (Internet Exchange Point)
- Country: Properties: country_code, name

**Relationships:**
- (AS)-[:DEPENDS_ON]->(AS) - Upstream/downstream relationships
- (AS)-[:MANAGED_BY]->(Organization)
- (AS)-[:PEERS_WITH]->(AS)
- (AS)-[:MEMBER_OF]->(IXP)
- (Entity)-[:COUNTRY]->(Country)
- (AS)-[:ORIGINATE]->(Prefix)

**Your task:**
1. Translate natural language queries to valid Cypher
2. Return ONLY valid Cypher code, no explanations in the query
3. Use LIMIT to prevent large result sets (default: 100)
4. Format your response as:
```cypher
<CYPHER_QUERY>
```

**Examples:**
User: "Find upstream providers of AS15169"
```cypher
MATCH (as:AS {asn: 15169})-[:DEPENDS_ON]->(upstream:AS)
RETURN as.asn AS source_asn, upstream.asn AS upstream_asn, upstream.name AS upstream_name
LIMIT 100
```

User: "Show organizations in the United States"
```cypher
MATCH (org:Organization)-[:COUNTRY]->(c:Country {country_code: 'US'})
RETURN org.name AS organization, c.name AS country
LIMIT 100
```"""

    def _build_user_prompt(self, query: str, context: Optional[Dict]) -> str:
        """Build user prompt with query and optional context"""
        prompt = f"Translate this query to Cypher:\n{query}"

        if context:
            if "asn" in context:
                prompt += f"\n\nContext: ASN = {context['asn']}"
            if "examples" in context:
                prompt += f"\n\nSimilar examples:\n{context['examples']}"

        return prompt

    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response to extract Cypher query"""
        # Extract Cypher from markdown code blocks
        if "```cypher" in response:
            start = response.find("```cypher") + len("```cypher")
            end = response.find("```", start)
            cypher = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            cypher = response[start:end].strip()
        else:
            # Assume entire response is Cypher
            cypher = response.strip()

        return {
            "success": True,
            "cypher": cypher,
            "explanation": "Translated natural language query to Cypher",
            "parameters": {}  # MVP: no parameter extraction yet
        }
