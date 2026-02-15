"""
Serper Search Node - Studio Standard (Universal Method)
Batch 112: Advanced Search & Knowledge
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("serper_search_node")
class SerperSearchNode(BaseNode):
    """
    Search the web using Serper.dev (Google Search API).
    """
    node_type = "serper_search_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["serper_auth"]

    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "The search query"
        },
        "search_type": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "news", "images", "videos", "places"],
            "description": "Type of search to perform"
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
            creds = await self.get_credential("serper_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Serper API Key is required"}

            query = self.get_config("query") or str(input_data)
            search_type = self.get_config("search_type", "search")
            num_results = int(self.get_config("num_results", 10))

            url = f"https://google.serper.dev/{search_type}"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": num_results
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        return {"status": "error", "error": f"Serper API error {response.status}"}
                    
                    data = await response.json()

            # Serper results are in "organic", "news", "images", etc.
            results = data.get("organic", []) or data.get("news", []) or data.get("images", []) or data.get("videos", []) or data.get("places", [])
            
            return {
                "status": "success",
                "data": {
                    "results": results,
                    "raw": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Serper Search failed: {str(e)}"}
