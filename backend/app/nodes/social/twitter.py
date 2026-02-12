import aiohttp
import json
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("twitter_action")
class TwitterNode(BaseNode):
    """
    Automate Twitter actions (Search).
    """
    node_type = "twitter_action"
    version = "1.0.0"
    category = "social"
    credentials_required = ["twitter_auth"]

    inputs = {
        "action": {"type": "string", "default": "search", "enum": ["search"]},
        "query": {"type": "string", "description": "Twitter search query"},
        "max_results": {"type": "number", "default": 10}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("twitter_auth")
            bearer_token = creds.get("bearer_token") or creds.get("token") if creds else self.get_config("bearer_token")
            
            if not bearer_token:
                return {"status": "error", "error": "Twitter Bearer Token is required."}

            action = self.get_config("action", "search")
            query = str(input_data) if input_data else self.get_config("query")

            if not query:
                return {"status": "error", "error": "Search query is required."}

            if action == "search":
                max_res = int(self.get_config("max_results", 10))
                url = "https://api.twitter.com/2/tweets/search/recent"
                headers = {"Authorization": f"Bearer {bearer_token}"}
                params = {"query": query, "max_results": max_res}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        result = await response.json()
                        if response.status >= 400:
                            return {"status": "error", "error": f"Twitter API Error: {result.get('title', 'Unknown error')}", "data": result}
                        
                        tweets = result.get("data", [])
                        return {
                            "status": "success",
                            "data": {
                                "results": tweets,
                                "count": len(tweets)
                            }
                        }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Twitter Node Error: {str(e)}"}
