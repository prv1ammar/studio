"""
WooCommerce Node - Studio Standard
Batch 52: Commerce Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("woocommerce_node")
class WooCommerceNode(BaseNode):
    """
    Manage WooCommerce store data via the REST API.
    """
    node_type = "woocommerce_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["woocommerce_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_products",
            "options": ["list_products", "get_product", "list_orders", "get_order", "list_customers"],
            "description": "WooCommerce action to perform"
        },
        "site_url": {
            "type": "string",
            "required": True,
            "description": "Wordpress/WooCommerce site URL (e.g., 'https://shop.example.com')"
        },
        "item_id": {
            "type": "string",
            "optional": True,
            "description": "Specific Product or Order ID"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Number of results to return"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "count": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("woocommerce_auth")
            consumer_key = None
            consumer_secret = None
            site_url = self.get_config("site_url")
            
            if creds:
                consumer_key = creds.get("consumer_key")
                consumer_secret = creds.get("consumer_secret")
                site_url = creds.get("site_url") or site_url
            
            if not consumer_key or not consumer_secret:
                consumer_key = self.get_config("consumer_key")
                consumer_secret = self.get_config("consumer_secret")

            if not all([consumer_key, consumer_secret, site_url]):
                return {"status": "error", "error": "WooCommerce Consumer Key, Secret, and Site URL are required."}

            site_url = site_url.rstrip("/")
            action = self.get_config("action", "list_products")
            limit = int(self.get_config("limit", 10))
            item_id = self.get_config("item_id") or (str(input_data) if isinstance(input_data, (str, int)) else None)

            # Basic Auth for WooCommerce API
            auth = aiohttp.BasicAuth(consumer_key, consumer_secret)
            base_api_url = f"{site_url}/wp-json/wc/v3"

            async with aiohttp.ClientSession(auth=auth) as session:
                if action == "list_products":
                    url = f"{base_api_url}/products"
                    params = {"per_page": limit}
                    async with session.get(url, params=params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"WooCommerce Error: {result}"}
                        return {
                            "status": "success",
                            "data": {"result": result, "count": len(result)}
                        }

                elif action == "get_product":
                    if not item_id:
                         return {"status": "error", "error": "Product ID is required."}
                    url = f"{base_api_url}/products/{item_id}"
                    async with session.get(url) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result, "status": "fetched"}
                        }

                elif action == "list_orders":
                    url = f"{base_api_url}/orders"
                    params = {"per_page": limit}
                    async with session.get(url, params=params) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result, "count": len(result)}
                        }

                elif action == "get_order":
                    if not item_id:
                         return {"status": "error", "error": "Order ID is required."}
                    url = f"{base_api_url}/orders/{item_id}"
                    async with session.get(url) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result, "status": "fetched"}
                        }

                elif action == "list_customers":
                    url = f"{base_api_url}/customers"
                    params = {"per_page": limit}
                    async with session.get(url, params=params) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result, "count": len(result)}
                        }

                return {"status": "error", "error": f"Unsupported WooCommerce action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"WooCommerce execution failed: {str(e)}"}
