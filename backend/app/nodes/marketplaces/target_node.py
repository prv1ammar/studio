"""
Target Node - Studio Standard (Universal Method)
Batch 87: Retail & Marketplaces
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("target_node")
class TargetNode(BaseNode):
    """
    Automated retrieval of Target retail inventory and pricing data.
    """
    node_type = "target_node"
    version = "1.0.0"
    category = "marketplaces"
    credentials_required = ["target_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_products",
            "options": ["search_products", "get_store_inventory", "get_product_price"],
            "description": "Target action"
        },
        "query": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("target_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Target API Key required."}

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API (Leveraging RedSky/Discovery endpoints)
            base_url = "https://redsky.target.com/redsky_aggregations/v1"
            action = self.get_config("action", "search_products")
            query = self.get_config("query") or str(input_data)

            async with aiohttp.ClientSession() as session:
                if action == "search_products":
                    url = f"{base_url}/web/lp_search_v1"
                    params = {
                        "key": api_key,
                        "keyword": query,
                        "page": "/s/" + query,
                        "pricing_store_id": "3991" # Sample Store ID
                    }
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Target API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("search", {}).get("products", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Target Node Failed: {str(e)}"}
