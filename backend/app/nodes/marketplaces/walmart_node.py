"""
Walmart Node - Studio Standard (Universal Method)
Batch 87: Retail & Marketplaces
"""
from typing import Any, Dict, Optional, List
import aiohttp
import uuid
from ..base import BaseNode
from ..registry import register_node

@register_node("walmart_node")
class WalmartNode(BaseNode):
    """
    Manage Walmart Marketplace items, orders, and fulfillment.
    """
    node_type = "walmart_node"
    version = "1.0.0"
    category = "marketplaces"
    credentials_required = ["walmart_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_orders',
            'options': [
                {'name': 'List Orders', 'value': 'list_orders'},
                {'name': 'Get Item Inventory', 'value': 'get_item_inventory'},
                {'name': 'List All Items', 'value': 'list_all_items'},
            ],
            'description': 'Walmart action',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_orders",
            "options": ["list_orders", "get_item_inventory", "list_all_items"],
            "description": "Walmart action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication (Client ID/Secret causing Access Token retrieval)
            creds = await self.get_credential("walmart_auth")
            access_token = creds.get("access_token")
            client_id = creds.get("client_id")
            
            if not access_token or not client_id:
                return {"status": "error", "error": "Walmart Access Token and Client ID required."}

            headers = {
                "WM_SEC.ACCESS_TOKEN": access_token,
                "WM_SVC.NAME": "Walmart Marketplace",
                "WM_QOS.CORRELATION_ID": str(uuid.uuid4()),
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://marketplace.walmartapis.com/v3"
            action = self.get_config("action", "list_orders")

            async with aiohttp.ClientSession() as session:
                if action == "list_orders":
                    url = f"{base_url}/orders"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Walmart Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("list", {}).get("elements", {}).get("order", [])}}

                elif action == "list_all_items":
                    url = f"{base_url}/items"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("ItemResponse", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Walmart Node Failed: {str(e)}"}