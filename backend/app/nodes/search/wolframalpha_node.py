"""
WolframAlpha Node - Studio Standard (Universal Method)
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("wolframalpha_node")
class WolframAlphaNode(BaseNode):
    """
    Enables queries to WolframAlpha for computational data, facts, and calculations.
    """
    node_type = "wolframalpha_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["wolframalpha_auth"]

    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "The mathematical or computational query"
        },
        "output_format": {
            "type": "dropdown",
            "default": "plaintext",
            "options": ["plaintext", "image", "xml"],
            "description": "The format of the response"
        }
    }

    outputs = {
        "result": {"type": "string"},
        "data": {"type": "dict"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("wolframalpha_auth")
            app_id = creds.get("app_id")
            
            if not app_id:
                return {"status": "error", "error": "WolframAlpha App ID is required"}

            query = self.get_config("query") or str(input_data)
            output_format = self.get_config("output_format", "plaintext")

            # Using WolframAlpha V2 API
            url = "http://api.wolframalpha.com/v2/query"
            params = {
                "input": query,
                "appid": app_id,
                "output": "json" if output_format == "plaintext" else output_format,
            }

            if output_format == "plaintext":
                # Simplified Short Answers API often better for LLMs
                # But V2 query gives more structured data.
                # Let's use the Query API as in their component.
                pass

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return {"status": "error", "error": f"WolframAlpha API returned status {response.status}"}
                    
                    data = await response.json()
            
            # Simple extractor for result
            result = "No result found"
            pods = data.get("queryresult", {}).get("pods", [])
            for pod in pods:
                if pod.get("primary"):
                    subpods = pod.get("subpods", [])
                    if subpods:
                        result = subpods[0].get("plaintext", result)
                        break

            return {
                "status": "success",
                "data": {
                    "result": result,
                    "raw": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"WolframAlpha Query Failed: {str(e)}"}
