"""
Ramp Node - Studio Standard (Universal Method)
Batch 85: SMB Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("ramp_node")
class RampNode(BaseNode):
    """
    Corporate card management and spend control via Ramp REST API.
    """
    node_type = "ramp_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["ramp_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_transactions",
            "options": ["list_transactions", "list_cards", "get_business_info", "list_departments"],
            "description": "Ramp action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number", "optional": True}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("ramp_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Ramp Access Token (OAuth2) is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.ramp.com/developer/v1"
            action = self.get_config("action", "list_transactions")

            async with aiohttp.ClientSession() as session:
                if action == "list_transactions":
                    url = f"{base_url}/transactions"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Ramp API Error: {resp.status}"}
                        res_data = await resp.json()
                        items = res_data.get("data", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "list_cards":
                    url = f"{base_url}/cards"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Ramp API Error: {resp.status}"}
                        res_data = await resp.json()
                        items = res_data.get("data", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "get_business_info":
                    url = f"{base_url}/business"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Ramp API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Ramp Node Failed: {str(e)}"}
