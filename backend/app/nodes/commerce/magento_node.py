"""
Magento Node - Studio Standard (Universal Method)
Batch 86: E-commerce Core
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("magento_node")
class MagentoNode(BaseNode):
    """
    Manage Magento (Adobe Commerce) store data including Orders, Products, and Invoices.
    """
    node_type = "magento_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["magento_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_orders",
            "options": ["list_orders", "list_products", "get_product_details", "get_order_details"],
            "description": "Magento action"
        },
        "base_url": {
            "type": "string",
            "required": True,
            "description": "Magento Base URL (e.g. https://yourstore.com)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("magento_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Magento Integration Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = self.get_config("base_url").rstrip("/")
            action = self.get_config("action", "list_orders")

            async with aiohttp.ClientSession() as session:
                # 3. Clear Actions & 4. Standard i/o
                if action == "list_orders":
                    url = f"{base_url}/rest/V1/orders"
                    params = {"searchCriteria[pageSize]": 10}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Magento Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "list_products":
                    url = f"{base_url}/rest/V1/products"
                    params = {"searchCriteria[pageSize]": 10}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Magento Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Magento Node Failed: {str(e)}"}
