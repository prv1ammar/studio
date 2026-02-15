"""
Bing Search Node - Studio Standard (Universal Method)
Batch 112: Advanced Search & Knowledge
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("bing_search_node")
class BingSearchNode(BaseNode):
    """
    Search the web using Bing Search API.
    """
    node_type = "bing_search_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["bing_auth"]

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
        },
        "market": {
            "type": "string",
            "default": "en-US",
            "description": "The market to search in (e.g., en-US, fr-FR)"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("bing_auth")
            subscription_key = creds.get("subscription_key")
            
            if not subscription_key:
                return {"status": "error", "error": "Bing Subscription Key is required"}

            query = self.get_config("query") or str(input_data)
            num_results = int(self.get_config("num_results", 10))
            market = self.get_config("market", "en-US")

            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            params = {
                "q": query,
                "count": num_results,
                "mkt": market,
                "offset": 0,
                "safesearch": "Moderate"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        return {"status": "error", "error": f"Bing API error {response.status}"}
                    
                    data = await response.json()

            results = data.get("webPages", {}).get("value", [])
            return {
                "status": "success",
                "data": {
                    "results": results
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Bing Search failed: {str(e)}"}
