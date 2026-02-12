from typing import Any, Dict, Optional, List
from langchain_community.utilities.serpapi import SerpAPIWrapper
from ..base import BaseNode
from ..registry import register_node

@register_node("serpapi_search")
class SerpApiNode(BaseNode):
    """
    Search engine results via SerpApi (Google, Bing, etc.).
    """
    node_type = "serpapi_search"
    version = "1.0.0"
    category = "search"
    credentials_required = ["serpapi_auth"]

    inputs = {
        "query": {"type": "string", "description": "Search query"},
        "engine": {"type": "string", "default": "google"},
        "max_results": {"type": "number", "default": 5}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            query = str(input_data) if input_data is not None else self.get_config("query")
            if not query:
                return {"status": "error", "error": "Search query is required."}

            creds = await self.get_credential("serpapi_auth")
            api_key = creds.get("api_key") if creds else self.get_config("serpapi_api_key")
            
            if not api_key:
                return {"status": "error", "error": "SerpApi API Key is required."}

            params = {
                "engine": self.get_config("engine", "google"),
            }
            
            wrapper = SerpAPIWrapper(serpapi_api_key=api_key, params=params)
            full_results = wrapper.results(query)
            
            organic = full_results.get("organic_results", [])[:int(self.get_config("max_results", 5))]
            
            results = []
            for item in organic:
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                })

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "query": query,
                    "count": len(results)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"SerpApi Search Failed: {str(e)}"}
