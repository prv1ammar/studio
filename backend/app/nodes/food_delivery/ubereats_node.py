"""
UberEats Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("ubereats_node")
class UberEatsNode(BaseNode):
    """
    Manage restaurant orders and menus via Uber Eats API.
    """
    node_type = "ubereats_node"
    version = "1.0.0"
    category = "food_delivery"
    credentials_required = ["ubereats_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_active_orders",
            "options": ["get_active_orders", "get_order_details", "update_order_status", "get_store_status"],
            "description": "Uber Eats action"
        },
        "order_id": {
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
            creds = await self.get_credential("ubereats_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Uber Eats Access Token required."}

            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            base_url = "https://api.uber.com/v1/eats"
            action = self.get_config("action", "get_active_orders")

            async with aiohttp.ClientSession() as session:
                if action == "get_active_orders":
                    url = f"{base_url}/order/active_orders"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"UberEats Node Failed: {str(e)}"}
