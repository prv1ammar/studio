from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("firecrawl_action")
class FirecrawlNode(BaseNode):
    """
    Automate Firecrawl actions (Scrape, Crawl, Map).
    Optimized for high-speed web data extraction for RAG pipelines.
    """
    node_type = "firecrawl_action"
    version = "1.1.0"
    category = "scraping"
    credentials_required = ["firecrawl_auth"]

    inputs = {
        "action": {"type": "string", "default": "scrape", "enum": ["scrape", "crawl", "map"]},
        "url": {"type": "string", "description": "Target URL to process"},
        "formats": {"type": "array", "default": ["markdown"]},
        "limit": {"type": "number", "default": 10}
    }
    outputs = {
        "markdown": {"type": "string"},
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from firecrawl import FirecrawlApp
        except ImportError:
            return {"status": "error", "error": "firecrawl-py not installed."}

        # 1. Resolve Auth
        creds = await self.get_credential("firecrawl_auth")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")
        
        if not api_key:
            return {"status": "error", "error": "Firecrawl API Key is required."}

        app = FirecrawlApp(api_key=api_key)
        action = self.get_config("action", "scrape")
        url = str(input_data) if isinstance(input_data, str) and input_data.startswith("http") else self.get_config("url")

        if not url:
            return {"status": "error", "error": "Target URL is required."}

        if action == "scrape":
            formats = self.get_config("formats", ["markdown"])
            result = app.scrape_url(url, params={"formats": formats, "onlyMainContent": True})
            return {
                "status": "success",
                "data": {
                    "markdown": result.get("markdown"),
                    "metadata": result.get("metadata"),
                    "raw": result
                }
            }

        elif action == "crawl":
            limit = int(self.get_config("limit", 10))
            result = app.crawl_url(url, params={"limit": limit, "scrapeOptions": {"formats": ["markdown"]}})
            return {
                "status": "success",
                "data": result
            }

        elif action == "map":
            result = app.map_url(url)
            return {
                "status": "success",
                "data": {
                    "results": result.get("links", []),
                    "count": len(result.get("links", []))
                }
            }

        return {"status": "error", "error": f"Unsupported Firecrawl action: {action}"}
