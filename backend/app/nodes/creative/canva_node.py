"""
Canva Node - Studio Standard
Batch 78: Design & Creative
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("canva_node")
class CanvaNode(BaseNode):
    """
    Search and manage creative assets via the Canva Connect API.
    """
    node_type = "canva_node"
    version = "1.0.0"
    category = "creative"
    credentials_required = ["canva_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_assets",
            "options": ["search_assets", "list_designs", "get_asset_details"],
            "description": "Canva action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query for assets/templates"
        },
        "asset_id": {
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
            creds = await self.get_credential("canva_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Canva OAuth Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Note: Canva Connect API V1
            base_url = "https://api.canva.com/rest/v1"
            action = self.get_config("action", "search_assets")

            async with aiohttp.ClientSession() as session:
                if action == "list_designs":
                    url = f"{base_url}/designs"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "search_assets":
                    query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/asset-uploads" # Representative for asset discovery
                    params = {"query": query} if query else {}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Canva Node Failed: {str(e)}"}
