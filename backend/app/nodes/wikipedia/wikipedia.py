from typing import Any, Dict, Optional, List
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from ..base import BaseNode
from ..registry import register_node

@register_node("wikipedia_search")
class WikipediaNode(BaseNode):
    """
    Search and retrieve summaries from Wikipedia.
    """
    node_type = "wikipedia_search"
    version = "1.0.0"
    category = "search"

    inputs = {
        "query": {"type": "string", "description": "Search query"},
        "lang": {"type": "string", "default": "en"},
        "top_k": {"type": "number", "default": 3},
        "max_chars": {"type": "number", "default": 4000}
    }
    outputs = {
        "results": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            query = str(input_data) if input_data is not None else self.get_config("query")
            if not query:
                return {"status": "error", "error": "Search query is required."}

            wiki = WikipediaAPIWrapper(
                top_k_results=int(self.get_config("top_k", 3)),
                lang=self.get_config("lang", "en"),
                doc_content_chars_max=int(self.get_config("max_chars", 4000))
            )
            
            results = wiki.run(query)

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "query": query
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Wikipedia Search Failed: {str(e)}"}
