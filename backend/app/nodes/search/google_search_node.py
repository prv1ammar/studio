"""
Google Search Node - Studio Standard (Universal Method)
Batch 112: Advanced Search & Knowledge
"""
from typing import Any, Dict, Optional
import aiohttp
from pydantic import BaseModel, Field
from ...base import BaseNode
from ...registry import register_node

class GoogleSearchConfig(BaseModel):
    num_results: int = Field(default=10, ge=1, le=10)

class GoogleSearchInput(BaseModel):
    query: str

@register_node("google_search_node")
class GoogleSearchNode(BaseNode):
    """
    Search the web using Google Search JSON API.
    """
    node_type = "google_search_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["google_search_auth"]
    
    config_model = GoogleSearchConfig
    input_model = GoogleSearchInput

    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "The search query"
        },
        "num_results": {
            "type": "number",
            "default": 10,
            "description": "Number of results to return"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("google_search_auth")
            api_key = creds.get("api_key")
            search_engine_id = creds.get("search_engine_id")
            
            if not api_key or not search_engine_id:
                return {"status": "error", "error": "Google API Key and Search Engine ID are required"}

            query = self.get_config("query") or str(input_data)
            num_results = int(self.get_config("num_results", 10))

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": num_results
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return {"status": "error", "error": f"Google Search API error {response.status}"}
                    
                    data = await response.json()

            results = data.get("items", [])
            return {
                "status": "success",
                "data": {
                    "results": results
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Google Search failed: {str(e)}"}
