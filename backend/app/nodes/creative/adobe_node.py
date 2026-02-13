"""
Adobe Creative Cloud Node - Studio Standard
Batch 78: Design & Creative
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("adobe_node")
class AdobeNode(BaseNode):
    """
    Manage Adobe Creative Cloud assets and metadata via the Adobe IDP/Cloud APIs.
    """
    node_type = "adobe_node"
    version = "1.0.0"
    category = "creative"
    credentials_required = ["adobe_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_assets",
            "options": ["list_assets", "get_asset_metadata", "search_stock"],
            "description": "Adobe action"
        },
        "asset_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the specific asset"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("adobe_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not access_token:
                return {"status": "error", "error": "Adobe OAuth Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "x-api-key": api_key or "",
                "Accept": "application/json"
            }
            
            # Adobe representative endpoints for asset discovery
            base_url = "https://cc-api-cp.adobe.io/api/v2"
            action = self.get_config("action", "list_assets")

            async with aiohttp.ClientSession() as session:
                if action == "list_assets":
                    url = f"{base_url}/assets"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "search_stock":
                    # Adobe Stock API
                    url = "https://stock.adobe.io/Rest/Libraries/1/Search/Files"
                    params = {"search_parameters[words]": str(input_data)}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Adobe Node Failed: {str(e)}"}
