"""
BigCommerce Node - Studio Standard (Universal Method)
Batch 86: E-commerce Core
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("bigcommerce_node")
class BigCommerceNode(BaseNode):
    """
    Manage BigCommerce store data including Orders, Products, and Customers.
    """
    node_type = "bigcommerce_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["bigcommerce_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_products',
            'options': [
                {'name': 'List Products', 'value': 'list_products'},
                {'name': 'List Orders', 'value': 'list_orders'},
                {'name': 'Get Store Info', 'value': 'get_store_info'},
                {'name': 'List Customers', 'value': 'list_customers'},
            ],
            'description': 'BigCommerce action',
        },
        {
            'displayName': 'Store Hash',
            'name': 'store_hash',
            'type': 'string',
            'default': '',
            'description': 'BigCommerce Store Hash (e.g. ac123xyz)',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_products",
            "options": ["list_products", "list_orders", "get_store_info", "list_customers"],
            "description": "BigCommerce action"
        },
        "store_hash": {
            "type": "string",
            "required": True,
            "description": "BigCommerce Store Hash (e.g. ac123xyz)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("bigcommerce_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "BigCommerce X-Auth-Token is required."}

            headers = {
                "X-Auth-Token": access_token,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            store_hash = self.get_config("store_hash")
            base_url = f"https://api.bigcommerce.com/stores/{store_hash}/v3"
            action = self.get_config("action", "list_products")

            async with aiohttp.ClientSession() as session:
                if action == "list_products":
                    url = f"{base_url}/catalog/products"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"BigCommerce Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "list_orders":
                    # Orders are still in V2 API usually, but let's try V3 catalog-aligned or common V2
                    url = f"https://api.bigcommerce.com/stores/{store_hash}/v2/orders"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"BigCommerce Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"BigCommerce Node Failed: {str(e)}"}