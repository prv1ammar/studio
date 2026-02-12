import httpx
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("agentql_action")
class AgentQLNode(BaseNode):
    """
    Automate AgentQL actions (Extract, Query).
    Uses AI to extract highly structured data from websites.
    """
    node_type = "agentql_action"
    version = "1.1.0"
    category = "scraping"
    credentials_required = ["agentql_auth"]

    inputs = {
        "url": {"type": "string", "description": "Page URL"},
        "query": {"type": "string", "description": "AgentQL query or natural language prompt"},
        "mode": {"type": "string", "default": "fast", "enum": ["fast", "standard"]}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("agentql_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "AgentQL API Key is required."}

            url = self.get_config("url")
            if isinstance(input_data, str) and input_data.startswith("http"):
                url = input_data
            
            query = self.get_config("query")
            if isinstance(input_data, dict):
                url = input_data.get("url") or url
                query = input_data.get("query") or query
            
            if not url or not query:
                return {"status": "error", "error": "URL and Query/Prompt are required."}

            endpoint = "https://api.agentql.com/v1/query-data"
            headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
            
            # Intelligent Routing: If query looks like natural language, use 'prompt' field
            is_prompt = " " in query and "{" not in query
            payload = {
                "url": url,
                "query": None if is_prompt else query,
                "prompt": query if is_prompt else None,
                "params": {"mode": self.get_config("mode", "fast")}
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(endpoint, headers=headers, json=payload, timeout=300)
                if resp.status_code >= 400:
                    return {"status": "error", "error": f"AgentQL API Error: {resp.text}"}
                
                result = resp.json()
                return {
                    "status": "success",
                    "data": {
                        "result": result.get("data"),
                        "metadata": result.get("metadata")
                    }
                }

        except Exception as e:
            return {"status": "error", "error": f"AgentQL Node Error: {str(e)}"}
