from typing import Any, Dict, Optional, List
from langchain_community.tools import DuckDuckGoSearchRun
from ..base import BaseNode
from ..registry import register_node

@register_node("duckduckgo_search")
class DuckDuckGoSearchNode(BaseNode):
    """
    Search the web using DuckDuckGo. No API key required.
    """
    node_type = "duckduckgo_search"
    version = "1.0.0"
    category = "search"

    inputs = {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {"type": "number", "default": 5}
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

            ddg = DuckDuckGoSearchRun()
            # Note: DuckDuckGoSearchRun returns a single concatenated string of results
            results = ddg.run(query)

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "query": query
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"DuckDuckGo Search Failed: {str(e)}"}
