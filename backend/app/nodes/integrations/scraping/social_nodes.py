from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional

@register_node("instagram_scrape")
class InstagramScrapeNode(BaseNode):
    """Scrapes Instagram profile or post data using JigsawStack."""
    node_type = "instagram_scrape"
    version = "1.0.0"
    category = "scraping"
    credentials_required = ["jigsawstack_api_key"]

    inputs = {
        "url": {"type": "string", "description": "Instagram Profile or Post URL"},
        "action": {"type": "string", "enum": ["profile", "post"], "default": "profile"}
    }
    outputs = {
        "data": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("jigsawstack_api_key")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "JigsawStack API Key is required."}

            from jigsawstack import JigsawStack, JigsawStackError
            client = JigsawStack(api_key=api_key)

            url = input_data if isinstance(input_data, str) and "instagram.com" in input_data else self.get_config("url")
            
            if not url:
                return {"status": "error", "error": "Instagram URL is required."}

            # JigsawStack scraper for Instagram
            # Note: This is an example based on JigsawStack's scraper capabilities
            resp = client.web.scrape({"url": url})
            
            if not resp.get("success", False):
                return {"status": "error", "error": "JigsawStack scraper failed.", "data": resp}

            return {
                "status": "success",
                "data": resp
            }

        except ImportError:
            return {"status": "error", "error": "jigsawstack library not installed."}
        except Exception as e:
            return {"status": "error", "error": f"Instagram Scrape Failed: {str(e)}"}
