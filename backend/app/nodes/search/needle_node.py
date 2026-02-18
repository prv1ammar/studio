"""
Needle Retriever Node - Studio Standard (Universal Method)
Batch 115: Specialized Tools
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("needle_node")
class NeedleNode(BaseNode):
    """
    Search collections using the Needle AI API.
    """
    node_type = "needle_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["needle_auth"]


    properties = [
        {
            'displayName': 'Collection Id',
            'name': 'collection_id',
            'type': 'string',
            'default': '',
            'description': 'The ID of the Needle collection to search',
            'required': True,
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Enter your search query here',
            'required': True,
        },
        {
            'displayName': 'Top K',
            'name': 'top_k',
            'type': 'string',
            'default': 20,
            'description': 'Number of results to return (min: 20)',
        },
    ]
    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "Enter your search query here"
        },
        "collection_id": {
            "type": "string",
            "required": True,
            "description": "The ID of the Needle collection to search"
        },
        "top_k": {
            "type": "number",
            "default": 20,
            "description": "Number of results to return (min: 20)"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("needle_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Needle API Key is required"}

            query = self.get_config("query") or str(input_data)
            collection_id = self.get_config("collection_id")
            top_k = max(20, int(self.get_config("top_k", 20)))

            url = f"https://api.needle-ai.com/v1/collections/{collection_id}/search"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": query,
                "top_k": top_k
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Needle API error {response.status}: {text}"}
                    
                    data = await response.json()

            return {
                "status": "success",
                "data": {
                    "results": data.get("results", [])
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Needle Search failed: {str(e)}"}