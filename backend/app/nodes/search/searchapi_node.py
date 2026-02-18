"""
SearchAPI Node - Studio Standard (Universal Method)
Batch 112: Advanced Search & Knowledge
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("searchapi_node")
class SearchAPINode(BaseNode):
    """
    Real-time results from Google, Bing, DuckDuckGo, and other search engines.
    """
    node_type = "searchapi_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["searchapi_auth"]


    properties = [
        {
            'displayName': 'Engine',
            'name': 'engine',
            'type': 'options',
            'default': 'google',
            'options': [
                {'name': 'Google', 'value': 'google'},
                {'name': 'Bing', 'value': 'bing'},
                {'name': 'Duckduckgo', 'value': 'duckduckgo'},
                {'name': 'Google News', 'value': 'google_news'},
                {'name': 'Google Jobs', 'value': 'google_jobs'},
            ],
            'description': 'The search engine to use',
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
        "engine": {
            "type": "dropdown",
            "default": "google",
            "options": ["google", "bing", "duckduckgo", "google_news", "google_jobs"],
            "description": "The search engine to use"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("searchapi_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "SearchAPI API Key is required"}

            query = self.get_config("query") or str(input_data)
            engine = self.get_config("engine", "google")

            url = "https://www.searchapi.io/api/v1/search"
            params = {
                "engine": engine,
                "q": query,
                "api_key": api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return {"status": "error", "error": f"SearchAPI Error: {response.status}"}
                    
                    data = await response.json()

            results = data.get("organic_results", [])
            return {
                "status": "success",
                "data": {
                    "results": results
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"SearchAPI logic failed: {str(e)}"}