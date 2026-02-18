"""
Universal Web Search Node - Studio Standard
Batch 48: Browsing & Search
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("web_search")
class WebSearchNode(BaseNode):
    """
    Search the web using various engines (Tavily, DuckDuckGo, Google).
    Optimized for RAG and agent research.
    """
    node_type = "web_search"
    version = "1.0.0"
    category = "search"
    credentials_required = ["search_auth"] # Optional key


    properties = [
        {
            'displayName': 'Engine',
            'name': 'engine',
            'type': 'options',
            'default': 'tavily',
            'options': [
                {'name': 'Tavily', 'value': 'tavily'},
                {'name': 'Duckduckgo', 'value': 'duckduckgo'},
                {'name': 'Google Serper', 'value': 'google_serper'},
            ],
            'description': 'Search engine to use',
        },
        {
            'displayName': 'Max Results',
            'name': 'max_results',
            'type': 'string',
            'default': 5,
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
        {
            'displayName': 'Search Depth',
            'name': 'search_depth',
            'type': 'options',
            'default': 'basic',
            'options': [
                {'name': 'Basic', 'value': 'basic'},
                {'name': 'Advanced', 'value': 'advanced'},
            ],
            'description': 'Depth of search (Tavily specific)',
        },
    ]
    inputs = {
        "engine": {
            "type": "dropdown",
            "default": "tavily",
            "options": ["tavily", "duckduckgo", "google_serper"],
            "description": "Search engine to use"
        },
        "query": {
            "type": "string",
            "required": True,
            "description": "The search query"
        },
        "max_results": {
            "type": "number",
            "default": 5,
            "description": "Maximum number of results to return"
        },
        "search_depth": {
            "type": "dropdown",
            "default": "basic",
            "options": ["basic", "advanced"],
            "description": "Depth of search (Tavily specific)"
        }
    }

    outputs = {
        "results": {"type": "array"},
        "snippets": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        engine = self.get_config("engine", "tavily")
        query = self.get_config("query")
        if isinstance(input_data, str) and input_data:
            query = input_data
            
        if not query:
            return {"status": "error", "error": "Search query is required."}

        max_results = int(self.get_config("max_results", 5))
        
        try:
            async with aiohttp.ClientSession() as session:
                if engine == "tavily":
                    creds = await self.get_credential("search_auth")
                    api_key = creds.get("tavily_api_key") or self.get_config("api_key")
                    
                    if not api_key:
                        return {"status": "error", "error": "Tavily API Key is required."}
                    
                    url = "https://api.tavily.com/search"
                    payload = {
                        "api_key": api_key,
                        "query": query,
                        "search_depth": self.get_config("search_depth", "basic"),
                        "max_results": max_results
                    }
                    async with session.post(url, json=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Tavily API Error: {result}"}
                        
                        results = result.get("results", [])
                        snippets = "\n\n".join([f"[{r.get('title')}]({r.get('url')}): {r.get('content')}" for r in results])
                        
                        return {
                            "status": "success",
                            "data": {
                                "results": results,
                                "snippets": snippets,
                                "answer": result.get("answer")
                            }
                        }

                elif engine == "duckduckgo":
                    # Simple DuckDuckGo scraper/api or package
                    try:
                        from duckduckgo_search import DDGS
                        with DDGS() as ddgs:
                            results = list(ddgs.text(query, max_results=max_results))
                            snippets = "\n\n".join([f"[{r.get('title')}]({r.get('href')}): {r.get('body')}" for r in results])
                            return {
                                "status": "success",
                                "data": {
                                    "results": results,
                                    "snippets": snippets
                                }
                            }
                    except ImportError:
                         return {"status": "error", "error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}

                elif engine == "google_serper":
                    creds = await self.get_credential("search_auth")
                    api_key = creds.get("serper_api_key") or self.get_config("serper_key")
                    if not api_key:
                        return {"status": "error", "error": "Serper API Key is required for Google Search."}
                    
                    url = "https://google.serper.dev/search"
                    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
                    payload = {"q": query, "num": max_results}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        organic = result.get("organic", [])
                        snippets = "\n\n".join([f"[{r.get('title')}]({r.get('link')}): {r.get('snippet')}" for r in organic])
                        return {
                            "status": "success",
                            "data": {
                                "results": organic,
                                "snippets": snippets
                            }
                        }

            return {"status": "error", "error": f"Unsupported engine: {engine}"}

        except Exception as e:
            return {"status": "error", "error": f"Search execution failed: {str(e)}"}