"""
Search Tool Node - Studio Standard
Batch 37: Tools & Utilities
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("search_tool")
class SearchToolNode(BaseNode):
    """
    Perform web searches using various providers.
    Supports Tavily, SerpAPI, Google Serper, and DuckDuckGo (free).
    """
    node_type = "search_tool"
    version = "1.1.0"
    category = "tools"
    credentials_required = ["tavily_auth", "serpapi_auth", "google_serper_auth"]


    properties = [
        {
            'displayName': 'Api Key',
            'name': 'api_key',
            'type': 'string',
            'default': '',
            'description': 'API Key for chosen provider (overrides credential)',
        },
        {
            'displayName': 'K',
            'name': 'k',
            'type': 'string',
            'default': 4,
            'description': 'Number of results to return',
        },
        {
            'displayName': 'Provider',
            'name': 'provider',
            'type': 'options',
            'default': 'DuckDuckGo',
            'options': [
                {'name': 'Duckduckgo', 'value': 'DuckDuckGo'},
                {'name': 'Tavily', 'value': 'Tavily'},
                {'name': 'Serpapi', 'value': 'SerpAPI'},
                {'name': 'Googleserper', 'value': 'GoogleSerper'},
            ],
            'description': 'Search provider to use',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Search query',
            'required': True,
        },
    ]
    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "Search query"
        },
        "provider": {
            "type": "dropdown",
            "default": "DuckDuckGo",
            "options": ["DuckDuckGo", "Tavily", "SerpAPI", "GoogleSerper"],
            "description": "Search provider to use"
        },
        "k": {
            "type": "number",
            "default": 4,
            "description": "Number of results to return"
        },
        "api_key": {
            "type": "string",
            "optional": True,
            "description": "API Key for chosen provider (overrides credential)"
        }
    }

    outputs = {
        "results": {"type": "array"},
        "summary": {"type": "string"},
        "links": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get query from input or config
            if isinstance(input_data, str):
                query = input_data
            else:
                query = self.get_config("query")
            
            if not query:
                return {"status": "error", "error": "Search query is required"}

            # Get configuration
            provider = self.get_config("provider", "DuckDuckGo")
            k = int(self.get_config("k", 4))
            
            # Helper to get API key (async/await compatible)
            creds = None
            api_key = self.get_config("api_key")

            results = []

            # Execute based on provider
            if provider == "DuckDuckGo":
                try:
                    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
                    wrapper = DuckDuckGoSearchAPIWrapper(max_results=k)
                    # DuckDuckGo returns list of dicts: {'snippet': ..., 'title': ..., 'link': ...}
                    raw_results = wrapper.results(query, max_results=k)
                    results = [
                        {
                            "title": r.get("title", "Result"),
                            "content": r.get("snippet", ""),
                            "link": r.get("link", "")
                        }
                        for r in raw_results
                    ]
                except ImportError:
                    return {"status": "error", "error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}
                except Exception as e:
                     return {"status": "error", "error": f"DuckDuckGo search failed: {str(e)}"}

            elif provider == "Tavily":
                try:
                    # Get credential asynchronously
                    if not api_key:
                        creds = await self.get_credential("tavily_auth")
                        api_key = creds.get("api_key") if creds else None
                    
                    if not api_key:
                        return {"status": "error", "error": "Tavily API Key is required"}
                    
                    from langchain_community.retrievers import TavilySearchAPIRetriever
                    retriever = TavilySearchAPIRetriever(k=k, api_key=api_key)
                    docs = await retriever.ainvoke(query)
                    results = [
                        {
                            "title": d.metadata.get("title", "Result"),
                            "content": d.page_content,
                            "link": d.metadata.get("source", "")
                        }
                        for d in docs
                    ]
                except ImportError:
                    return {"status": "error", "error": "langchain-community not installed"}
                except Exception as e:
                     return {"status": "error", "error": f"Tavily search failed: {str(e)}"}

            elif provider == "SerpAPI":
                try:
                    if not api_key:
                        creds = await self.get_credential("serpapi_auth")
                        api_key = creds.get("api_key") if creds else None
                        
                    if not api_key:
                        return {"status": "error", "error": "SerpAPI Key is required"}
                
                    from langchain_community.utilities import SerpAPIWrapper
                    wrapper = SerpAPIWrapper(serpapi_api_key=api_key)
                    # SerpAPI results method returns a dict usually
                    raw_results = wrapper.results(query)
                    
                    # SerpAPI structure varies, try to extract organic results
                    organic = raw_results.get("organic_results", [])
                    results = [
                        {
                            "title": r.get("title", "Result"),
                            "content": r.get("snippet", ""),
                            "link": r.get("link", "")
                        }
                        for r in organic[:k]
                    ]
                except ImportError:
                    return {"status": "error", "error": "google-search-results not installed. Run: pip install google-search-results"}
                except Exception as e:
                     return {"status": "error", "error": f"SerpAPI search failed: {str(e)}"}

            elif provider == "GoogleSerper":
                try:
                    if not api_key:
                        creds = await self.get_credential("google_serper_auth")
                        api_key = creds.get("api_key") if creds else None
                        
                    if not api_key:
                        return {"status": "error", "error": "Serper API Key is required"}
                
                    from langchain_community.utilities import GoogleSerperAPIWrapper
                    wrapper = GoogleSerperAPIWrapper(serper_api_key=api_key, k=k)
                    raw_results = wrapper.results(query)
                    
                    organic = raw_results.get("organic", [])
                    results = [
                        {
                            "title": r.get("title", "Result"),
                            "content": r.get("snippet", ""),
                            "link": r.get("link", "")
                        }
                        for r in organic[:k]
                    ]
                except ImportError:
                    return {"status": "error", "error": "langchain-community not installed"}
                except Exception as e:
                     return {"status": "error", "error": f"GoogleSerper search failed: {str(e)}"}

            else:
                return {"status": "error", "error": f"Unknown provider: {provider}"}

            # Format summary
            summary_parts = []
            for i, r in enumerate(results):
                title = r.get('title', 'Result')
                content = r.get('content', '')
                link = r.get('link', '')
                summary_parts.append(f"{i+1}. **{title}**\n   {content}\n   Source: {link}")
            
            summary = "\n\n".join(summary_parts)
            links = [r.get("link", "") for r in results]

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "summary": summary,
                    "links": links,
                    "count": len(results)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Search execution failed: {str(e)}"
            }