import httpx
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("tavily_search")
class TavilySearchNode(BaseNode):
    """
    Tavily Search is an AI-optimized search engine that returns structured results for RAG.
    """
    node_type = "tavily_search"
    version = "1.0.0"
    category = "search"
    credentials_required = ["tavily_auth"]

    inputs = {
        "query": {"type": "string", "description": "Search query"},
        "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "advanced"},
        "max_results": {"type": "number", "default": 5},
        "include_images": {"type": "boolean", "default": False},
        "include_answer": {"type": "boolean", "default": True}
    }
    outputs = {
        "results": {"type": "array"},
        "answer": {"type": "string"},
        "images": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            query = str(input_data) if input_data is not None else self.get_config("query")
            if not query:
                return {"status": "error", "error": "Search query is required."}

            creds = await self.get_credential("tavily_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Tavily API Key is required."}

            url = "https://api.tavily.com/search"
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": self.get_config("search_depth", "advanced"),
                "max_results": int(self.get_config("max_results", 5)),
                "include_images": self.get_config("include_images", False),
                "include_answer": self.get_config("include_answer", True),
                "topic": self.get_config("topic", "general")
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                    "score": r.get("score")
                })

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "answer": data.get("answer"),
                    "images": data.get("images", []),
                    "count": len(results)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Tavily Search Failed: {str(e)}"}
