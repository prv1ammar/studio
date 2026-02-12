from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp
import json

class TwitterConfig(NodeConfig):
    credentials_id: Optional[str] = Field(None, description="Twitter OAuth 1.0a/Bearer Token ID")

@register_node("twitter_post")
class TwitterPostNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        text = input_data if isinstance(input_data, str) else input_data.get("text", "")
        
        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Twitter credentials are required."}
            
        # Simplified: Assumes creds_data contains 'bearer_token' for search or 'access_token' for posting
        # Real-world Twitter posting needs OAuth 1.0a signatures
        # For this prototype, we'll implement the Bearer-based search as it's more common in automations
        return {"error": "Twitter Post requires OAuth 1.0a signatures. Try twitter_search for Bearer-based access."}

@register_node("twitter_search")
class TwitterSearchNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        query = input_data if isinstance(input_data, str) else input_data.get("query", "")
        
        creds_data = await self.get_credential("credentials_id")
        bearer_token = creds_data.get("bearer_token") if creds_data else None
        
        if not bearer_token:
            return {"error": "Twitter Bearer Token is required."}

        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {"query": query, "max_results": 10}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status >= 400:
                    text = await response.text()
                    return {"error": f"Twitter API Error {response.status}", "details": text}
                
                data = await response.json()
                return data.get("data", [])
