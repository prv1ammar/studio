"""
Exa Search Node - Studio Standard (Universal Method)
Batch 112: Advanced Search & Knowledge
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("exa_search_node")
class ExaSearchNode(BaseNode):
    """
    Search and retrieve content using Exa's neural search.
    """
    node_type = "exa_search_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["exa_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search',
            'options': [
                {'name': 'Search', 'value': 'search'},
                {'name': 'Find Similar', 'value': 'find_similar'},
                {'name': 'Get Contents', 'value': 'get_contents'},
            ],
            'description': 'Exa action to perform',
        },
        {
            'displayName': 'Num Results',
            'name': 'num_results',
            'type': 'string',
            'default': 5,
            'description': 'Number of results to return',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'The search query or URL',
        },
        {
            'displayName': 'Use Autoprompt',
            'name': 'use_autoprompt',
            'type': 'boolean',
            'default': True,
            'description': 'Use Exa's autoprompt feature',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "find_similar", "get_contents"],
            "description": "Exa action to perform"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "The search query or URL"
        },
        "num_results": {
            "type": "number",
            "default": 5,
            "description": "Number of results to return"
        },
        "use_autoprompt": {
            "type": "boolean",
            "default": True,
            "description": "Use Exa's autoprompt feature"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "result": {"type": "dict"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("exa_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Exa API Key (Metaphor) is required"}

            action = self.get_config("action", "search")
            query = self.get_config("query") or str(input_data)
            num_results = int(self.get_config("num_results", 5))
            use_autoprompt = self.get_config("use_autoprompt", True)

            base_url = "https://api.exa.ai"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "search":
                    payload = {
                        "query": query,
                        "useAutoprompt": use_autoprompt,
                        "numResults": num_results
                    }
                    async with session.post(f"{base_url}/search", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data.get("results", [])}}

                elif action == "find_similar":
                    payload = {
                        "url": query,
                        "numResults": num_results
                    }
                    async with session.post(f"{base_url}/findSimilar", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data.get("results", [])}}

                elif action == "get_contents":
                    # query is expected to be a list of IDs or comma-separated
                    ids = [i.strip() for i in query.split(",")] if isinstance(query, str) else query
                    payload = {"ids": ids}
                    async with session.post(f"{base_url}/contents", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data.get("results", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Exa Search failed: {str(e)}"}