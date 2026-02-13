"""
Firecrawl Search & Scraping Node - Studio Standard
Batch 48: Browsing & Search
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("firecrawl_node")
class FirecrawlNode(BaseNode):
    """
    Firecrawl - Scrape, Crawl, and Map websites into Markdown/LLM-ready formats.
    Optimized for RAG pipelines.
    """
    node_type = "firecrawl_node"
    version = "1.1.0"
    category = "search"
    credentials_required = ["firecrawl_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "scrape",
            "options": ["scrape", "crawl", "map"],
            "description": "Scraping action"
        },
        "url": {
            "type": "string",
            "required": True,
            "description": "Target URL to process"
        },
        "formats": {
            "type": "array",
            "default": ["markdown"],
            "description": "Output formats (markdown, html, raw, content)"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Crawl limit (number of pages)"
        },
        "only_main_content": {
            "type": "boolean",
            "default": True,
            "description": "Extract only the main content (skip headers/footers)"
        }
    }

    outputs = {
        "markdown": {"type": "string"},
        "result": {"type": "any"},
        "links": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from firecrawl import FirecrawlApp
        except ImportError:
            return {"status": "error", "error": "firecrawl-py not installed. Run: pip install firecrawl-py"}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("firecrawl_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Firecrawl API Key is required."}

            app = FirecrawlApp(api_key=api_key)
            action = self.get_config("action", "scrape")
            
            # Dynamic URL override
            url = self.get_config("url")
            if isinstance(input_data, str) and input_data.startswith("http"):
                url = input_data

            if not url:
                return {"status": "error", "error": "Target URL is required."}

            result_data = {}

            if action == "scrape":
                formats = self.get_config("formats", ["markdown"])
                only_main = self.get_config("only_main_content", True)
                
                result = app.scrape_url(url, params={
                    "formats": formats, 
                    "onlyMainContent": only_main
                })
                
                result_data = {
                    "markdown": result.get("markdown"),
                    "result": result,
                    "status": "success"
                }

            elif action == "crawl":
                limit = int(self.get_config("limit", 10))
                formats = self.get_config("formats", ["markdown"])
                
                # Crawl returns a job or result depending on SDK version/API
                result = app.smart_crawl_url(url, params={
                    "limit": limit,
                    "scrapeOptions": {"formats": formats}
                })
                
                result_data = {
                    "result": result,
                    "status": "success"
                }

            elif action == "map":
                result = app.map_url(url)
                result_data = {
                    "links": result.get("links", []),
                    "result": result,
                    "status": "success"
                }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except Exception as e:
            return {"status": "error", "error": f"Firecrawl execution failed: {str(e)}"}
