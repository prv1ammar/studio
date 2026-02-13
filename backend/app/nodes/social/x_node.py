"""
X (Twitter) Social Node - Studio Standard
Batch 54: Social Engagement & Influence
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("x_node")
class XNode(BaseNode):
    """
    Automate X (formerly Twitter) actions including Posting and Searching.
    """
    node_type = "x_node"
    version = "1.1.0"
    category = "social"
    credentials_required = ["x_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "post_tweet",
            "options": ["post_tweet", "search_recent", "get_user_info"],
            "description": "X action to perform"
        },
        "text": {
            "type": "string",
            "optional": True,
            "description": "Tweet content (for post_tweet)"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query (for search_recent)"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Max results for search"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "tweet_id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth (Supports Bearer or OAuth2 User Token)
            creds = await self.get_credential("x_auth")
            token = creds.get("token") or creds.get("access_token") or self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "X API Token is required."}

            action = self.get_config("action", "post_tweet")
            text = self.get_config("text")
            query = self.get_config("query")
            
            # Dynamic Override
            if isinstance(input_data, str) and input_data:
                if action == "post_tweet":
                    text = input_data
                else:
                    query = input_data

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.twitter.com/2"

            async with aiohttp.ClientSession() as session:
                if action == "post_tweet":
                    if not text:
                         return {"status": "error", "error": "Tweet text is required."}
                    
                    url = f"{base_url}/tweets"
                    payload = {"text": text}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"X API Error: {result}"}
                        
                        tweet_id = result.get("data", {}).get("id")
                        return {
                            "status": "success",
                            "data": {"tweet_id": tweet_id, "result": result.get("data"), "status": "posted"}
                        }

                elif action == "search_recent":
                    if not query:
                         return {"status": "error", "error": "Search query is required."}
                    
                    url = f"{base_url}/tweets/search/recent"
                    params = {"query": query, "max_results": int(self.get_config("limit", 10))}
                    async with session.get(url, headers=headers, params=params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"X API Error: {result}"}
                        
                        tweets = result.get("data", [])
                        return {
                            "status": "success",
                            "data": {"result": tweets, "count": len(tweets)}
                        }

                elif action == "get_user_info":
                    url = f"{base_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("data"), "status": "fetched"}
                        }

                return {"status": "error", "error": f"Unsupported X action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"X Node Failed: {str(e)}"}
