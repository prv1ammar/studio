"""
Glean Search Node - Studio Standard (Universal Method)
Batch 115: Specialized Tools
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("glean_search_node")
class GleanSearchNode(BaseNode):
    """
    Search using Glean's API (Internal Enterprise Knowledge).
    """
    node_type = "glean_search_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["glean_auth"]


    properties = [
        {
            'displayName': 'Act As',
            'name': 'act_as',
            'type': 'string',
            'default': '',
            'description': 'Email or ID to act as (X-Scio-ActAs header)',
        },
        {
            'displayName': 'Page Size',
            'name': 'page_size',
            'type': 'string',
            'default': 10,
            'description': 'Maximum number of results to return',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'The search query',
            'required': True,
        },
    ]
    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "The search query"
        },
        "page_size": {
            "type": "number",
            "default": 10,
            "description": "Maximum number of results to return"
        },
        "act_as": {
            "type": "string",
            "required": False,
            "description": "Email or ID to act as (X-Scio-ActAs header)"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("glean_auth")
            api_url = creds.get("api_url")
            access_token = creds.get("access_token")
            
            if not api_url or not access_token:
                return {"status": "error", "error": "Glean API URL and Access Token are required"}

            query = self.get_config("query") or str(input_data)
            page_size = int(self.get_config("page_size", 10))
            act_as = self.get_config("act_as") or creds.get("act_as") or "studio-agent@internal.com"

            url = f"{api_url.rstrip('/')}/search"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Scio-ActAs": act_as,
                "Content-Type": "application/json"
            }
            payload = {
                "query": query,
                "pageSize": page_size
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Glean API error {response.status}: {text}"}
                    
                    data = await response.json()

            results = data.get("results", [])
            return {
                "status": "success",
                "data": {
                    "results": results
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Glean Search failed: {str(e)}"}