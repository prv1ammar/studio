"""
RSS Feed Node - Studio Standard (Universal Method)
Batch 99: Web & Utilities (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import feedparser
from ...base import BaseNode
from ...registry import register_node

@register_node("rss_feed_node")
class RSSFeedNode(BaseNode):
    """
    Read RSS and Atom feeds.
    """
    node_type = "rss_feed_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []

    inputs = {
        "url": {
            "type": "string",
            "required": True,
            "description": "Feed URL"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Max entries"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            url = self.get_config("url") or str(input_data)
            limit = int(self.get_config("limit", 10))
            
            if not url:
                return {"status": "error", "error": "url required"}
            
            feed = feedparser.parse(url)
            
            # Extract standard fields
            entries = []
            for entry in feed.entries[:limit]:
                 entry_dict = {
                     "title": entry.get("title"),
                     "link": entry.get("link"),
                     "author": entry.get("author"),
                     "published": entry.get("published"),
                     "summary": entry.get("summary")
                 }
                 entries.append(entry_dict)
            
            return {"status": "success", "data": {"result": entries}}

        except Exception as e:
            return {"status": "error", "error": f"RSS Feed Node Failed: {str(e)}"}
