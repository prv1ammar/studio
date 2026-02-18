"""
Twitter v2 Node - Studio Standard (Universal Method)
Batch 92: Social Media Integration (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("twitter_v2_node")
class TwitterV2Node(BaseNode):
    """
    Manage Twitter/X posts and timeline via Twitter API v2.
    """
    node_type = "twitter_v2_node"
    version = "1.0.0"
    category = "social"
    credentials_required = ["twitter_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_tweet',
            'options': [
                {'name': 'Create Tweet', 'value': 'create_tweet'},
                {'name': 'Get Me', 'value': 'get_me'},
                {'name': 'Search Recent Tweets', 'value': 'search_recent_tweets'},
                {'name': 'Get User', 'value': 'get_user'},
            ],
            'description': 'Twitter action',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_tweet",
            "options": ["create_tweet", "get_me", "search_recent_tweets", "get_user"],
            "description": "Twitter action"
        },
        "query": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("twitter_auth")
            bearer_token = creds.get("bearer_token")
            # For posting, we might need OAuth 1.0a or OAuth 2.0 User Context, 
            # but Bearer is good for search/read.
            # Here assuming OAuth 2.0 Bearer for read, or User Access Token for write.
            
            if not bearer_token:
                return {"status": "error", "error": "Twitter Bearer Token required."}

            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.twitter.com/2"
            action = self.get_config("action", "create_tweet")

            async with aiohttp.ClientSession() as session:
                if action == "create_tweet":
                    text = self.get_config("query") or str(input_data)
                    url = f"{base_url}/tweets"
                    payload = {"text": text}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Twitter API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {})}}

                elif action == "search_recent_tweets":
                    query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/tweets/search/recent"
                    params = {"query": query, "max_results": 10}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Twitter API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "get_me":
                    url = f"{base_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Twitter API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Twitter Node Failed: {str(e)}"}