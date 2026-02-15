"""
Upstash Node - Studio Standard (Universal Method)
Batch 118: AI Essentials & Local Inference
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("upstash_node")
class UpstashNode(BaseNode):
    """
    Search and store data in Upstash Vector or Redis.
    """
    node_type = "upstash_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["upstash_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "vec_search",
            "options": ["vec_search", "vec_upsert", "redis_get", "redis_set"],
            "description": "The action to perform"
        },
        "index_url": {
            "type": "string",
            "required": True,
            "description": "Upstash Index or Redis URL"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query or value to set"
        },
        "top_k": {
            "type": "number",
            "default": 10
        }
    }

    outputs = {
        "results": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("upstash_auth")
            token = creds.get("token")
            
            if not token:
                return {"status": "error", "error": "Upstash Token is required"}

            action = self.get_config("action")
            url = self.get_config("index_url").rstrip('/')
            query = self.get_config("query") or str(input_data)
            top_k = int(self.get_config("top_k", 10))

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "vec_search":
                    # For Upstash Vector search
                    payload = {"data": query, "topK": top_k, "includeMetadata": True}
                    async with session.post(f"{url}/query", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

                elif action == "redis_get":
                    # For Upstash Redis GET
                    async with session.get(f"{url}/get/{query}", headers=headers) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data.get("result")}}

                elif action == "redis_set":
                    # For Upstash Redis SET
                    # input_data might be the value
                    val = str(input_data) if input_data else "1"
                    async with session.get(f"{url}/set/{query}/{val}", headers=headers) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

            return {"status": "error", "error": f"Action {action} not yet implemented."}

        except Exception as e:
            return {"status": "error", "error": f"Upstash failed: {str(e)}"}
