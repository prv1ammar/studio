"""
Squarespace Node - Studio Standard (Universal Method)
Batch 86: E-commerce Core
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("squarespace_node")
class SquarespaceNode(BaseNode):
    """
    Manage Squarespace commerce data including Inventory, Orders, and Transactions.
    """
    node_type = "squarespace_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["squarespace_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_orders",
            "options": ["list_orders", "list_inventory", "list_transactions"],
            "description": "Squarespace action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("squarespace_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Squarespace API Key is required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Studio/v3.0.0",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.squarespace.com/1.0/commerce"
            action = self.get_config("action", "list_orders")

            async with aiohttp.ClientSession() as session:
                if action == "list_orders":
                    url = f"{base_url}/orders"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Squarespace Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("result", [])}}

                elif action == "list_inventory":
                    url = f"{base_url}/inventory"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Squarespace Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("inventory", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Squarespace Node Failed: {str(e)}"}
