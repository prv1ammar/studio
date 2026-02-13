"""
URL Loader Node - Studio Standard
Batch 35: Document Loaders
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("url_loader")
class URLLoaderNode(BaseNode):
    """
    Load content from URLs.
    Supports basic HTML loading, Selenium for dynamic content, and Firecrawl integration.
    """
    node_type = "url_loader"
    version = "1.0.0"
    category = "input_output"
    credentials_required = []

    inputs = {
        "url": {
            "type": "string",
            "required": True,
            "description": "URL to scrape"
        },
        "loader_type": {
            "type": "dropdown",
            "default": "WebBaseLoader",
            "options": ["WebBaseLoader", "Selenium", "Firecrawl", "Playwright"],
            "description": "Method to load the URL"
        },
        "max_depth": {
            "type": "number",
            "default": 1,
            "description": "Maximum depth for crawling (Firecrawl only)"
        }
    }

    outputs = {
        "documents": {"type": "array"},
        "text": {"type": "string"},
        "metadata": {"type": "object"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get input URL
            url = input_data if isinstance(input_data, str) else self.get_config("url")
            
            if not url:
                return {"status": "error", "error": "URL is required"}

            # Get configuration
            loader_type = self.get_config("loader_type", "WebBaseLoader")
            max_depth = int(self.get_config("max_depth", 1))

            # Select loader
            if loader_type == "WebBaseLoader":
                try:
                    from langchain_community.document_loaders import WebBaseLoader
                    loader = WebBaseLoader(url)
                    docs = loader.load()
                except ImportError:
                    return {"status": "error", "error": "langchain-community/bs4 not installed. Run: pip install langchain-community beautifulsoup4"}

            elif loader_type == "Selenium":
                try:
                    from langchain_community.document_loaders import SeleniumURLLoader
                    loader = SeleniumURLLoader(urls=[url])
                    docs = loader.load()
                except ImportError:
                    return {"status": "error", "error": "selenium/webdriver not installed. Run: pip install selenium webdriver-manager"}

            elif loader_type == "Playwright":
                try:
                    from langchain_community.document_loaders import PlaywrightLoader
                    loader = PlaywrightLoader(urls=[url], remove_selectors=["header", "footer"])
                    # Playwright requires async loading in some contexts, but let's try synch first
                    docs = await loader.aload()
                except ImportError:
                    return {"status": "error", "error": "playwright not installed. Run: pip install playwright && playwright install"}

            elif loader_type == "Firecrawl":
                # Firecrawl is an external API service
                api_key = self.get_config("firecrawl_api_key")
                if not api_key:
                    # Try getting credential
                    creds = await self.get_credential("firecrawl_auth")
                    api_key = creds.get("api_key") if creds else None
                
                if not api_key:
                    return {"status": "error", "error": "Firecrawl API Key required"}

                try:
                    from langchain_community.document_loaders import FireCrawlLoader
                    loader = FireCrawlLoader(api_key=api_key, url=url, mode="scrape")
                    docs = loader.load()
                except ImportError:
                    return {"status": "error", "error": "Firecrawl SDK not installed"}
            
            else:
                return {"status": "error", "error": f"Unknown loader type: {loader_type}"}

            # Format output documents
            full_text = "\n\n".join([doc.page_content for doc in docs])
            
            output_docs = [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]

            return {
                "status": "success",
                "data": {
                    "documents": output_docs,
                    "text": full_text,
                    "metadata": {
                        "source": url,
                        "pages": len(docs),
                        "loader_used": loader_type
                    }
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"URL Loading failed: {str(e)}"
            }
